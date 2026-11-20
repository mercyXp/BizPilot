import type { Metadata } from "next";
import Link from "next/link";

import { SiteFooter } from "@/components/marketing/SiteFooter";
import { SiteHeader } from "@/components/marketing/SiteHeader";
import { Button } from "@/components/ui/button";

export const metadata: Metadata = {
  title: "Contact · BizPilot",
  description: "Talk to BizPilot about a demo, pricing or onboarding for your store in Zambia.",
};

export default function ContactPage() {
  return (
    <div className="flex min-h-screen flex-col bg-canvas">
      <SiteHeader active="contact" />
      <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-16">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-brand">Contact</p>
        <h1 className="mt-3 text-4xl font-semibold tracking-tight text-ink">See BizPilot in your store.</h1>
        <p className="mt-4 text-base leading-relaxed text-secondary">
          Create an account to walk the till yourself, or write to us about Premium, Entreprise,
          Accounting and Payroll for Zambia.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Button href="/sign-up" size="lg">
            Create account
          </Button>
          <Button href="/pricing" size="lg" variant="outline">
            View pricing
          </Button>
        </div>
        <p className="mt-8 text-sm text-muted">
          Already have access?{" "}
          <Link href="/sign-in" className="font-medium text-brand hover:text-brand-deep">
            Login
          </Link>
        </p>
      </main>
      <SiteFooter />
    </div>
  );
}
