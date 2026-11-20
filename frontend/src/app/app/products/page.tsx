"use client";

import { useEffect, useState, type FormEvent } from "react";

import { useAuth } from "@/components/AuthProvider";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Field, Input } from "@/components/ui/input";
import { PageHeader } from "@/components/ui/page-header";
import { Alert } from "@/components/ui/alert";
import { readError } from "@/lib/api";

type Product = { id: string; name: string; sku: string | null; type: string };

export default function ProductsPage() {
  const { tenantFetch, permissions } = useAuth();
  const canManage = permissions.includes("catalogue.manage");
  const [rows, setRows] = useState<Product[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function reload() {
    const response = await tenantFetch("/api/v1/products");
    if (!response.ok) {
      setError(await readError(response));
      return;
    }
    setRows((await response.json()) as Product[]);
  }

  useEffect(() => {
    void reload();
  }, []);

  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const uoms = await tenantFetch("/api/v1/units-of-measure");
    if (!uoms.ok) {
      setError(await readError(uoms));
      return;
    }
    const uomId = ((await uoms.json()) as { id: string }[])[0]?.id;
    const response = await tenantFetch("/api/v1/products", {
      method: "POST",
      body: JSON.stringify({
        name: String(form.get("name") || ""),
        type: "goods",
        uom_id: uomId,
        sku: String(form.get("sku") || "") || null,
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
      <PageHeader title="Products" description={`${rows.length} products in the Mwamba catalogue`} />
      {error ? (
        <Alert tone="critical" className="mb-4">
          {error}
        </Alert>
      ) : null}
      {canManage ? (
        <Card className="mb-4 p-4">
          <form className="flex flex-wrap items-end gap-3" onSubmit={(event) => void create(event)}>
            <Field label="New product">
              <Input name="name" required placeholder="e.g. 25kg breakfast mealie meal" />
            </Field>
            <Field label="SKU">
              <Input name="sku" placeholder="MRG-NEW" />
            </Field>
            <Button type="submit">Add product</Button>
          </form>
        </Card>
      ) : null}
      <Card className="overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-border bg-canvas text-xs uppercase text-secondary">
            <tr>
              <th className="px-3 py-2">Name</th>
              <th className="px-3 py-2">SKU</th>
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 40).map((row) => (
              <tr key={row.id} className="border-b border-border">
                <td className="px-3 py-2">{row.name}</td>
                <td className="px-3 py-2 text-secondary">{row.sku}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
