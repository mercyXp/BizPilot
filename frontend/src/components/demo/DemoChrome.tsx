"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";

import { useAuth } from "@/components/AuthProvider";
import { Button } from "@/components/ui/button";
import { DEMO_ROLES } from "@/components/demo/roles";
import { isDemoTourDone, setDemoTourDone } from "@/lib/session";

const tourSteps = [
  {
    title: "This business is live data",
    body: "Home, POS, inventory and reports all use the same seeded tenant for the industry you chose.",
  },
  {
    title: "Switch roles and branches",
    body: "Owners can consolidate every branch. Managers stay on the branches they are granted.",
  },
  {
    title: "Reset anytime",
    body: "Reset demo data restores this business’s original seed, including stock and journals.",
  },
];

export function DemoChrome() {
  const pathname = usePathname();
  const { isDemo, demoRole, demoSnapshot, branches, branchId, selectBranch, switchDemoRole, resetDemo, tenantFetch } =
    useAuth();
  const [tourOpen, setTourOpen] = useState(false);
  const [step, setStep] = useState(0);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (isDemo && !isDemoTourDone()) setTourOpen(true);
  }, [isDemo]);

  useEffect(() => {
    if (!isDemo) return;
    const module = pathname.replace("/app", "") || "home";
    void tenantFetch("/api/v1/demo/events", {
      method: "POST",
      body: JSON.stringify({ module, action: "view", role: demoRole }),
    });
  }, [demoRole, isDemo, pathname, tenantFetch]);

  if (!isDemo) return null;

  return (
    <>
      <div className="border-b border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-950">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wide">Demo environment · Safe to explore</p>
            <p className="text-xs">
              {demoSnapshot?.organization.name ?? "Demo"} · sample data only. Changes here will not
              affect real business records.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {branches.length ? (
              <select
                className="rounded-md border border-amber-300 bg-white px-2 py-1 text-xs"
                value={branchId ?? ""}
                onChange={(event) => selectBranch(event.target.value)}
                aria-label="Demo branch"
              >
                {branches.map((branch) => (
                  <option key={branch.id} value={branch.id}>
                    {branch.name}
                  </option>
                ))}
              </select>
            ) : null}
            <select
              className="rounded-md border border-amber-300 bg-white px-2 py-1 text-xs"
              value={demoRole ?? "owner"}
              onChange={(event) => {
                setBusy(true);
                void switchDemoRole(event.target.value).finally(() => setBusy(false));
              }}
              aria-label="Demo role"
              disabled={busy}
            >
              {DEMO_ROLES.map((role) => (
                <option key={role.key} value={role.key}>
                  {role.title}
                </option>
              ))}
            </select>
            <Button size="sm" variant="ghost" href="/demo">
              Change business
            </Button>
            <Button
              size="sm"
              variant="outline"
              disabled={busy}
              onClick={() => {
                setBusy(true);
                void resetDemo().finally(() => setBusy(false));
              }}
            >
              Reset demo data
            </Button>
          </div>
        </div>
        <p className="mt-1 text-[11px] text-amber-900/80">
          Demo session · Reset available · {demoSnapshot?.role_title ?? "Explorer"}
        </p>
      </div>

      {tourOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 p-4">
          <div className="max-w-md rounded-xl bg-surface p-5 shadow-lift">
            <p className="text-xs font-semibold uppercase tracking-wide text-brand-deep">Guided demo</p>
            <h2 className="mt-2 text-lg font-semibold text-ink">{tourSteps[step].title}</h2>
            <p className="mt-2 text-sm text-secondary">{tourSteps[step].body}</p>
            <div className="mt-4 flex justify-between gap-2">
              <Button
                variant="ghost"
                onClick={() => {
                  setDemoTourDone();
                  setTourOpen(false);
                }}
              >
                Skip tour
              </Button>
              <Button
                onClick={() => {
                  if (step >= tourSteps.length - 1) {
                    setDemoTourDone();
                    setTourOpen(false);
                    return;
                  }
                  setStep((value) => value + 1);
                }}
              >
                {step >= tourSteps.length - 1 ? "Start exploring" : "Next"}
              </Button>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
