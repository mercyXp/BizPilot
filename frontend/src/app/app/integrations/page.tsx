"use client";

import { useState } from "react";
import { CheckCircle2, Plug } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Field, Input } from "@/components/ui/input";
import { PageHeader } from "@/components/ui/page-header";
import { Alert } from "@/components/ui/alert";
import { cn } from "@/lib/cn";

const integrations = [
  { id: "odoo", name: "Odoo ERP", note: "Needs the External Integrations module", approval: false },
  { id: "zra", name: "ZRA Smart Invoice", note: "Not linked", approval: true },
  { id: "manager", name: "Manager.io", note: "Not linked", approval: false },
];

const events = [
  { group: "PRODUCT", items: ["product.created", "product.updated", "product.deleted"] },
  { group: "SALE", items: ["sale.created", "sale.returned"] },
  { group: "INVENTORY", items: ["inventory.counted", "inventory.adjusted"] },
  { group: "PRODUCTION", items: ["production.recorded", "production.cancelled"] },
  { group: "CUSTOMER", items: ["customer.payment_received", "customer.payment_deleted"] },
];

export default function IntegrationsPage() {
  const [selected, setSelected] = useState(integrations[0]);

  return (
    <div>
      <PageHeader title="Integrations" description="Connect this store to the systems you already use" />
      <div className="grid gap-4 lg:grid-cols-[240px_1fr]">
        <div className="space-y-2">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-muted">Available</p>
          {integrations.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => setSelected(item)}
              className={cn(
                "w-full rounded-lg border p-3 text-left transition-colors duration-standard",
                selected.id === item.id ? "border-brand bg-brand-soft/50" : "border-border bg-surface hover:border-brand/30",
              )}
            >
              <p className="flex items-center gap-2 text-sm font-medium text-ink">
                <Plug className="h-4 w-4 text-brand" />
                {item.name}
              </p>
              <p className="mt-1 text-xs text-secondary">{item.note}</p>
              {item.approval ? (
                <Badge tone="warning" className="mt-2">
                  Requires approval
                </Badge>
              ) : (
                <Badge tone="muted" className="mt-2">
                  Not linked
                </Badge>
              )}
            </button>
          ))}
        </div>
        <div className="space-y-4">
          <Card className="p-5">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-ink">{selected.name}</h2>
              <Badge tone="muted">Not linked</Badge>
            </div>
            <p className="mt-1 text-sm text-secondary">{selected.note}</p>
            <h3 className="mt-5 text-sm font-medium text-ink">Connection details</h3>
            <p className="text-xs text-secondary">Enter the credentials, test them, then link. Nothing is sent until you link.</p>
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              <Field label="Host">
                <Input placeholder="https://" autoComplete="off" />
              </Field>
              <Field label="Database">
                <Input autoComplete="off" />
              </Field>
              <Field label="Username">
                <Input autoComplete="off" />
              </Field>
              <Field label="Password">
                <Input type="password" autoComplete="new-password" />
              </Field>
            </div>
            <div className="mt-4 flex gap-2">
              <Button variant="outline">Test connection</Button>
              <Button disabled>Link</Button>
            </div>
          </Card>
          <Card className="p-5">
            <h3 className="text-sm font-semibold text-ink">Events it reacts to</h3>
            <p className="text-xs text-secondary">Once linked, these store events are forwarded.</p>
            <div className="mt-4 space-y-3">
              {events.map((group) => (
                <div key={group.group}>
                  <p className="text-[11px] font-semibold uppercase tracking-wide text-muted">{group.group}</p>
                  <div className="mt-1.5 flex flex-wrap gap-1.5">
                    {group.items.map((item) => (
                      <code key={item} className="rounded bg-muted-bg px-2 py-0.5 text-[11px] text-brand-deep">
                        {item}
                      </code>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </Card>
          <Card className="p-5">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-ink">Recent failures</h3>
              <Button variant="ghost" size="sm">
                Refresh
              </Button>
            </div>
            <Alert tone="success" className="mt-3">
              <span className="inline-flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4" />
                No failed events. Everything this integration was sent went through.
              </span>
            </Alert>
          </Card>
        </div>
      </div>
    </div>
  );
}
