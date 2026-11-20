import { semanticColors, type StatusKey } from "./colors";

export type { StatusKey };

export type StatusVisual = {
  key: StatusKey;
  label: string;
  className: string;
};

const labels: Record<StatusKey, string> = {
  paid: "Paid",
  completed: "Completed",
  pending: "Pending",
  awaiting_approval: "Awaiting approval",
  failed: "Failed",
  rejected: "Rejected",
  processing: "Processing",
  draft: "Draft",
  cancelled: "Cancelled",
  cancelled_neutral: "Cancelled",
  ai_generated: "AI-generated",
};

const classNames: Record<StatusKey, string> = {
  paid: "bg-success-bg text-success border-success-border",
  completed: "bg-success-bg text-success border-success-border",
  pending: "bg-warning-bg text-warning border-warning-border",
  awaiting_approval: "bg-warning-bg text-warning border-warning-border",
  failed: "bg-danger-bg text-danger border-danger-border",
  rejected: "bg-danger-bg text-danger border-danger-border",
  processing: "bg-info-bg text-info border-info-border",
  draft: "bg-muted-bg text-secondary border-border",
  cancelled: "bg-danger-bg text-danger border-danger-border",
  cancelled_neutral: "bg-muted-bg text-secondary border-border",
  ai_generated: "bg-ai-bg text-ai border-ai-border",
};

export function getStatusVisual(key: StatusKey): StatusVisual {
  return { key, label: labels[key], className: classNames[key] };
}

export const alertToneClass = {
  critical: "bg-danger-bg/80 text-danger border-danger-border",
  warning: "bg-warning-bg/80 text-warning border-warning-border",
  success: "bg-success-bg/80 text-success border-success-border",
  information: "bg-info-bg/80 text-info border-info-border",
  ai: "bg-ai-bg/80 text-ai border-ai-border",
} as const;

export type AlertTone = keyof typeof alertToneClass;

export { semanticColors };
