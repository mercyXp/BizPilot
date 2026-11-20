import { chartColors, chartGrid, chartLegend, type ChartMetric } from "@/lib/colors";

export const chartTheme = {
  colors: chartColors,
  grid: chartGrid,
  legend: chartLegend,
  tooltipStyle: {
    backgroundColor: chartGrid.tooltipBackground,
    border: `1px solid ${chartGrid.tooltipBorder}`,
    borderRadius: 8,
    color: "#000000",
    fontSize: 12,
    boxShadow: "0 8px 24px rgb(15 118 110 / 0.10)",
  },
  animationDuration: 800,
} as const;

export function seriesColor(metric: ChartMetric): string {
  return chartColors[metric];
}

export const monthLabels = ["Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov"];

/** Honest empty series — zeros, not invented revenue. */
export function emptyTrend(keys: ChartMetric[]) {
  return monthLabels.map((month) => {
    const point: Record<string, string | number> = { month };
    for (const key of keys) point[key] = 0;
    return point;
  });
}
