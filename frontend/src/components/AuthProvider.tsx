"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  apiFetch,
  type AuthResponse,
  type DemoSnapshot,
  type OrganizationPublic,
  type UserPublic,
} from "@/lib/api";
import {
  clearCsrfToken,
  clearDemoSession,
  clearStoredOrgId,
  getCsrfToken,
  getStoredBranchId,
  getStoredDemoRole,
  getStoredOrgId,
  setCsrfToken,
  setStoredBranchId,
  setStoredDemoRole,
  setStoredOrgId,
} from "@/lib/session";

type AuthResponseWithDemo = AuthResponse & { demo?: DemoSnapshot };

type AuthState = {
  user: UserPublic | null;
  accessToken: string | null;
  organizations: OrganizationPublic[];
  currentOrg: OrganizationPublic | null;
  loading: boolean;
  permissions: string[];
  branchId: string | null;
  branches: DemoSnapshot["branches"];
  isDemo: boolean;
  demoRole: string | null;
  demoSnapshot: DemoSnapshot | null;
  setSession: (payload: AuthResponse) => Promise<void>;
  refresh: () => Promise<boolean>;
  logout: () => Promise<void>;
  selectOrg: (org: OrganizationPublic) => void;
  selectBranch: (id: string) => void;
  reloadMemberships: () => Promise<void>;
  enterDemo: (role: string) => Promise<void>;
  switchDemoRole: (role: string) => Promise<void>;
  resetDemo: () => Promise<void>;
  tenantFetch: (path: string, options?: RequestInit & { idempotencyKey?: string }) => Promise<Response>;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserPublic | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [organizations, setOrganizations] = useState<OrganizationPublic[]>([]);
  const [currentOrg, setCurrentOrg] = useState<OrganizationPublic | null>(null);
  const [loading, setLoading] = useState(true);
  const [permissions, setPermissions] = useState<string[]>([]);
  const [branchId, setBranchId] = useState<string | null>(null);
  const [branches, setBranches] = useState<DemoSnapshot["branches"]>([]);
  const [demoSnapshot, setDemoSnapshot] = useState<DemoSnapshot | null>(null);
  const [demoRole, setDemoRole] = useState<string | null>(null);

  const applyDemo = useCallback((snapshot: DemoSnapshot | null, role?: string) => {
    setDemoSnapshot(snapshot);
    const nextRole = role ?? snapshot?.role ?? getStoredDemoRole();
    setDemoRole(nextRole);
    if (nextRole) setStoredDemoRole(nextRole);
    if (snapshot?.branches?.length) {
      setBranches(snapshot.branches);
      const stored = getStoredBranchId();
      const selected = snapshot.branches.find((row) => row.id === stored) ?? snapshot.branches[0];
      setBranchId(selected.id);
      setStoredBranchId(selected.id);
    }
  }, []);

  const loadMemberships = useCallback(async (token: string) => {
    const response = await apiFetch("/api/v1/me/memberships", { accessToken: token });
    if (!response.ok) {
      setOrganizations([]);
      setCurrentOrg(null);
      return [] as OrganizationPublic[];
    }
    const rows = (await response.json()) as OrganizationPublic[];
    setOrganizations(rows);
    const stored = getStoredOrgId();
    const selected = rows.find((row) => row.id === stored) ?? rows[0] ?? null;
    setCurrentOrg(selected);
    if (selected) {
      setStoredOrgId(selected.id);
    }
    return rows;
  }, []);

  const loadContext = useCallback(
    async (token: string, orgId: string, nextBranch?: string) => {
      const response = await apiFetch("/api/v1/authorization/context", {
        accessToken: token,
        organizationId: orgId,
        branchId: nextBranch ?? branchId ?? undefined,
      });
      if (!response.ok) {
        setPermissions([]);
        return;
      }
      const body = (await response.json()) as { permissions: string[] };
      setPermissions(body.permissions);
    },
    [branchId],
  );

  const setSession = useCallback(
    async (payload: AuthResponseWithDemo) => {
      setAccessToken(payload.access_token);
      setUser(payload.user);
      setCsrfToken(payload.csrf_token);
      const rows = await loadMemberships(payload.access_token);
      if (payload.demo) {
        applyDemo(payload.demo);
        const org = rows.find((row) => row.id === payload.demo?.organization.id) ?? rows[0];
        if (org) {
          setCurrentOrg(org);
          setStoredOrgId(org.id);
          await loadContext(payload.access_token, org.id, payload.demo.branches[0]?.id);
        }
      } else if (rows[0]) {
        await loadContext(payload.access_token, rows[0].id);
      }
    },
    [applyDemo, loadContext, loadMemberships],
  );

  const refresh = useCallback(async () => {
    const csrf = getCsrfToken();
    if (!csrf) {
      setLoading(false);
      return false;
    }
    const response = await apiFetch("/api/v1/auth/refresh", {
      method: "POST",
      csrfToken: csrf,
    });
    if (!response.ok) {
      clearCsrfToken();
      setUser(null);
      setAccessToken(null);
      setLoading(false);
      return false;
    }
    const payload = (await response.json()) as AuthResponse;
    await setSession(payload);
    setLoading(false);
    return true;
  }, [setSession]);

  const logout = useCallback(async () => {
    if (accessToken) {
      await apiFetch("/api/v1/auth/logout", {
        method: "POST",
        accessToken,
        csrfToken: getCsrfToken() ?? undefined,
      });
    }
    setUser(null);
    setAccessToken(null);
    setOrganizations([]);
    setCurrentOrg(null);
    setPermissions([]);
    setDemoSnapshot(null);
    setDemoRole(null);
    clearCsrfToken();
    clearStoredOrgId();
    clearDemoSession();
  }, [accessToken]);

  const selectOrg = useCallback((org: OrganizationPublic) => {
    setCurrentOrg(org);
    setStoredOrgId(org.id);
  }, []);

  const selectBranch = useCallback((id: string) => {
    setBranchId(id);
    setStoredBranchId(id);
  }, []);

  const reloadMemberships = useCallback(async () => {
    if (accessToken) {
      await loadMemberships(accessToken);
    }
  }, [accessToken, loadMemberships]);

  const enterDemo = useCallback(
    async (role: string) => {
      const response = await apiFetch("/api/v1/demo/enter", {
        method: "POST",
        body: JSON.stringify({ role }),
      });
      if (!response.ok) {
        throw new Error("Could not open the live demo");
      }
      const payload = (await response.json()) as AuthResponseWithDemo;
      await setSession(payload);
    },
    [setSession],
  );

  const switchDemoRole = useCallback(
    async (role: string) => {
      if (!accessToken) return;
      const response = await apiFetch("/api/v1/demo/switch", {
        method: "POST",
        accessToken,
        body: JSON.stringify({ role }),
      });
      if (!response.ok) {
        throw new Error("Could not switch demo role");
      }
      const payload = (await response.json()) as AuthResponseWithDemo;
      await setSession(payload);
    },
    [accessToken, setSession],
  );

  const resetDemo = useCallback(async () => {
    if (!accessToken) return;
    const role = demoRole || "owner";
    const response = await apiFetch("/api/v1/demo/reset", {
      method: "POST",
      accessToken,
      body: JSON.stringify({ role }),
    });
    if (!response.ok) {
      throw new Error("Could not reset demo data");
    }
    const payload = (await response.json()) as AuthResponseWithDemo;
    await setSession(payload);
  }, [accessToken, demoRole, setSession]);

  const tenantFetch = useCallback(
    (path: string, options: RequestInit & { idempotencyKey?: string } = {}) => {
      return apiFetch(path, {
        ...options,
        accessToken: accessToken ?? undefined,
        organizationId: currentOrg?.id,
        branchId: branchId ?? undefined,
        csrfToken: getCsrfToken() ?? undefined,
      });
    },
    [accessToken, branchId, currentOrg?.id],
  );

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    if (!accessToken || !currentOrg || !user?.email.endsWith("@demo.bizpilot.local")) return;
    void loadContext(accessToken, currentOrg.id, branchId ?? undefined);
    void apiFetch("/api/v1/demo/snapshot", {
      accessToken,
      organizationId: currentOrg.id,
      branchId: branchId ?? undefined,
    }).then(async (response) => {
      if (!response.ok) return;
      const snapshot = (await response.json()) as DemoSnapshot;
      applyDemo(snapshot);
    });
  }, [accessToken, applyDemo, branchId, currentOrg, loadContext, user?.email]);

  const isDemo = Boolean(demoSnapshot?.is_demo || user?.email.endsWith("@demo.bizpilot.local"));

  const value = useMemo(
    () => ({
      user,
      accessToken,
      organizations,
      currentOrg,
      loading,
      permissions,
      branchId,
      branches,
      isDemo,
      demoRole,
      demoSnapshot,
      setSession,
      refresh,
      logout,
      selectOrg,
      selectBranch,
      reloadMemberships,
      enterDemo,
      switchDemoRole,
      resetDemo,
      tenantFetch,
    }),
    [
      user,
      accessToken,
      organizations,
      currentOrg,
      loading,
      permissions,
      branchId,
      branches,
      isDemo,
      demoRole,
      demoSnapshot,
      setSession,
      refresh,
      logout,
      selectOrg,
      selectBranch,
      reloadMemberships,
      enterDemo,
      switchDemoRole,
      resetDemo,
      tenantFetch,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
