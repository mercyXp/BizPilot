"use client";

import { Search, Shapes } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/ui/page-header";

export default function Page() {
  return (
    <div>
      <PageHeader
        title="Sections"
        description="Parts of your shop, like Bakery or Butchery. Put items in sections, then run the Sales or Profit Report for one section."
        actions={
          <>
            <Button variant="outline">Refresh</Button>
            <Button>+ New section</Button>
          </>
        }
      />
      <div className="relative max-w-sm">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
        <Input className="pl-9" placeholder="Search sections" />
      </div>
      <div className="mt-16 flex flex-col items-center text-center">
        <Shapes className="h-10 w-10 text-muted" />
        <p className="mt-3 text-sm text-secondary">No sections yet. Add one with New section.</p>
      </div>
      <p className="mt-10 text-sm text-secondary">Items in no section: 0</p>
    </div>
  );
}
