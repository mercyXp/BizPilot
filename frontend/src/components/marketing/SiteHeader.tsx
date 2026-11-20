"use client";

import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Logo } from "@/components/ui/logo";
import { cn } from "@/lib/cn";

const links = [
  { href: "/", label: "Home", id: "home" },
  { href: "/#solutions", label: "Solutions", id: "solutions" },
  { href: "/#industries", label: "Industries", id: "industries" },
  { href: "/pricing", label: "Pricing", id: "pricing" },
  { href: "/#about", label: "About Us", id: "about" },
  { href: "/#contact", label: "Contact", id: "contact" },
] as const;

type SiteHeaderProps = {
  active?: (typeof links)[number]["id"];
};

export function SiteHeader({ active }: SiteHeaderProps) {
  return (
    <header className="sticky top-0 z-30 border-b border-border bg-surface/90 backdrop-blur">
      <div className="relative mx-auto flex h-16 max-w-6xl items-center px-4 sm:px-6">
        <Link href="/" aria-label="BizPilot home" className="relative z-10 shrink-0">
          <Logo height={36} priority />
        </Link>
        <nav className="absolute inset-x-0 hidden justify-center gap-6 text-sm md:flex">
          {links.map((link) => (
            <Link
              key={link.id}
              href={link.href}
              className={cn(
                "py-1 text-secondary hover:text-ink",
                active === link.id && "font-semibold text-brand-deep",
                active === link.id && link.id === "home" && "border-b-2 border-brand",
              )}
            >
              {link.label}
            </Link>
          ))}
        </nav>
        <div className="relative z-10 ml-auto flex items-center gap-2">
          <Button href="/sign-in" variant="ghost" size="sm">
            Login
          </Button>
          <Button href="/sign-up" size="sm">
            See Demo
          </Button>
        </div>
      </div>
    </header>
  );
}
