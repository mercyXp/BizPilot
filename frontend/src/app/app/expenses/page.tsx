"use client";

import { useEffect, useState, type FormEvent } from "react";

import { useAuth } from "@/components/AuthProvider";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Field, Input } from "@/components/ui/input";
import { PageHeader } from "@/components/ui/page-header";
import { Alert } from "@/components/ui/alert";
import { readError } from "@/lib/api";

type Expense = {
  id: string;
  document_number: string;
  vendor_name: string;
  amount: number;
  status: string;
  incurred_on: string;
};

export default function ExpensesPage() {
  const { tenantFetch, permissions } = useAuth();
  const canCreate = permissions.includes("expenses.create");
  const [rows, setRows] = useState<Expense[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function reload() {
    const response = await tenantFetch("/api/v1/demo/expenses");
    if (!response.ok) {
      setError(await readError(response));
      return;
    }
    setRows(((await response.json()) as { items: Expense[] }).items);
  }

  useEffect(() => {
    void reload();
  }, []);

  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const response = await tenantFetch("/api/v1/expenses", {
      method: "POST",
      body: JSON.stringify({
        vendor_name: String(form.get("vendor") || "Demo vendor"),
        amount: Number(form.get("amount") || 0),
        incurred_on: new Date().toISOString().slice(0, 10),
        payment_method: "cash",
      }),
    });
    if (!response.ok) {
      setError(await readError(response));
      return;
    }
    event.currentTarget.reset();
    await reload();
  }

  return (
    <div>
      <PageHeader title="Expenses" description="Operating costs posted against Mwamba’s ledger." />
      {error ? (
        <Alert tone="critical" className="mb-4">
          {error}
        </Alert>
      ) : null}
      {canCreate ? (
        <Card className="mb-4 p-4">
          <form className="flex flex-wrap items-end gap-3" onSubmit={(event) => void create(event)}>
            <Field label="Vendor">
              <Input name="vendor" required placeholder="ZESCO" />
            </Field>
            <Field label="Amount (ZMW)">
              <Input name="amount" type="number" min={1} step="0.01" required />
            </Field>
            <Button type="submit">Record expense</Button>
          </form>
        </Card>
      ) : null}
      <Card className="overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-border bg-canvas text-xs uppercase text-secondary">
            <tr>
              <th className="px-3 py-2">Number</th>
              <th className="px-3 py-2">Vendor</th>
              <th className="px-3 py-2">Amount</th>
              <th className="px-3 py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} className="border-b border-border">
                <td className="px-3 py-2">{row.document_number}</td>
                <td className="px-3 py-2">{row.vendor_name}</td>
                <td className="px-3 py-2">ZMW {row.amount.toFixed(2)}</td>
                <td className="px-3 py-2">{row.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
