"use client";

import { useState } from "react";
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

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/page-header";
import { Select } from "@/components/ui/input";
import { cn } from "@/lib/cn";
import { chartColors } from "@/lib/colors";

const reports = [
  { id: "sales", title: "Sales Report", body: "Revenue by store, top items, and trends over time.", icon: ShoppingBag, color: chartColors.sales },
  { id: "profit", title: "Profit Analysis Report", body: "Margins, cost vs price analysis, profitability by item.", icon: TrendingUp, color: chartColors.profit },
  { id: "purchases", title: "Purchases Report", body: "Supplier spend, purchase orders, and category breakdown.", icon: Truck, color: chartColors.purchases },
  { id: "inventory", title: "Inventory Report", body: "Opening and closing stock of each item, and its value.", icon: LayoutGrid, color: chartColors.revenue },
  { id: "movement", title: "Stock Movement Report", body: "Stock in and out of each item, by type of movement.", icon: BarChart3, color: chartColors.revenue },
  { id: "centres", title: "Storage Centers Report", body: "Stock and its value at cost price in each storage center.", icon: Warehouse, color: chartColors.purchases },
  { id: "expenses", title: "Expenses Report", body: "Operating costs by category and date range.", icon: Wallet, color: chartColors.expenses },
  { id: "debts", title: "Customer Debts Report", body: "Who owes how much and for how long, and how customer debt moved over time.", icon: Users, color: chartColors.outstanding },
  { id: "customer-sales", title: "Customer Sales Report", body: "Top customers by what they spent, their spend over time, and who stopped buying.", icon: Users, color: chartColors.customers },
  { id: "tax", title: "Taxation Report", body: "ZRA tax filing summary and computations.", icon: FileSpreadsheet, color: chartColors.purchases },
  { id: "shifts", title: "Shifts Report", body: "Each shift opened, cashier, cash, sales and variance.", icon: Clock, color: chartColors.revenue },
  { id: "variance", title: "Shift Variance Report", body: "Closed shifts that were over or short, by cashier.", icon: Clock, color: chartColors.outstanding },
];

export default function ReportsPage() {
  const [selected, setSelected] = useState(reports[0]);

  return (
    <div>
      <PageHeader title="Reports" description="Generate and download business reports" />
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
          <div className="mt-6 grid gap-3 sm:grid-cols-3">
            <label className="text-xs font-medium text-secondary">
              Date range
              <Select className="mt-1" defaultValue="month">
                <option value="today">Today</option>
                <option value="week">Week</option>
                <option value="month">Month</option>
                <option value="custom">Custom</option>
              </Select>
            </label>
            <label className="text-xs font-medium text-secondary">
              Report type
              <Select className="mt-1" defaultValue="summarized">
                <option value="summarized">Summarized</option>
                <option value="detailed">Detailed</option>
              </Select>
            </label>
            <label className="text-xs font-medium text-secondary">
              File type
              <Select className="mt-1" defaultValue="pdf">
                <option value="pdf">PDF</option>
                <option value="xlsx">Excel</option>
              </Select>
            </label>
          </div>
          <Button className="mt-4" disabled>
            Download report
          </Button>
          <p className="mt-6 rounded-md bg-muted-bg px-3 py-8 text-center text-sm text-muted">
            Choose the date range and file type, then download the report. Downloads connect when reporting is live.
          </p>
        </Card>
      </div>
    </div>
  );
}
