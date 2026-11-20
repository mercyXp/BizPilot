"use client";

import Link from "next/link";
import { ChevronDown, Menu, X } from "lucide-react";
import { useState, type ReactNode } from "react";

import { Logo } from "@/components/ui/logo";
import { STORE_TYPES } from "@/lib/pricing";

export type MarketingNavId =
  | "home"
  | "solutions"
  | "industries"
  | "pricing"
  | "about"
  | "contact";

type SiteHeaderProps = {
  active?: MarketingNavId;
};

const SOLUTIONS = [
  { href: "/#pos", label: "Point of sale" },
  { href: "/pricing#accounting", label: "Accounting" },
  { href: "/pricing#payroll", label: "Payroll" },
];

export function SiteHeader({ active = "home" }: SiteHeaderProps) {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-30 border-b border-border/80 bg-surface">
      <div className="relative">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-y-0 right-0 w-1/3 bg-gradient-to-l from-brand-soft/90 via-brand-soft/40 to-transparent"
        />
        <div className="relative mx-auto flex h-[4.25rem] max-w-6xl items-center gap-4 px-4 sm:px-6">
          <Link href="/" className="relative z-10 flex shrink-0 items-center" aria-label="BizPilot home">
            <Logo height={36} priority />
          </Link>

          <nav className="ml-2 hidden flex-1 items-center gap-5 text-sm font-medium text-ink lg:flex xl:gap-6">
            <NavLink href="/" active={active === "home"}>
              Home
            </NavLink>
            <HoverMenu label="Solutions" active={active === "solutions"}>
              {SOLUTIONS.map((item) => (
                <DropdownLink key={item.href} href={item.href}>
                  {item.label}
                </DropdownLink>
              ))}
            </HoverMenu>
            <HoverMenu label="Industries" active={active === "industries"}>
              {STORE_TYPES.map((type) => (
                <DropdownLink key={type.id} href={`/pricing?store=${type.id}`}>
                  {type.label}
                </DropdownLink>
              ))}
            </HoverMenu>
            <NavLink href="/pricing" active={active === "pricing"}>
              Pricing
            </NavLink>
            <NavLink href="/about" active={active === "about"}>
              About Us
            </NavLink>
            <NavLink href="/contact" active={active === "contact"}>
              Contact
            </NavLink>
          </nav>

          <div className="ml-auto hidden items-center gap-4 lg:flex">
            <Link href="/sign-in" className="text-sm font-medium text-ink hover:text-brand-deep">
              Login
            </Link>
            <Link
              href="/#demo"
              className="rounded-full bg-brand px-5 py-2 text-sm font-semibold text-white shadow-sm hover:bg-brand-deep focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2"
            >
              See Demo
            </Link>
          </div>

          <button
            type="button"
            className="ml-auto inline-flex h-10 w-10 items-center justify-center rounded-lg text-ink hover:bg-canvas lg:hidden"
            aria-expanded={open}
            aria-controls="mobile-nav"
            onClick={() => setOpen((value) => !value)}
          >
            <span className="sr-only">Menu</span>
            {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {open ? (
        <div id="mobile-nav" className="border-t border-border bg-surface px-4 py-4 lg:hidden">
          <div className="flex flex-col gap-3 text-sm font-medium text-ink">
            <Link href="/" onClick={() => setOpen(false)}>
              Home
            </Link>
            <p className="text-xs font-semibold uppercase tracking-wide text-muted">Solutions</p>
            {SOLUTIONS.map((item) => (
              <Link key={item.href} href={item.href} className="pl-2" onClick={() => setOpen(false)}>
                {item.label}
              </Link>
            ))}
            <p className="text-xs font-semibold uppercase tracking-wide text-muted">Industries</p>
            {STORE_TYPES.map((type) => (
              <Link
                key={type.id}
                href={`/pricing?store=${type.id}`}
                className="pl-2"
                onClick={() => setOpen(false)}
              >
                {type.label}
              </Link>
            ))}
            <Link href="/pricing" onClick={() => setOpen(false)}>
              Pricing
            </Link>
            <Link href="/about" onClick={() => setOpen(false)}>
              About Us
            </Link>
            <Link href="/contact" onClick={() => setOpen(false)}>
              Contact
            </Link>
            <Link href="/sign-in" onClick={() => setOpen(false)}>
              Login
            </Link>
            <Link
              href="/#demo"
              className="mt-1 inline-flex w-fit rounded-full bg-brand px-5 py-2 text-sm font-semibold text-white"
              onClick={() => setOpen(false)}
            >
              See Demo
            </Link>
          </div>
        </div>
      ) : null}
    </header>
  );
}

function NavLink({
  href,
  active,
  children,
}: {
  href: string;
  active?: boolean;
  children: string;
}) {
  return (
    <Link
      href={href}
      className={
        active
          ? "relative text-ink after:absolute after:-top-[1.35rem] after:left-1/2 after:h-[7px] after:w-10 after:-translate-x-1/2 after:rounded-b-full after:bg-brand"
          : "text-ink/80 hover:text-ink"
      }
    >
      {children}
    </Link>
  );
}

function HoverMenu({
  label,
  active,
  children,
}: {
  label: string;
  active?: boolean;
  children: ReactNode;
}) {
  return (
    <div className="group relative">
      <button
        type="button"
        className={
          active
            ? "relative inline-flex items-center gap-1 text-ink after:absolute after:-top-[1.35rem] after:left-1/2 after:h-[7px] after:w-10 after:-translate-x-1/2 after:rounded-b-full after:bg-brand"
            : "inline-flex items-center gap-1 text-ink/80 hover:text-ink"
        }
        aria-haspopup="menu"
      >
        {label}
        <ChevronDown className="h-3.5 w-3.5" aria-hidden />
      </button>
      <div className="invisible absolute left-0 top-full z-40 pt-2 opacity-0 group-hover:visible group-hover:opacity-100 group-focus-within:visible group-focus-within:opacity-100">
        <div className="min-w-52 rounded-xl border border-border bg-surface py-2 shadow-card">
          {children}
        </div>
      </div>
    </div>
  );
}

function DropdownLink({ href, children }: { href: string; children: string }) {
  return (
    <Link
      href={href}
      className="block px-4 py-2 text-sm font-medium text-ink hover:bg-brand-soft hover:text-brand-deep"
    >
      {children}
    </Link>
  );
}
