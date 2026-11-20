"use client";

import { useEffect, useState, type FormEvent } from "react";
import { Globe, MonitorSmartphone, Receipt, Scale, User, Info } from "lucide-react";

import { useAuth } from "@/components/AuthProvider";
import { useI18n } from "@/components/I18nProvider";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Field, Input, Select } from "@/components/ui/input";
import { PageHeader } from "@/components/ui/page-header";
import { Badge } from "@/components/ui/badge";
import { Alert } from "@/components/ui/alert";
import { apiFetch, readError, type OrganizationPublic } from "@/lib/api";
import { cn } from "@/lib/cn";

const sections = [
  { id: "hardware", label: "Hardware", icon: MonitorSmartphone },
  { id: "receipts", label: "Receipts", icon: Receipt },
  { id: "rules", label: "Selling rules", icon: Scale },
  { id: "account", label: "My account", icon: User },
  { id: "language", label: "Language", icon: Globe },
  { id: "org", label: "Organisation", icon: Info },
] as const;

type SectionId = (typeof sections)[number]["id"];

const BARCODE_KEY = "bizpilot.barcodeMode";

export default function SettingsPage() {
  const {
    user,
    organizations,
    currentOrg,
    selectOrg,
    accessToken,
    reloadMemberships,
    tenantFetch,
  } = useAuth();
  const { t, locale, setLocale, professionalKeys } = useI18n();
  const [section, setSection] = useState<SectionId>("hardware");
  const [barcode, setBarcode] = useState(false);
  const [scan, setScan] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  useEffect(() => {
    setBarcode(window.localStorage.getItem(BARCODE_KEY) === "1");
  }, []);

  async function createOrg(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken) return;
    setPending(true);
    setError(null);
    const form = new FormData(event.currentTarget);
    const response = await apiFetch("/api/v1/organizations", {
      method: "POST",
      accessToken,
      body: JSON.stringify({ name: String(form.get("name") || "") }),
    });
    setPending(false);
    if (!response.ok) {
      setError(await readError(response));
      return;
    }
    const org = (await response.json()) as OrganizationPublic;
    await reloadMemberships();
    selectOrg(org);
    event.currentTarget.reset();
  }

  return (
    <div>
      <PageHeader
        title="Settings"
        description="Each section says who its settings change."
      />
      <div className="grid gap-4 lg:grid-cols-[220px_1fr]">
        <Card className="h-fit p-2">
          {sections.map((item) => {
            const Icon = item.icon;
            const active = item.id === section;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => setSection(item.id)}
                className={cn(
                  "flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm transition-colors duration-standard",
                  active ? "bg-brand-soft font-medium text-brand-deep" : "text-secondary hover:bg-muted-bg",
                )}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </button>
            );
          })}
        </Card>

        {section === "hardware" ? (
          <Card className="p-5">
            <div className="flex items-center gap-2">
              <h2 className="text-base font-semibold text-ink">Hardware</h2>
              <Badge tone="warning">This computer</Badge>
            </div>
            <div className="mt-4 flex items-start justify-between gap-4 border-b border-border pb-4">
              <div>
                <p className="text-sm font-medium text-ink">Start sales with Barcode Mode on</p>
                <p className="text-sm text-secondary">
                  Each new sale opens ready for the scanner. Saved on this computer only.
                </p>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={barcode}
                onClick={() => {
                  const next = !barcode;
                  setBarcode(next);
                  window.localStorage.setItem(BARCODE_KEY, next ? "1" : "0");
                }}
                className={cn(
                  "relative h-6 w-11 rounded-full transition-colors duration-standard",
                  barcode ? "bg-brand" : "bg-border",
                )}
              >
                <span
                  className={cn(
                    "absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform duration-standard",
                    barcode ? "translate-x-5" : "translate-x-0.5",
                  )}
                />
              </button>
            </div>
            <div className="pt-4">
              <p className="text-sm font-medium text-ink">Test your scanner</p>
              <p className="text-sm text-secondary">
                Scan any item to see the code read and whether the scanner pressed Enter. Nothing is sold.
              </p>
              <Input
                className="mt-3 max-w-md"
                placeholder="Scan any item"
                value={scan}
                onChange={(event) => setScan(event.target.value)}
              />
              <p className="mt-2 text-xs text-muted">{scan ? `Last scan: ${scan}` : "Nothing scanned yet."}</p>
            </div>
          </Card>
        ) : null}

        {section === "receipts" ? (
          <Card className="p-5">
            <h2 className="text-base font-semibold text-ink">Receipts</h2>
            <p className="mt-2 text-sm text-secondary">
              Receipt layout and printer pairing arrive with POS. Footer text and logo stay store-scoped.
            </p>
          </Card>
        ) : null}

        {section === "rules" ? (
          <Card className="p-5">
            <h2 className="text-base font-semibold text-ink">Selling rules</h2>
            <p className="mt-2 text-sm text-secondary">
              Discounts, price overrides and credit limits will live here. They are not configured yet.
            </p>
          </Card>
        ) : null}

        {section === "account" ? (
          <Card className="p-5">
            <h2 className="text-base font-semibold text-ink">My account</h2>
            <dl className="mt-4 space-y-2 text-sm">
              <div>
                <dt className="text-secondary">Name</dt>
                <dd className="font-medium text-ink">{user?.full_name}</dd>
              </div>
              <div>
                <dt className="text-secondary">Email</dt>
                <dd className="font-medium text-ink">{user?.email}</dd>
              </div>
              <div>
                <dt className="text-secondary">Email verified</dt>
                <dd>{user?.email_verified ? <Badge tone="success">Verified</Badge> : <Badge tone="warning">Pending</Badge>}</dd>
              </div>
            </dl>
          </Card>
        ) : null}

        {section === "language" ? (
          <Card className="p-5">
            <h2 className="text-base font-semibold text-ink">{t("settings.language")}</h2>
            <p className="mt-2 text-sm text-secondary">{t("settings.language_hint")}</p>
            <label className="mt-4 block max-w-xs text-xs font-medium text-secondary">
              Locale
              <Select
                className="mt-1"
                value={locale}
                onChange={(event) => {
                  const next = event.target.value;
                  setLocale(next);
                  void tenantFetch("/api/v1/organization-locale", {
                    method: "PUT",
                    body: JSON.stringify({
                      default_locale: next,
                      enabled_locales: ["en", next],
                    }),
                  });
                }}
              >
                <option value="en">English</option>
                <option value="ny">Chichewa</option>
              </Select>
            </label>
            {professionalKeys.length ? (
              <p className="mt-3 text-xs text-secondary">
                Professional translations locked: {professionalKeys.join(", ")}
              </p>
            ) : null}
          </Card>
        ) : null}

        {section === "org" ? (
          <div className="space-y-4">
            <Card className="p-5">
              <h2 className="text-sm font-semibold text-ink">Switch organisation</h2>
              {organizations.length === 0 ? (
                <p className="mt-2 text-sm text-secondary">You do not belong to an organisation yet.</p>
              ) : (
                <ul className="mt-3 space-y-2">
                  {organizations.map((org) => (
                    <li key={org.id}>
                      <button
                        type="button"
                        onClick={() => selectOrg(org)}
                        className={cn(
                          "w-full rounded-md border px-3 py-2 text-left text-sm transition-colors duration-standard",
                          currentOrg?.id === org.id
                            ? "border-brand bg-brand-soft"
                            : "border-border hover:border-brand/40",
                        )}
                      >
                        <span className="font-medium text-ink">{org.name}</span>
                        <span className="ml-2 text-secondary">
                          {org.base_currency_code}
                          {org.is_owner ? " · owner" : ""}
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
            <Card className="p-5">
              <h2 className="text-sm font-semibold text-ink">Create organisation</h2>
              <p className="mt-1 text-sm text-secondary">Requires a verified email. Default currency is ZMW.</p>
              {error ? (
                <Alert tone="critical" className="mt-3">
                  {error}
                </Alert>
              ) : null}
              <form className="mt-4 max-w-md space-y-3" onSubmit={createOrg}>
                <Field label="Organisation name">
                  <Input name="name" required minLength={2} />
                </Field>
                <Button type="submit" disabled={pending}>
                  {pending ? "Creating…" : "Create organisation"}
                </Button>
              </form>
            </Card>
          </div>
        ) : null}
      </div>
    </div>
  );
}
