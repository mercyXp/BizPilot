"use client";

import { useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { Card } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/page-header";
import { Alert } from "@/components/ui/alert";
import { readError } from "@/lib/api";

type AuditRow = {
  id: string;
  action: string;
  entity_type: string;
  entity_id: string | null;
  created_at: string | null;
};

export default function AuditPage() {
  const { tenantFetch, permissions } = useAuth();
  const [rows, setRows] = useState<AuditRow[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void tenantFetch("/api/v1/demo/audit").then(async (response) => {
      if (!response.ok) {
        setError(await readError(response));
        return;
      }
      setRows(((await response.json()) as { items: AuditRow[] }).items);
    });
  }, [tenantFetch]);

  if (!permissions.includes("accounting.reports.view") && !permissions.includes("reports.view")) {
    return (
      <Alert tone="warning" title="Audit trail is restricted">
        Salespeople cannot open the audit log, including by changing the URL.
      </Alert>
    );
  }

  return (
    <div>
      <PageHeader title="Audit trail" description="Seeded and live demo actions for Mwamba Retail Group." />
      {error ? (
        <Alert tone="critical" className="mb-4">
          {error}
        </Alert>
      ) : null}
      <Card className="overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-border bg-canvas text-xs uppercase text-secondary">
            <tr>
              <th className="px-3 py-2">When</th>
              <th className="px-3 py-2">Action</th>
              <th className="px-3 py-2">Entity</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} className="border-b border-border">
                <td className="px-3 py-2 text-secondary">{row.created_at}</td>
                <td className="px-3 py-2">{row.action}</td>
                <td className="px-3 py-2">
                  {row.entity_type} {row.entity_id}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
