import type { Metadata } from "next";

import { SiteFooter } from "@/components/marketing/SiteFooter";
import { SiteHeader } from "@/components/marketing/SiteHeader";

export const metadata: Metadata = {
  title: "About Us · BizPilot",
  description: "BizPilot is a Zambia-first operations platform for shops that need honest books.",
};

export default function AboutPage() {
  return (
    <div className="flex min-h-screen flex-col bg-canvas">
      <SiteHeader active="about" />
      <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-16">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-brand">About Us</p>
        <h1 className="mt-3 text-4xl font-semibold tracking-tight text-ink">
          Built for shops that keep their own books.
        </h1>
        <p className="mt-4 text-base leading-relaxed text-secondary">
          BizPilot is a Zambia-first operations platform for sales, inventory, expenses, accounting
          and payroll. Teal is the brand. Colour elsewhere means status, risk or insight.
        </p>
        <p className="mt-4 text-base leading-relaxed text-secondary">
          We start with English and ZMW, then grow with the store: branches, warehouses, industry
          packs and the modules you actually run on the floor.
        </p>
      </main>
      <SiteFooter />
    </div>
  );
}
