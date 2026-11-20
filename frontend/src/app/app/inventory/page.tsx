"use client";

import { useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/page-header";
import { Alert } from "@/components/ui/alert";
import { readError } from "@/lib/api";

type Balance = {
  warehouse_id: string;
  variant_id: string;
  qty_on_hand: number;
  avg_unit_cost: number;
};

type CatalogItem = { variant_id: string; name: string };

export default function InventoryPage() {
  const { tenantFetch, permissions, branchId } = useAuth();
  const canReceive = permissions.includes("inventory.adjust");
  const [rows, setRows] = useState<Balance[]>([]);
  const [catalog, setCatalog] = useState<CatalogItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function reload() {
    const response = await tenantFetch("/api/v1/stock-balances");
    if (!response.ok) {
      setError(await readError(response));
      return;
    }
    setRows((await response.json()) as Balance[]);
  }

  useEffect(() => {
    void reload();
    void tenantFetch("/api/v1/demo/catalog").then(async (response) => {
      if (response.ok) {
        setCatalog(((await response.json()) as { items: CatalogItem[] }).items);
      }
    });
  }, [tenantFetch]);

  async function receive() {
    setError(null);
    const warehouses = await tenantFetch(`/api/v1/warehouses?branch_id=${branchId ?? ""}`);
    if (!warehouses.ok) {
      setError(await readError(warehouses));
      return;
    }
    const warehouse = ((await warehouses.json()) as { id: string; is_default: boolean }[]).find(
      (row) => row.is_default,
    );
    const item = catalog[0];
    if (!warehouse || !item) {
      setError("Need a warehouse and a product to receive stock.");
      return;
    }
    const response = await tenantFetch("/api/v1/inventory/adjustments", {
      method: "POST",
      body: JSON.stringify({
        warehouse_id: warehouse.id,
        variant_id: item.variant_id,
        qty_delta: 12,
        unit_cost: 8,
        source_type: "purchase_receipt",
      }),
    });
    if (!response.ok) {
      setError(await readError(response));
      return;
    }
    setMessage(`Received 12 units of ${item.name}`);
    await reload();
  }

  return (
    <div>
      <PageHeader
        title="Stock levels"
        description="Opening balances plus receipts. Switch branch from the demo banner."
        actions={
          canReceive ? (
            <Button onClick={() => void receive()}>Receive delivery</Button>
          ) : undefined
        }
      />
      {error ? (
        <Alert tone="critical" className="mb-4">
          {error}
        </Alert>
      ) : null}
      {message ? (
        <Alert tone="success" className="mb-4">
          {message}
        </Alert>
      ) : null}
      <Card className="overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-border bg-canvas text-xs uppercase text-secondary">
            <tr>
              <th className="px-3 py-2">Variant</th>
              <th className="px-3 py-2">On hand</th>
              <th className="px-3 py-2">Avg cost</th>
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 40).map((row) => (
              <tr key={`${row.warehouse_id}-${row.variant_id}`} className="border-b border-border">
                <td className="px-3 py-2">{catalog.find((item) => item.variant_id === row.variant_id)?.name ?? row.variant_id}</td>
                <td className="px-3 py-2">{row.qty_on_hand}</td>
                <td className="px-3 py-2">ZMW {row.avg_unit_cost.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
