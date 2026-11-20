export const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

export type HealthReady = {
  status: string;
  service: string;
  checks?: Record<string, string>;
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
