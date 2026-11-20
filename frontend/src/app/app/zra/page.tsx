"use client";

import { Clock } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/page-header";

export default function ZraPage() {
  return (
    <div>
      <PageHeader
        title="ZRA Smart Invoice"
        description="Sync sales with Zambia Revenue Authority"
      />
      <Card className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-full bg-muted-bg text-secondary">
            <Clock className="h-5 w-5" />
          </span>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-muted">Current status</p>
              <Badge tone="muted">Not enrolled</Badge>
            </div>
            <h2 className="mt-1 text-base font-semibold text-ink">Not enrolled yet</h2>
            <p className="text-sm text-secondary">
              Enrol this store with ZRA Smart Invoicing to start syncing sales and inventory with Zambia Revenue Authority.
            </p>
          </div>
        </div>
        <Button disabled arrow>
          Start enrollment
        </Button>
      </Card>
    </div>
  );
}
