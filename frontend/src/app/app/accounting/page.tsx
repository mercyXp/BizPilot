"use client";

import { useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { Card } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/page-header";
import { Alert } from "@/components/ui/alert";
import { readError } from "@/lib/api";

type PnL = { income: number; expense: number; net_income: number };

export default function AccountingPage() {
  const { tenantFetch, permissions } = useAuth();
  const [pnl, setPnl] = useState<PnL | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void tenantFetch("/api/v1/reports/profit-and-loss").then(async (response) => {
      if (!response.ok) {
        setError(await readError(response));
        return;
      }
      setPnl((await response.json()) as PnL);
    });
  }, [tenantFetch]);

  if (!permissions.includes("accounting.reports.view")) {
    return (
      <Alert tone="warning" title="Accounting is restricted">
        This role cannot read financial statements. Switch to Owner, Manager or Auditor.
      </Alert>
    );
  }

  return (
    <div>
      <PageHeader title="Accounting" description="Profit and loss from posted demo journals." />
      {error ? (
        <Alert tone="critical" className="mb-4">
          {error}
        </Alert>
      ) : null}
      <div className="grid gap-3 sm:grid-cols-3">
        <Card className="p-4">
          <p className="text-xs text-secondary">Income</p>
          <p className="mt-1 text-xl font-semibold">ZMW {(pnl?.income ?? 0).toLocaleString()}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-secondary">Expenses</p>
          <p className="mt-1 text-xl font-semibold">ZMW {(pnl?.expense ?? 0).toLocaleString()}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-secondary">Net income</p>
          <p className="mt-1 text-xl font-semibold">ZMW {(pnl?.net_income ?? 0).toLocaleString()}</p>
        </Card>
      </div>
    </div>
  );
}
