import { describe, expect, it } from "vitest";

import {
  ACCOUNTING_ADDON_KW,
  FEATURE_ORDER,
  PAYROLL_PER_EMPLOYEE_KW,
  PLANS,
  STORE_TYPES,
  compareHeading,
  featureLabel,
  formatKw,
  planBlurb,
  planCardFeatures,
  visibleFeatures,
} from "./pricing";

describe("subscription prices", () => {
  it("makes Basic free and prices paid plans below the previous list", () => {
    const basic = PLANS.find((plan) => plan.id === "basic");
    const premium = PLANS.find((plan) => plan.id === "premium");
    const enterprise = PLANS.find((plan) => plan.id === "enterprise");
    expect(basic?.monthlyKw).toBe(0);
    expect(formatKw(0)).toBe("Free");
    expect(premium?.monthlyKw).toBe(320);
    expect(enterprise?.monthlyKw).toBe(490);
    expect(premium?.monthlyKw).toBeLessThan(380);
    expect(enterprise?.monthlyKw).toBeLessThan(580);
    expect(formatKw(320)).toBe("K320");
    expect(formatKw(490)).toBe("K490");
  });

  it("keeps the Entreprise spelling on the third plan", () => {
    expect(PLANS.find((plan) => plan.id === "enterprise")?.name).toBe("Entreprise");
  });

  it("keeps accounting and payroll add-on rates", () => {
    expect(ACCOUNTING_ADDON_KW).toBe(650);
    expect(PAYROLL_PER_EMPLOYEE_KW).toBe(75);
    expect(formatKw(320 + 650)).toBe("K970");
  });
});

describe("store-type feature visibility", () => {
  it("omits purchase and supplier rows for service providers", () => {
    const features = visibleFeatures("service");
    expect(features).not.toContain("purchases");
    expect(features).not.toContain("purchase_returns");
    expect(features).not.toContain("suppliers");
    expect(planCardFeatures("premium", "service")).not.toContain("purchases");
    expect(planCardFeatures("enterprise", "service")).not.toContain("suppliers");
    expect(planCardFeatures("premium", "service")).toContain("inventory");
  });

  it("keeps purchasing rows for retail, grocery, restaurant, pharmacy and manufacturer", () => {
    for (const store of ["retail", "grocery", "restaurant", "pharmacy", "manufacturer"] as const) {
      expect(visibleFeatures(store)).toContain("purchases");
      expect(visibleFeatures(store)).toContain("suppliers");
      expect(planCardFeatures("premium", store)).toContain("purchases");
      expect(planCardFeatures("basic", store)).not.toContain("purchases");
    }
  });

  it("uses store-specific inventory labels", () => {
    expect(featureLabel("retail", "inventory")).toBe("Products, stock levels and transfers");
    expect(featureLabel("grocery", "inventory")).toBe("Products, stock levels and transfers");
    expect(featureLabel("manufacturer", "inventory")).toBe("Products, stock levels and transfers");
    expect(featureLabel("service", "inventory")).toBe("Services, stock levels and transfers");
    expect(featureLabel("restaurant", "inventory")).toBe("Menu items, stock levels and transfers");
    expect(featureLabel("pharmacy", "inventory")).toBe(
      "Medications, stock levels and transfers",
    );
    expect(featureLabel("pharmacy", "warehouses")).toBe(
      "Storage centres, with stock moved between them",
    );
    expect(featureLabel("pharmacy", "sections")).toBe("Store sections, with sales for each section");
    expect(featureLabel("service", "sections")).toBe("Store sections, with sales for each section");
  });

  it("does not advertise manufacturing as an included row", () => {
    for (const store of STORE_TYPES) {
      for (const feature of visibleFeatures(store.id)) {
        expect(featureLabel(store.id, feature).toLowerCase()).not.toMatch(/manufactur/);
      }
    }
    expect(planBlurb("enterprise", "manufacturer")).toMatch(/except Manufacturing/);
  });

  it("drops purchasing from the service Premium blurb", () => {
    expect(planBlurb("premium", "retail")).toMatch(/purchasing, suppliers/);
    expect(planBlurb("premium", "service")).not.toMatch(/purchas|supplier/i);
    expect(planBlurb("premium", "service")).toMatch(/services/i);
    expect(planBlurb("premium", "pharmacy")).toMatch(/medications/i);
  });

  it("builds a lowercase compare heading per industry", () => {
    expect(compareHeading("pharmacy")).toBe("What a pharmacy gets on each plan");
    expect(compareHeading("retail")).toBe("What a retail store gets on each plan");
    expect(compareHeading("service")).toBe("What a service provider gets on each plan");
    expect(compareHeading("restaurant")).toBe("What a restaurant gets on each plan");
    expect(compareHeading("grocery")).toBe("What a grocery store gets on each plan");
    expect(compareHeading("manufacturer")).toBe("What a manufacturer gets on each plan");
  });

  it("lists pharmacy rows in screenshot order", () => {
    expect(visibleFeatures("pharmacy").map((feature) => featureLabel("pharmacy", feature))).toEqual([
      "Sales and receipts",
      "Sales returns and credit notes",
      "Purchases from suppliers",
      "Purchase returns",
      "Supplier directory",
      "Customers and what they owe",
      "Medications, stock levels and transfers",
      "Storage centres, with stock moved between them",
      "Store sections, with sales for each section",
      "Expense tracking",
      "Business reports and analytics",
      "Profit, taxation, stock movement and storage centre reports",
      "Store assistants and permissions",
      "Cashier shifts, with opening and closing cash",
      "AI business assistant",
      "ZRA Smart Invoice",
      "External integrations (Odoo, Manager.io, more coming)",
    ]);
    expect(PLANS.find((plan) => plan.id === "enterprise")?.features).toEqual(FEATURE_ORDER);
  });
});
