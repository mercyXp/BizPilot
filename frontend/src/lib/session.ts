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
