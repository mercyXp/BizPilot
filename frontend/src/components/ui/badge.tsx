import type { HTMLAttributes } from "react";

import { cn } from "@/lib/cn";

const tones = {
  brand: "bg-brand-soft text-brand-deep border-brand/20",
  success: "bg-success-bg text-success border-success-border",
  danger: "bg-danger-bg text-danger border-danger-border",
  warning: "bg-warning-bg text-warning border-warning-border",
  info: "bg-info-bg text-info border-info-border",
  ai: "bg-ai-bg text-ai border-ai-border",
  customer: "bg-customer-bg text-customer border-customer-border",
  muted: "bg-muted-bg text-secondary border-border",
} as const;

export function Badge({
  tone = "muted",
  className,
  ...props
}: HTMLAttributes<HTMLSpanElement> & { tone?: keyof typeof tones }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium tracking-wide transition-colors duration-standard ease-entrance",
        tones[tone],
        className,
      )}
      {...props}
    />
  );
}
