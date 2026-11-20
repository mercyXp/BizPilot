from typing import TypedDict

from app.modules.demo.catalog import BUSINESSES, business_by_slug

DEMO_EMAIL_DOMAIN = "demo.bizpilot.local"
DEMO_SLUG = "mwamba"
DEMO_ORG_NAME = BUSINESSES[DEMO_SLUG]["name"]
DEMO_LEGAL_NAME = BUSINESSES[DEMO_SLUG]["legal_name"]
DEMO_INDUSTRY = "grocery"
DEMO_MONTHLY_REVENUE = BUSINESSES[DEMO_SLUG]["monthly_revenue"]
DEMO_MONTHLY_EXPENSES = BUSINESSES[DEMO_SLUG]["monthly_expenses"]

BRANCHES = tuple((row["code"], row["name"], row["city"]) for row in BUSINESSES[DEMO_SLUG]["branches"])
CATEGORIES = BUSINESSES[DEMO_SLUG]["categories"]


class DemoRoleSpec(TypedDict):
    key: str
    full_name: str
    role_codes: list[str]
    title: str
    summary: str
    extra_allows: list[str]
    access_all_branches: bool


DEMO_ROLES: tuple[DemoRoleSpec, ...] = (
    {
        "key": "owner",
        "full_name": "Chanda Mwamba",
        "role_codes": ["owner"],
        "title": "Business Owner",
        "summary": "Financial overview, branches, performance and business control.",
        "extra_allows": [],
        "access_all_branches": True,
    },
    {
        "key": "admin",
        "full_name": "Mutale Banda",
        "role_codes": ["org_admin"],
        "title": "Administrator",
        "summary": "Users, permissions, settings and operational oversight.",
        "extra_allows": [],
        "access_all_branches": True,
    },
    {
        "key": "manager",
        "full_name": "Thandiwe Phiri",
        "role_codes": ["manager"],
        "title": "Manager",
        "summary": "Daily operations, stock, staff and sales supervision.",
        "extra_allows": ["expenses.create", "expenses.approve", "users.manage"],
        "access_all_branches": False,
    },
    {
        "key": "accountant",
        "full_name": "Lillian Ngoma",
        "role_codes": ["accountant"],
        "title": "Accountant",
        "summary": "Journals, expenses, payroll view and financial reports.",
        "extra_allows": [],
        "access_all_branches": True,
    },
    {
        "key": "salesperson",
        "full_name": "Kabwe Zulu",
        "role_codes": ["sales", "cashier"],
        "title": "Salesperson / Cashier",
        "summary": "POS, transactions, receipts and customer sales.",
        "extra_allows": [],
        "access_all_branches": False,
    },
    {
        "key": "stock",
        "full_name": "Nchimunya Tembo",
        "role_codes": ["inventory_manager"],
        "title": "Stock Controller",
        "summary": "Inventory, stock movements and replenishment.",
        "extra_allows": ["purchases.receive", "purchases.view"],
        "access_all_branches": False,
    },
    {
        "key": "auditor",
        "full_name": "Lweendo Siame",
        "role_codes": ["viewer"],
        "title": "Auditor / Read-only Viewer",
        "summary": "Reports, financial records and audit trails without editing.",
        "extra_allows": [],
        "access_all_branches": True,
    },
)

SCALE_COMPACT = {
    "products": 12,
    "customers": 8,
    "suppliers": 4,
    "sales": 10,
    "purchase_orders": 4,
    "expenses": 6,
    "stock_movements": 12,
    "employees": 8,
    "journals": 24,
    "notifications": 6,
    "audit_logs": 20,
}


def demo_email(slug: str, role_key: str) -> str:
    return f"{slug}.{role_key}@{DEMO_EMAIL_DOMAIN}"


def role_by_key(key: str) -> DemoRoleSpec:
    for spec in DEMO_ROLES:
        if spec["key"] == key:
            return spec
    raise KeyError(key)


def scale_for(slug: str, compact: bool) -> dict[str, int]:
    if compact:
        return dict(SCALE_COMPACT)
    spec = business_by_slug(slug)
    if spec["slug"] == "mwamba":
        products = spec["products"]
    else:
        products = 48 if spec["products"] >= 80 else max(12, spec["products"])
    return {
        "products": products,
        "customers": max(8, spec["employees"]),
        "suppliers": 6,
        "sales": 24,
        "purchase_orders": 8,
        "expenses": 10,
        "stock_movements": 16,
        "employees": spec["employees"],
        "journals": 40,
        "notifications": 8,
        "audit_logs": 24,
    }
