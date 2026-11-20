from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.email import send_email
from app.core.errors import ApiError
from app.core.ids import new_uuid
from app.core.security import hash_token, new_url_token
from app.core.tenancy import apply_rls
from app.models.audit import AuditLog
from app.models.invitation import Invitation
from app.models.organization import Organization, OrganizationMembership
from app.models.user import User


async def _audit(
    session: AsyncSession,
    *,
    actor_user_id: UUID | None,
    action: str,
    entity_type: str,
    entity_id: str,
    organization_id: UUID | None = None,
) -> None:
    session.add(
        AuditLog(
            id=new_uuid(),
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
        )
    )


def require_verified(user: User) -> None:
    if user.email_verified_at is None:
        raise ApiError(403, "email_unverified", "Verify your email before creating an organization")


async def create_organization(
    session: AsyncSession,
    user: User,
    *,
    name: str,
    legal_name: str | None,
) -> tuple[Organization, OrganizationMembership]:
    require_verified(user)
    await apply_rls(session, user.id)

    org = Organization(
        id=new_uuid(),
        name=name.strip(),
        legal_name=legal_name.strip() if legal_name else None,
        created_by_user_id=user.id,
    )
    session.add(org)
    await session.flush()

    membership = OrganizationMembership(
        id=new_uuid(),
        organization_id=org.id,
        user_id=user.id,
        status="active",
        is_owner=True,
        access_all_branches=True,
    )
    session.add(membership)
    await session.flush()
    await _audit(
        session,
        actor_user_id=user.id,
        action="organization.create",
        entity_type="organization",
        entity_id=str(org.id),
        organization_id=org.id,
    )
    return org, membership


async def list_memberships(
    session: AsyncSession, user: User
) -> list[tuple[OrganizationMembership, Organization]]:
    await apply_rls(session, user.id)
    rows = await session.execute(
        select(OrganizationMembership, Organization)
        .join(Organization, Organization.id == OrganizationMembership.organization_id)
        .where(
            OrganizationMembership.user_id == user.id,
            OrganizationMembership.status == "active",
        )
        .order_by(Organization.created_at.asc())
    )
    return list(rows.all())


async def get_active_membership(
    session: AsyncSession, user: User, organization_id: UUID
) -> OrganizationMembership:
    await apply_rls(session, user.id, organization_id)
    membership = await session.scalar(
        select(OrganizationMembership).where(
            OrganizationMembership.user_id == user.id,
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.status == "active",
        )
    )
    if membership is None:
        raise ApiError(403, "permission_denied", "You do not have access to this organization")
    return membership


async def get_organization(session: AsyncSession, organization_id: UUID) -> Organization:
    org = await session.get(Organization, organization_id)
    if org is None or org.status != "active":
        raise ApiError(404, "not_found", "Organization not found")
    return org


async def create_invitation(
    session: AsyncSession,
    settings: Settings,
    *,
    user: User,
    membership: OrganizationMembership,
    organization: Organization,
    email: str,
) -> tuple[Invitation, str]:
    if not membership.is_owner:
        raise ApiError(403, "permission_denied", "Only organization owners can invite members")

    email_norm = email.strip().lower()
    if email_norm == user.email:
        raise ApiError(400, "validation_error", "You already belong to this organization")

    existing_user = await session.scalar(select(User).where(User.email == email_norm))
    if existing_user is not None:
        existing_membership = await session.scalar(
            select(OrganizationMembership).where(
                OrganizationMembership.organization_id == organization.id,
                OrganizationMembership.user_id == existing_user.id,
                OrganizationMembership.status == "active",
            )
        )
        if existing_membership is not None:
            raise ApiError(409, "conflict", "That user is already a member")

    pending = await session.scalar(
        select(Invitation).where(
            Invitation.organization_id == organization.id,
            Invitation.email == email_norm,
            Invitation.accepted_at.is_(None),
            Invitation.expires_at > datetime.now(UTC),
        )
    )
    if pending is not None:
        raise ApiError(409, "conflict", "An invitation is already pending for that email")

    raw_token = new_url_token()
    invitation = Invitation(
        id=new_uuid(),
        organization_id=organization.id,
        email=email_norm,
        token_hash=hash_token(raw_token),
        invited_by_user_id=user.id,
        expires_at=datetime.now(UTC) + timedelta(days=settings.invitation_days),
    )
    session.add(invitation)
    await session.flush()
    accept_url = f"{settings.public_app_url.rstrip('/')}/accept-invite?token={raw_token}"
    await send_email(
        session,
        to_email=email_norm,
        template="organization_invite",
        payload={
            "accept_url": accept_url,
            "token": raw_token,
            "organization_name": organization.name,
        },
        organization_id=organization.id,
    )
    await _audit(
        session,
        actor_user_id=user.id,
        action="organization.invite",
        entity_type="invitation",
        entity_id=str(invitation.id),
        organization_id=organization.id,
    )
    return invitation, raw_token


async def lookup_invitation(session: AsyncSession, token: str) -> Invitation | None:
    result = await session.execute(
        text(
            "SELECT id, organization_id, email, token_hash, invited_by_user_id, "
            "expires_at, accepted_at, created_at "
            "FROM lookup_invitation_by_hash(:token_hash)"
        ),
        {"token_hash": hash_token(token)},
    )
    row = result.mappings().first()
    if row is None or row["id"] is None:
        return None
    invitation = Invitation(
        id=row["id"],
        organization_id=row["organization_id"],
        email=row["email"],
        token_hash=row["token_hash"],
        invited_by_user_id=row["invited_by_user_id"],
        expires_at=row["expires_at"],
        accepted_at=row["accepted_at"],
        created_at=row["created_at"],
    )
    return invitation


async def accept_invitation(
    session: AsyncSession, user: User, token: str
) -> tuple[Organization, OrganizationMembership]:
    invitation = await lookup_invitation(session, token)
    if (
        invitation is None
        or invitation.accepted_at is not None
        or invitation.expires_at < datetime.now(UTC)
    ):
        raise ApiError(400, "invalid_token", "This invitation is invalid or has expired")
    if invitation.email != user.email:
        raise ApiError(403, "permission_denied", "This invitation was sent to a different email address")

    await apply_rls(session, user.id, invitation.organization_id)
    existing = await session.scalar(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == invitation.organization_id,
            OrganizationMembership.user_id == user.id,
        )
    )
    if existing and existing.status == "active":
        raise ApiError(409, "conflict", "You already belong to this organization")

    if existing:
        existing.status = "active"
        membership = existing
    else:
        membership = OrganizationMembership(
            id=new_uuid(),
            organization_id=invitation.organization_id,
            user_id=user.id,
            status="active",
            is_owner=False,
            access_all_branches=True,
        )
        session.add(membership)

    db_invite = await session.get(Invitation, invitation.id)
    if db_invite is not None:
        db_invite.accepted_at = datetime.now(UTC)

    org = await get_organization(session, invitation.organization_id)
    await session.flush()
    await _audit(
        session,
        actor_user_id=user.id,
        action="organization.join",
        entity_type="organization",
        entity_id=str(org.id),
        organization_id=org.id,
    )
    return org, membership
