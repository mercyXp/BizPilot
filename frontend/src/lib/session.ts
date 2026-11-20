const CSRF_KEY = "bizpilot_csrf";
const ORG_KEY = "bizpilot_org";

export function getCsrfToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.sessionStorage.getItem(CSRF_KEY);
}

export function setCsrfToken(token: string): void {
  window.sessionStorage.setItem(CSRF_KEY, token);
}

export function clearCsrfToken(): void {
  window.sessionStorage.removeItem(CSRF_KEY);
}

export function getStoredOrgId(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(ORG_KEY);
}

export function setStoredOrgId(id: string): void {
  window.localStorage.setItem(ORG_KEY, id);
}

export function clearStoredOrgId(): void {
  window.localStorage.removeItem(ORG_KEY);
}

const BRANCH_KEY = "bizpilot_branch";
const DEMO_ROLE_KEY = "bizpilot_demo_role";
const DEMO_TOUR_KEY = "bizpilot_demo_tour_done";

export function getStoredBranchId(): string | null {
  if (typeof window === "undefined") return null;
  return window.sessionStorage.getItem(BRANCH_KEY);
}

export function setStoredBranchId(id: string): void {
  window.sessionStorage.setItem(BRANCH_KEY, id);
}

export function getStoredDemoRole(): string | null {
  if (typeof window === "undefined") return null;
  return window.sessionStorage.getItem(DEMO_ROLE_KEY);
}

export function setStoredDemoRole(role: string): void {
  window.sessionStorage.setItem(DEMO_ROLE_KEY, role);
}

export function clearDemoSession(): void {
  window.sessionStorage.removeItem(DEMO_ROLE_KEY);
  window.sessionStorage.removeItem(BRANCH_KEY);
}

export function isDemoTourDone(): boolean {
  if (typeof window === "undefined") return true;
  return window.localStorage.getItem(DEMO_TOUR_KEY) === "1";
}

export function setDemoTourDone(): void {
  window.localStorage.setItem(DEMO_TOUR_KEY, "1");
}
