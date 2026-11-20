"""Permission catalogue and system role templates.

Templates are copied into each organization when it is created. Platform
permissions are never copied onto an organization role.

Cashier `sales.refund` is the limited refund grant from the Phase 0 matrix.
Amount and age limits arrive with the sales module. Cashiers still cannot
post journals, and viewers cannot adjust stock.
"""

from app.core.ids import new_uuid

PERMISSIONS: tuple[tuple[str, str, str], ...] = (
    ("org.manage", "organization", "Manage organization profile and lifecycle"),
    ("org.settings", "organization", "Update organization settings"),
    ("branches.manage", "organization", "Create and update branches"),
    ("users.invite", "identity", "Invite users"),
    ("users.manage", "identity", "Manage memberships, roles, and branch grants"),
    ("catalogue.view", "catalogue", "View products, variants, and prices"),
    ("catalogue.manage", "catalogue", "Manage products, variants, and prices"),
    ("sales.create", "sales", "Create sales"),
    ("sales.view", "sales", "View sales"),
    ("sales.refund", "sales", "Refund sales"),
    ("pos.session.open", "sales", "Open a POS session"),
    ("pos.session.close", "sales", "Close a POS session"),
    ("inventory.view", "inventory", "View stock"),
    ("inventory.adjust", "inventory", "Adjust stock"),
    ("inventory.transfer", "inventory", "Transfer stock"),
    ("inventory.count", "inventory", "Count stock"),
    ("purchases.create", "purchasing", "Create purchase documents"),
    ("purchases.approve", "purchasing", "Approve purchases"),
    ("purchases.receive", "purchasing", "Receive goods"),
    ("purchases.pay", "purchasing", "Pay suppliers"),
    ("customers.manage", "crm", "Manage customers"),
    ("customers.credit", "crm", "Manage customer credit"),
    ("accounting.journal.create", "accounting", "Create draft journals"),
    ("accounting.journal.post", "accounting", "Post journals"),
    ("accounting.reports.view", "accounting", "View financial reports"),
    ("accounting.period.close", "accounting", "Close accounting periods"),
    ("expenses.create", "expenses", "Create expenses"),
    ("expenses.approve", "expenses", "Approve expenses"),
    ("employees.manage", "payroll", "Manage employees"),
    ("payroll.process", "payroll", "Process payroll"),
    ("payroll.view", "payroll", "View payroll"),
    ("reports.view", "reporting", "View operational reports"),
    ("ai.use", "ai", "Use read-only AI tools"),
    ("ai.act", "ai", "Create AI drafts"),
    ("platform.orgs.manage", "platform", "Platform organization administration"),
)

PLATFORM_CODES: frozenset[str] = frozenset(
    code for code, module, _description in PERMISSIONS if module == "platform"
)
TENANT_CODES: frozenset[str] = frozenset(
    code for code, _module, _description in PERMISSIONS if code not in PLATFORM_CODES
)

_ORG_ADMIN: frozenset[str] = frozenset(
    {
        "org.settings",
        "branches.manage",
        "users.invite",
        "users.manage",
        "catalogue.view",
        "catalogue.manage",
        "sales.create",
        "sales.view",
        "sales.refund",
        "pos.session.open",
        "pos.session.close",
        "inventory.view",
        "inventory.adjust",
        "inventory.transfer",
        "inventory.count",
        "purchases.create",
        "purchases.approve",
        "purchases.receive",
        "purchases.pay",
        "customers.manage",
        "customers.credit",
        "accounting.reports.view",
        "expenses.create",
        "expenses.approve",
        "employees.manage",
        "payroll.view",
        "reports.view",
        "ai.use",
        "ai.act",
    }
)
_MANAGER: frozenset[str] = frozenset(
    {
        "catalogue.view",
        "catalogue.manage",
        "sales.create",
        "sales.view",
        "sales.refund",
        "pos.session.open",
        "pos.session.close",
        "inventory.view",
        "inventory.adjust",
        "inventory.transfer",
        "inventory.count",
        "purchases.create",
        "purchases.approve",
        "purchases.receive",
        "customers.manage",
        "accounting.reports.view",
        "reports.view",
        "ai.use",
        "ai.act",
    }
)
_ACCOUNTANT: frozenset[str] = frozenset(
    {
        "accounting.journal.create",
        "accounting.journal.post",
        "accounting.reports.view",
        "accounting.period.close",
        "expenses.create",
        "expenses.approve",
        "payroll.process",
        "payroll.view",
        "reports.view",
        "ai.use",
    }
)
_CASHIER: frozenset[str] = frozenset(
    {
        "catalogue.view",
        "sales.create",
        "sales.view",
        "sales.refund",
        "pos.session.open",
        "pos.session.close",
        "inventory.view",
        "ai.use",
    }
)
_SALES: frozenset[str] = frozenset(
    {
        "catalogue.view",
        "sales.create",
        "sales.view",
        "customers.manage",
        "inventory.view",
        "ai.use",
    }
)
_INVENTORY_MANAGER: frozenset[str] = frozenset(
    {
        "catalogue.view",
        "catalogue.manage",
        "inventory.view",
        "inventory.adjust",
        "inventory.transfer",
        "inventory.count",
        "reports.view",
        "ai.use",
        "ai.act",
    }
)
_PROCUREMENT: frozenset[str] = frozenset(
    {
        "catalogue.view",
        "purchases.create",
        "purchases.approve",
        "purchases.receive",
        "purchases.pay",
        "ai.use",
        "ai.act",
    }
)
_HR: frozenset[str] = frozenset(
    {
        "employees.manage",
        "payroll.process",
        "payroll.view",
        "ai.use",
    }
)
_VIEWER: frozenset[str] = frozenset(
    {
        "catalogue.view",
        "sales.view",
        "inventory.view",
        "accounting.reports.view",
        "reports.view",
        "ai.use",
    }
)

ROLE_TEMPLATES: tuple[tuple[str, str, frozenset[str]], ...] = (
    ("owner", "Owner", TENANT_CODES),
    ("org_admin", "Organization Administrator", _ORG_ADMIN),
    ("manager", "Manager", _MANAGER),
    ("accountant", "Accountant", _ACCOUNTANT),
    ("cashier", "Cashier", _CASHIER),
    ("sales", "Salesperson", _SALES),
    ("inventory_manager", "Inventory Manager", _INVENTORY_MANAGER),
    ("procurement", "Procurement Officer", _PROCUREMENT),
    ("hr", "HR Manager", _HR),
    ("viewer", "Viewer", _VIEWER),
)


def apply_overrides(
    role_permissions: set[str],
    overrides: list[tuple[str, str]],
) -> frozenset[str]:
    """Apply allow overrides, then deny overrides. Deny wins."""

    granted = set(role_permissions)
    for code, effect in overrides:
        if effect == "allow":
            granted.add(code)
    for code, effect in overrides:
        if effect == "deny":
            granted.discard(code)
    return frozenset(granted)


def build_role_seed() -> list[dict[str, object]]:
    """UUID v7 ids for the roles and role-permission rows copied into a new organization."""

    return [
        {
            "id": str(new_uuid()),
            "code": code,
            "name": name,
            "permissions": [
                {"id": str(new_uuid()), "code": permission}
                for permission in sorted(permissions)
            ],
        }
        for code, name, permissions in ROLE_TEMPLATES
    ]

