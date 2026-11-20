from uuid import UUID

from sqlalchemy import CheckConstraint, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.core.db import Base
from app.core.ids import new_uuid


class TranslationResource(Base):
    __tablename__ = "translation_resources"
    __table_args__ = (
        UniqueConstraint("locale", "key", name="uq_translation_resources_locale_key"),
        CheckConstraint("provenance IN ('system', 'professional')", name="ck_translation_provenance"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    locale: Mapped[str] = mapped_column(String(16), nullable=False)
    key: Mapped[str] = mapped_column(String(200), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    provenance: Mapped[str] = mapped_column(
        String(16), nullable=False, default="system", server_default=text("'system'")
    )
