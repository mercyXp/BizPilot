/** Central colour tokens. Keep in sync with `globals.css` `:root` variables. */

export const brandColors = {
  primary: "#0D9488",
  deep: "#0F766E",
  soft: "#CCFBF1",
  text: "#000000",
  textSecondary: "#525252",
  background: "#F8FAFC",
  surface: "#FFFFFF",
  border: "#E5E7EB",
  muted: "#6B7280",
  mutedBackground: "#F3F4F6",
} as const;

export const semanticColors = {
  success: { fg: "#16A34A", bg: "#DCFCE7", border: "#86EFAC" },
  danger: { fg: "#DC2626", bg: "#FEE2E2", border: "#FECACA" },
  warning: { fg: "#D97706", bg: "#FEF3C7", border: "#FDE68A" },
  information: { fg: "#2563EB", bg: "#DBEAFE", border: "#93C5FD" },
  ai: { fg: "#7C3AED", bg: "#EDE9FE", border: "#C4B5FD" },
  customer: { fg: "#DB2777", bg: "#FCE7F3", border: "#F9A8D4" },
} as const;

/** Chart series — one colour per metric, reused in every analytics view. */
export const chartColors = {
  revenue: "#0D9488",
  expenses: "#F59E0B",
  profit: "#16A34A",
  purchases: "#3B82F6",
  customers: "#8B5CF6",
  sales: "#EC4899",
  outstanding: "#EF4444",
} as const;

export const chartGrid = {
  stroke: "#E5E7EB",
  background: "#FFFFFF",
  tooltipBackground: "#FFFFFF",
  tooltipBorder: "#E5E7EB",
  axis: "#525252",
} as const;

export type ChartMetric = keyof typeof chartColors;
export type SemanticTone = keyof typeof semanticColors;

export const chartLegend: Record<ChartMetric, string> = {
  revenue: "Revenue",
  expenses: "Expenses",
  profit: "Profit",
  purchases: "Purchases",
  customers: "Customers",
  sales: "Sales",
  outstanding: "Outstanding balances",
};

export const statusTone = {
  paid: "success",
  completed: "success",
  pending: "warning",
  awaiting_approval: "warning",
  failed: "danger",
  rejected: "danger",
  processing: "information",
  draft: "muted",
  cancelled: "danger",
  cancelled_neutral: "muted",
  ai_generated: "ai",
} as const;

export type StatusKey = keyof typeof statusTone;
