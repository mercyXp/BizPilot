"use client";

import { Alert } from "@/components/ui/alert";
import { PageHeader } from "@/components/ui/page-header";

export default function Page() {
  return (
    <div>
      <PageHeader
        title="Storage Center Transfers"
        description="Move stock between the places this store keeps it"
      />
      <div className="mb-4 flex gap-4 border-b border-border text-sm">
        <span className="border-b-2 border-brand px-1 py-2 font-medium text-brand-deep">New transfer</span>
        <span className="px-1 py-2 text-secondary">History</span>
      </div>
      <Alert tone="information" title="Add a second storage centre">
        Add a second storage centre to move stock between centres.
      </Alert>
    </div>
  );
}
