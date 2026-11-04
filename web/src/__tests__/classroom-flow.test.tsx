import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import ClassroomCasePage from "@/app/classroom/case/[id]/page";
import ClassroomPage from "@/app/classroom/page";
import {
  getCase,
  getOutcome,
  listCases,
  predictCase,
  type FinSenseCase,
  type FinSenseOutcome,
  type FinSensePrediction,
} from "@/lib/finsenseApi";

vi.mock("next/link", () => ({
  default: ({ children, ...props }: React.ComponentProps<"a">) =>
    React.createElement("a", props, children),
}));

vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "case-001" }),
}));

vi.mock("@/lib/finsenseApi", () => ({
  getCase: vi.fn(),
  getOutcome: vi.fn(),
  listCases: vi.fn(),
  predictCase: vi.fn(),
}));

const caseData: FinSenseCase = {
  id: "case-001",
  asset: "AAPL",
  event_timestamp: "2026-09-01T00:00:00Z",
  snapshot: { price_at_event: 100 },
  context: "Synthetic case context for the Classroom UI test.",
  horizon_days: 21,
  my_prediction: null,
};

const prediction: FinSensePrediction = {
  id: "prediction-001",
  case_id: caseData.id,
  direction: "UP",
  probability: 0.7,
  reason: "Price structure and volume suggest continued upward pressure.",
  committed_at: "2026-09-22T12:00:00Z",
};

const outcome: FinSenseOutcome = {
  case_id: caseData.id,
  actual_direction: "UP",
  actual_return_pct: 1.9,
  resolved_at: "2026-09-22T00:00:00Z",
  your_prediction: prediction,
  evaluation: {
    direction_correct: true,
    binary_outcome: 1,
    probability_error: -0.3,
  },
};

afterEach(() => cleanup());

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(listCases).mockResolvedValue([caseData]);
  vi.mocked(getCase).mockResolvedValue(caseData);
  vi.mocked(predictCase).mockResolvedValue(prediction);
  vi.mocked(getOutcome).mockResolvedValue(outcome);
});

describe("FinSense Classroom flow", () => {
  it("lists a case, commits a reasoned prediction, and reveals its outcome", async () => {
    render(<ClassroomPage />);

    const startLink = await screen.findByText("Start Thinking →");
    expect(startLink.closest("a")?.getAttribute("href")).toBe(
      "/classroom/case/case-001",
    );
    expect(vi.mocked(listCases)).toHaveBeenCalledOnce();

    cleanup();
    render(<ClassroomCasePage />);
    expect(await screen.findByText("What was happening?")).toBeTruthy();
    expect(vi.mocked(getCase)).toHaveBeenCalledWith(caseData.id);

    fireEvent.click(screen.getByRole("button", { name: /Start thinking/ }));
    fireEvent.click(screen.getByRole("button", { name: "UP" }));
    fireEvent.click(screen.getByRole("button", { name: "Continue →" }));

    expect(await screen.findByText("How confident are you?")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "70%" }));
    fireEvent.click(screen.getByRole("button", { name: "Continue →" }));

    expect(await screen.findByText("Why?")).toBeTruthy();
    const reason = "Price structure and volume suggest continued upward pressure.";
    fireEvent.change(screen.getByRole("textbox"), { target: { value: reason } });
    fireEvent.click(screen.getByRole("button", { name: "Continue →" }));

    expect(await screen.findByText("Your prediction")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Commit Prediction" }));

    await waitFor(() => {
      expect(vi.mocked(predictCase)).toHaveBeenCalledWith(caseData.id, {
        direction: "UP",
        probability: 0.7,
        reason,
      });
      expect(vi.mocked(getOutcome)).toHaveBeenCalledWith(caseData.id);
    });
    expect(await screen.findByText("Outcome revealed")).toBeTruthy();
    expect(screen.getByText("Actual direction: UP")).toBeTruthy();
    expect(screen.getByText("Correct")).toBeTruthy();
  });
});