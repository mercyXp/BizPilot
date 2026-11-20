import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="bg-ink text-white">
      <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-8 text-sm text-white/80 sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <p>BizPilot · Zambia · Prices in ZMW</p>
        <div className="flex flex-wrap gap-4">
          <Link href="/pricing" className="hover:text-white">
            Pricing
          </Link>
          <Link href="/pricing#accounting" className="hover:text-white">
            Accounting
          </Link>
          <Link href="/pricing#payroll" className="hover:text-white">
            Payroll
          </Link>
          <Link href="/sign-up" className="hover:text-white">
            Create account
          </Link>
        </div>
      </div>
    </footer>
  );
}
