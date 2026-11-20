import { fetchHealthReady } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const health = await fetchHealthReady();

  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col gap-8 px-6 py-16">
      <header className="space-y-2">
        <p className="text-sm font-medium uppercase tracking-wide text-slate-500">
          BizPilot
        </p>
        <h1 className="text-3xl font-semibold tracking-tight text-slate-900">
          Operations platform
        </h1>
        <p className="max-w-xl text-slate-600">
          Phase 1 foundation is running. Authentication and tenancy land in
          Phase 2.
        </p>
      </header>

      <section className="rounded-lg border border-slate-200 bg-white p-6">
        <h2 className="text-sm font-semibold text-slate-900">API status</h2>
        <p className="mt-1 text-sm text-slate-500">
          Next.js server fetch to FastAPI <code>/api/v1/health/ready</code>
        </p>
        <p className="mt-4 text-lg font-medium">
          {health.ok ? "Connected" : "Unavailable"}
        </p>
        {health.body ? (
          <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
            <div>
              <dt className="text-slate-500">HTTP</dt>
              <dd>{health.statusCode}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Service</dt>
              <dd>{health.body.service}</dd>
            </div>
            {health.body.checks
              ? Object.entries(health.body.checks).map(([key, value]) => (
                  <div key={key}>
                    <dt className="text-slate-500">{key}</dt>
                    <dd>{value}</dd>
                  </div>
                ))
              : null}
          </dl>
        ) : (
          <p className="mt-4 text-sm text-red-700">{health.error}</p>
        )}
      </section>
    </main>
  );
}
