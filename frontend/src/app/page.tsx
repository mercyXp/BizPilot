import Link from "next/link";

import { fetchHealthReady } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const health = await fetchHealthReady();

  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col gap-8 px-6 py-16">
      <header className="space-y-2">
        <p className="text-sm font-medium uppercase tracking-wide text-slate-500">BizPilot</p>
        <h1 className="text-3xl font-semibold tracking-tight text-slate-900">
          Operations platform
        </h1>
        <p className="max-w-xl text-slate-600">
          Sign in to manage organizations. Phase 2 adds authentication, invitations, and
          tenant isolation.
        </p>
      </header>
      <div className="flex gap-3 text-sm">
        <Link className="rounded-md bg-slate-900 px-4 py-2 font-medium text-white" href="/sign-in">
          Sign in
        </Link>
        <Link className="rounded-md border border-slate-300 px-4 py-2" href="/sign-up">
          Create account
        </Link>
      </div>
      <section className="rounded-lg border border-slate-200 bg-white p-6 text-sm">
        <p className="font-medium">API {health.ok ? "connected" : "unavailable"}</p>
        {health.body?.checks ? (
          <p className="mt-2 text-slate-500">
            schema {health.body.checks.schema_phase} · database {health.body.checks.database}
          </p>
        ) : null}
      </section>
    </main>
  );
}
