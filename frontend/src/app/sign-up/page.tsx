import type { Metadata } from "next";
import Link from "next/link";

import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import {
  ACCOUNTING_ADDON_KW,
  PAYROLL_PER_EMPLOYEE_KW,
  PLANS,
  formatKw,
  type PlanId,
} from "@/lib/pricing";

export const metadata: Metadata = {
  title: "Get started · BizPilot",
};

const PLAN_IDS: PlanId[] = ["basic", "premium", "enterprise"];

export default async function SignUpPage({
  searchParams,
}: {
  searchParams: Promise<{ plan?: string; addon?: string }>;
}) {
  const params = await searchParams;
  const planId = PLAN_IDS.includes(params.plan as PlanId) ? (params.plan as PlanId) : "basic";
  const plan = PLANS.find((item) => item.id === planId)!;
  const addon =
    params.addon === "payroll" ? "payroll" : params.addon === "accounting" ? "accounting" : null;

  const title =
    addon === "accounting"
      ? "Add BizPilot Accounting"
      : addon === "payroll"
        ? "Add BizPilot Payroll"
        : `Get ${plan.name}`;

  const summary =
    addon === "accounting"
      ? `Accounting starts from ${formatKw(ACCOUNTING_ADDON_KW)} per month, billed in ZMW. Add it to any POS plan or use it on its own.`
      : addon === "payroll"
        ? `Payroll is ${formatKw(PAYROLL_PER_EMPLOYEE_KW)} per employee per month, billed in ZMW. You do not need a POS plan.`
        : `${plan.name} is ${plan.monthlyKw === 0 ? "free" : `${formatKw(plan.monthlyKw)} per month`}, billed in ZMW. Create your organisation from the API today; the full sign-up screens ship with the app shell.`;

  return (
    <div className="min-h-screen bg-[#f4f7fb]">
      <SiteHeader />
      <main className="mx-auto max-w-lg px-6 py-16">
        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-brand-600">
          Get started
        </p>
        <h1 className="mt-3 text-3xl font-bold tracking-tight text-slate-900">{title}</h1>
        <p className="mt-3 text-slate-600">{summary}</p>
        {addon ? null : (
          <p className="mt-6 rounded-2xl border border-slate-200 bg-white p-5 text-sm text-slate-700 shadow-sm">
            {plan.blurb}
          </p>
        )}
        <div className="mt-8 flex flex-wrap gap-3">
          <Link
            href="/pricing"
            className="rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-700"
          >
            Back to pricing
          </Link>
          <Link href="/" className="rounded-lg px-4 py-2.5 text-sm font-medium text-slate-700">
            Home
          </Link>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
