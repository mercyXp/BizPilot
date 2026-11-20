import type { Metadata } from "next";

import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";

import { PricingContent } from "./pricing-content";

export const metadata: Metadata = {
  title: "Pricing · BizPilot",
  description: "POS, accounting and payroll plans for businesses in Zambia, billed in ZMW.",
};

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-[#f4f7fb]">
      <SiteHeader active="pricing" />
      <main>
        <PricingContent />
      </main>
      <SiteFooter />
    </div>
  );
}
