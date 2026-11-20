"use client";

import { AlertTriangle, Package, ShoppingBag, TrendingUp } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";

import { useAuth } from "@/components/AuthProvider";
import { SalesByStoreChart, SalesOverviewChart } from "@/components/charts/DashboardCharts";
import { KpiCard } from "@/components/charts/KpiCard";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { kpiVariants, staggerContainer, withReducedMotion } from "@/lib/motion";

function greeting(date = new Date()): string {
  const hour = date.getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

function firstName(fullName: string, email: string): string {
  const fromName = fullName.trim().split(/\s+/)[0];
  if (fromName) return fromName;
  return email.split("@")[0] ?? "there";
}

export function DashboardHome() {
  const { user, currentOrg, demoSnapshot, isDemo } = useAuth();
  const reduce = useReducedMotion();
  const name = user ? firstName(user.full_name, user.email) : "there";
  const store = currentOrg?.name ?? "your store";
  const revenue = isDemo ? demoSnapshot?.kpis.monthly_revenue ?? 0 : 0;
  const expenses = isDemo ? demoSnapshot?.kpis.monthly_expenses ?? 0 : 0;
  const products = isDemo ? demoSnapshot?.kpis.products ?? 0 : 0;
  const profit = revenue - expenses;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-ink">
            {greeting()}, {name}
          </h1>
          <p className="mt-1 text-sm text-secondary">Here is what is happening at {store} today</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">Export report</Button>
          <Button href="/app/pos">+ New sale</Button>
        </div>
      </div>

      <motion.div
        className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4"
        variants={staggerContainer(0.07)}
        initial="hidden"
        animate="show"
      >
        {[
          { label: "Monthly revenue", value: revenue, format: "currency" as const, icon: ShoppingBag, tone: "brand" as const },
          { label: "Catalogue", value: products, format: "number" as const, icon: Package, tone: "sales" as const },
          { label: "Profit", value: profit, format: "currency" as const, icon: TrendingUp, tone: "profit" as const },
          { label: "Expenses", value: expenses, format: "currency" as const, icon: AlertTriangle, tone: "warning" as const },
        ].map((kpi) => (
          <motion.div key={kpi.label} variants={withReducedMotion(reduce, kpiVariants)}>
            <KpiCard
              label={kpi.label}
              value={kpi.value}
              format={kpi.format}
              icon={kpi.icon}
              tone={kpi.tone}
              hint="0% vs last week"
            />
          </motion.div>
        ))}
      </motion.div>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <SalesOverviewChart />
        </div>
        <SalesByStoreChart />
      </div>

      <Card className="p-4">
        <div className="mb-3 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-ink">Sales by section</h2>
            <p className="text-xs text-secondary">Net sales after returns, tax out of ZRA sales, profit</p>
          </div>
          <div className="flex rounded-md border border-border p-0.5 text-xs">
            {["Today", "7 days", "30 days"].map((label, index) => (
              <span
                key={label}
                className={
                  index === 0
                    ? "rounded bg-brand-soft px-2 py-1 font-medium text-brand-deep"
                    : "px-2 py-1 text-secondary"
                }
              >
                {label}
              </span>
            ))}
          </div>
        </div>
        <p className="py-10 text-center text-sm text-muted">No section sales in this period.</p>
      </Card>
    </div>
  );
}
