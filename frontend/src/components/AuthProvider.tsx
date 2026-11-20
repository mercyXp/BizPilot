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
  type OrganizationPublic,
  type UserPublic,
} from "@/lib/api";
import {
  clearCsrfToken,
  clearStoredOrgId,
  getCsrfToken,
  getStoredOrgId,
  setCsrfToken,
  setStoredOrgId,
} from "@/lib/session";

type AuthState = {
  user: UserPublic | null;
  accessToken: string | null;
  organizations: OrganizationPublic[];
  currentOrg: OrganizationPublic | null;
  loading: boolean;
  setSession: (payload: AuthResponse) => Promise<void>;
  refresh: () => Promise<boolean>;
  logout: () => Promise<void>;
  selectOrg: (org: OrganizationPublic) => void;
  reloadMemberships: () => Promise<void>;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserPublic | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [organizations, setOrganizations] = useState<OrganizationPublic[]>([]);
  const [currentOrg, setCurrentOrg] = useState<OrganizationPublic | null>(null);
  const [loading, setLoading] = useState(true);

  const loadMemberships = useCallback(async (token: string) => {
    const response = await apiFetch("/api/v1/me/memberships", { accessToken: token });
    if (!response.ok) {
      setOrganizations([]);
      setCurrentOrg(null);
      return;
    }
    const rows = (await response.json()) as OrganizationPublic[];
    setOrganizations(rows);
    const stored = getStoredOrgId();
    const selected = rows.find((row) => row.id === stored) ?? rows[0] ?? null;
    setCurrentOrg(selected);
    if (selected) {
      setStoredOrgId(selected.id);
    }
  }, []);

  const setSession = useCallback(
    async (payload: AuthResponse) => {
      setAccessToken(payload.access_token);
      setUser(payload.user);
      setCsrfToken(payload.csrf_token);
      await loadMemberships(payload.access_token);
    },
    [loadMemberships],
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
    clearCsrfToken();
    clearStoredOrgId();
  }, [accessToken]);

  const selectOrg = useCallback((org: OrganizationPublic) => {
    setCurrentOrg(org);
    setStoredOrgId(org.id);
  }, []);

  const reloadMemberships = useCallback(async () => {
    if (accessToken) {
      await loadMemberships(accessToken);
    }
  }, [accessToken, loadMemberships]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const value = useMemo(
    () => ({
      user,
      accessToken,
      organizations,
      currentOrg,
      loading,
      setSession,
      refresh,
      logout,
      selectOrg,
      reloadMemberships,
    }),
    [
      user,
      accessToken,
      organizations,
      currentOrg,
      loading,
      setSession,
      refresh,
      logout,
      selectOrg,
      reloadMemberships,
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
