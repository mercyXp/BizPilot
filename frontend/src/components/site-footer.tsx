import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="border-t border-slate-200 bg-white">
      <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-8 text-sm text-slate-500 sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <p>BizPilot · Zambia · Prices in ZMW</p>
        <div className="flex flex-wrap gap-4">
          <Link href="/pricing" className="hover:text-slate-900">
            Pricing
          </Link>
          <Link href="/pricing#accounting" className="hover:text-slate-900">
            Accounting
          </Link>
          <Link href="/pricing#payroll" className="hover:text-slate-900">
            Payroll
          </Link>
          <Link href="/sign-up" className="hover:text-slate-900">
            Create account
          </Link>
        </div>
      </div>
    </footer>
  );
}
