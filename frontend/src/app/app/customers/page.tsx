"use client";

import { Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/ui/page-header";
import { Badge } from "@/components/ui/badge";

export default function CustomersPage() {
  return (
    <div>
      <PageHeader
        title="Customers"
        description="Keep a customer list and record who bought what"
        actions={
          <>
            <Button variant="outline">Refresh</Button>
            <Button variant="outline">Import</Button>
            <Button variant="outline">Export</Button>
            <Button>+ Add customer</Button>
          </>
        }
      />
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="relative max-w-sm flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
          <Input className="pl-9" placeholder="Search by name, phone, email or TPIN" />
        </div>
        <p className="text-sm text-secondary">
          Owed to you in all <span className="font-semibold text-warning">ZMW 0.00</span>
        </p>
      </div>
      <div className="mb-3 flex gap-2">
        <Badge tone="muted">All customers (0)</Badge>
        <Badge tone="warning">Owes money (0)</Badge>
      </div>
      <Card className="overflow-hidden">
        <table className="w-full text-left text-sm [&_tbody_tr]:transition-colors [&_tbody_tr]:duration-fast hover:[&_tbody_tr]:bg-canvas">
          <thead className="border-b border-border bg-canvas text-[11px] uppercase tracking-wide text-secondary">
            <tr>
              {["Code", "Customer", "Phone", "Owes", "Email", "TPIN", "Address", "Actions"].map((h) => (
                <th key={h} className="px-3 py-2 font-medium">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr>
              <td colSpan={8} className="px-3 py-16 text-center text-sm text-muted">
                No customers yet. Add one to track sales on account.
              </td>
            </tr>
          </tbody>
        </table>
      </Card>
    </div>
  );
}
