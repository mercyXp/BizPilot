"use client";

import { useEffect, useRef, useState } from "react";
import { useReducedMotion } from "framer-motion";
import type { LucideIcon } from "lucide-react";

import { cn } from "@/lib/cn";
import { Card } from "@/components/ui/card";

function formatValue(value: number, format: "currency" | "number"): string {
  if (format === "currency") {
    return `ZMW ${value.toLocaleString("en-ZM", { maximumFractionDigits: 0 })}`;
  }
  return value.toLocaleString("en-ZM");
}

function CountUp({
  value,
  format,
}: {
  value: number;
  format: "currency" | "number";
}) {
  const reduce = useReducedMotion();
  const [display, setDisplay] = useState(reduce ? value : 0);
  const seen = useRef(false);
  const ref = useRef<HTMLParagraphElement>(null);

  useEffect(() => {
    if (reduce) {
      setDisplay(value);
      return;
    }
    const node = ref.current;
    if (!node) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting || seen.current) return;
        seen.current = true;
        const start = performance.now();
        const duration = 700;
        const tick = (now: number) => {
          const progress = Math.min((now - start) / duration, 1);
          const eased = 1 - Math.pow(1 - progress, 3);
          setDisplay(Math.round(value * eased));
          if (progress < 1) requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
      },
      { threshold: 0.4 },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, [reduce, value]);

  return (
    <p ref={ref} className="mt-3 text-2xl font-semibold tracking-tight text-ink">
      {formatValue(display, format)}
    </p>
  );
}

export function KpiCard({
  label,
  value,
  format = "number",
  hint,
  icon: Icon,
  tone = "brand",
}: {
  label: string;
  value: number;
  format?: "currency" | "number";
  hint?: string;
  icon: LucideIcon;
  tone?: "brand" | "profit" | "warning" | "sales";
}) {
  const iconClass = {
    brand: "text-brand bg-brand-soft",
    profit: "text-success bg-success-bg",
    warning: "text-warning bg-warning-bg",
    sales: "text-customer bg-customer-bg",
  }[tone];

  return (
    <Card className="p-4">
      <div className="flex items-start justify-between">
        <p className="text-[11px] font-semibold uppercase tracking-wide text-secondary">{label}</p>
        <span className={cn("flex h-8 w-8 items-center justify-center rounded-lg", iconClass)}>
          <Icon className="h-4 w-4" aria-hidden />
        </span>
      </div>
      <CountUp value={value} format={format} />
      {hint ? <p className="mt-1 text-xs text-muted">{hint}</p> : null}
    </Card>
  );
}
