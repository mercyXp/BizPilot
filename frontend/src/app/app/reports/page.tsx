"use client";

import { useEffect, useMemo, useState } from "react";
import {
  BarChart3,
  Clock,
  FileSpreadsheet,
  LayoutGrid,
  ShoppingBag,
  TrendingUp,
  Truck,
  Users,
  Wallet,
  Warehouse,
} from "lucide-react";

import { useAuth } from "@/components/AuthProvider";
import { useI18n } from "@/components/I18nProvider";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/page-header";
import { Select } from "@/components/ui/input";
import { cn } from "@/lib/cn";
import { chartColors } from "@/lib/colors";
import { readError } from "@/lib/api";

const reports = [
  { id: "sales", kind: "sales", title: "Sales Report", body: "Revenue by store, top items, and trends over time.", icon: ShoppingBag, color: chartColors.sales },
  { id: "profit", kind: "sales", title: "Profit Analysis Report", body: "Revenue from completed sales in the selected period.", icon: TrendingUp, color: chartColors.profit },
  { id: "purchases", kind: "purchases", title: "Purchases Report", body: "Supplier spend, purchase orders, and category breakdown.", icon: Truck, color: chartColors.purchases },
  { id: "inventory", kind: "inventory", title: "Inventory Report", body: "On-hand stock of each item, and its value.", icon: LayoutGrid, color: chartColors.revenue },
  { id: "movement", kind: "movement", title: "Stock Movement Report", body: "Stock in and out of each item, by type of movement.", icon: BarChart3, color: chartColors.revenue },
  { id: "centres", kind: "inventory", title: "Storage Centers Report", body: "Stock and its value at cost price in each storage center.", icon: Warehouse, color: chartColors.purchases },
  { id: "expenses", kind: "expenses", title: "Expenses Report", body: "Operating costs by category and date range.", icon: Wallet, color: chartColors.expenses },
  { id: "debts", kind: "customers", title: "Customer Debts Report", body: "Who owes how much, from credit accounts.", icon: Users, color: chartColors.outstanding },
  { id: "customer-sales", kind: "customers", title: "Customer Sales Report", body: "Top customers by completed sales.", icon: Users, color: chartColors.customers },
  { id: "tax", kind: "tax", title: "Taxation Report", body: "Output tax from completed sales. Not an official ZRA filing.", icon: FileSpreadsheet, color: chartColors.purchases },
  { id: "shifts", kind: "shifts", title: "Shifts Report", body: "Each shift opened, cash float, and variance.", icon: Clock, color: chartColors.revenue },
  { id: "variance", kind: "shifts", title: "Shift Variance Report", body: "Closed shifts that were over or short.", icon: Clock, color: chartColors.outstanding },
];

function rangeDates(preset: string): { from: string; to: string } {
  const to = new Date();
  const from = new Date();
  if (preset === "today") {
    return { from: to.toISOString().slice(0, 10), to: to.toISOString().slice(0, 10) };
  }
  if (preset === "week") {
    from.setDate(to.getDate() - 6);
  } else {
    from.setDate(1);
  }
  return { from: from.toISOString().slice(0, 10), to: to.toISOString().slice(0, 10) };
}

