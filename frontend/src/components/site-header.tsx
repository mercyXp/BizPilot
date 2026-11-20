import Link from "next/link";

import { BrandLogo } from "@/components/brand-logo";

type SiteHeaderProps = {
  active?: "product" | "pricing";
};

export function SiteHeader({ active }: SiteHeaderProps) {
  return (
    <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/90 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <BrandLogo />
        <nav className="flex items-center gap-5 text-sm sm:gap-6">
          <Link
            href="/#pos"
            className={
              active === "product"
                ? "font-semibold text-slate-900"
                : "text-slate-600 hover:text-slate-900"
            }
          >
            Product
          </Link>
          <Link
            href="/pricing"
            className={
              active === "pricing"
                ? "font-semibold text-slate-900"
                : "text-slate-600 hover:text-slate-900"
            }
          >
            Pricing
          </Link>
          <Link
            href="/sign-up"
            className="rounded-full bg-brand-600 px-3.5 py-1.5 font-semibold text-white hover:bg-brand-700"
          >
            Get started
          </Link>
        </nav>
      </div>
    </header>
  );
}
