import type { Metadata } from "next";

import { SiteFooter } from "@/components/marketing/SiteFooter";
import { SiteHeader } from "@/components/marketing/SiteHeader";

import { PricingContent } from "./pricing-content";

export const metadata: Metadata = {
  title: "Pricing · BizPilot",
  description: "POS, accounting and payroll plans for businesses in Zambia, billed in ZMW.",
};

export default function PricingPage() {
  return (
    <div className="flex min-h-screen flex-col bg-canvas">
      <SiteHeader active="pricing" />
      <main className="flex-1">
        <PricingContent />
      </main>
      <SiteFooter />
    </div>
  );
}
