# Phase 0 — Security, Tenant Isolation, Authorization

## 1. Identity

**Users** are global. They are not owned by an organization.

- Email unique (normalized lowercase)
- Password hashed with Argon2id (or bcrypt if Argon2 unavailable; prefer Argon2id)
- `email_verified_at`
- Optional TOTP secret (recommended for Owner/Accountant; implement in Phase 2 as optional, enforce later by policy)

**Sessions / refresh tokens**

- Access JWT: short-lived (e.g. 15 minutes). Claims: `sub` (user_id), `sid` (session_id), `pv` (password/session version). **No organization_id in the access token** so org switching does not require re-issue of a long-lived org-bound token.
- Refresh token: opaque, stored hashed, rotated on every use. Reuse of an old token in a family **revokes the family**.
- Logout revokes the session.
- Org and branch are **request context headers**, verified every request.

Password reset and email verification use single-use hashed tokens with expiry.

## 2. Tenancy model

```
User 1──* OrganizationMembership *──1 Organization
OrganizationMembership 1──* MembershipRole *──1 Role
OrganizationMembership 1──* MembershipBranch *──1 Branch
Role *──* Permission
User + Organization ── UserPermissionOverride
```

- A user may have many memberships (`unique(user_id, organization_id)`).
- Membership status: `invited | active | suspended`.
- First user to create an organization becomes Owner (system role, not deletable).
- Invitations carry email, org, roles, branch set, expiry, inviter.

**Frontend-supplied IDs:** `X-Organization-Id` and `X-Branch-Id` are hints. Backend loads membership; if missing/suspended → 403. Branch must be in the membership’s allowed set unless `access_all_branches`.

## 3. PostgreSQL RLS

All tenant tables include `organization_id NOT NULL` and enable **FORCE ROW LEVEL SECURITY**.

Policies (conceptual):

```sql
USING (organization_id = current_setting('app.current_organization_id', true)::uuid)
WITH CHECK (organization_id = current_setting('app.current_organization_id', true)::uuid)
```

Request transaction:

```sql
SET LOCAL app.current_organization_id = '<uuid>';
SET LOCAL app.current_user_id = '<uuid>';
```

**Database roles**

| Role | Use |
| --- | --- |
| `bizpilot_app` | API runtime; BYPASSRLS **off** |
| `bizpilot_migrator` | Alembic; BYPASSRLS on |
| `bizpilot_platform` | Narrow platform-admin queries; still audited in app |

Application code uses `bizpilot_app` only. Tests that verify isolation must use the app role, not superuser.

Global tables (no org RLS): `users`, `user_sessions`, `industries` (catalogue of packs), `permissions` (seed), `subscription_plans` (platform), and similar platform catalogs. `organizations` is readable by members via membership join; list-orgs for a user is `WHERE id IN (select organization_id from memberships where user_id = ...)`.

**Never** pass client `organization_id` into a query without also setting RLS context from the verified membership.

## 4. Authorization model

Permissions are strings `domain.action` (and occasionally `domain.action.qualifier`).

Initial seed permissions include (non-exhaustive; full seed in Phase 3):

- `org.manage`, `org.settings`, `branches.manage`, `users.invite`, `users.manage`
- `sales.create`, `sales.view`, `sales.refund`, `pos.session.open`, `pos.session.close`
- `inventory.view`, `inventory.adjust`, `inventory.transfer`, `inventory.count`
- `purchases.create`, `purchases.approve`, `purchases.receive`, `purchases.pay`
- `customers.manage`, `customers.credit`
- `accounting.journal.create`, `accounting.journal.post`, `accounting.reports.view`, `accounting.period.close`
- `expenses.create`, `expenses.approve`
- `employees.manage`, `payroll.process`, `payroll.view`
- `reports.view`, `ai.use`, `ai.act` (write-tools / drafts)
- `platform.orgs.manage` (super admin only)

**Roles** are org-owned **except** system templates copied at org creation. Platform Super Administrator is **not** an org role; it is `users.platform_role = super_admin`.

**Evaluation order**

1. If platform admin on platform routes → allow those routes only.
2. If no membership → deny tenant routes.
3. Collect permissions from assigned roles.
4. Apply overrides: grant or deny (`effect`). Deny wins.
5. Branch: if resource is branch-scoped and branch not allowed → deny.
6. Industry/module disabled → treat as not found / forbidden.
7. Subscription feature gated → 402 or 403 with `code: plan_limit`.

Cashiers cannot post journals. Viewers cannot adjust stock. AI tools call the same checkers with the same `TenantContext`.

## 5. Default role matrix (initial)

| Permission area | Owner | Org Admin | Manager | Accountant | Cashier | Sales | Inv Mgr | Procurement | HR | Viewer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Users / branches | Y | Y | — | — | — | — | — | — | — | — |
| POS / sales create | Y | Y | Y | — | Y | Y | — | — | — | — |
| Sales refund | Y | Y | Y | — | limited | — | — | — | — | — |
| Inventory adjust | Y | Y | Y | — | — | — | Y | — | — | — |
| Purchases approve | Y | Y | Y | — | — | — | — | Y | — | — |
| Journal post | Y | — | — | Y | — | — | — | — | — | — |
| Financial reports | Y | Y | Y | Y | — | — | — | — | — | Y* |
| Payroll process | Y | — | — | Y* | — | — | — | — | Y | — |
| AI use | Y | Y | Y | Y | Y* | Y* | Y | Y | Y | Y* |

\* configurable; defaults are conservative (viewers: reports if granted; cashiers: AI read tools for stock/price lookup only).

Exact seed tables are implemented in Phase 3 and may be tuned; the **enforcement mechanism** is not optional.

## 6. Security controls

| Control | Approach |
| --- | --- |
| Input validation | Pydantic on API; Zod on UI; DB constraints |
| Rate limiting | Redis sliding window: login, reset, register, AI |
| CORS | Explicit origin allowlist |
| Headers | Helmet-equivalent: CSP, nosniff, frame deny, HSTS in prod |
| CSRF | If refresh token is httpOnly cookie, use SameSite + CSRF on cookie-auth routes. Access token in `Authorization` is not cookie-CSRF-vulnerable |
| Secrets | Env / secret manager; never in git |
| Uploads | MIME allowlist, size cap, malware-agnostic: no execute, random keys, no user-controlled path |
| Errors | Generic 500 to clients; log internally with request id |
| Audit | Append-only `audit_logs`; no update/delete API |
| Outbox | Same transaction as business commit for emails/webhooks |

## 7. Isolation test contract (must exist from Phase 2)

- User A in Org 1 cannot GET/PATCH Org 2 resources by swapping IDs.
- Direct SQL as `bizpilot_app` without `SET LOCAL` returns zero tenant rows.
- Membership in Org 1 with branch X cannot read branch Y sales if not granted.
- AI tool with Org 1 context cannot return Org 2 aggregates even if prompt asks.

## 8. Data protection

Plan for Zambia Data Protection Act alignment by Phase 15: retention policy, export of org data for owners, access logging. Not implemented in Phase 0–2 beyond audit and isolation.
