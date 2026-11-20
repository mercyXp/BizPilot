import { describe, expect, it } from "vitest";

import { translate } from "./i18n";

describe("translate", () => {
  it("uses the catalogue then the built-in fallback", () => {
    expect(translate({ "reports.title": "Malipoti" }, "reports.title")).toBe("Malipoti");
    expect(translate({}, "reports.title")).toBe("Reports");
    expect(translate({}, "unknown.key")).toBe("unknown.key");
  });

  it("substitutes placeholders", () => {
    expect(translate({ hello: "Hello {name}" }, "hello", { name: "Mercy" })).toBe("Hello Mercy");
  });
});
