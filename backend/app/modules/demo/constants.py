from typing import TypedDict


class DemoRoleSpec(TypedDict):
    key: str
    email: str
    full_name: str
    role_codes: list[str]
    title: str
    summary: str
    extra_allows: list[str]


DEMO_SLUG = "mwamba"
DEMO_ORG_NAME = "Mwamba Retail Group"
DEMO_LEGAL_NAME = "Mwamba Retail Group Limited"
DEMO_EMAIL_DOMAIN = "demo.bizpilot.local"
DEMO_INDUSTRY = "general"
DEMO_MONTHLY_REVENUE = 248_650
DEMO_MONTHLY_EXPENSES = 76_420

BRANCHES: tuple[tuple[str, str, str], ...] = (
    ("LSK", "Lusaka Central", "Lusaka"),
    ("CHE", "Chelstone", "Lusaka"),
    ("KTW", "Kitwe", "Kitwe"),
)

CATEGORIES: tuple[str, ...] = (
    "Maize meal",
    "Cooking oil",
    "Sugar",
    "Rice",
    "Beans",
    "Kapenta",
    "Fresh produce",
    "Butchery",
    "Dairy",
    "Bakery",
    "Beverages",
    "Soft drinks",
    "Water",
    "Snacks",
    "Household",
    "Cleaning",
    "Personal care",
    "Baby",
    "Pharmacy OTC",
    "Stationery",
    "Airtime",
    "Charcoal",
    "Hardware mini",
    "Frozen",
    "Salt and spices",
)

DEMO_ROLES: tuple[DemoRoleSpec, ...] = (
    {
        "key": "owner",
        "email": f"owner@{DEMO_EMAIL_DOMAIN}",
        "full_name": "Chanda Mwamba",
        "role_codes": ["owner"],
        "title": "Business Owner",
        "summary": "Financial overview, branches, performance and business control.",
        "extra_allows": [],
    },
    {
        "key": "admin",
        "email": f"admin@{DEMO_EMAIL_DOMAIN}",
        "full_name": "Mutale Banda",
        "role_codes": ["org_admin"],
        "title": "Administrator",
        "summary": "Users, permissions, settings and operational oversight.",
        "extra_allows": [],
    },
    {
        "key": "manager",
        "email": f"manager@{DEMO_EMAIL_DOMAIN}",
        "full_name": "Thandiwe Phiri",
        "role_codes": ["manager"],
        "title": "Manager",
        "summary": "Daily operations, stock, staff and sales supervision.",
        "extra_allows": ["expenses.create", "expenses.approve", "users.manage"],
    },
    {
        "key": "salesperson",
        "email": f"sales@{DEMO_EMAIL_DOMAIN}",
        "full_name": "Kabwe Zulu",
        "role_codes": ["sales", "cashier"],
        "title": "Salesperson",
        "summary": "POS, transactions, receipts and customer sales.",
        "extra_allows": [],
    },
    {
        "key": "stock",
        "email": f"stock@{DEMO_EMAIL_DOMAIN}",
        "full_name": "Nchimunya Tembo",
        "role_codes": ["inventory_manager"],
        "title": "Stock Controller",
        "summary": "Inventory, stock movements and replenishment.",
        "extra_allows": ["purchases.receive", "purchases.view"],
    },
    {
        "key": "auditor",
        "email": f"auditor@{DEMO_EMAIL_DOMAIN}",
        "full_name": "Lweendo Siame",
        "role_codes": ["viewer"],
        "title": "Auditor / Viewer",
        "summary": "Reports, financial records and audit trails without editing.",
        "extra_allows": [],
    },
)

SCALE_FULL = {
    "products": 1250,
    "customers": 180,
    "suppliers": 35,
    "sales": 500,
    "purchase_orders": 100,
    "expenses": 150,
    "stock_movements": 350,
    "employees": 15,
    "journals": 1000,
    "notifications": 30,
    "audit_logs": 200,
}

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


def role_by_key(key: str) -> DemoRoleSpec:
    for spec in DEMO_ROLES:
        if spec["key"] == key:
            return spec
    raise KeyError(key)
