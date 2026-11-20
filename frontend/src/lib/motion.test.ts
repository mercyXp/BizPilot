import { describe, expect, it } from "vitest";

import { fadeUp, motionDuration, motionEase, reducedFade, withReducedMotion } from "./motion";

describe("motion tokens", () => {
  it("exposes the official duration scale", () => {
    expect(motionDuration.fast).toBe(150);
    expect(motionDuration.standard).toBe(200);
    expect(motionDuration.card).toBe(250);
    expect(motionDuration.dropdown).toBe(200);
    expect(motionDuration.sidebar).toBe(280);
    expect(motionDuration.modal).toBe(220);
    expect(motionDuration.section).toBe(550);
    expect(motionDuration.hero).toBe(700);
    expect(motionDuration.chart).toBe(800);
    expect(motionEase).toEqual([0.22, 1, 0.36, 1]);
  });

  it("collapses variants when reduced motion is requested", () => {
    expect(withReducedMotion(true, fadeUp())).toEqual(reducedFade);
    expect(withReducedMotion(false, fadeUp())).not.toEqual(reducedFade);
  });
});
