from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import TenantContext


@dataclass(frozen=True)
class JournalLineCommand:
    account_id: UUID
    debit: Decimal
    credit: Decimal
    branch_id: UUID | None = None
    party_type: str | None = None
    party_id: UUID | None = None
    tax_rate_id: UUID | None = None
    memo: str | None = None


@dataclass(frozen=True)
class PostCommand:
    source_type: str
    source_id: UUID
    description: str
    occurred_at: datetime
    branch_id: UUID | None
    lines: tuple[JournalLineCommand, ...]
    idempotency_key: str | None = None
    reverses_journal_id: UUID | None = None


class PostingEngine(Protocol):
    async def post(
        self, session: AsyncSession, ctx: TenantContext, command: PostCommand
    ) -> object: ...
