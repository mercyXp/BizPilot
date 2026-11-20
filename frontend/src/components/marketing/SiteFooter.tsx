import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="border-t border-border bg-canvas px-6 py-8 text-xs text-muted">
      <div className="mx-auto flex max-w-6xl flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p>BizPilot · Zambia-first operations · Prices in ZMW</p>
        <div className="flex flex-wrap gap-4">
          <Link href="/pricing" className="hover:text-ink">
            Pricing
          </Link>
          <Link href="/pricing#accounting" className="hover:text-ink">
            Accounting
          </Link>
          <Link href="/pricing#payroll" className="hover:text-ink">
            Payroll
          </Link>
          <Link href="/sign-up" className="hover:text-ink">
            See Demo
          </Link>
        </div>
      </div>
    </footer>
  );
}
