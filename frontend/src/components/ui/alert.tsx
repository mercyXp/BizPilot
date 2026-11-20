import { AlertCircle, AlertTriangle, CheckCircle2, Info, Sparkles } from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "@/lib/cn";
import type { AlertTone } from "@/lib/status";
import { alertToneClass } from "@/lib/status";

const icons = {
  critical: AlertCircle,
  warning: AlertTriangle,
  success: CheckCircle2,
  information: Info,
  ai: Sparkles,
} as const;

const labels: Record<AlertTone, string> = {
  critical: "Critical",
  warning: "Warning",
  success: "Success",
  information: "Information",
  ai: "AI insight",
};

export function Alert({
  tone,
  title,
  children,
  className,
}: {
  tone: AlertTone;
  title?: string;
  children: ReactNode;
  className?: string;
}) {
  const Icon = icons[tone];
  return (
    <div
      role="status"
      className={cn(
        "flex gap-3 rounded-lg border px-3.5 py-3 text-sm",
        alertToneClass[tone],
        className,
      )}
    >
      <Icon className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
      <div className="min-w-0">
        <p className="text-[11px] font-semibold uppercase tracking-wide opacity-80">{labels[tone]}</p>
        {title ? <p className="mt-0.5 font-medium text-ink">{title}</p> : null}
        <div className={cn("text-secondary", title ? "mt-0.5" : "mt-0")}>{children}</div>
      </div>
    </div>
  );
}
