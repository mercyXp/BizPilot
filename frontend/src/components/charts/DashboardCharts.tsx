"use client";

import { useReducedMotion } from "framer-motion";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { chartColors, chartLegend } from "@/lib/colors";
import { Card } from "@/components/ui/card";
import { chartTheme, emptyTrend } from "@/components/charts/theme";

type TrendPoint = { date?: string | null; revenue: number };
type BranchPoint = { branch_name: string; revenue: number };

function ChartTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: { name: string; value: number; color: string }[];
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div style={chartTheme.tooltipStyle} className="px-3 py-2">
      <p className="text-xs font-medium text-ink">{label}</p>
      {payload.map((item) => (
        <p key={item.name} className="mt-1 flex items-center gap-2 text-xs text-secondary">
          <span className="h-2 w-2 rounded-full" style={{ background: item.color }} />
          <span>{item.name}</span>
          <span className="font-medium text-ink">ZMW {item.value}</span>
        </p>
      ))}
    </div>
  );
}

export function SalesOverviewChart({ trend }: { trend?: TrendPoint[] }) {
  const reduce = useReducedMotion();
  const salesData =
    trend && trend.length
      ? trend.map((point) => ({ month: point.date ?? "", revenue: point.revenue }))
      : emptyTrend(["revenue"]);
  return (
    <Card className="p-4">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-ink">Sales overview</h2>
          <p className="text-xs text-secondary">Revenue · selected period</p>
        </div>
        <div className="flex items-center gap-2 text-[11px] text-secondary">
          <span className="h-2 w-2 rounded-full" style={{ background: chartColors.revenue }} />
          {chartLegend.revenue}
        </div>
      </div>
      <div className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={salesData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid stroke={chartTheme.grid.stroke} vertical={false} />
            <XAxis dataKey="month" tick={{ fill: "#525252", fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: "#525252", fontSize: 11 }} axisLine={false} tickLine={false} width={36} />
            <Tooltip content={<ChartTooltip />} />
            <Area
              type="monotone"
              dataKey="revenue"
              name={chartLegend.revenue}
              stroke={chartColors.revenue}
              fill={chartColors.revenue}
              fillOpacity={0.12}
              strokeWidth={2}
              isAnimationActive={!reduce}
              animationDuration={chartTheme.animationDuration}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}

export function SalesByStoreChart({ branches }: { branches?: BranchPoint[] }) {
  const reduce = useReducedMotion();
  const storeData =
    branches && branches.length
      ? branches.map((row) => ({ store: row.branch_name, revenue: row.revenue }))
      : [{ store: "This store", revenue: 0 }];
  const total = storeData.reduce((sum, row) => sum + row.revenue, 0);
  return (
    <Card className="p-4">
      <div className="mb-3">
        <h2 className="text-sm font-semibold text-ink">Sales by store</h2>
        <p className="text-xs text-secondary">This month</p>
      </div>
      <div className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={storeData} layout="vertical" margin={{ top: 8, right: 16, left: 8, bottom: 0 }}>
            <CartesianGrid stroke={chartTheme.grid.stroke} horizontal={false} />
            <XAxis type="number" tick={{ fill: "#525252", fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis
              type="category"
              dataKey="store"
              tick={{ fill: "#525252", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              width={80}
            />
            <Tooltip content={<ChartTooltip />} />
            <Bar
              dataKey="revenue"
              name={chartLegend.revenue}
              fill={chartColors.revenue}
              radius={[0, 4, 4, 0]}
              barSize={14}
              isAnimationActive={!reduce}
              animationDuration={chartTheme.animationDuration}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-2 text-right text-xs text-secondary">ZMW {total}</p>
    </Card>
  );
}
