import { describe, expect, it } from "vitest";

import { LOGO_SRC } from "./logo";

describe("brand logo", () => {
  it("points at the official compass lockup", () => {
    expect(LOGO_SRC).toBe("/logo/BizPilot_logo.png");
  });
});
