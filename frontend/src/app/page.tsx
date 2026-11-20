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
    <div className="min-h-screen bg-[#f4f7fb]">
      <SiteHeader active="product" />
      <main>
        <section className="relative overflow-hidden">
          <div
            className="pointer-events-none absolute inset-0 bg-grid bg-[size:28px_28px]"
            aria-hidden
          />
          <div className="relative mx-auto max-w-6xl px-6 py-20">
            <p className="text-sm font-semibold uppercase tracking-wide text-brand-600">
              Built for Zambia
            </p>
            <h1 className="mt-3 max-w-3xl text-4xl font-semibold tracking-tight text-slate-900 sm:text-5xl">
              One system for the till, the stock room and the books.
            </h1>
            <p className="mt-5 max-w-2xl text-lg text-slate-600">
              BizPilot is POS, inventory, purchasing, accounting and payroll for stores in
              Zambia. Default currency ZMW. Start on Basic at no cost, then add inventory and
              books when you need them.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                href="/pricing"
                className="rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-700"
              >
                See pricing
              </Link>
              <Link
                href="/sign-up?plan=basic"
                className="rounded-lg bg-white px-4 py-2.5 text-sm font-semibold text-slate-900 ring-1 ring-slate-200 hover:bg-slate-50"
              >
                Start free with Basic
              </Link>
            </div>
          </div>
        </section>

        <section id="pos" className="scroll-mt-20 border-t border-slate-200 bg-white">
          <div className="mx-auto max-w-6xl px-6 py-16">
            <h2 className="text-2xl font-semibold tracking-tight text-slate-900">
              What the POS does
            </h2>
            <p className="mt-3 max-w-2xl text-slate-600">
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
                <li key={item.title} className="rounded-xl border border-slate-200 p-5">
                  <h3 className="font-medium text-slate-900">{item.title}</h3>
                  <p className="mt-2 text-sm text-slate-600">{item.body}</p>
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-6 py-16">
          <h2 className="text-2xl font-semibold tracking-tight text-slate-900">Plans</h2>
          <p className="mt-2 text-slate-600">Per store, billed monthly in Kwacha.</p>
          <ul className="mt-8 grid gap-4 sm:grid-cols-3">
            {[basic, premium, enterprise].map((plan) => (
              <li key={plan.id} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                <p className="text-sm font-medium text-brand-600">{plan.name}</p>
                <p className="mt-2 text-2xl font-semibold text-slate-900">
                  {formatKw(plan.monthlyKw)}
                </p>
                <p className="mt-1 text-sm text-slate-500">
                  {plan.monthlyKw === 0 ? "No monthly fee" : "per month"}
                </p>
                <p className="mt-3 text-sm text-slate-600">{plan.blurb}</p>
              </li>
            ))}
          </ul>
          <Link
            href="/pricing"
            className="mt-6 inline-block text-sm font-semibold text-brand-600 underline underline-offset-2"
          >
            Compare every feature
          </Link>
        </section>

        <section className="border-t border-slate-200 bg-white">
          <div className="mx-auto max-w-6xl px-6 py-10">
            <h2 className="text-sm font-semibold text-slate-900">API status</h2>
            <p className="mt-1 text-sm text-slate-500">
              Next.js server fetch to FastAPI <code>/api/v1/health/ready</code>
            </p>
            <p className="mt-3 text-sm font-medium">
              {health.ok ? "Connected" : "Unavailable"}
            </p>
            {health.body?.checks ? (
              <p className="mt-1 text-sm text-slate-500">
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
