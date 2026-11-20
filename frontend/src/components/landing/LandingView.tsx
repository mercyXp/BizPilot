
"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import {
  ArrowRight,
  BarChart3,
  Boxes,
  Check,
  ChevronRight,
  Landmark,
  ShieldCheck,
  Sparkles,
  Store,
  Wallet,
  ShoppingCart,
  Users,
  TrendingUp,
  Zap,
  Globe2,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Logo, LogoMark } from "@/components/ui/logo";
import { SiteFooter } from "@/components/marketing/SiteFooter";
import { SiteHeader } from "@/components/marketing/SiteHeader";
import {
  fadeUp,
  scaleIn,
  staggerContainer,
  withReducedMotion,
} from "@/lib/motion";
import { Reveal } from "@/components/motion/Reveal";
import { chartColors } from "@/lib/colors";

const features = [
  {
    icon: Store,
    number: "01",
    title: "Store operations",
    body: "Manage sales, purchases, inventory and expenses from one connected workspace.",
    color: "bg-brand-soft",
  },
  {
    icon: Landmark,
    number: "02",
    title: "Accounting",
    body: "Keep your double-entry records organised and understand your financial position.",
    color: "bg-blue-50",
  },
  {
    icon: Boxes,
    number: "03",
    title: "Inventory control",
    body: "Track stock across storage centres, transfers and sections with greater accuracy.",
    color: "bg-emerald-50",
  },
  {
    icon: BarChart3,
    number: "04",
    title: "Business intelligence",
    body: "Understand revenue, expenses and profit through clear business reports.",
    color: "bg-amber-50",
  },
  {
    icon: Wallet,
    number: "05",
    title: "Financial management",
    body: "Keep track of customer balances, supplier bills and business expenses.",
    color: "bg-violet-50",
  },
  {
    icon: Sparkles,
    number: "06",
    title: "BizPilot AI",
    body: "Get AI-powered assistance and insights through supported business tools.",
    color: "bg-purple-50",
  },
];

const steps = [
  {
    n: "01",
    title: "Create your organisation",
    body: "Register, verify your email and set up your business. Your default currency is ZMW.",
    icon: Store,
  },
  {
    n: "02",
    title: "Bring your team on board",
    body: "Invite store assistants and give your team access to the tools they need.",
    icon: Users,
  },
  {
    n: "03",
    title: "Take control",
    body: "Manage sales, monitor stock, review reports and run your business with clarity.",
    icon: TrendingUp,
  },
];

const plans = [
  {
    name: "Basic",
    price: "Free",
    description: "A simple starting point for your store.",
    features: [
      "Sales and receipts",
      "Sales returns and credit notes",
      "Customers and what they owe",
      "Expense tracking",
    ],
    cta: "Get Basic",
    href: "/sign-up?plan=basic",
    featured: false,
  },
  {
    name: "Premium",
    price: "K320",
    description: "Everything you need to manage daily operations.",
    features: [
      "Everything in Basic",
      "Inventory and stock transfers",
      "Purchases and supplier management",
      "Purchase returns",
      "Business reports and analytics",
      "Store assistants and permissions",
      "Cashier shifts and cash management",
    ],
    cta: "Get Premium",
    href: "/sign-up?plan=premium",
    featured: true,
  },
  {
    name: "Entreprise",
    price: "K490",
    description: "Advanced tools for growing businesses.",
    features: [
      "Everything in Premium",
      "AI business assistant",
      "ZRA Smart Invoice",
      "External integrations",
      "Advanced business reporting",
    ],
    cta: "Get Entreprise",
    href: "/sign-up?plan=enterprise",
    featured: false,
  },
];