export default function ReportsPage() {
  const { permissions, tenantFetch } = useAuth();
  const { t } = useI18n();
  const [selected, setSelected] = useState(reports[0]);
  const [preset, setPreset] = useState("month");
  const [payload, setPayload] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const allowed = permissions.includes("reports.view");
  const dates = useMemo(() => rangeDates(preset), [preset]);

  useEffect(() => {
    if (!allowed) return;
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      const params = new URLSearchParams({ from_date: dates.from, to_date: dates.to });
      const response = await tenantFetch(`/api/v1/reporting/${selected.kind}?${params.toString()}`);
      if (cancelled) return;
      if (!response.ok) {
        setError(await readError(response));
        setPayload(null);
        setLoading(false);
        return;
      }
      setPayload((await response.json()) as Record<string, unknown>);
      setLoading(false);
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [allowed, dates.from, dates.to, selected.kind, tenantFetch]);

  async function downloadCsv() {
    const params = new URLSearchParams({
      from_date: dates.from,
      to_date: dates.to,
      export: "csv",
    });
    const response = await tenantFetch(`/api/v1/reporting/${selected.kind}?${params.toString()}`);
    if (!response.ok) {
      setError(await readError(response));
      return;
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${selected.kind}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  }

  const totals = (payload?.totals as Record<string, number | string> | undefined) ?? {};
  const lines = (payload?.lines as Record<string, unknown>[] | undefined) ?? [];

  return (
    <div>
      <PageHeader title={t("reports.title")} description={t("reports.description")} />
      {!allowed ? (
        <Alert tone="warning">{t("reports.forbidden")}</Alert>
      ) : (
        <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
          <div className="space-y-2">
            {reports.map((report) => {
              const Icon = report.icon;
              const active = report.id === selected.id;
              return (
                <button
                  key={report.id}
                  type="button"
                  onClick={() => setSelected(report)}
                  className={cn(
                    "flex w-full items-start gap-3 rounded-lg border px-3 py-2.5 text-left transition-colors duration-standard ease-entrance",
                    active ? "border-brand bg-brand-soft/60" : "border-border bg-surface hover:border-brand/30",
                  )}
                >
                  <span
                    className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-surface"
                    style={{ color: report.color }}
                  >
                    <Icon className="h-4 w-4" />
                  </span>
                  <span>
                    <span className="block text-sm font-medium text-ink">{report.title}</span>
                    <span className="mt-0.5 block text-xs text-secondary">{report.body}</span>
                  </span>
                </button>
              );
            })}
          </div>
          <Card className="h-fit p-5">
            <div className="flex items-start gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-soft text-brand">
                <selected.icon className="h-5 w-5" />
              </span>
              <div>
                <h2 className="text-base font-semibold text-ink">{selected.title}</h2>
                <p className="text-sm text-secondary">{selected.body}</p>
              </div>
            </div>
            <div className="mt-6 grid gap-3 sm:grid-cols-2">
              <label className="text-xs font-medium text-secondary">
                Date range
                <Select className="mt-1" value={preset} onChange={(event) => setPreset(event.target.value)}>
                  <option value="today">Today</option>
                  <option value="week">Week</option>
                  <option value="month">Month</option>
                </Select>
              </label>
              <label className="text-xs font-medium text-secondary">
                File type
                <Select className="mt-1" defaultValue="csv">
                  <option value="csv">CSV</option>
                </Select>
              </label>
            </div>
            <Button className="mt-4" onClick={() => void downloadCsv()} disabled={loading}>
              {t("reports.download")}
            </Button>
            {selected.kind === "tax" ? (
              <Alert tone="warning" className="mt-4">
                {t("reports.tax_disclaimer")}
              </Alert>
            ) : null}
            {error ? (
              <Alert tone="critical" className="mt-4">
                {error}
              </Alert>
            ) : null}
            <dl className="mt-6 grid gap-3 sm:grid-cols-3">
              {Object.entries(totals).map(([key, value]) => (
                <div key={key} className="rounded-md border border-border px-3 py-2">
                  <dt className="text-xs text-secondary">{key.replaceAll("_", " ")}</dt>
                  <dd className="mt-1 text-sm font-semibold text-ink">{String(value)}</dd>
                </div>
              ))}
            </dl>
            {loading ? (
              <p className="mt-6 text-center text-sm text-muted">Loading…</p>
            ) : lines.length === 0 ? (
              <p className="mt-6 rounded-md bg-muted-bg px-3 py-8 text-center text-sm text-muted">
                {t("reports.empty")}
              </p>
            ) : (
              <div className="mt-6 overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-border text-xs text-secondary">
                      {Object.keys(lines[0]).map((key) => (
                        <th key={key} className="px-2 py-2 font-medium">
                          {key.replaceAll("_", " ")}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {lines.slice(0, 50).map((line, index) => (
                      <tr key={index} className="border-b border-border/70">
                        {Object.values(line).map((value, cell) => (
                          <td key={cell} className="px-2 py-2 text-ink">
                            {String(value ?? "")}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
