"use client";

import { Sparkles } from "lucide-react";
import { useReducedMotion } from "framer-motion";
import type { ReactNode } from "react";

import { cn } from "@/lib/cn";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";

export function AiAvailability({ available }: { available: boolean }) {
  const reduce = useReducedMotion();
  return (
    <span className="inline-flex items-center gap-2 text-sm text-ai">
      <Sparkles
        className={cn("h-4 w-4", available && !reduce && "animate-ai-pulse")}
        aria-hidden
      />
      {available ? "Assistant available" : "Assistant offline"}
    </span>
  );
}

export function TypingIndicator() {
  return (
    <div className="flex items-center gap-1.5 text-sm text-ai" role="status" aria-live="polite">
      <span className="sr-only">Generating a response</span>
      {[0, 1, 2].map((index) => (
        <span
          key={index}
          className="h-1.5 w-1.5 rounded-full bg-ai"
          style={{ animation: `typing-bounce 1s ease-in-out ${index * 0.12}s infinite` }}
        />
      ))}
    </div>
  );
}

export function AiInsightCard({
  title,
  children,
  state,
}: {
  title: string;
  children: ReactNode;
  state: "loading" | "completed" | "failed";
}) {
  return (
    <Card className="border-ai-border bg-ai-bg/40 p-4">
      <div className="flex items-center justify-between gap-2">
        <p className="inline-flex items-center gap-2 text-sm font-medium text-ink">
          <Sparkles className="h-4 w-4 text-ai" />
          {title}
        </p>
        <Badge tone={state === "failed" ? "danger" : state === "completed" ? "ai" : "muted"}>
          {state === "loading" ? "Generating" : state === "completed" ? "AI-generated" : "Failed"}
        </Badge>
      </div>
      <div className="mt-3 text-sm text-secondary">
        {state === "loading" ? <TypingIndicator /> : children}
      </div>
    </Card>
  );
}
