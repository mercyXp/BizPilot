from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import OrganizationIn, OrganizationOut
from app.core.db import get_db
from app.modules.authorization.catalog import build_role_seed
from app.modules.authorization.deps import get_current_user
from app.modules.identity.models import User
from app.modules.tenancy.service import create_organization, list_organizations

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("", response_model=OrganizationOut, status_code=201)
async def create_org(
    body: OrganizationIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> OrganizationOut:
    organization, membership = await create_organization(
        session,
        user,
        name=body.name,
        legal_name=body.legal_name,
        roles_payload=build_role_seed(),
    )
    return OrganizationOut(
        id=organization.id,
        name=organization.name,
        status=organization.status,
        membership_id=membership.id,
    )


@router.get("", response_model=list[OrganizationOut])
async def list_orgs(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[OrganizationOut]:
    rows = await list_organizations(session, user)
    return [OrganizationOut(id=row.id, name=row.name, status=row.status) for row in rows]
