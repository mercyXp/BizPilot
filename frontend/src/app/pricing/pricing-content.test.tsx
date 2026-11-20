// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { STORE_TYPES, compareHeading, featureLabel, visibleFeatures } from "@/lib/pricing";

import { PricingContent } from "./pricing-content";

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

afterEach(() => {
  cleanup();
});

describe("PricingContent", () => {
  it("shows free Basic, K320 Premium, K490 Entreprise and retail inventory copy", () => {
    render(<PricingContent />);
    expect(screen.getAllByText("Free").length).toBeGreaterThan(0);
    expect(screen.getAllByText("K320").length).toBeGreaterThan(0);
    expect(screen.getAllByText("K490").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Entreprise").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Products, stock levels and transfers").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Purchases from suppliers").length).toBeGreaterThan(0);
    expect(
      screen.getByRole("heading", { name: "What a retail store gets on each plan" }),
    ).toBeTruthy();
    expect(screen.getByText("Compare")).toBeTruthy();
    expect(screen.getAllByRole("link", { name: "Get Basic" }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("link", { name: "Get Premium" }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("link", { name: "Get Entreprise" }).length).toBeGreaterThan(0);
  });

  it("hides purchasing rows for Service Provider and lists services instead of products", () => {
    render(<PricingContent />);
    fireEvent.click(screen.getByRole("tab", { name: "Service Provider" }));
    expect(screen.queryByText("Purchases from suppliers")).toBeNull();
    expect(screen.queryByText("Purchase returns")).toBeNull();
    expect(screen.queryByText("Supplier directory")).toBeNull();
    expect(screen.queryByText("Products, stock levels and transfers")).toBeNull();
    expect(screen.getAllByText("Services, stock levels and transfers").length).toBeGreaterThan(0);
    expect(
      screen.getByRole("heading", { name: "What a service provider gets on each plan" }),
    ).toBeTruthy();
  });

  it("matches the pharmacy screenshot rows and heading", () => {
    render(<PricingContent />);
    fireEvent.click(screen.getByRole("tab", { name: "Pharmacy" }));
    expect(
      screen.getByRole("heading", { name: "What a pharmacy gets on each plan" }),
    ).toBeTruthy();
    expect(screen.getAllByText("Medications, stock levels and transfers").length).toBeGreaterThan(0);
    expect(screen.queryByText("Medicines, batches, stock levels and transfers")).toBeNull();

    const table = screen.getByRole("table");
    const labels = within(table)
      .getAllByRole("row")
      .slice(1, -1)
      .map((row) => within(row).getByRole("rowheader").textContent);

    expect(labels).toEqual(
      visibleFeatures("pharmacy").map((feature) => featureLabel("pharmacy", feature)),
    );
    expect(within(table).queryByText("Not included")).toBeNull();
  });

  it("updates the compare heading and inventory label for every store type", () => {
    render(<PricingContent />);
    for (const type of STORE_TYPES) {
      fireEvent.click(screen.getByRole("tab", { name: type.label }));
      expect(screen.getByRole("heading", { name: compareHeading(type.id) })).toBeTruthy();
      expect(
        screen.getAllByText(featureLabel(type.id, "inventory")).length,
      ).toBeGreaterThan(0);
    }
  });
});
