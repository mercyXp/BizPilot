import { describe, expect, it } from "vitest";

import { canSeeNavItem, isNavActive, navGroups, settingsItem } from "./nav";

describe("store navigation", () => {
  it("groups modules in the screenshot information architecture", () => {
    const labels = navGroups.map((group) => group.label);
    expect(labels).toEqual([
      "Store Dashboard",
      "Sales",
      "Purchases",
      "Inventory",
      "Expenses",
      "Store Assistants",
      "Store Reports",
      "BizPilot AI",
      "Compliance",
    ]);
    expect(settingsItem.href).toBe("/app/settings");
  });

  it("treats /app as an exact home match", () => {
    expect(isNavActive("/app", "/app")).toBe(true);
    expect(isNavActive("/app/sales", "/app")).toBe(false);
    expect(isNavActive("/app/sales/returns", "/app/sales")).toBe(true);
  });

  it("hides accounting from a salesperson permission set", () => {
    const accounting = navGroups
      .flatMap((group) => group.items)
      .find((item) => item.href === "/app/accounting");
    expect(accounting).toBeDefined();
    expect(canSeeNavItem(accounting!, ["sales.view", "sales.create", "pos.session.open"])).toBe(false);
    expect(canSeeNavItem(accounting!, ["accounting.reports.view"])).toBe(true);
  });
});
