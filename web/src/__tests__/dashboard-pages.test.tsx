/**
 * Frontend tests for critical dashboard pages.
 * Tests: render, key UI elements, data source indicators.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";

// Mock next/link
vi.mock("next/link", () => ({
  default: ({ children, ...props }: any) =>
    React.createElement("a", props, children),
}));

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), back: vi.fn() }),
  usePathname: () => "/dashboard",
}));

// Mock useStockPrices hook
vi.mock("@/lib/useStockPrices", () => ({
  useStockPrices: () => ({ data: {}, loading: false }),
}));

// Mock fetch for stock_presets.json
beforeEach(() => {
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: () =>
      Promise.resolve({
        presets: [{ name: "Test", symbols: ["AAPL", "MSFT", "NVDA"] }],
      }),
  });
});

describe("Dashboard Overview", () => {
  it("renders without crashing", async () => {
    const { default: Page } = await import(
      "@/app/dashboard/page"
    );
    const { container } = render(React.createElement(Page));
    expect(container).toBeTruthy();
  });

  it("shows loading spinner initially", async () => {
    const { default: Page } = await import(
      "@/app/dashboard/page"
    );
    const { container } = render(React.createElement(Page));
    // Page starts with Loader2 spinner while loading presets
    expect(container.querySelector("svg")).toBeTruthy();
  });
});

describe("Scanner Page", () => {
  it("renders without crashing", async () => {
    const { default: Page } = await import(
      "@/app/dashboard/scanner/page"
    );
    const { container } = render(React.createElement(Page));
    expect(container).toBeTruthy();
  });

  it("shows loading state or heading", async () => {
    const { default: Page } = await import(
      "@/app/dashboard/scanner/page"
    );
    const { container } = render(React.createElement(Page));
    // Page may show loading spinner or heading depending on preset fetch timing
    expect(container.querySelector("svg") || container.textContent?.includes("Scanner")).toBeTruthy();
  });
});

describe("Watchlist Page", () => {
  it("renders without crashing", async () => {
    const { default: Page } = await import(
      "@/app/dashboard/watchlist/page"
    );
    const { container } = render(React.createElement(Page));
    expect(container).toBeTruthy();
  });

  it("shows default tickers", async () => {
    const { default: Page } = await import(
      "@/app/dashboard/watchlist/page"
    );
    render(React.createElement(Page));
    expect(screen.getByText("NVDA")).toBeTruthy();
    expect(screen.getByText("AAPL")).toBeTruthy();
  });
});

describe("Settings Page", () => {
  it("renders without crashing", async () => {
    const { default: Page } = await import(
      "@/app/dashboard/settings/page"
    );
    const { container } = render(React.createElement(Page));
    expect(container).toBeTruthy();
  });

  it("shows Settings heading", async () => {
    const { default: Page } = await import(
      "@/app/dashboard/settings/page"
    );
    render(React.createElement(Page));
    expect(screen.getByText("Settings")).toBeTruthy();
  });

  it("shows Save button", async () => {
    const { default: Page } = await import(
      "@/app/dashboard/settings/page"
    );
    render(React.createElement(Page));
    expect(screen.getByText("Save")).toBeTruthy();
  });
});

describe("AI Lab Page", () => {
  it("renders without crashing", async () => {
    const { default: Page } = await import(
      "@/app/dashboard/ai-lab/page"
    );
    const { container } = render(React.createElement(Page));
    expect(container).toBeTruthy();
  });

  it("shows AI Laboratory heading", async () => {
    const { default: Page } = await import(
      "@/app/dashboard/ai-lab/page"
    );
    render(React.createElement(Page));
    expect(screen.getByText("AI Laboratory")).toBeTruthy();
  });

  it("shows tab buttons", async () => {
    const { default: Page } = await import(
      "@/app/dashboard/ai-lab/page"
    );
    render(React.createElement(Page));
    expect(screen.getByText("DRL Models")).toBeTruthy();
    expect(screen.getByText("Optuna")).toBeTruthy();
  });
});
