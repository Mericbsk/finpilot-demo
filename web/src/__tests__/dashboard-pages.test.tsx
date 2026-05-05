/**
 * Frontend tests for critical dashboard pages.
 * Tests: render, key UI elements, data source indicators.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { act, render, screen } from "@testing-library/react";
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
  global.fetch = vi.fn((input: string | URL | Request) => {
    const url = typeof input === "string"
      ? input
      : input instanceof URL
        ? input.toString()
        : input.url;

    const jsonResponse = (body: unknown, init?: { ok?: boolean; status?: number }) =>
      Promise.resolve({
        ok: init?.ok ?? true,
        status: init?.status ?? 200,
        json: () => Promise.resolve(body),
      });

    if (url.includes("/stock_presets.json")) {
      return jsonResponse({
        sector_test: {
          name: "Test",
          icon: "T",
          category: "Sectors",
          symbols: ["AAPL", "MSFT", "NVDA"],
        },
      });
    }

    if (url.includes("/py-api/health")) {
      return jsonResponse({ status: "ok" });
    }

    if (url.includes("/py-api/user/settings")) {
      return jsonResponse({ user_id: "default", settings: {} });
    }

    if (url.includes("/py-api/models")) {
      return jsonResponse([]);
    }

    if (url.includes("/py-api/inference-cache")) {
      return jsonResponse({});
    }

    if (url.includes("/py-api/inference/run")) {
      return jsonResponse({
        results: {},
        model_id: null,
        count: 0,
        timestamp: "2026-04-16T00:00:00Z",
      });
    }

    if (url.includes("/py-api/optuna/agents")) {
      return jsonResponse([]);
    }

    if (url.includes("/py-api/optuna/results")) {
      return jsonResponse({
        best_trial: 0,
        best_value: 0,
        best_params: {},
        best_attrs: {},
        all_trials: [],
      });
    }

    if (url.includes("/py-api/optuna/run")) {
      return jsonResponse({ job_id: "job-1", status: "running", progress: 0 });
    }

    if (url.includes("/py-api/optuna/status/")) {
      return jsonResponse({ job_id: "job-1", status: "done", progress: 100 });
    }

    if (url.includes("/py-api/trade/account")) {
      return jsonResponse({ detail: "Unauthorized" }, { ok: false, status: 401 });
    }

    if (url.includes("/py-api/trade/positions") || url.includes("/py-api/trade/orders")) {
      return jsonResponse([], { ok: false, status: 401 });
    }

    return jsonResponse({});
  }) as typeof fetch;
});

async function renderPage(modulePath: string) {
  const imported = await import(modulePath);
  let rendered: ReturnType<typeof render> | undefined;

  await act(async () => {
    rendered = render(React.createElement(imported.default));
    await Promise.resolve();
  });

  return rendered!;
}

describe("Dashboard Overview", () => {
  it("renders without crashing", async () => {
    const { container } = await renderPage("@/app/dashboard/page");
    expect(container).toBeTruthy();
  });

  it("shows loading spinner initially", async () => {
    const { container } = await renderPage("@/app/dashboard/page");
    // Page starts with Loader2 spinner while loading presets
    expect(container.querySelector("svg")).toBeTruthy();
  });
});

describe("Scanner Page", () => {
  it("renders without crashing", async () => {
    const { container } = await renderPage("@/app/dashboard/scanner/page");
    expect(container).toBeTruthy();
  });

  it("shows loading state or heading", async () => {
    const { container } = await renderPage("@/app/dashboard/scanner/page");
    // Page may show loading spinner or heading depending on preset fetch timing
    expect(container.querySelector("svg") || container.textContent?.includes("Scanner")).toBeTruthy();
  });
});

describe("Watchlist Page", () => {
  it("renders without crashing", async () => {
    const { container } = await renderPage("@/app/dashboard/watchlist/page");
    expect(container).toBeTruthy();
  });

  it("shows default tickers", async () => {
    await renderPage("@/app/dashboard/watchlist/page");
    expect(screen.getByText("NVDA")).toBeTruthy();
    expect(screen.getByText("AAPL")).toBeTruthy();
  });
});

describe("Settings Page", () => {
  it("renders without crashing", async () => {
    const { container } = await renderPage("@/app/dashboard/settings/page");
    expect(container).toBeTruthy();
  });

  it("shows Settings heading", async () => {
    await renderPage("@/app/dashboard/settings/page");
    expect(screen.getByText("Settings")).toBeTruthy();
  });

  it("shows Save button", async () => {
    await renderPage("@/app/dashboard/settings/page");
    expect(screen.getByText("Save")).toBeTruthy();
  });
});

describe("AI Lab Page", () => {
  it("renders without crashing", async () => {
    const { container } = await renderPage("@/app/dashboard/ai-lab/page");
    expect(container).toBeTruthy();
  });

  it("shows AI Laboratory heading", async () => {
    await renderPage("@/app/dashboard/ai-lab/page");
    expect(screen.getByText("AI Laboratory")).toBeTruthy();
  });

  it("shows tab buttons", async () => {
    await renderPage("@/app/dashboard/ai-lab/page");
    expect(screen.getByText("DRL Models")).toBeTruthy();
    expect(screen.getByText("Optuna")).toBeTruthy();
  });
});
