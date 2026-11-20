// @vitest-environment jsdom
import { cleanup, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SiteHeader } from "./SiteHeader";
import { LOGO_SRC } from "@/components/ui/logo";

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

afterEach(() => {
  cleanup();
});

describe("marketing header", () => {
  it("uses the official PNG lockup and See Demo, not Book a Demo", () => {
    render(<SiteHeader active="home" />);
    const logo = screen.getByAltText("BizPilot");
    expect(logo.getAttribute("src")).toBe(LOGO_SRC);
    expect(LOGO_SRC).toBe("/logo/BizPilot_logo.png");
    expect(screen.getAllByText("See Demo").length).toBeGreaterThan(0);
    expect(screen.queryByText("Book a Demo")).toBeNull();
    expect(screen.getByText("Home")).toBeTruthy();
    expect(screen.getByText("Solutions")).toBeTruthy();
    expect(screen.getByText("Industries")).toBeTruthy();
    expect(screen.getByText("Pricing")).toBeTruthy();
    expect(screen.getByText("About Us")).toBeTruthy();
    expect(screen.getByText("Contact")).toBeTruthy();
    expect(screen.getAllByText("Login").length).toBeGreaterThan(0);
  });
});
