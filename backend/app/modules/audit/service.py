from hashlib import sha256
from typing import Any
from uuid import UUID

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import TenantContext
from app.core.errors import AppError
from app.modules.audit.models import AuditLog, IdempotencyKey, OutboxEvent


def require_idempotency_key(request: Request) -> str:
    key = request.headers.get("idempotency-key")
    if key is None or not key.strip():
        raise AppError(422, "Idempotency-Key is required", code="validation_error")
    return key.strip()[:128]


def request_hash(payload: object) -> str:
    return sha256(repr(payload).encode("utf-8")).hexdigest()


async def get_idempotent(
    session: AsyncSession, ctx: TenantContext, key: str, digest: str
) -> dict | None:
    row = await session.scalar(
        select(IdempotencyKey).where(
            IdempotencyKey.organization_id == ctx.organization_id,
            IdempotencyKey.key == key,
        )
    )
    if row is None:
        return None
    if row.request_hash != digest:
        raise AppError(409, "Idempotency key was reused with a different payload", code="conflict")
    if row.response_json is None:
        raise AppError(409, "A request with this idempotency key is already in progress", code="conflict")
    return row.response_json


async def store_idempotent(
    session: AsyncSession,
    ctx: TenantContext,
    key: str,
    digest: str,
    response: dict[str, Any],
) -> None:
    row = await session.scalar(
        select(IdempotencyKey).where(
            IdempotencyKey.organization_id == ctx.organization_id,
            IdempotencyKey.key == key,
        )
    )
    if row is None:
        session.add(
            IdempotencyKey(
                organization_id=ctx.organization_id,
                key=key,
                request_hash=digest,
                response_json=response,
            )
        )
        try:
            await session.flush()
        except IntegrityError as exc:
            raise AppError(409, "Idempotency key already used", code="conflict") from exc
        return
    if row.request_hash != digest:
        raise AppError(409, "Idempotency key was reused with a different payload", code="conflict")
    row.response_json = response
    await session.flush()


async def write_outbox(
    session: AsyncSession,
    ctx: TenantContext,
    event_type: str,
    payload: dict,
) -> OutboxEvent:
    event = OutboxEvent(
        organization_id=ctx.organization_id,
        event_type=event_type,
        payload_json=payload,
        status="pending",
    )
    session.add(event)
    await session.flush()
    return event


async def write_audit(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    action: str,
    entity_type: str,
    entity_id: UUID | None,
    after: dict | None = None,
) -> None:
    session.add(
        AuditLog(
            organization_id=ctx.organization_id,
            actor_user_id=ctx.user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            after_json=after,
        )
    )
    await session.flush()
