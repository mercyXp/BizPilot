import { getStatusVisual, type StatusKey } from "@/lib/status";
import { cn } from "@/lib/cn";

export function StatusBadge({
  status,
  className,
}: {
  status: StatusKey;
  className?: string;
}) {
  const visual = getStatusVisual(status);
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium transition-colors duration-standard ease-entrance",
        visual.className,
        className,
      )}
    >
      {visual.label}
    </span>
  );
}
