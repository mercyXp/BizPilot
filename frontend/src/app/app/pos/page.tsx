"use client";

import { useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/page-header";
import { Alert } from "@/components/ui/alert";
import { readError } from "@/lib/api";

type CatalogItem = {
  product_id: string;
  variant_id: string;
  name: string;
  sku: string | null;
  price: number;
  qty_on_hand: number;
};

type Warehouse = { id: string; branch_id: string; name: string; is_default: boolean };

export default function PosPage() {
  const { tenantFetch, permissions, branchId } = useAuth();
  const canSell = permissions.includes("sales.create") && permissions.includes("pos.session.open");
  const [items, setItems] = useState<CatalogItem[]>([]);
  const [cart, setCart] = useState<Record<string, number>>({});
  const [receipt, setReceipt] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  useEffect(() => {
    void tenantFetch("/api/v1/demo/catalog")
      .then(async (response) => {
        if (!response.ok) return;
        const body = (await response.json()) as { items: CatalogItem[] };
        setItems(body.items);
      });
  }, [tenantFetch]);

  const total = useMemo(() => {
    return items.reduce((sum, item) => sum + (cart[item.variant_id] || 0) * item.price, 0);
  }, [cart, items]);

  async function checkout() {
    setError(null);
    setReceipt(null);
    setPending(true);
    const warehouses = await tenantFetch(`/api/v1/warehouses?branch_id=${branchId ?? ""}`);
    if (!warehouses.ok) {
      setPending(false);
      setError(await readError(warehouses));
      return;
    }
    const rows = (await warehouses.json()) as Warehouse[];
    const warehouse = rows.find((row) => row.is_default) ?? rows[0];
    if (!warehouse) {
      setPending(false);
      setError("This branch has no warehouse.");
      return;
    }
    const session = await tenantFetch("/api/v1/pos/sessions", {
      method: "POST",
      body: JSON.stringify({ warehouse_id: warehouse.id, opening_float: 200 }),
    });
    if (!session.ok) {
      setPending(false);
      setError(await readError(session));
      return;
    }
    const pos = (await session.json()) as { id: string };
    const saleItems = items
      .filter((item) => (cart[item.variant_id] || 0) > 0)
      .map((item) => ({ variant_id: item.variant_id, qty: cart[item.variant_id] }));
    const sale = await tenantFetch(`/api/v1/pos/sessions/${pos.id}/sales`, {
      method: "POST",
      idempotencyKey: crypto.randomUUID(),
      body: JSON.stringify({
        items: saleItems,
        payments: [{ method: "cash", amount: total }],
      }),
    });
    setPending(false);
    if (!sale.ok) {
      setError(await readError(sale));
      return;
    }
    const body = (await sale.json()) as { document_number: string; total: number };
    setReceipt(`${body.document_number} · ZMW ${body.total.toFixed(2)}`);
    setCart({});
  }

  if (!canSell) {
    return (
      <Alert tone="warning" title="POS is not available for this role">
        Switch to Salesperson or Manager to complete a checkout. Backend permissions still apply if the URL is
        forced.
      </Alert>
    );
  }

  return (
    <div>
      <PageHeader title="Point of Sale" description="Complete a demo sale and print a receipt number." />
      {error ? (
        <Alert tone="critical" className="mb-4" title="Checkout failed">
          {error}
        </Alert>
      ) : null}
      {receipt ? (
        <Alert tone="success" className="mb-4" title="Receipt">
          {receipt}
        </Alert>
      ) : null}
      <div className="grid gap-4 lg:grid-cols-[1fr_280px]">
        <Card className="p-4">
          <ul className="divide-y divide-border">
            {items.slice(0, 16).map((item) => (
              <li key={item.variant_id} className="flex items-center justify-between gap-3 py-2">
                <div>
                  <p className="text-sm font-medium text-ink">{item.name}</p>
                  <p className="text-xs text-secondary">
                    ZMW {item.price.toFixed(2)} · {item.qty_on_hand} on hand
                  </p>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setCart((current) => ({ ...current, [item.variant_id]: (current[item.variant_id] || 0) + 1 }))}
                >
                  Add
                </Button>
              </li>
            ))}
          </ul>
        </Card>
        <Card className="h-fit p-4">
          <h2 className="text-sm font-semibold text-ink">Basket</h2>
          <p className="mt-2 text-2xl font-semibold text-ink">ZMW {total.toFixed(2)}</p>
          <Button className="mt-4 w-full" disabled={pending || total <= 0} onClick={() => void checkout()}>
            {pending ? "Posting…" : "Complete sale"}
          </Button>
        </Card>
      </div>
    </div>
  );
}
