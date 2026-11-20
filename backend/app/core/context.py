from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class TenantContext:
    """Request-scoped identity and authorization context.

    `permissions` is the evaluated set: role grants, then allow overrides, then deny overrides.
    """

    user_id: UUID
    organization_id: UUID
    membership_id: UUID
    branch_id: UUID | None
    permissions: frozenset[str]
    is_platform_admin: bool
    access_all_branches: bool
    branch_ids: frozenset[UUID]

    def can_access_branch(self, branch_id: UUID) -> bool:
        return self.access_all_branches or branch_id in self.branch_ids
