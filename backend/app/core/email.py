import json
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ids import new_uuid
from app.models.email import OutboundEmail

logger = logging.getLogger(__name__)


async def send_email(
    session: AsyncSession,
    *,
    to_email: str,
    template: str,
    payload: dict,
    organization_id: UUID | None = None,
) -> OutboundEmail:
    record = OutboundEmail(
        id=new_uuid(),
        organization_id=organization_id,
        to_email=to_email,
        template=template,
        payload_json=json.dumps(payload),
    )
    session.add(record)
    logger.info("outbound_email template=%s to=%s", template, to_email)
    return record
