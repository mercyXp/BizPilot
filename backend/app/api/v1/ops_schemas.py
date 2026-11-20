from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class CustomerIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    code: str | None = None
    phone: str | None = None
    email: str | None = None
    credit_limit: float = 0


class CustomerOut(BaseModel):
    id: UUID
    code: str
    name: str
    is_active: bool


class CreditOut(BaseModel):
    customer_id: UUID
    credit_limit: float
    balance: float
    status: str


class CreditIn(BaseModel):
    credit_limit: float


class NoteIn(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


class PosSessionIn(BaseModel):
    warehouse_id: UUID
    opening_float: float = 0


class PosSessionOut(BaseModel):
    id: UUID
    branch_id: UUID
    warehouse_id: UUID
    status: str
    opening_float: float
    closing_counted_cash: float | None = None


class CashMovementIn(BaseModel):
    type: str = Field(pattern="^(in|out)$")
    amount: float
    reason: str | None = None


class CloseSessionIn(BaseModel):
    counted_cash: float


class SaleItemIn(BaseModel):
    variant_id: UUID
    qty: float
    discount_amount: float = 0
    tax_rate_id: UUID | None = None
    batch_id: UUID | None = None


class PaymentIn(BaseModel):
    method: str = Field(pattern="^(cash|mobile_money|card|bank_transfer|store_credit)$")
    amount: float
    provider: str | None = None


class SaleCompleteIn(BaseModel):
    items: list[SaleItemIn] = Field(min_length=1)
    payments: list[PaymentIn] = Field(min_length=1)
    customer_id: UUID | None = None


class SaleOut(BaseModel):
    id: UUID
    document_number: str
    status: str
    subtotal: float
    tax_total: float
    total: float
    customer_id: UUID | None = None


class PaymentOut(BaseModel):
    id: UUID
    method: str
    status: str
    amount: float
    provider: str | None = None
    provider_ref: str | None = None


class RefundItemIn(BaseModel):
    sale_item_id: UUID
    qty: float


class RefundIn(BaseModel):
    items: list[RefundItemIn] = Field(min_length=1)
    reason: str | None = None
    restock: bool = True


class RefundOut(BaseModel):
    id: UUID
    sale_id: UUID
    status: str
    total: float
    restock: bool


class ReceiptOut(BaseModel):
    id: UUID
    sale_id: UUID
    document_number: str
    payload_json: dict


class SupplierIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    code: str | None = None
    payment_terms_days: int = 0


class SupplierOut(BaseModel):
    id: UUID
    code: str
    name: str


class LineQtyIn(BaseModel):
    variant_id: UUID
    qty: float
    unit_cost: float = 0


class RequisitionIn(BaseModel):
    items: list[LineQtyIn] = Field(min_length=1)


class PurchaseOrderIn(BaseModel):
    supplier_id: UUID
    items: list[LineQtyIn] = Field(min_length=1)


class DocumentOut(BaseModel):
    id: UUID
    document_number: str
    status: str


class GrnItemIn(BaseModel):
    purchase_order_item_id: UUID
    qty_accepted: float
    qty_rejected: float = 0
    batch_id: UUID | None = None


class GrnIn(BaseModel):
    purchase_order_id: UUID
    warehouse_id: UUID
    items: list[GrnItemIn] = Field(min_length=1)


class SupplierInvoiceIn(BaseModel):
    supplier_id: UUID
    purchase_order_id: UUID | None = None
    subtotal: float
    tax_total: float = 0
    document_number: str | None = None


class SupplierPaymentIn(BaseModel):
    supplier_id: UUID
    invoice_id: UUID | None = None
    amount: float
    method: str = "cash"


class JournalLineIn(BaseModel):
    account_id: UUID
    debit: float = 0
    credit: float = 0
    memo: str | None = None
    branch_id: UUID | None = None


class ManualJournalIn(BaseModel):
    description: str = Field(min_length=1, max_length=255)
    lines: list[JournalLineIn] = Field(min_length=2)


class JournalOut(BaseModel):
    id: UUID
    entry_number: str
    status: str
    source_type: str
    description: str


class AccountOut(BaseModel):
    id: UUID
    code: str
    name: str
    type: str


class PeriodOut(BaseModel):
    id: UUID
    name: str
    starts_on: date
    ends_on: date
    status: str


class ExpenseIn(BaseModel):
    vendor_name: str = Field(min_length=1, max_length=200)
    amount: float
    tax_amount: float = 0
    incurred_on: date
    payment_method: str = "cash"
    account_id: UUID | None = None


class ExpenseOut(BaseModel):
    id: UUID
    document_number: str
    status: str
    amount: float


class BankAccountIn(BaseModel):
    account_id: UUID
    name: str = Field(min_length=1, max_length=200)
    bank_name: str | None = None


class BankAccountOut(BaseModel):
    id: UUID
    name: str
    account_id: UUID


class BankTxIn(BaseModel):
    bank_account_id: UUID
    posted_on: date
    amount: float
    description: str | None = None
    external_ref: str | None = None


class BankTxOut(BaseModel):
    id: UUID
    amount: float
    status: str


class ReconItemIn(BaseModel):
    bank_transaction_id: UUID
    journal_line_id: UUID | None = None


class ReconIn(BaseModel):
    bank_account_id: UUID
    statement_date: date
    items: list[ReconItemIn] = Field(min_length=1)


class EmployeeIn(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    hire_on: date
    job_title: str | None = None
    department_id: UUID | None = None
    base_salary: float
    employee_number: str | None = None


class EmployeeOut(BaseModel):
    id: UUID
    employee_number: str
    full_name: str
    status: str
    base_salary: float


class LeaveIn(BaseModel):
    employee_id: UUID
    type: str = Field(min_length=1, max_length=32)
    starts_on: date
    ends_on: date


class LeaveOut(BaseModel):
    id: UUID
    employee_id: UUID
    status: str
    type: str


class LeaveDecisionIn(BaseModel):
    status: str = Field(pattern="^(approved|rejected)$")


class ComponentIn(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=200)
    kind: str = Field(pattern="^(earning|deduction|employer_contribution)$")
    calculation: dict
    effective_from: date | None = None
    effective_to: date | None = None


class ComponentOut(BaseModel):
    id: UUID
    code: str
    name: str
    kind: str
    calculation: dict


class PayrollPeriodIn(BaseModel):
    starts_on: date
    ends_on: date


class PayrollPeriodOut(BaseModel):
    id: UUID
    starts_on: date
    ends_on: date
    status: str


class PayrollRunIn(BaseModel):
    period_id: UUID


class PayrollRunOut(BaseModel):
    id: UUID
    period_id: UUID
    status: str


class TaxRateIn(BaseModel):
    code: str
    name: str
    rate: float
    inclusive: bool = False


class TaxRateOut(BaseModel):
    id: UUID
    code: str
    name: str
    rate: float
    inclusive: bool
