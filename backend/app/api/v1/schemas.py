from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=200)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
    totp_code: str | None = Field(default=None, min_length=6, max_length=8)


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    email_verified: bool = False
    totp_enabled: bool = False


class RegisterOut(UserOut):
    verification_token: str | None = None


class TokenOut(BaseModel):
    access_token: str | None = None
    token_type: str = "bearer"
    email_verified: bool = False
    totp_required: bool = False


class VerifyEmailIn(BaseModel):
    token: str = Field(min_length=8)


class EmailIn(BaseModel):
    email: EmailStr


class PasswordResetConfirmIn(BaseModel):
    token: str = Field(min_length=8)
    password: str = Field(min_length=8, max_length=128)


class TotpConfirmIn(BaseModel):
    code: str = Field(min_length=6, max_length=8)


class TotpDisableIn(BaseModel):
    password: str = Field(min_length=1)
    code: str = Field(min_length=6, max_length=8)


class OrganizationIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    legal_name: str | None = Field(default=None, max_length=200)
    industry_code: str = "general"
    timezone: str = "Africa/Lusaka"
    base_currency_code: str = Field(default="ZMW", min_length=3, max_length=3)
    country_code: str = Field(default="ZM", min_length=2, max_length=2)


class BranchSeedIn(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=200)
    phone: str | None = None


class WarehouseSeedIn(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=200)


class OnboardingIn(OrganizationIn):
    branch: BranchSeedIn
    warehouse: WarehouseSeedIn | None = None


class OrganizationOut(BaseModel):
    id: UUID
    name: str
    legal_name: str | None = None
    status: str
    industry_code: str | None = None
    timezone: str | None = None
    base_currency_code: str | None = None
    country_code: str | None = None
    membership_id: UUID | None = None
    branch_id: UUID | None = None
    warehouse_id: UUID | None = None


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


class InvitationIn(BaseModel):
    email: EmailStr
    role_codes: list[str] = Field(min_length=1)
    branch_ids: list[UUID] = []
    access_all_branches: bool = False


class InvitationAcceptIn(BaseModel):
    token: str = Field(min_length=8)


class InvitationOut(BaseModel):
    id: UUID
    email: EmailStr
    access_all_branches: bool
    accepted: bool
    token: str | None = None


class WarehouseIn(BaseModel):
    branch_id: UUID
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=200)
    is_default: bool = False


class WarehouseOut(BaseModel):
    id: UUID
    branch_id: UUID
    code: str
    name: str
    is_default: bool
    is_active: bool


class SettingsOut(BaseModel):
    organization_id: UUID
    settings: dict


class SettingsIn(BaseModel):
    settings: dict


class IndustryOut(BaseModel):
    id: UUID
    code: str
    name: str
    default_modules: dict
    default_settings: dict


class UomIn(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=200)
    is_integer: bool = True


class UomOut(BaseModel):
    id: UUID
    code: str
    name: str
    is_integer: bool


class ProductIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    type: str = Field(pattern="^(goods|service|bundle)$")
    uom_id: UUID
    sku: str | None = None
    category_id: UUID | None = None
    tax_category_id: UUID | None = None
    track_inventory: bool | None = None
    track_batches: bool | None = None
    track_expiry: bool | None = None


class ProductOut(BaseModel):
    id: UUID
    name: str
    type: str
    sku: str | None
    track_inventory: bool
    track_batches: bool
    is_active: bool


class VariantIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    sku: str | None = None
    attributes: dict = {}


class VariantOut(BaseModel):
    id: UUID
    product_id: UUID
    name: str
    sku: str | None
    attributes: dict


class PriceIn(BaseModel):
    variant_id: UUID
    amount: float
    currency_code: str = "ZMW"
    branch_id: UUID | None = None
    price_list_code: str = "retail"


class PriceOut(BaseModel):
    id: UUID
    variant_id: UUID
    branch_id: UUID | None
    amount: float
    currency_code: str
    price_list_code: str


class AdjustmentIn(BaseModel):
    warehouse_id: UUID
    variant_id: UUID
    qty_delta: float
    unit_cost: float = 0
    batch_id: UUID | None = None
    source_type: str = "adjustment"


class MovementOut(BaseModel):
    id: UUID
    warehouse_id: UUID
    variant_id: UUID
    qty_delta: float
    unit_cost: float
    movement_type: str
    source_type: str


class BalanceOut(BaseModel):
    warehouse_id: UUID
    variant_id: UUID
    batch_id: UUID | None
    qty_on_hand: float
    avg_unit_cost: float


class BatchIn(BaseModel):
    variant_id: UUID
    batch_number: str = Field(min_length=1, max_length=64)


class BatchOut(BaseModel):
    id: UUID
    variant_id: UUID
    batch_number: str


class TransferItemIn(BaseModel):
    variant_id: UUID
    qty: float
    batch_id: UUID | None = None


class TransferIn(BaseModel):
    source_warehouse_id: UUID
    dest_warehouse_id: UUID
    items: list[TransferItemIn] = Field(min_length=1)


class TransferReceiptIn(BaseModel):
    item_id: UUID
    qty: float


class TransferReceiveIn(BaseModel):
    items: list[TransferReceiptIn] = Field(min_length=1)


class TransferOut(BaseModel):
    id: UUID
    document_number: str
    status: str
    source_warehouse_id: UUID
    dest_warehouse_id: UUID


class CountItemIn(BaseModel):
    variant_id: UUID
    counted_qty: float | None = None
    batch_id: UUID | None = None


class CountIn(BaseModel):
    warehouse_id: UUID
    items: list[CountItemIn] = Field(min_length=1)


class CountOut(BaseModel):
    id: UUID
    warehouse_id: UUID
    status: str
