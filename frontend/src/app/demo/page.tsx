"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Boxes,
  ClipboardList,
  Landmark,
  ShieldCheck,
  Store,
  UserCog,
  Wallet,
} from "lucide-react";

import { useAuth } from "@/components/AuthProvider";
import { SiteFooter } from "@/components/marketing/SiteFooter";
import { SiteHeader } from "@/components/marketing/SiteHeader";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Alert } from "@/components/ui/alert";

const roles = [
  {
    key: "owner",
    title: "Business Owner",
    summary: "Financial overview, branches, performance and business control.",
    icon: Landmark,
  },
  {
    key: "admin",
    title: "Administrator",
    summary: "Users, permissions, settings and operational oversight.",
    icon: UserCog,
  },
  {
    key: "manager",
    title: "Manager",
    summary: "Daily operations, stock, staff and sales supervision.",
    icon: ClipboardList,
  },
  {
    key: "salesperson",
    title: "Salesperson",
    summary: "POS, transactions, receipts and customer sales.",
    icon: Wallet,
  },
  {
    key: "stock",
    title: "Stock Controller",
    summary: "Inventory, stock movements and replenishment.",
    icon: Boxes,
  },
  {
    key: "auditor",
    title: "Auditor / Viewer",
    summary: "Reports, financial records and audit trails without editing.",
    icon: ShieldCheck,
  },
] as const;

export default function DemoAccessPage() {
  const router = useRouter();
  const { enterDemo } = useAuth();
  const [pending, setPending] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function choose(role: string) {
    setError(null);
    setPending(role);
    try {
      await enterDemo(role);
      router.push("/app");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not open the live demo");
    } finally {
      setPending(null);
    }
  }

  return (
    <div className="min-h-screen bg-canvas">
      <SiteHeader />
      <main className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
        <p className="text-xs font-semibold uppercase tracking-wider text-brand-deep">BizPilot</p>
        <p className="mt-1 text-sm text-secondary">Live demo environment</p>
        <h1 className="mt-4 text-4xl font-semibold tracking-tight text-ink">Experience BizPilot.</h1>
        <p className="mt-3 max-w-2xl text-base text-secondary">
          Explore a fully populated demonstration business. No registration required.
        </p>
        <p className="mt-3 text-xs font-medium uppercase tracking-wide text-muted">
          Sample business · Demo data · ZMW
        </p>

        <Card className="mt-8 p-5">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-muted">Demo business</p>
              <h2 className="mt-1 text-2xl font-semibold text-ink">Mwamba Retail Group</h2>
              <p className="text-sm text-secondary">Retail and wholesale · Lusaka, Zambia</p>
            </div>
            <Store className="h-8 w-8 text-brand" />
          </div>
          <dl className="mt-6 grid gap-3 sm:grid-cols-4">
            {[
              ["ZMW 248,650", "Monthly revenue"],
              ["ZMW 76,420", "Monthly expenses"],
              ["1,250", "Products"],
              ["3", "Branches"],
            ].map(([value, label]) => (
              <div key={label} className="rounded-lg bg-muted-bg px-3 py-3">
                <dt className="text-xs text-secondary">{label}</dt>
                <dd className="mt-1 text-lg font-semibold text-ink">{value}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-4 text-sm text-secondary">
            Demo branches: Lusaka Central · Chelstone · Kitwe
          </p>
          <p className="mt-1 text-xs text-muted">Illustrative figures, not actual business records.</p>
        </Card>

        <h2 className="mt-10 text-lg font-semibold text-ink">Choose how you want to explore</h2>
        {error ? (
          <Alert tone="critical" className="mt-4" title="Demo unavailable">
            {error}
          </Alert>
        ) : null}
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          {roles.map((role) => {
            const Icon = role.icon;
            return (
              <button
                key={role.key}
                type="button"
                onClick={() => void choose(role.key)}
                disabled={pending !== null}
                className="rounded-xl border border-border bg-surface p-4 text-left transition-colors hover:border-brand/40 hover:bg-brand-soft/40 disabled:opacity-60"
              >
                <span className="flex items-center gap-2 text-sm font-semibold text-ink">
                  <Icon className="h-4 w-4 text-brand" />
                  {role.title}
                </span>
                <span className="mt-2 block text-sm text-secondary">{role.summary}</span>
                <span className="mt-3 inline-block text-xs font-medium text-brand-deep">
                  {pending === role.key ? "Signing in…" : "Enter as this role"}
                </span>
              </button>
            );
          })}
        </div>
        <p className="mt-6 text-sm text-secondary">
          Each role uses a preconfigured account. Clicking a role signs you in with no password and no
          registration. Everyone explores the same Mwamba tenant so a sale in POS can be reviewed as manager
          or owner.
        </p>
        <div className="mt-8">
          <Button href="/sign-up" variant="ghost">
            Prefer a real trial instead?
          </Button>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
