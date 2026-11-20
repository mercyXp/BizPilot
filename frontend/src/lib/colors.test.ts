import { describe, expect, it } from "vitest";

import { brandColors, chartColors, chartLegend, semanticColors, statusTone } from "./colors";
import { getStatusVisual } from "./status";

describe("design tokens", () => {
  it("keeps the locked brand identity", () => {
    expect(brandColors.primary).toBe("#0D9488");
    expect(brandColors.deep).toBe("#0F766E");
    expect(brandColors.soft).toBe("#CCFBF1");
    expect(brandColors.text).toBe("#000000");
    expect(brandColors.background).toBe("#F8FAFC");
    expect(brandColors.surface).toBe("#FFFFFF");
    expect(brandColors.border).toBe("#E5E7EB");
    expect(brandColors.textSecondary).toBe("#525252");
  });

  it("assigns a unique colour to each chart metric", () => {
    const values = Object.values(chartColors);
    expect(new Set(values).size).toBe(values.length);
    expect(chartColors.revenue).toBe(brandColors.primary);
    expect(Object.keys(chartLegend).sort()).toEqual(Object.keys(chartColors).sort());
  });

  it("maps business statuses to stable semantic tones", () => {
    expect(statusTone.paid).toBe("success");
    expect(statusTone.pending).toBe("warning");
    expect(statusTone.failed).toBe("danger");
    expect(statusTone.processing).toBe("information");
    expect(statusTone.ai_generated).toBe("ai");
    expect(getStatusVisual("paid").label).toBe("Paid");
    expect(getStatusVisual("ai_generated").className).toContain("text-ai");
  });

  it("provides tinted backgrounds for semantic colours", () => {
    expect(semanticColors.success.bg).toBe("#DCFCE7");
    expect(semanticColors.danger.bg).toBe("#FEE2E2");
    expect(semanticColors.warning.bg).toBe("#FEF3C7");
    expect(semanticColors.information.bg).toBe("#DBEAFE");
    expect(semanticColors.ai.bg).toBe("#EDE9FE");
    expect(semanticColors.customer.bg).toBe("#FCE7F3");
  });
});
