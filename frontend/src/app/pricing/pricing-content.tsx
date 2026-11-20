"use client";

import Link from "next/link";
import { useState } from "react";

import {
  ACCOUNTING_ADDON_KW,
  BILLING_COUNTRIES,
  PAYROLL_PER_EMPLOYEE_KW,
  PLANS,
  STORE_TYPES,
  TRUSTED_BY,
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
        className="pointer-events-none absolute inset-0 bg-grid bg-[length:44px_44px]"
      />
      <div className="relative mx-auto max-w-6xl px-4 py-14 sm:px-6 sm:py-16">
        <div className="mx-auto max-w-3xl text-center">
          <p className="inline-flex items-center gap-1.5 rounded-full bg-brand-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-brand-600 ring-1 ring-brand-100">
            <DiamondIcon />
            Pricing
          </p>
          <h1 className="mt-5 text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
            Subscription plans
          </h1>
          <p className="mt-4 text-lg font-medium text-brand-600 sm:text-xl">
            Prices for POS, accounting and payroll in Zambia
          </p>
          <p className="mt-4 text-base leading-relaxed text-slate-500">
            Three plans, one price list. Pick the one that fits your business in Zambia. Plans
            are per store, billed monthly in Kwacha. Cancel anytime.{" "}
            <Link href="/#pos" className="font-medium text-brand-600 hover:text-brand-700">
              See what the POS does
            </Link>
            .
          </p>
        </div>

        <div className="mx-auto mt-10 max-w-xl text-center">
          <label htmlFor="billing-country" className="text-sm font-medium text-slate-800">
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
              className="w-full appearance-none rounded-xl border border-slate-200 bg-white py-3 pl-12 pr-10 text-left text-sm text-slate-800 shadow-sm outline-none ring-brand-500 focus:border-brand-500 focus:ring-2"
            >
              {BILLING_COUNTRIES.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.label}
                </option>
              ))}
            </select>
            <span className="pointer-events-none absolute inset-y-0 right-3 flex items-center text-slate-400">
              <ChevronIcon />
            </span>
          </div>
          <p className="mt-2 text-sm text-slate-500">
            You are billed in Zambian Kwacha whichever country you pick.
          </p>
        </div>

        <div className="mt-8 flex justify-center">
          <div
            className="inline-flex max-w-full flex-wrap justify-center gap-1 rounded-full bg-white p-1 shadow-sm ring-1 ring-slate-200"
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
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                  }`}
                >
                  {type.label}
                </button>
              );
            })}
          </div>
        </div>
        <p className="mt-4 text-center text-sm text-slate-500">
          Prices are the same for every store type — the tabs only change what each plan unlocks.
        </p>
        {storeType === "manufacturer" ? (
          <p className="mt-2 text-center text-sm text-slate-600">
            Manufacturing bills of materials stay off every plan, including Entreprise.
          </p>
        ) : null}

        <div className="mt-12 grid items-stretch gap-6 lg:grid-cols-3">
          {PLANS.map((plan) => {
            const included = planCardFeatures(plan.id, storeType);
            return (
              <article
                key={plan.id}
                className={`relative flex flex-col rounded-3xl bg-white p-6 shadow-card sm:p-8 ${
                  plan.popular ? "border-2 border-brand-600" : "border border-slate-200"
                }`}
              >
                {plan.popular ? (
                  <p className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-brand-600 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-white">
                    Most popular
                  </p>
                ) : null}
                <h2 className="text-xl font-bold text-slate-900">{plan.name}</h2>
                <p className="mt-2 min-h-12 text-sm leading-relaxed text-slate-500">
                  {planBlurb(plan.id, storeType)}
                </p>
                <p className="mt-6 flex items-end gap-2">
                  <span className="text-4xl font-bold tracking-tight text-slate-900">
                    {formatKw(plan.monthlyKw)}
                  </span>
                  {plan.monthlyKw === 0 ? null : (
                    <span className="mb-1 text-sm font-medium text-slate-500">per month</span>
                  )}
                </p>
                <ul className="mt-6 flex-1 space-y-2.5 text-sm text-slate-700">
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
          <p className="text-center text-[11px] font-semibold uppercase tracking-[0.22em] text-brand-600">
            Compare
          </p>
          <h2
            id="compare-heading"
            className="mt-3 text-center text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl"
          >
            {heading}
          </h2>
          <p className="mt-4 text-center text-xs text-slate-500 sm:hidden">
            Swipe sideways to compare Basic, Premium and Entreprise
          </p>
          <div className="mt-6 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm sm:mt-8">
            <div className="overflow-x-auto">
              <table className="min-w-[720px] w-full text-sm">
                <thead>
                  <tr className="bg-slate-50">
                    <th className="sticky left-0 z-10 w-44 max-w-44 bg-slate-50 px-4 py-5 text-left text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500 sm:w-auto sm:max-w-none sm:px-6">
                      What you get
                    </th>
                    {PLANS.map((plan) => (
                      <th key={plan.id} className="min-w-[7.5rem] px-3 py-5 text-center sm:px-4">
                        <div className="text-sm font-semibold text-slate-900">{plan.name}</div>
                        <div className="mt-0.5 text-xs font-medium text-slate-500">
                          {plan.monthlyKw === 0 ? "Free" : `${formatKw(plan.monthlyKw)}/mo`}
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {features.map((feature) => (
                    <tr key={feature} className="border-t border-slate-100">
                      <th
                        scope="row"
                        className="sticky left-0 w-44 max-w-44 bg-white px-4 py-3.5 text-left font-normal text-slate-700 shadow-[6px_0_10px_-8px_rgba(15,23,42,0.35)] sm:w-auto sm:max-w-none sm:px-6"
                      >
                        {featureLabel(storeType, feature)}
                      </th>
                      {PLANS.map((plan) => {
                        const included = planIncludes(plan.id, feature);
                        return (
                          <td key={plan.id} className="px-4 py-3.5 text-center">
                            {included ? (
                              <span className="inline-flex justify-center text-emerald-500">
                                <CheckIcon />
                                <span className="sr-only">Included</span>
                              </span>
                            ) : (
                              <span className="text-slate-300" aria-label="Not included">
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
                  <tr className="border-t border-slate-100 bg-slate-50">
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

        <section className="mt-20 text-center">
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">Trusted by</h2>
          <ul className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            {TRUSTED_BY.map((name) => (
              <li
                key={name}
                className="rounded-2xl border border-slate-200 bg-white px-4 py-6 text-sm font-semibold text-slate-800 shadow-sm"
              >
                {name}
              </li>
            ))}
          </ul>
        </section>

        <section id="accounting" className="mt-20 scroll-mt-24">
          <p className="text-center text-[11px] font-semibold uppercase tracking-[0.18em] text-brand-600">
            Add-on or standalone
          </p>
          <div className="mt-4 grid gap-8 rounded-3xl border border-slate-200 bg-white p-6 shadow-card sm:p-8 lg:grid-cols-2">
            <div>
              <h2 className="text-2xl font-bold text-slate-900">Add BizPilot Accounting</h2>
              <p className="mt-3 leading-relaxed text-slate-600">
                Full bookkeeping run for you and kept on our cloud. We give you your own login,
                set it up and keep it backed up. Add it to any POS plan, or take it on its own
                if you do not need a till.
              </p>
              <ul className="mt-5 space-y-2.5 text-sm text-slate-700">
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
            <div className="flex flex-col justify-between rounded-2xl bg-slate-50 p-6">
              <div>
                <p className="text-sm font-medium text-slate-500">BizPilot Accounting</p>
                <p className="mt-2 text-4xl font-bold tracking-tight text-slate-900">
                  from {formatKw(ACCOUNTING_ADDON_KW)}
                </p>
                <p className="mt-1 text-sm text-slate-500">per month</p>
                <p className="mt-4 text-sm leading-relaxed text-slate-600">
                  {formatKw(ACCOUNTING_ADDON_KW)} minimum whether you add it to a POS plan or use
                  it alone; larger books cost more. Billed monthly in Kwacha.
                </p>
              </div>
              <div className="mt-6">
                <Link
                  href="/sign-up?addon=accounting"
                  className="inline-flex rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-700"
                >
                  See Accounting
                </Link>
                <p className="mt-4 text-sm text-slate-600">
                  Example: Premium {formatKw(premium.monthlyKw)} + Accounting{" "}
                  {formatKw(ACCOUNTING_ADDON_KW)} ={" "}
                  {formatKw(premium.monthlyKw + ACCOUNTING_ADDON_KW)} a month.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section id="payroll" className="mt-16 scroll-mt-24">
          <p className="text-center text-[11px] font-semibold uppercase tracking-[0.18em] text-brand-600">
            Payroll
          </p>
          <div className="mt-4 grid gap-8 rounded-3xl border border-slate-200 bg-white p-6 shadow-card sm:p-8 lg:grid-cols-2">
            <div>
              <h2 className="text-2xl font-bold text-slate-900">BizPilot Payroll</h2>
              <p className="mt-3 leading-relaxed text-slate-600">
                Run payroll every month, with PAYE, NAPSA and NHIMA worked out from rates you
                configure. Your staff get their payslips by email. You do not need a POS plan to
                use it.
              </p>
              <ul className="mt-5 space-y-2.5 text-sm text-slate-700">
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
            <div className="flex flex-col justify-between rounded-2xl bg-slate-50 p-6">
              <div>
                <p className="text-sm font-medium text-slate-500">BizPilot Payroll</p>
                <p className="mt-2 text-4xl font-bold tracking-tight text-slate-900">
                  {formatKw(PAYROLL_PER_EMPLOYEE_KW)}
                </p>
                <p className="mt-1 text-sm text-slate-500">per employee per month</p>
                <p className="mt-4 text-sm leading-relaxed text-slate-600">
                  Billed monthly in Kwacha. Cancel anytime.
                </p>
              </div>
              <Link
                href="/sign-up?addon=payroll"
                className="mt-8 inline-flex w-fit rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-700"
              >
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
    ? "mt-8 block rounded-lg px-4 py-2.5 text-center text-sm font-semibold transition"
    : "inline-flex rounded-lg px-4 py-2 text-sm font-semibold transition";
  return (
    <Link
      href={`/sign-up?plan=${planId}`}
      className={
        emphasis === "solid"
          ? `${base} bg-brand-600 text-white hover:bg-brand-700`
          : `${base} bg-white text-brand-600 ring-1 ring-brand-600 hover:bg-brand-50`
      }
    >
      Get {name}
    </Link>
  );
}

function CheckIcon() {
  return (
    <svg
      viewBox="0 0 20 20"
      className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500"
      fill="currentColor"
      aria-hidden
    >
      <path d="M16.704 5.29a1 1 0 0 1 .006 1.414l-7.2 7.25a1 1 0 0 1-1.424.003L3.29 9.14A1 1 0 1 1 4.71 7.73l3.08 3.1 6.494-6.54a1 1 0 0 1 1.42 0Z" />
    </svg>
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
