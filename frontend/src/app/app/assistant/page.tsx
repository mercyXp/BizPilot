"use client";

import { useState } from "react";

import { AiAvailability, AiInsightCard, TypingIndicator } from "@/components/ai/AiStates";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/page-header";
import { Textarea } from "@/components/ui/input";
import { Alert } from "@/components/ui/alert";

export default function AssistantPage() {
  const [draft, setDraft] = useState("");
  const [demo, setDemo] = useState<"idle" | "loading" | "completed" | "failed">("idle");

  return (
    <div>
      <PageHeader
        title="BizPilot AI"
        description="Grok answers only by calling tools. Animation never implies success before the API does."
        actions={<AiAvailability available />}
      />
      <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
        <Card className="p-5">
          <Textarea
            rows={5}
            placeholder="Ask about this store. The assistant will not run until the AI phase is live."
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
          />
          <div className="mt-3 flex gap-2">
            <Button disabled={!draft} onClick={() => setDemo("loading")}>
              Send
            </Button>
            <Button variant="outline" onClick={() => setDemo("completed")}>
              Preview completed
            </Button>
            <Button variant="ghost" onClick={() => setDemo("failed")}>
              Preview failed
            </Button>
          </div>
          <div className="mt-6 space-y-3">
            {demo === "idle" ? (
              <p className="text-sm text-secondary">No conversation yet. Preview states use the shared AI visual language.</p>
            ) : null}
            {demo === "loading" ? (
              <AiInsightCard title="Working" state="loading">
                <TypingIndicator />
              </AiInsightCard>
            ) : null}
            {demo === "completed" ? (
              <AiInsightCard title="Store insight" state="completed">
                This is a visual preview only. Live answers wait for the AI phase and a confirmed tool result.
              </AiInsightCard>
            ) : null}
            {demo === "failed" ? (
              <Alert tone="critical" title="Generation failed">
                The model did not finish. Nothing was posted to sales, inventory or accounts.
              </Alert>
            ) : null}
          </div>
        </Card>
        <AiInsightCard title="How colour is used" state="completed">
          Purple is reserved for AI. Green, amber, red and blue stay success, warning, danger and information —
          never used to decorate a model reply.
        </AiInsightCard>
      </div>
    </div>
  );
}
