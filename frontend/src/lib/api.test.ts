import { describe, expect, it } from "vitest";

import { apiBaseUrl } from "./api";

describe("api client", () => {
  it("defaults to local FastAPI origin", () => {
    expect(apiBaseUrl).toMatch(/^https?:\/\//);
  });
});
