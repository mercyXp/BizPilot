import type { HTMLAttributes } from "react";

import { cn } from "@/lib/cn";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("rounded-xl border border-border bg-surface shadow-card", className)}
      {...props}
    />
  );
}

export function InteractiveCard({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <Card className={cn("card-hover", className)} {...props} />;
}
