from app.modules.authorization.catalog import (
    PERMISSIONS,
    PLATFORM_CODES,
    ROLE_TEMPLATES,
    TENANT_CODES,
    apply_overrides,
)


def test_templates_use_only_known_tenant_permissions() -> None:
    known = {code for code, _module, _description in PERMISSIONS}
    assert PLATFORM_CODES == {"platform.orgs.manage"}
    assert TENANT_CODES.isdisjoint(PLATFORM_CODES)
    for code, _name, permissions in ROLE_TEMPLATES:
        assert permissions <= known
        assert permissions.isdisjoint(PLATFORM_CODES), code


def test_owner_cashier_viewer_matrix() -> None:
    roles = {code: permissions for code, _name, permissions in ROLE_TEMPLATES}
    assert roles["owner"] == TENANT_CODES
    assert "accounting.journal.post" in roles["owner"]
    assert "accounting.journal.post" in roles["accountant"]
    assert "accounting.journal.post" not in roles["cashier"]
    assert "accounting.journal.post" not in roles["org_admin"]
    assert "accounting.journal.post" not in roles["viewer"]
    assert "inventory.adjust" in roles["inventory_manager"]
    assert "inventory.adjust" not in roles["cashier"]
    assert "inventory.adjust" not in roles["viewer"]
    assert "branches.manage" in roles["owner"]
    assert "branches.manage" not in roles["cashier"]


def test_deny_wins_over_role_grant_and_allow() -> None:
    effective = apply_overrides(
        {"accounting.journal.post", "sales.view"},
        [
            ("inventory.adjust", "allow"),
            ("accounting.journal.post", "deny"),
            ("inventory.adjust", "deny"),
        ],
    )
    assert effective == frozenset({"sales.view"})
