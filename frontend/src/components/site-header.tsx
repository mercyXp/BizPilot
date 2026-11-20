import Link from "next/link";

import { BrandLogo } from "@/components/brand-logo";

type SiteHeaderProps = {
  active?: "product" | "pricing";
};

export function SiteHeader({ active }: SiteHeaderProps) {
  return (
    <header className="sticky top-0 z-30 border-b border-ink/10 bg-surface/90 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <BrandLogo />
        <nav className="flex items-center gap-3 text-sm sm:gap-6">
          <Link
            href="/#pos"
            className={
              active === "product"
                ? "hidden font-semibold text-brand-600 sm:inline"
                : "hidden text-ink-muted hover:text-ink sm:inline"
            }
          >
            Product
          </Link>
          <Link
            href="/pricing"
            className={
              active === "pricing"
                ? "font-semibold text-brand-600"
                : "text-ink-muted hover:text-ink"
            }
          >
            Pricing
          </Link>
          <Link
            href="/sign-up"
            className="rounded-full bg-brand-600 px-3 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-brand-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 sm:px-3.5 sm:text-sm"
          >
            Get started
          </Link>
        </nav>
      </div>
    </header>
  );
}
