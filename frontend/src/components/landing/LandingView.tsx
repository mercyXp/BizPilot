"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import {
  BarChart3,
  Boxes,
  Landmark,
  ShieldCheck,
  Sparkles,
  Store,
  Wallet,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Logo, LogoMark } from "@/components/ui/logo";
import { SiteFooter } from "@/components/marketing/SiteFooter";
import { SiteHeader } from "@/components/marketing/SiteHeader";
import { fadeUp, heroContainer, scaleIn, staggerContainer, withReducedMotion } from "@/lib/motion";
import { Reveal } from "@/components/motion/Reveal";
import { chartColors } from "@/lib/colors";

const features = [
  {
    icon: Store,
    title: "Store operations",
    body: "Sales, purchases, inventory and expenses in one workspace built for Zambia-first retail.",
  },
  {
    icon: Landmark,
    title: "Accounts that post",
    body: "Double-entry stays the source of truth. Status colours mean the same thing in every module.",
  },
  {
    icon: Boxes,
    title: "Stock you can trust",
    body: "Storage centres, transfers and sections so bakery, butchery and shop floor stay distinct.",
  },
  {
    icon: BarChart3,
    title: "Reports that read clearly",
    body: "Revenue teal, expenses amber, profit green — the same palette on every chart and legend.",
  },
  {
    icon: Wallet,
    title: "Money in, money out",
    body: "Customer balances, supplier bills and expenses use semantic colour, not decoration.",
  },
  {
    icon: Sparkles,
    title: "BizPilot AI",
    body: "Grok only acts through tools. Insights are purple so you always know what the model produced.",
  },
];

const steps = [
  { n: "01", title: "Create your organisation", body: "Verify email, then open a tenant. Default currency is ZMW." },
  { n: "02", title: "Invite the floor team", body: "Owners invite store assistants. They join with the same email address." },
  { n: "03", title: "Run the shop", body: "Sell, count, report and keep ZRA and integrations ready when you enrol." },
];

const plans = [
  { name: "Basic", price: "Free", body: "Sales, sales returns, customers and expense tracking.", cta: "Get Basic", href: "/sign-up?plan=basic", featured: false },
  { name: "Premium", price: "K320", body: "Inventory, purchasing, reports and store assistants. Billed monthly in ZMW.", cta: "Get Premium", href: "/sign-up?plan=premium", featured: true },
  { name: "Entreprise", price: "K490", body: "AI assistant, ZRA Smart Invoice and integrations. Manufacturing stays off.", cta: "Get Entreprise", href: "/sign-up?plan=enterprise", featured: false },
];