function DashboardPreview() {
  const reduce = useReducedMotion();

  return (
    <motion.div
      variants={withReducedMotion(reduce, scaleIn(0.15))}
      className="relative mx-auto w-full max-w-xl"
    >
      {/* Decorative glow */}
      <div className="absolute inset-8 rounded-full bg-brand/20 blur-3xl" />

      <div className="relative overflow-hidden rounded-2xl border border-white/70 bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <div className="flex items-center gap-2.5">
            <LogoMark size={30} />
            <div>
              <p className="text-sm font-semibold text-ink">
                Business overview
              </p>
              <p className="text-[10px] text-muted">
                Your store at a glance
              </p>
            </div>
          </div>

          <span className="rounded-full bg-brand-soft px-3 py-1 text-[10px] font-semibold text-brand-deep">
            Dashboard
          </span>
        </div>

        <div className="grid grid-cols-2 gap-3 p-4 sm:grid-cols-4">
          {[
            { label: "Today's sales", value: "ZMW 0", color: chartColors.revenue },
            { label: "Items sold", value: "0", color: chartColors.sales },
            { label: "Profit", value: "ZMW 0", color: chartColors.profit },
            { label: "Low stock", value: "0", color: chartColors.expenses },
          ].map((item) => (
            <div
              key={item.label}
              className="rounded-xl border border-border bg-canvas/60 p-3"
            >
              <p className="text-[9px] font-medium text-secondary">
                {item.label}
              </p>
              <p className="mt-2 text-sm font-bold text-ink">
                {item.value}
              </p>
              <div
                className="mt-3 h-1 rounded-full"
                style={{ background: item.color }}
              />
            </div>
          ))}
        </div>

        <div className="grid gap-3 px-4 pb-4 sm:grid-cols-5">
          <div className="rounded-xl border border-border p-4 sm:col-span-3">
            <div className="flex items-center justify-between">
              <p className="text-xs font-semibold text-ink">Sales overview</p>
              <span className="text-[10px] text-muted">Overview</span>
            </div>

            <svg
              viewBox="0 0 320 120"
              className="mt-4 h-28 w-full"
              role="img"
              aria-label="Sales overview chart preview"
            >
              {[25, 55, 85].map((y) => (
                <line
                  key={y}
                  x1="0"
                  y1={y}
                  x2="320"
                  y2={y}
                  stroke="#E2E8F0"
                  strokeDasharray="4 4"
                />
              ))}
              <path
                d="M0 85 H320"
                stroke={chartColors.revenue}
                strokeWidth="2"
                fill="none"
              />
            </svg>
          </div>

          <div className="rounded-xl border border-border p-4 sm:col-span-2">
            <p className="text-xs font-semibold text-ink">Business activity</p>

            <div className="mt-4 space-y-4 text-[11px]">
              {[
                ["Sales", "bg-brand"],
                ["Purchases", "bg-warning"],
                ["Expenses", "bg-danger"],
                ["AI insights", "bg-ai"],
              ].map(([label, color]) => (
                <div key={label} className="flex items-center gap-2">
                  <span className={`h-2 w-2 rounded-full ${color}`} />
                  <span className="text-secondary">{label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Floating product labels */}
      <div className="absolute -left-5 top-1/4 hidden rounded-xl border border-border bg-white p-3 shadow-xl sm:flex sm:items-center sm:gap-2">
        <div className="rounded-lg bg-brand-soft p-2 text-brand">
          <ShoppingCart size={17} />
        </div>
        <span className="text-xs font-semibold text-ink">POS management</span>
      </div>

      <div className="absolute -right-5 bottom-12 hidden rounded-xl border border-border bg-white p-3 shadow-xl sm:flex sm:items-center sm:gap-2">
        <div className="rounded-lg bg-emerald-50 p-2 text-emerald-600">
          <Boxes size={17} />
        </div>
        <span className="text-xs font-semibold text-ink">Inventory control</span>
      </div>
    </motion.div>
  );
}

export function LandingView({ apiOk }: { apiOk: boolean }) {
  const reduce = useReducedMotion();
  const item = withReducedMotion(reduce, fadeUp());

  return (
    <main className="overflow-hidden bg-canvas text-ink">

      {/* HERO */}
      <section className="relative isolate min-h-[680px] overflow-hidden">
        <SiteHeader active="home" />

        {/* Replace this image with your BizPilot hero illustration */}
        <div
          aria-hidden="true"
          className="absolute inset-0 -z-20 bg-[url('/images/bizpilot-hero-illustration.png')] bg-cover bg-center opacity-20 blur-[3px]"
        />

        <div className="absolute inset-0 -z-10 bg-gradient-to-r from-canvas via-canvas/95 to-canvas/65" />

        <div className="pointer-events-none absolute -left-32 top-20 -z-10 h-96 w-96 rounded-full bg-brand/15 blur-3xl" />
        <div className="pointer-events-none absolute right-0 top-32 -z-10 h-96 w-96 rounded-full bg-brand-soft blur-3xl" />

        <motion.div
          className="relative mx-auto grid max-w-7xl items-center gap-14 px-6 pb-24 pt-20 lg:grid-cols-2 lg:pt-24"
          variants={staggerContainer(0.1)}
          initial="hidden"
          animate="show"
        >
          <div className="max-w-xl">
            <motion.div variants={item}>
              <span className="inline-flex items-center gap-2 rounded-full border border-brand/20 bg-white/80 px-4 py-2 text-xs font-semibold text-brand-deep shadow-sm">
                <span className="h-2 w-2 rounded-full bg-brand" />
                BUSINESS MANAGEMENT, SIMPLIFIED
              </span>
            </motion.div>

            <motion.h1
              variants={item}
              className="mt-7 text-5xl font-bold leading-[1.08] tracking-tight text-ink sm:text-6xl lg:text-[68px]"
            >
              Run your business.
              <span className="block text-brand">
                Keep everything
                <br />
                in control.
              </span>
            </motion.h1>

            <motion.p
              variants={item}
              className="mt-6 max-w-lg text-base leading-7 text-secondary sm:text-lg"
            >
              From sales and inventory to purchasing, accounting and payroll,
              BizPilot brings your retail operations together in one powerful
              platform built for businesses in Zambia.
            </motion.p>

            <motion.div
              variants={item}
              className="mt-8 flex flex-wrap gap-3"
            >
              <Button href="/sign-up" size="lg" arrow>
                Get started for free
              </Button>

              <Button href="/demo" size="lg" variant="outline">
                Explore live demo
              </Button>
            </motion.div>

            <motion.div
              variants={item}
              className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-3 text-xs font-medium text-secondary"
            >
              <span className="flex items-center gap-2">
                <Check className="h-4 w-4 text-brand" />
                Free Basic plan
              </span>
              <span className="flex items-center gap-2">
                <Check className="h-4 w-4 text-brand" />
                Zambian Kwacha
              </span>
              <span className="flex items-center gap-2">
                <Check className="h-4 w-4 text-brand" />
                Easy onboarding
              </span>
            </motion.div>
          </div>

          <div className="relative" id="demo">
            <DashboardPreview />
          </div>
        </motion.div>

        {/* MODULE STRIP */}
        <div className="border-y border-border/70 bg-white/75 backdrop-blur-xl">
          <div className="mx-auto flex max-w-7xl flex-wrap justify-center gap-x-10 gap-y-4 px-6 py-5 text-xs font-semibold text-secondary">
            {[
              [ShoppingCart, "Point of Sale"],
              [Boxes, "Inventory"],
              [Store, "Purchasing"],
              [Landmark, "Accounting"],
              [Users, "Payroll"],
              [BarChart3, "Reports"],
            ].map(([Icon, label]: any) => (
              <div key={label} className="flex items-center gap-2">
                <Icon className="h-4 w-4 text-brand" />
                {label}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section
        id="pos"
        className="mx-auto max-w-7xl scroll-mt-24 px-6 py-24"
      >
        <Reveal>
          <div className="mx-auto max-w-2xl text-center">
            <span className="rounded-full bg-brand-soft px-4 py-2 text-xs font-semibold text-brand-deep">
              ONE CONNECTED PLATFORM
            </span>

            <h2 className="mt-6 text-3xl font-bold tracking-tight sm:text-4xl">
              Everything your store needs.
              <span className="block text-brand">All in one place.</span>
            </h2>

            <p className="mt-4 text-sm leading-7 text-secondary sm:text-base">
              Stop jumping between disconnected systems. Manage the important
              parts of your business from one organised workspace.
            </p>
          </div>
        </Reveal>

        <motion.div
          className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-3"
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
                className="group rounded-2xl border border-border bg-white p-7 shadow-card transition-all duration-300 hover:-translate-y-1 hover:border-brand/40 hover:shadow-lift"
              >
                <div className="flex items-center justify-between">
                  <div
                    className={`flex h-12 w-12 items-center justify-center rounded-xl ${feature.color} text-brand-deep`}
                  >
                    <Icon size={23} />
                  </div>
                  <span className="text-xs font-semibold text-muted">
                    {feature.number}
                  </span>
                </div>

                <h3 className="mt-6 text-lg font-semibold text-ink">
                  {feature.title}
                </h3>

                <p className="mt-3 text-sm leading-6 text-secondary">
                  {feature.body}
                </p>

                <div className="mt-6 flex items-center gap-2 text-xs font-semibold text-brand opacity-0 transition-opacity group-hover:opacity-100">
                  Discover more <ArrowRight size={14} />
                </div>
              </motion.article>
            );
          })}
        </motion.div>
      </section>

      {/* VALUE PROPOSITION */}
      <section className="relative overflow-hidden bg-white py-24">
        <div className="pointer-events-none absolute -right-20 top-0 h-96 w-96 rounded-full bg-brand-soft/70 blur-3xl" />

        <div className="relative mx-auto grid max-w-7xl items-center gap-14 px-6 lg:grid-cols-2">
          <Reveal>
            <span className="rounded-full bg-brand-soft px-4 py-2 text-xs font-semibold text-brand-deep">
              WHY BIZPILOT
            </span>

            <h2 className="mt-6 text-3xl font-bold leading-tight sm:text-4xl">
              More control.
              <span className="block text-brand">
                Less guesswork.
              </span>
            </h2>

            <p className="mt-5 max-w-lg text-base leading-7 text-secondary">
              Your business deserves more than scattered records and manual
              processes. BizPilot gives you a connected view of your daily
              operations so you can make better-informed decisions.
            </p>

            <div className="mt-8 grid gap-4 sm:grid-cols-2">
              {[
                "Know your business performance",
                "Improve stock accountability",
                "Better visibility into operations",
                "Easier financial monitoring",
                "Smarter purchasing decisions",
                "Less reliance on manual processes",
              ].map((benefit) => (
                <div key={benefit} className="flex items-start gap-3">
                  <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand-soft text-brand">
                    <Check size={12} />
                  </span>
                  <span className="text-sm text-secondary">{benefit}</span>
                </div>
              ))}
            </div>

            <Button href="/demo" className="mt-9" arrow>
              Discover BizPilot
            </Button>
          </Reveal>

          <Reveal delay={0.15}>
            <div className="relative rounded-3xl bg-gradient-to-br from-brand-soft via-canvas to-blue-50 p-6 sm:p-10">
              <div className="absolute right-8 top-8 rounded-full bg-white p-3 shadow-card">
                <Sparkles className="h-5 w-5 text-brand" />
              </div>

              <div className="rounded-2xl border border-white bg-white p-5 shadow-lift">
                <div className="flex items-center gap-3 border-b border-border pb-4">
                  <LogoMark size={32} />
                  <div>
                    <p className="text-sm font-bold">BizPilot</p>
                    <p className="text-xs text-muted">Business dashboard</p>
                  </div>
                </div>

                <div className="mt-6 grid grid-cols-2 gap-3">
                  {[
                    ["Sales", "ZMW", chartColors.revenue],
                    ["Profit", "ZMW", chartColors.profit],
                    ["Inventory", "Stock", chartColors.sales],
                    ["Expenses", "ZMW", chartColors.expenses],
                  ].map(([label, value, color]) => (
                    <div
                      key={label}
                      className="rounded-xl bg-canvas p-4"
                    >
                      <span
                        className="mb-3 block h-1 w-8 rounded-full"
                        style={{ background: color }}
                      />
                      <p className="text-xs text-secondary">{label}</p>
                      <p className="mt-1 text-sm font-bold text-ink">
                        {value}
                      </p>
                    </div>
                  ))}
                </div>

                <div className="mt-4 rounded-xl bg-brand p-5 text-white">
                  <p className="text-xs font-medium text-white/70">
                    One platform. Connected operations.
                  </p>
                  <p className="mt-2 text-xl font-bold">
                    Run with clarity.
                  </p>
                </div>
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="mx-auto max-w-7xl px-6 py-24">
        <Reveal>
          <div className="text-center">
            <span className="rounded-full bg-brand-soft px-4 py-2 text-xs font-semibold text-brand-deep">
              GET STARTED
            </span>
            <h2 className="mt-6 text-3xl font-bold sm:text-4xl">
              Up and running in three steps.
            </h2>
            <p className="mt-4 text-sm text-secondary">
              Getting your business organised doesn't have to be complicated.
            </p>
          </div>
        </Reveal>

        <div className="relative mt-14 grid gap-6 md:grid-cols-3">
          <div className="absolute left-[16%] right-[16%] top-10 hidden border-t border-dashed border-brand/30 md:block" />

          {steps.map((step, index) => {
            const Icon = step.icon;

            return (
              <Reveal key={step.n} delay={index * 0.1}>
                <article className="relative rounded-2xl border border-border bg-white p-7 shadow-card">
                  <div className="flex items-center justify-between">
                    <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand text-white shadow-lg shadow-brand/20">
                      <Icon size={22} />
                    </span>
                    <span className="text-3xl font-bold text-brand/15">
                      {step.n}
                    </span>
                  </div>

                  <h3 className="mt-7 text-lg font-semibold">
                    {step.title}
                  </h3>
                  <p className="mt-3 text-sm leading-6 text-secondary">
                    {step.body}
                  </p>
                </article>
              </Reveal>
            );
          })}
        </div>
      </section>

      {/* PRICING */}
      <section id="pricing" className="bg-white py-24">
        <div className="mx-auto max-w-7xl px-6">
          <Reveal>
            <div className="mx-auto max-w-2xl text-center">
              <span className="rounded-full bg-brand-soft px-4 py-2 text-xs font-semibold text-brand-deep">
                SIMPLE PRICING
              </span>
              <h2 className="mt-6 text-3xl font-bold sm:text-4xl">
                The right plan for your business.
              </h2>
              <p className="mt-4 text-sm leading-6 text-secondary">
                Start free and upgrade as your business grows. Prices are in
                Zambian Kwacha.
              </p>
            </div>
          </Reveal>

          <div className="mt-14 grid gap-6 md:grid-cols-3">
            {plans.map((plan, index) => (
              <Reveal key={plan.name} delay={index * 0.1}>
                <article
                  className={`relative flex h-full flex-col rounded-2xl p-7 ${
                    plan.featured
                      ? "border-2 border-brand bg-brand/[0.035] shadow-lift"
                      : "border border-border bg-white shadow-card"
                  }`}
                >
                  {plan.featured && (
                    <span className="absolute -top-3 left-7 rounded-full bg-brand px-4 py-1 text-[10px] font-bold uppercase tracking-wider text-white">
                      Most popular
                    </span>
                  )}

                  <h3 className="text-lg font-bold">{plan.name}</h3>
                  <p className="mt-2 min-h-10 text-sm text-secondary">
                    {plan.description}
                  </p>

                  <div className="mt-6 flex items-baseline gap-2">
                    <span className="text-4xl font-bold tracking-tight">
                      {plan.price}
                    </span>
                    {plan.price !== "Free" && (
                      <span className="text-xs text-secondary">/ month</span>
                    )}
                  </div>

                  <div className="my-7 h-px bg-border" />

                  <ul className="flex-1 space-y-4">
                    {plan.features.map((feature) => (
                      <li
                        key={feature}
                        className="flex items-start gap-3 text-sm text-secondary"
                      >
                        <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand-soft text-brand">
                          <Check size={12} />
                        </span>
                        {feature}
                      </li>
                    ))}
                  </ul>

                  <Button
                    href={plan.href}
                    className="mt-8 w-full"
                    variant={plan.featured ? "primary" : "outline"}
                  >
                    {plan.cta}
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </article>
              </Reveal>
            ))}
          </div>

          <p className="mt-8 text-center text-xs text-secondary">
            Need more details?{" "}
            <Link
              href="/pricing"
              className="font-semibold text-brand hover:underline"
            >
              Compare all plan features
            </Link>
          </p>
        </div>
      </section>

      {/* ZAMBIA */}
      <section className="relative overflow-hidden bg-canvas py-20">
        <div className="mx-auto grid max-w-7xl items-center gap-10 px-6 md:grid-cols-2">
          <Reveal>
            <span className="rounded-full bg-brand-soft px-4 py-2 text-xs font-semibold text-brand-deep">
              MADE FOR ZAMBIA
            </span>
            <h2 className="mt-6 text-3xl font-bold sm:text-4xl">
              Local businesses.
              <span className="block text-brand">Clearer operations.</span>
            </h2>
            <p className="mt-5 max-w-lg text-sm leading-7 text-secondary">
              BizPilot is designed around the day-to-day needs of businesses
              operating in Zambia, with ZMW as the default currency and
              business tools designed for retail operations.
            </p>
          </Reveal>

          <Reveal delay={0.15}>
            <div className="grid grid-cols-2 gap-4">
              {[
                [Globe2, "ZMW default currency"],
                [ShieldCheck, "ZRA-ready workflows"],
                [Users, "Team management"],
                [Zap, "Connected operations"],
              ].map(([Icon, label]: any) => (
                <div
                  key={label}
                  className="rounded-2xl border border-border bg-white p-6 shadow-card"
                >
                  <Icon className="h-6 w-6 text-brand" />
                  <p className="mt-5 text-sm font-semibold text-ink">
                    {label}
                  </p>
                </div>
              ))}
            </div>
          </Reveal>
        </div>
      </section>

      {/* FINAL CTA */}
      <section className="px-6 py-24">
        <Reveal>
          <div className="relative mx-auto max-w-7xl overflow-hidden rounded-3xl bg-brand px-8 py-16 text-center shadow-lift sm:px-16">
            <div className="pointer-events-none absolute -left-20 -top-32 h-80 w-80 rounded-full border border-white/10" />
            <div className="pointer-events-none absolute -bottom-40 -right-20 h-96 w-96 rounded-full border border-white/10" />

            <div className="relative">
              <LogoMark size={54} />

              <h2 className="mx-auto mt-7 max-w-2xl text-3xl font-bold tracking-tight text-white sm:text-5xl">
                Your business deserves to run with clarity.
              </h2>

              <p className="mx-auto mt-5 max-w-xl text-sm leading-7 text-white/80 sm:text-base">
                Bring your sales, inventory, purchasing, accounting and
                operations together with BizPilot.
              </p>

              <div className="mt-9 flex flex-wrap justify-center gap-3">
                <Button
                  href="/sign-up"
                  size="lg"
                  className="bg-white text-brand hover:bg-brand-soft"
                >
                  Start using BizPilot <ArrowRight className="ml-2 h-4 w-4" />
                </Button>

                <Button
                  href="/demo"
                  size="lg"
                  variant="outline"
                  className="border-white/60 bg-transparent text-white hover:bg-white/10"
                >
                  Explore live demo
                </Button>
              </div>
            </div>
          </div>
        </Reveal>
      </section>

      <SiteFooter />
    </main>
  );
}
