import Link from "next/link";

import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { fetchHealthReady } from "@/lib/api";
import { formatKw, PLANS } from "@/lib/pricing";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const health = await fetchHealthReady();
  const basic = PLANS.find((plan) => plan.id === "basic")!;
  const premium = PLANS.find((plan) => plan.id === "premium")!;
  const enterprise = PLANS.find((plan) => plan.id === "enterprise")!;

  return (
    <div className="flex min-h-screen flex-col bg-canvas">
      <SiteHeader active="product" />
      <main className="flex-1">
        <section className="relative overflow-hidden">
          <div
            className="pointer-events-none absolute inset-0 bg-grid bg-[size:28px_28px]"
            aria-hidden
          />
          <div className="relative mx-auto max-w-6xl px-6 py-20">
            <p className="inline-flex items-center rounded-full bg-info px-3 py-1 text-sm font-semibold text-ink">
              Built for Zambia
            </p>
            <h1 className="mt-4 max-w-3xl text-4xl font-semibold tracking-tight text-ink sm:text-5xl">
              One system for the till, the stock room and the books.
            </h1>
            <p className="mt-5 max-w-2xl text-lg text-ink-muted">
              BizPilot is POS, inventory, purchasing, accounting and payroll for stores in
              Zambia. Default currency ZMW. Start on Basic at no cost, then add inventory and
              books when you need them.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/pricing" className="btn-primary">
                See pricing
              </Link>
              <Link href="/sign-up?plan=basic" className="btn-outline">
                Start free with Basic
              </Link>
            </div>
          </div>
        </section>

        <section id="pos" className="scroll-mt-20 border-t border-ink/10 bg-surface">
          <div className="mx-auto max-w-6xl px-6 py-16">
            <h2 className="text-2xl font-semibold tracking-tight text-ink">
              What the POS does
            </h2>
            <p className="mt-3 max-w-2xl text-ink-muted">
              Open a cashier shift, sell, take cash or pending mobile money, print a receipt,
              and refund with restock. Stock only moves when the sale is actually paid.
            </p>
            <ul className="mt-8 grid gap-4 sm:grid-cols-3">
              {[
                {
                  title: "Sales and receipts",
                  body: "Server-side prices and tax. Duplicate payments cannot double a sale.",
                },
                {
                  title: "Stock that matches the till",
                  body: "Goods leave the warehouse on a completed sale. Purchase orders never receive stock; goods receipts do.",
                },
                {
                  title: "Books and payroll when you are ready",
                  body: "Posted journals stay balanced. Payroll uses rates you configure — not unofficial statutory guesses.",
                },
              ].map((item) => (
                <li key={item.title} className="rounded-xl border border-ink/10 bg-surface p-5">
                  <h3 className="font-medium text-ink">{item.title}</h3>
                  <p className="mt-2 text-sm text-ink-muted">{item.body}</p>
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-6 py-16">
          <h2 className="text-2xl font-semibold tracking-tight text-ink">Plans</h2>
          <p className="mt-2 text-ink-muted">Per store, billed monthly in Kwacha.</p>
          <ul className="mt-8 grid gap-4 sm:grid-cols-3">
            {[basic, premium, enterprise].map((plan) => (
              <li
                key={plan.id}
                className={`relative rounded-2xl border bg-surface p-5 shadow-sm ${
                  plan.popular ? "border-2 border-brand-600" : "border-ink/10"
                }`}
              >
                {plan.popular ? (
                  <p className="mb-3 inline-flex rounded-full bg-highlight px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-[0.12em] text-ink">
                    Most popular
                  </p>
                ) : null}
                <p className="text-sm font-medium text-brand-600">{plan.name}</p>
                <p className="mt-2 text-2xl font-semibold text-ink">
                  {formatKw(plan.monthlyKw)}
                </p>
                <p className="mt-1 text-sm text-ink-faint">
                  {plan.monthlyKw === 0 ? "No monthly fee" : "per month"}
                </p>
                <p className="mt-3 text-sm text-ink-muted">{plan.blurb}</p>
              </li>
            ))}
          </ul>
          <Link
            href="/pricing"
            className="mt-6 inline-block text-sm font-semibold text-brand-600 underline underline-offset-2 hover:text-brand-700"
          >
            Compare every feature
          </Link>
        </section>

        <section className="border-t border-ink/10 bg-surface">
          <div className="mx-auto max-w-6xl px-6 py-10">
            <h2 className="text-sm font-semibold text-ink">API status</h2>
            <p className="mt-1 text-sm text-ink-faint">
              Next.js server fetch to FastAPI <code>/api/v1/health/ready</code>
            </p>
            <p className="mt-3">
              {health.ok ? (
                <span className="inline-flex rounded-full bg-mint px-2.5 py-1 text-sm font-semibold text-brand-700">
                  Connected
                </span>
              ) : (
                <span className="text-sm font-medium text-red-700">Unavailable</span>
              )}
            </p>
            {health.body?.checks ? (
              <p className="mt-2 text-sm text-ink-faint">
                {Object.entries(health.body.checks)
                  .map(([key, value]) => `${key}: ${value}`)
                  .join(" · ")}
              </p>
            ) : health.error ? (
              <p className="mt-1 text-sm text-red-700">{health.error}</p>
            ) : null}
          </div>
        </section>
      </main>
      <SiteFooter />
    </div>
  );
}
