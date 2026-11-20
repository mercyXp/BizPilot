from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class CreateOrganizationRequest(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    legal_name: str | None = Field(default=None, max_length=200)


class OrganizationPublic(BaseModel):
    id: UUID
    name: str
    legal_name: str | None
    country_code: str
    base_currency_code: str
    timezone: str
    status: str
    is_owner: bool
    membership_id: UUID
    created_at: datetime


class CreateInvitationRequest(BaseModel):
    email: EmailStr


class InvitationPublic(BaseModel):
    id: UUID
    email: str
    organization_id: UUID
    organization_name: str | None = None
    expires_at: datetime
    accepted: bool


class AcceptInvitationRequest(BaseModel):
    token: str = Field(min_length=16)
