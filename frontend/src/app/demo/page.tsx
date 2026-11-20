"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Play } from "lucide-react";
import Link from "next/link";

import { useAuth } from "@/components/AuthProvider";
import { Logo } from "@/components/ui/logo";
import { Alert } from "@/components/ui/alert";
import { apiFetch } from "@/lib/api";

type BranchOption = {
  code: string;
  name: string;
  city: string;
  kind: string;
  label: string;
};

type BusinessOption = {
  slug: string;
  name: string;
  size_label: string;
  summary: string;
  branches: BranchOption[];
};

type IndustryOption = {
  key: string;
  name: string;
  summary: string;
  businesses: BusinessOption[];
};

type RoleOption = { key: string; title: string; summary: string };

const selectClass =
  "mt-3 h-12 w-full rounded-full border border-slate-200 bg-white px-5 text-sm text-ink shadow-sm outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20 disabled:bg-slate-50 disabled:text-muted";

export default function DemoAccessPage() {
  const router = useRouter();
  const { enterDemo } = useAuth();
  const [industries, setIndustries] = useState<IndustryOption[]>([]);
  const [roles, setRoles] = useState<RoleOption[]>([]);
  const [industryKey, setIndustryKey] = useState("");
  const [businessSlug, setBusinessSlug] = useState("");
  const [branchCode, setBranchCode] = useState("");
  const [roleKey, setRoleKey] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void apiFetch("/api/v1/demo/centre").then(async (response) => {
      if (!response.ok) return;
      const body = (await response.json()) as { industries: IndustryOption[]; roles: RoleOption[] };
      setIndustries(body.industries);
      setRoles(body.roles);
    });
  }, []);

  const industry = industries.find((row) => row.key === industryKey);
  const business = industry?.businesses.find((row) => row.slug === businessSlug);
  const ready = Boolean(industryKey && businessSlug && branchCode && roleKey);

  const branchOptions = useMemo(() => {
    if (!business) return [];
    const ownerLike = ["owner", "admin", "accountant", "auditor"].includes(roleKey);
    const rows = business.branches.map((row) => ({
      value: row.code,
      label: row.kind === "headquarters" ? `${row.name} · Headquarters · ${row.city}` : `${row.name} · Retail branch · ${row.city}`,
    }));
    if (ownerLike) {
      return [{ value: "ALL", label: "All branches · consolidated view" }, ...rows];
    }
    return rows;
  }, [business, roleKey]);

  async function launch() {
    if (!ready) return;
    setError(null);
    setPending(true);
    try {
      await enterDemo(roleKey, {
        business: businessSlug,
        branchCode: branchCode === "ALL" ? undefined : branchCode,
      });
      router.push("/app");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not open the live demo");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#eefbf8] text-ink">
      <div
        aria-hidden
        className="pointer-events-none absolute -left-24 top-[-6rem] h-[28rem] w-[28rem] rounded-full bg-[#b7f3ea]/70 blur-3xl"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute -right-16 top-8 h-[34rem] w-[34rem] rounded-full bg-[#c7f6ef]/80 blur-3xl"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute bottom-40 left-1/3 h-72 w-72 rounded-full bg-white/50 blur-2xl"
      />

      <header className="relative z-10 mx-auto flex max-w-5xl items-center px-4 py-5 sm:px-6">
        <Link href="/" aria-label="BizPilot home">
          <Logo height={36} />
        </Link>
      </header>

      <main className="relative z-10 mx-auto max-w-3xl px-4 pb-20 pt-6 text-center sm:px-6">
        <p className="inline-flex items-center gap-2 rounded-full bg-white/80 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-brand-deep shadow-sm">
          <Play className="h-3 w-3 fill-current" />
          Interactive demo
        </p>
        <h1 className="mt-6 text-4xl font-semibold tracking-tight text-slate-900 sm:text-5xl">
          Explore BizPilot
          <span className="block text-brand">in action.</span>
        </h1>
        <p className="mx-auto mt-4 max-w-xl text-base text-slate-600">
          Choose an industry. Explore real businesses and experience BizPilot from different user
          roles. No registration required.
        </p>

        {error ? (
          <Alert tone="critical" className="mt-6 text-left" title="Demo unavailable">
            {error}
          </Alert>
        ) : null}

        <ol className="mt-10 space-y-8 text-left">
          <li>
            <Step n={1} title="Choose an industry" body="Select the type of business you want to explore." />
            <select
              className={selectClass}
              value={industryKey}
              onChange={(event) => {
                setIndustryKey(event.target.value);
                setBusinessSlug("");
                setBranchCode("");
              }}
            >
              <option value="">Choose Industry</option>
              {industries.map((row) => (
                <option key={row.key} value={row.key}>
                  {row.name}
                </option>
              ))}
            </select>
          </li>
          <li>
            <Step n={2} title="Choose a business" body="Explore sample businesses in this industry." />
            <select
              className={selectClass}
              value={businessSlug}
              disabled={!industry}
              onChange={(event) => {
                setBusinessSlug(event.target.value);
                setBranchCode("");
              }}
            >
              <option value="">Choose Business</option>
              {industry?.businesses.map((row) => (
                <option key={row.slug} value={row.slug}>
                  {row.name} — {row.size_label}
                </option>
              ))}
            </select>
          </li>
          <li>
            <Step n={3} title="Choose a branch and role" body="Select a branch and the role you want to experience." />
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              <select
                className={selectClass + " mt-0"}
                value={branchCode}
                disabled={!business}
                onChange={(event) => setBranchCode(event.target.value)}
              >
                <option value="">Choose Branch</option>
                {branchOptions.map((row) => (
                  <option key={row.value} value={row.value}>
                    {row.label}
                  </option>
                ))}
              </select>
              <select
                className={selectClass + " mt-0"}
                value={roleKey}
                onChange={(event) => {
                  setRoleKey(event.target.value);
                  if (event.target.value && ["owner", "admin", "accountant", "auditor"].includes(event.target.value) === false && branchCode === "ALL") {
                    setBranchCode("");
                  }
                }}
              >
                <option value="">Choose Role</option>
                {roles.map((row) => (
                  <option key={row.key} value={row.key}>
                    {row.title}
                  </option>
                ))}
              </select>
            </div>
          </li>
        </ol>

        <button
          type="button"
          onClick={() => void launch()}
          disabled={!ready || pending}
          className="mt-10 inline-flex h-12 items-center gap-2 rounded-full bg-brand px-10 text-sm font-semibold text-white shadow-sm transition hover:bg-brand-deep disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Play className="h-4 w-4 fill-current" />
          {pending ? "Launching…" : "Launch Demo"}
        </button>
      </main>

      <DemoCentreFooter />
    </div>
  );
}

function Step({ n, title, body }: { n: number; title: string; body: string }) {
  return (
    <div className="flex gap-4">
      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand text-sm font-semibold text-white">
        {n}
      </span>
      <div>
        <p className="text-base font-semibold text-slate-900">{title}</p>
        <p className="mt-1 text-sm text-slate-500">{body}</p>
      </div>
    </div>
  );
}

function DemoCentreFooter() {
  return (
    <footer className="relative z-10 bg-[#0b3b40] text-white">
      <div className="mx-auto grid max-w-6xl gap-8 px-6 py-10 sm:grid-cols-5">
        <div>
          <Logo height={36} className="brightness-0 invert" />
          <p className="mt-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-white/70">
            Run your business with clarity.
          </p>
        </div>
        <div>
          <p className="text-sm font-semibold">Quick Links</p>
          <ul className="mt-3 space-y-2 text-sm text-white/75">
            <li><Link href="/">Home</Link></li>
            <li><Link href="/#pos">Solutions</Link></li>
            <li><Link href="/pricing">Pricing</Link></li>
          </ul>
        </div>
        <div>
          <p className="text-sm font-semibold">Support</p>
          <ul className="mt-3 space-y-2 text-sm text-white/75">
            <li><Link href="/contact">FAQs</Link></li>
            <li><Link href="/contact">Contact Us</Link></li>
            <li><Link href="/about">Help Center</Link></li>
          </ul>
        </div>
        <div>
          <p className="text-sm font-semibold">Follow Us</p>
          <p className="mt-3 text-sm text-white/75">Facebook · LinkedIn · YouTube</p>
        </div>
        <div className="sm:text-right">
          <p className="text-sm text-white/90">🇿🇲 Proudly supporting Zambian businesses</p>
        </div>
      </div>
      <div className="border-t border-white/10 px-6 py-4 text-xs text-white/60">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 sm:flex-row sm:justify-between">
          <p>© 2026 BizPilot. All rights reserved.</p>
          <p>Privacy Policy | Terms of Service</p>
        </div>
      </div>
    </footer>
  );
}
