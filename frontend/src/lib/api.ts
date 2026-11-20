export const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

export function clientApiBase(): string {
  if (typeof window !== "undefined") {
    return "";
  }
  return apiBaseUrl;
}

export type HealthReady = {
  status: string;
  service: string;
  checks?: Record<string, string>;
};

export type UserPublic = {
  id: string;
  email: string;
  full_name: string;
  email_verified: boolean;
  created_at: string;
};

export type OrganizationPublic = {
  id: string;
  name: string;
  legal_name: string | null;
  country_code: string;
  base_currency_code: string;
  timezone: string;
  status: string;
  is_owner: boolean;
  membership_id: string;
  created_at: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
  expires_in: number;
  csrf_token: string;
  user: UserPublic;
};

export type ApiErrorBody = {
  error?: { code?: string; message?: string };
};

export async function fetchHealthReady(): Promise<{
  ok: boolean;
  statusCode: number;
  body: HealthReady | null;
  error?: string;
}> {
  try {
    const response = await fetch(`${apiBaseUrl}/api/v1/health/ready`, {
      cache: "no-store",
    });
    const body = (await response.json()) as HealthReady;
    return { ok: response.ok, statusCode: response.status, body };
  } catch (error) {
    return {
      ok: false,
      statusCode: 0,
      body: null,
      error: error instanceof Error ? error.message : "Unable to reach API",
    };
  }
}

export type DemoSnapshot = {
  organization: {
    id: string;
    name: string;
    legal_name: string | null;
    industry: string;
    location: string;
    currency: string;
    demo_key: string;
  };
  kpis: {
    monthly_revenue: number;
    monthly_expenses: number;
    products: number;
    branches: number;
    journals: number;
  };
  branches: { id: string; code: string; name: string }[];
  role: string | null;
  role_title: string | null;
  is_demo: boolean;
  access_all_branches?: boolean;
  preferred_branch_id?: string | null;
  access: { roles_explored?: string[]; modules_visited?: string[] };
};

export async function apiFetch(
  path: string,
  options: RequestInit & {
    accessToken?: string;
    organizationId?: string;
    branchId?: string;
    csrfToken?: string;
    idempotencyKey?: string;
  } = {},
): Promise<Response> {
  const { accessToken, organizationId, branchId, csrfToken, idempotencyKey, headers, ...rest } = options;
  const merged = new Headers(headers);
  merged.set("Content-Type", "application/json");
  if (accessToken) {
    merged.set("Authorization", `Bearer ${accessToken}`);
  }
  if (organizationId) {
    merged.set("X-Organization-Id", organizationId);
  }
  if (branchId) {
    merged.set("X-Branch-Id", branchId);
  }
  if (csrfToken) {
    merged.set("X-CSRF-Token", csrfToken);
  }
  if (idempotencyKey) {
    merged.set("Idempotency-Key", idempotencyKey);
  }
  return fetch(`${clientApiBase()}${path}`, {
    ...rest,
    headers: merged,
    credentials: "include",
  });
}

export async function readError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as ApiErrorBody;
    return body.error?.message || "Request failed";
  } catch {
    return "Request failed";
  }
}
