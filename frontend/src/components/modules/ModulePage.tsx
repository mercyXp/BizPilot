"use client";

import { RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { PageHeader } from "@/components/ui/page-header";
import { modules, type ModuleDef, type ModuleSlug } from "@/components/modules/registry";

export function ModulePage({ slug }: { slug: ModuleSlug }) {
  const def: ModuleDef = modules[slug];
  const Icon = def.icon;
  return (
    <div>
      <PageHeader
        title={def.title}
        description={def.description}
        actions={
          <>
            <Button variant="outline" icon={<RefreshCw className="h-3.5 w-3.5" />}>
              Refresh
            </Button>
            {def.actionLabel ? <Button icon={<span>+</span>}>{def.actionLabel}</Button> : null}
          </>
        }
      />
      <EmptyState
        icon={Icon}
        title={def.emptyTitle}
        description={def.emptyDescription}
        action={def.actionLabel ? <Button icon={<span>+</span>}>{def.actionLabel}</Button> : undefined}
      />
    </div>
  );
}
