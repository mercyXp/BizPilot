from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=200)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class OrganizationIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    legal_name: str | None = Field(default=None, max_length=200)


class OrganizationOut(BaseModel):
    id: UUID
    name: str
    status: str
    membership_id: UUID | None = None


class BranchIn(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=200)
    phone: str | None = Field(default=None, max_length=32)


class BranchOut(BaseModel):
    id: UUID
    code: str
    name: str
    is_active: bool


class MembershipIn(BaseModel):
    email: EmailStr
    role_code: str = Field(min_length=1, max_length=64)
    access_all_branches: bool = False
    branch_ids: list[UUID] = []


class MembershipStatusIn(BaseModel):
    status: str = Field(pattern="^(active|suspended)$")


class RoleAssignIn(BaseModel):
    role_code: str = Field(min_length=1, max_length=64)


class OverrideIn(BaseModel):
    permission_code: str = Field(min_length=1, max_length=128)
    effect: str = Field(pattern="^(allow|deny)$")


class BranchGrantsIn(BaseModel):
    access_all_branches: bool
    branch_ids: list[UUID] = []


class MembershipOut(BaseModel):
    id: UUID
    user_id: UUID
    email: EmailStr
    full_name: str
    status: str
    access_all_branches: bool
    role_codes: list[str]
    branch_ids: list[UUID]


class AuthorizationContextOut(BaseModel):
    organization_id: UUID
    membership_id: UUID
    branch_id: UUID | None
    access_all_branches: bool
    branch_ids: list[UUID]
    permissions: list[str]
    is_platform_admin: bool


class GateOut(BaseModel):
    status: str
    action: str
    effect: str
