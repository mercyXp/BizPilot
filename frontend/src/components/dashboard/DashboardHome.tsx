"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, Package, ShoppingBag, TrendingUp } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";

import { useAuth } from "@/components/AuthProvider";
import { useI18n } from "@/components/I18nProvider";
import { SalesByStoreChart, SalesOverviewChart } from "@/components/charts/DashboardCharts";
import { KpiCard } from "@/components/charts/KpiCard";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { kpiVariants, staggerContainer, withReducedMotion } from "@/lib/motion";

type Summary = {
  today_revenue: number;
  month_revenue: number;
  month_expenses: number;
  month_profit: number;
  low_stock: number;
  stock_value: number;
  by_branch: { branch_name: string; revenue: number }[];
  trend: { date?: string | null; revenue: number }[];
};

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
  const { user, currentOrg, demoSnapshot, isDemo, permissions, tenantFetch } = useAuth();
  const { t } = useI18n();
  const reduce = useReducedMotion();
  const name = user ? firstName(user.full_name, user.email) : "there";
  const store = currentOrg?.name ?? "your store";
  const [summary, setSummary] = useState<Summary | null>(null);
  const canReport = permissions.includes("reports.view");

  useEffect(() => {
    if (!canReport || !currentOrg) return;
    let cancelled = false;
    void tenantFetch("/api/v1/reporting/summary").then(async (response) => {
      if (!response.ok || cancelled) return;
      setSummary((await response.json()) as Summary);
    });
    return () => {
      cancelled = true;
    };
  }, [canReport, currentOrg, tenantFetch]);

  const revenue = summary?.month_revenue ?? (isDemo ? demoSnapshot?.kpis.monthly_revenue ?? 0 : 0);
  const expenses = summary?.month_expenses ?? (isDemo ? demoSnapshot?.kpis.monthly_expenses ?? 0 : 0);
  const products = isDemo ? demoSnapshot?.kpis.products ?? 0 : summary?.low_stock ?? 0;
  const profit = summary?.month_profit ?? revenue - expenses;

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
          <Button variant="outline" href="/app/reports">
            Export report
          </Button>
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
          { label: t("dashboard.monthly_revenue"), value: revenue, format: "currency" as const, icon: ShoppingBag, tone: "brand" as const },
          { label: t("dashboard.catalogue"), value: products, format: "number" as const, icon: Package, tone: "sales" as const },
          { label: t("dashboard.profit"), value: profit, format: "currency" as const, icon: TrendingUp, tone: "profit" as const },
          { label: t("dashboard.expenses"), value: expenses, format: "currency" as const, icon: AlertTriangle, tone: "warning" as const },
        ].map((kpi) => (
          <motion.div key={kpi.label} variants={withReducedMotion(reduce, kpiVariants)}>
            <KpiCard
              label={kpi.label}
              value={kpi.value}
              format={kpi.format}
              icon={kpi.icon}
              tone={kpi.tone}
              hint={canReport ? "From live reports" : "0% vs last week"}
            />
          </motion.div>
        ))}
      </motion.div>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <SalesOverviewChart trend={summary?.trend} />
        </div>
        <SalesByStoreChart branches={summary?.by_branch} />
      </div>

      <Card className="p-4">
        <div className="mb-3 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-ink">Today</h2>
            <p className="text-xs text-secondary">Completed sales revenue for today</p>
          </div>
        </div>
        <p className="py-6 text-center text-sm text-muted">
          {summary ? `ZMW ${summary.today_revenue}` : "No report data in this period."}
        </p>
      </Card>
    </div>
  );
}
