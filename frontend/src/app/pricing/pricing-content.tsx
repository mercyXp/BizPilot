"use client";

import Link from "next/link";
import { useState } from "react";

import {
  ACCOUNTING_ADDON_KW,
  BILLING_COUNTRIES,
  PAYROLL_PER_EMPLOYEE_KW,
  PLANS,
  STORE_TYPES,
  compareHeading,
  featureLabel,
  formatKw,
  planBlurb,
  planCardFeatures,
  planIncludes,
  visibleFeatures,
  type PlanId,
  type StoreTypeId,
} from "@/lib/pricing";

export function PricingContent() {
  const [storeType, setStoreType] = useState<StoreTypeId>("retail");
  const [country, setCountry] = useState<(typeof BILLING_COUNTRIES)[number]["id"]>("zm");
  const selectedCountry = BILLING_COUNTRIES.find((item) => item.id === country) ?? BILLING_COUNTRIES[0];
  const premium = PLANS.find((plan) => plan.id === "premium")!;
  const features = visibleFeatures(storeType);
  const heading = compareHeading(storeType);

  return (
    <div className="relative overflow-hidden">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 app-grid-bg"
      />
      <div className="relative mx-auto max-w-6xl px-4 py-14 sm:px-6 sm:py-16">
        <div className="mx-auto max-w-3xl text-center">
          <p className="inline-flex items-center gap-1.5 rounded-full bg-brand-soft px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-brand-deep ring-1 ring-brand-soft">
            <DiamondIcon />
            Pricing
          </p>
          <h1 className="mt-5 text-4xl font-bold tracking-tight text-ink sm:text-5xl">
            Subscription plans
          </h1>
          <p className="mt-4 text-lg font-medium text-brand-deep sm:text-xl">
            Prices for POS, accounting and payroll in Zambia
          </p>
          <p className="mt-4 text-base leading-relaxed text-muted">
            Three plans, one price list. Pick the one that fits your business in Zambia. Plans
            are per store, billed monthly in Kwacha. Cancel anytime.{" "}
            <Link href="/#pos" className="font-medium text-brand-deep hover:text-brand-deep">
              See what the POS does
            </Link>
            .
          </p>
        </div>

        <div className="mx-auto mt-10 max-w-xl text-center">
          <label htmlFor="billing-country" className="text-sm font-medium text-ink">
            Show prices for
          </label>
          <div className="relative mt-2">
            <span className="pointer-events-none absolute inset-y-0 left-4 flex items-center text-base">
              {selectedCountry.flag}
            </span>
            <select
              id="billing-country"
              value={country}
              onChange={(event) =>
                setCountry(event.target.value as (typeof BILLING_COUNTRIES)[number]["id"])
              }
              className="w-full appearance-none rounded-xl border border-border bg-surface py-3 pl-12 pr-10 text-left text-sm text-ink shadow-sm outline-none ring-brand focus:border-brand focus:ring-2"
            >
              {BILLING_COUNTRIES.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.label}
                </option>
              ))}
            </select>
            <span className="pointer-events-none absolute inset-y-0 right-3 flex items-center text-muted">
              <ChevronIcon />
            </span>
          </div>
          <p className="mt-2 text-sm text-muted">
            You are billed in Zambian Kwacha whichever country you pick.
          </p>
        </div>

        <div className="mt-8 flex justify-center">
          <div
            className="inline-flex max-w-full flex-wrap justify-center gap-1 rounded-full bg-surface p-1 shadow-sm ring-1 ring-ink/10"
            role="tablist"
            aria-label="Store type"
          >
            {STORE_TYPES.map((type) => {
              const selected = type.id === storeType;
              return (
                <button
                  key={type.id}
                  type="button"
                  role="tab"
                  aria-selected={selected}
                  onClick={() => setStoreType(type.id)}
                  className={`rounded-full px-4 py-2 text-sm font-medium transition ${
                    selected
                      ? "bg-brand-600 text-white shadow-sm"
                      : "text-secondary hover:bg-lavender hover:text-ink"
                  }`}
                >
                  {type.label}
                </button>
              );
            })}
          </div>
        </div>
        <p className="mt-4 text-center text-sm text-muted">
          Prices are the same for every store type — the tabs only change what each plan unlocks.
        </p>
        {storeType === "manufacturer" ? (
          <p className="mt-2 text-center text-sm text-secondary">
            Manufacturing bills of materials stay off every plan, including Entreprise.
          </p>
        ) : null}

        <div className="mt-12 grid items-stretch gap-6 lg:grid-cols-3">
          {PLANS.map((plan) => {
            const included = planCardFeatures(plan.id, storeType);
            return (
              <article
                key={plan.id}
                className={`relative flex flex-col rounded-3xl bg-surface p-6 shadow-card sm:p-8 ${
                  plan.popular ? "border-2 border-brand-600" : "border border-border"
                }`}
              >
                {plan.popular ? (
                  <p className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-highlight px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-ink">
                    Most popular
                  </p>
                ) : null}
                <h2 className="text-xl font-bold text-ink">{plan.name}</h2>
                <p className="mt-2 min-h-12 text-sm leading-relaxed text-muted">
                  {planBlurb(plan.id, storeType)}
                </p>
                <p className="mt-6 flex items-end gap-2">
                  <span className="text-4xl font-bold tracking-tight text-ink">
                    {formatKw(plan.monthlyKw)}
                  </span>
                  {plan.monthlyKw === 0 ? null : (
                    <span className="mb-1 text-sm font-medium text-muted">per month</span>
                  )}
                </p>
                <ul className="mt-6 flex-1 space-y-2.5 text-sm text-secondary">
                  {included.map((feature) => (
                    <li key={feature} className="flex items-start gap-2">
                      <CheckIcon />
                      <span>{featureLabel(storeType, feature)}</span>
                    </li>
                  ))}
                </ul>
                <GetPlanLink planId={plan.id} name={plan.name} emphasis={plan.popular ? "solid" : "outline"} wide />
              </article>
            );
          })}
        </div>

        <section className="mt-20" aria-labelledby="compare-heading">
          <p className="text-center text-[11px] font-semibold uppercase tracking-[0.22em] text-brand-deep">
            Compare
          </p>
          <h2
            id="compare-heading"
            className="mt-3 text-center text-3xl font-bold tracking-tight text-ink sm:text-4xl"
          >
            {heading}
          </h2>
          <p className="mt-4 text-center text-xs text-muted sm:hidden">
            Swipe sideways to compare Basic, Premium and Entreprise
          </p>
          <div className="mt-6 overflow-hidden rounded-2xl border border-border bg-surface shadow-sm sm:mt-8">
            <div className="overflow-x-auto">
              <table className="min-w-[720px] w-full text-sm">
                <thead>
                  <tr className="bg-canvas">
                    <th className="sticky left-0 z-10 w-44 max-w-44 bg-canvas px-4 py-5 text-left text-[11px] font-semibold uppercase tracking-[0.16em] text-muted sm:w-auto sm:max-w-none sm:px-6">
                      What you get
                    </th>
                    {PLANS.map((plan) => (
                      <th key={plan.id} className="min-w-[7.5rem] px-3 py-5 text-center sm:px-4">
                        <div className="text-sm font-semibold text-ink">{plan.name}</div>
                        <div className="mt-0.5 text-xs font-medium text-muted">
                          {plan.monthlyKw === 0 ? "Free" : `${formatKw(plan.monthlyKw)}/mo`}
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {features.map((feature) => (
                    <tr key={feature} className="border-t border-ink/5">
                      <th
                        scope="row"
                        className="sticky left-0 w-44 max-w-44 bg-surface px-4 py-3.5 text-left font-normal text-secondary shadow-[6px_0_10px_-8px_rgba(15,23,42,0.35)] sm:w-auto sm:max-w-none sm:px-6"
                      >
                        {featureLabel(storeType, feature)}
                      </th>
                      {PLANS.map((plan) => {
                        const included = planIncludes(plan.id, feature);
                        return (
                          <td key={plan.id} className="px-4 py-3.5 text-center">
                            {included ? (
                              <span className="inline-flex justify-center">
                                <CheckIcon />
                                <span className="sr-only">Included</span>
                              </span>
                            ) : (
                              <span className="text-ink/20" aria-label="Not included">
                                —
                              </span>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="border-t border-ink/5 bg-canvas">
                    <td className="px-6 py-5" />
                    {PLANS.map((plan) => (
                      <td key={plan.id} className="px-4 py-5 text-center">
                        <GetPlanLink
                          planId={plan.id}
                          name={plan.name}
                          emphasis={plan.popular ? "solid" : "outline"}
                        />
                      </td>
                    ))}
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        </section>

        <section id="accounting" className="mt-20 scroll-mt-24">
          <p className="text-center text-[11px] font-semibold uppercase tracking-[0.18em] text-brand-deep">
            Add-on or standalone
          </p>
          <div className="mt-4 grid gap-8 rounded-3xl border border-border bg-surface p-6 shadow-card sm:p-8 lg:grid-cols-2">
            <div>
              <h2 className="text-2xl font-bold text-ink">Add BizPilot Accounting</h2>
              <p className="mt-3 leading-relaxed text-secondary">
                Full bookkeeping run for you and kept on our cloud. We give you your own login,
                set it up and keep it backed up. Add it to any POS plan, or take it on its own
                if you do not need a till.
              </p>
              <ul className="mt-5 space-y-2.5 text-sm text-secondary">
                {[
                  "Invoices, quotes, bills and expenses",
                  "Bank reconciliation",
                  "Profit and loss, balance sheet, cash flow",
                  "VAT-ready tax reports",
                  "Your own login, on any device",
                  "Sales and purchases flow in from POS",
                ].map((item) => (
                  <li key={item} className="flex items-start gap-2">
                    <CheckIcon />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="flex flex-col justify-between rounded-2xl bg-canvas p-6">
              <div>
                <p className="text-sm font-medium text-muted">BizPilot Accounting</p>
                <p className="mt-2 text-4xl font-bold tracking-tight text-ink">
                  from {formatKw(ACCOUNTING_ADDON_KW)}
                </p>
                <p className="mt-1 text-sm text-muted">per month</p>
                <p className="mt-4 text-sm leading-relaxed text-secondary">
                  {formatKw(ACCOUNTING_ADDON_KW)} minimum whether you add it to a POS plan or use
                  it alone; larger books cost more. Billed monthly in Kwacha.
                </p>
              </div>
              <div className="mt-6">
                <Link href="/sign-up?addon=accounting" className="inline-flex items-center rounded-md bg-brand px-3.5 py-2 text-sm font-medium text-white hover:bg-brand-deep">
                  See Accounting
                </Link>
                <p className="mt-4 text-sm text-secondary">
                  Example: Premium {formatKw(premium.monthlyKw)} + Accounting{" "}
                  {formatKw(ACCOUNTING_ADDON_KW)} ={" "}
                  {formatKw(premium.monthlyKw + ACCOUNTING_ADDON_KW)} a month.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section id="payroll" className="mt-16 scroll-mt-24">
          <p className="text-center text-[11px] font-semibold uppercase tracking-[0.18em] text-brand-deep">
            Payroll
          </p>
          <div className="mt-4 grid gap-8 rounded-3xl border border-border bg-surface p-6 shadow-card sm:p-8 lg:grid-cols-2">
            <div>
              <h2 className="text-2xl font-bold text-ink">BizPilot Payroll</h2>
              <p className="mt-3 leading-relaxed text-secondary">
                Run payroll every month, with PAYE, NAPSA and NHIMA worked out from rates you
                configure. Your staff get their payslips by email. You do not need a POS plan to
                use it.
              </p>
              <ul className="mt-5 space-y-2.5 text-sm text-secondary">
                {[
                  "PAYE, NAPSA and NHIMA set up from your rates",
                  "Payslip PDFs, emailed to staff",
                  "A bank payment file for every pay run",
                  "A portal where staff see their own payslips",
                  "Leave, with unpaid leave taken off pay",
                  "Import your employees from Excel",
                ].map((item) => (
                  <li key={item} className="flex items-start gap-2">
                    <CheckIcon />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="flex flex-col justify-between rounded-2xl bg-canvas p-6">
              <div>
                <p className="text-sm font-medium text-muted">BizPilot Payroll</p>
                <p className="mt-2 text-4xl font-bold tracking-tight text-ink">
                  {formatKw(PAYROLL_PER_EMPLOYEE_KW)}
                </p>
                <p className="mt-1 text-sm text-muted">per employee per month</p>
                <p className="mt-4 text-sm leading-relaxed text-secondary">
                  Billed monthly in Kwacha. Cancel anytime.
                </p>
              </div>
              <Link href="/sign-up?addon=payroll" className="mt-8 inline-flex w-fit items-center rounded-md bg-brand px-3.5 py-2 text-sm font-medium text-white hover:bg-brand-deep">
                See Payroll
              </Link>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

function GetPlanLink({
  planId,
  name,
  emphasis,
  wide,
}: {
  planId: PlanId;
  name: string;
  emphasis: "solid" | "outline";
  wide?: boolean;
}) {
  const base = wide
    ? "mt-8 block rounded-lg px-4 py-2.5 text-center text-sm font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2"
    : "inline-flex rounded-lg px-4 py-2 text-sm font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2";
  return (
    <Link
      href={`/sign-up?plan=${planId}`}
      className={
        emphasis === "solid"
          ? `${base} bg-brand-600 text-white hover:bg-brand-700`
          : `${base} bg-surface text-brand-deep ring-1 ring-brand-600 hover:bg-brand-soft`
      }
    >
      Get {name}
    </Link>
  );
}

function CheckIcon() {
  return (
    <span className="mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-mint">
      <svg viewBox="0 0 20 20" className="h-3 w-3 text-brand-deep" fill="currentColor" aria-hidden>
        <path d="M16.704 5.29a1 1 0 0 1 .006 1.414l-7.2 7.25a1 1 0 0 1-1.424.003L3.29 9.14A1 1 0 1 1 4.71 7.73l3.08 3.1 6.494-6.54a1 1 0 0 1 1.42 0Z" />
      </svg>
    </span>
  );
}

function DiamondIcon() {
  return (
    <svg viewBox="0 0 12 12" className="h-3 w-3" fill="currentColor" aria-hidden>
      <path d="M6 1.15 10.85 6 6 10.85 1.15 6Z" />
    </svg>
  );
}

function ChevronIcon() {
  return (
    <svg viewBox="0 0 20 20" className="h-4 w-4" fill="currentColor" aria-hidden>
      <path
        fillRule="evenodd"
        d="M5.23 7.21a.75.75 0 0 1 1.06.02L10 11.094l3.71-3.863a.75.75 0 1 1 1.08 1.04l-4.24 4.41a.75.75 0 0 1-1.08 0l-4.24-4.41a.75.75 0 0 1 .02-1.06Z"
        clipRule="evenodd"
      />
    </svg>
  );
}
