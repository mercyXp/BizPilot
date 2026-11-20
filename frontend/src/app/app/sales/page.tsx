"use client";

import { useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { Card } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/page-header";
import { Alert } from "@/components/ui/alert";
import { readError } from "@/lib/api";

type Sale = { id: string; document_number: string; status: string; total: number };

export default function SalesPage() {
  const { tenantFetch, permissions } = useAuth();
  const [rows, setRows] = useState<Sale[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void tenantFetch("/api/v1/sales").then(async (response) => {
      if (!response.ok) {
        setError(await readError(response));
        return;
      }
      setRows((await response.json()) as Sale[]);
    });
  }, [tenantFetch]);

  if (!permissions.includes("sales.view")) {
    return (
      <Alert tone="warning" title="Sales are restricted">
        This role cannot list sales documents.
      </Alert>
    );
  }

  return (
    <div>
      <PageHeader title="Sales" description="Completed POS and invoice documents for the selected organisation." />
      {error ? (
        <Alert tone="critical" className="mb-4">
          {error}
        </Alert>
      ) : null}
      <Card className="overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-border bg-canvas text-xs uppercase text-secondary">
            <tr>
              <th className="px-3 py-2">Number</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2">Total</th>
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 50).map((row) => (
              <tr key={row.id} className="border-b border-border">
                <td className="px-3 py-2">{row.document_number}</td>
                <td className="px-3 py-2">{row.status}</td>
                <td className="px-3 py-2">ZMW {row.total.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