function DashboardPreview() {
  const reduce = useReducedMotion();
  return (
    <motion.div
      variants={withReducedMotion(reduce, scaleIn(0.15))}
      className={reduce ? undefined : "animate-float"}
    >
      <div className="overflow-hidden rounded-2xl border border-border bg-surface shadow-lift">
        <div className="flex items-center justify-between border-b border-border px-4 py-2.5">
          <div className="flex items-center gap-2">
            <LogoMark size={24} />
            <span className="text-xs font-medium text-ink">Store dashboard</span>
          </div>
          <span className="rounded-full bg-brand-soft px-2 py-0.5 text-[10px] font-medium text-brand-deep">Live preview</span>
        </div>
        <div className="grid gap-3 p-4 sm:grid-cols-4">
          {[
            { label: "Today’s sales", value: "ZMW 0", color: chartColors.revenue },
            { label: "Items sold", value: "0", color: chartColors.sales },
            { label: "Profit", value: "ZMW 0", color: chartColors.profit },
            { label: "Low stock", value: "0", color: chartColors.expenses },
          ].map((kpi) => (
            <div key={kpi.label} className="rounded-lg border border-border p-3">
              <p className="text-[10px] uppercase tracking-wide text-secondary">{kpi.label}</p>
              <p className="mt-1 text-sm font-semibold text-ink">{kpi.value}</p>
              <span className="mt-2 block h-1 rounded-full" style={{ background: kpi.color }} />
            </div>
          ))}
        </div>
        <div className="grid gap-3 px-4 pb-4 sm:grid-cols-3">
          <div className="sm:col-span-2 rounded-lg border border-border p-3">
            <p className="text-xs font-medium text-ink">Sales overview</p>
            <svg viewBox="0 0 320 96" className="mt-2 h-24 w-full" role="img" aria-label="Empty revenue trend">
              <line x1="0" y1="80" x2="320" y2="80" stroke="#E5E7EB" />
              <line x1="0" y1="48" x2="320" y2="48" stroke="#E5E7EB" />
              <path d="M0 80 H320" stroke={chartColors.revenue} strokeWidth="2" fill="none" />
            </svg>
          </div>
          <div className="rounded-lg border border-border p-3">
            <p className="text-xs font-medium text-ink">Statuses</p>
            <div className="mt-2 space-y-1.5 text-[11px]">
              <p><span className="mr-2 inline-block h-2 w-2 rounded-full bg-success" />Paid</p>
              <p><span className="mr-2 inline-block h-2 w-2 rounded-full bg-warning" />Pending</p>
              <p><span className="mr-2 inline-block h-2 w-2 rounded-full bg-danger" />Failed</p>
              <p><span className="mr-2 inline-block h-2 w-2 rounded-full bg-ai" />AI insight</p>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

export function LandingView({ apiOk }: { apiOk: boolean }) {
  const reduce = useReducedMotion();
  const item = withReducedMotion(reduce, fadeUp());

  return (
    <div className="relative overflow-hidden bg-canvas">
      <div
        aria-hidden
        className="pointer-events-none absolute -left-24 -top-24 h-80 w-80 rounded-full bg-brand/15 blur-3xl animate-ambient-shift"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute right-0 top-32 h-72 w-72 rounded-full bg-brand-soft blur-3xl animate-ambient-shift"
      />

      <SiteHeader active="home" />

      <motion.section
        className="relative mx-auto grid max-w-6xl items-center gap-12 px-6 pb-20 pt-8 lg:grid-cols-2"
        variants={heroContainer}
        initial="hidden"
        animate="show"
      >
        <div>
          <motion.div variants={item} className="mb-5">
            <Logo height={52} priority />
          </motion.div>
          <motion.h1 variants={item} className="text-4xl font-semibold tracking-tight text-ink sm:text-5xl">
            Run the shop. Keep the books honest.
          </motion.h1>
          <motion.p variants={item} className="mt-4 max-w-lg text-base text-secondary">
            BizPilot is a Zambia-first operations platform for sales, inventory, expenses and
            reporting. Teal is the brand. Colour elsewhere means status, risk or insight.
          </motion.p>
          <motion.div variants={item} className="mt-7 flex flex-wrap gap-3">
            <Button href="/sign-up" size="lg" arrow>
              Start free trial
            </Button>
            <Button href="/sign-in" size="lg" variant="outline">
              Sign in
            </Button>
            <Button href="/demo" size="lg" variant="outline">
              Explore Live Demo
            </Button>
          </motion.div>
          <motion.p variants={item} className="mt-4 text-xs text-muted">
            API {apiOk ? "connected" : "unreachable"} · English first · ZMW default
          </motion.p>
        </div>
        <div id="demo">
          <DashboardPreview />
        </div>
      </motion.section>

      <section id="pos" className="relative mx-auto max-w-6xl scroll-mt-24 px-6 py-16">
        <Reveal>
          <h2 className="text-2xl font-semibold text-ink">Built for day-to-day operations</h2>
          <p className="mt-2 max-w-2xl text-sm text-secondary">
            The same information architecture as your store: dashboard, sales, purchases, inventory,
            expenses, assistants, reports, compliance.
          </p>
        </Reveal>
        <motion.div
          className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
          variants={staggerContainer(0.08)}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, amount: 0.15 }}
        >
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <motion.article
                key={feature.title}
                variants={item}
                className="card-hover rounded-xl border border-border bg-surface p-5 shadow-card"
              >
                <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-soft text-brand-deep transition-transform duration-standard ease-entrance group-hover:scale-105">
                  <Icon className="h-4 w-4 transition-transform duration-standard hover:rotate-3" />
                </span>
                <h3 className="mt-3 text-sm font-semibold text-ink">{feature.title}</h3>
                <p className="mt-1 text-sm text-secondary">{feature.body}</p>
              </motion.article>
            );
          })}
        </motion.div>
      </section>

      <section className="relative mx-auto max-w-6xl px-6 py-16">
        <Reveal>
          <h2 className="text-2xl font-semibold text-ink">How it works</h2>
        </Reveal>
        <div className="relative mt-8 grid gap-6 md:grid-cols-3">
          <div className="pointer-events-none absolute left-[16%] right-[16%] top-6 hidden h-px bg-border md:block" />
          {steps.map((step, index) => (
            <Reveal key={step.n} delay={index * 0.08}>
              <div className="relative rounded-xl border border-border bg-surface p-5 shadow-card">
                <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-brand text-xs font-semibold text-white">
                  {step.n}
                </span>
                <h3 className="mt-3 text-sm font-semibold text-ink">{step.title}</h3>
                <p className="mt-1 text-sm text-secondary">{step.body}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      <section className="relative mx-auto max-w-6xl px-6 py-16">
        <Reveal>
          <h2 className="text-2xl font-semibold text-ink">Simple plans</h2>
          <p className="mt-2 text-sm text-secondary">
            Basic is free. Premium is K320 a month. Entreprise is K490.{" "}
            <Link href="/pricing" className="font-medium text-brand hover:text-brand-deep">
              Compare what each store type gets
            </Link>
            .
          </p>
        </Reveal>
        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {plans.map((plan, index) => (
            <Reveal key={plan.name} delay={index * 0.08}>
              <article
                className={
                  plan.featured
                    ? "rounded-xl border-2 border-brand bg-surface p-6 shadow-lift"
                    : "rounded-xl border border-border bg-surface p-6 shadow-card"
                }
              >
                {plan.featured ? (
                  <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-brand">Recommended</p>
                ) : null}
                <h3 className="text-sm font-semibold text-ink">{plan.name}</h3>
                <p className="mt-1 text-2xl font-semibold text-ink">{plan.price}</p>
                <p className="mt-2 text-sm text-secondary">{plan.body}</p>
                <Button href="/pricing" className="mt-5 w-full" variant={plan.featured ? "primary" : "outline"}>
                  {plan.cta}
                </Button>
              </article>
            </Reveal>
          ))}
        </div>
      </section>

      <section className="relative mx-auto max-w-6xl px-6 py-16">
        <Reveal>
          <div className="rounded-2xl border border-border bg-surface px-8 py-12 text-center shadow-card">
            <ShieldCheck className="mx-auto h-8 w-8 text-brand" />
            <h2 className="mt-4 text-2xl font-semibold text-ink">Ready when the till is.</h2>
            <p className="mx-auto mt-2 max-w-lg text-sm text-secondary">
              Create an account, verify email, then open your first organisation. No dark mode, no
              navy chrome — teal, black text, and colour that means something.
            </p>
            <div className="mt-6 flex justify-center gap-3">
              <Button href="/sign-up" size="lg" arrow>
                Create account
              </Button>
              <Button href="/sign-in" size="lg" variant="outline">
                Sign in
              </Button>
            </div>
          </div>
        </Reveal>
      </section>

      <SiteFooter />
    </div>
  );
}
