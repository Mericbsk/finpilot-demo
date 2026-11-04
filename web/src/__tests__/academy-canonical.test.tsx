import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import AcademyPage from "@/app/academy/page";
import {
  getAcademyCatalog,
  type AcademyLocale,
  type FinSenseAcademyCatalog,
} from "@/lib/finsenseAcademyApi";

vi.mock("next/link", () => ({
  default: ({ children, ...props }: React.ComponentProps<"a">) =>
    React.createElement("a", props, children),
}));

vi.mock("@/lib/finsenseAcademyApi", () => ({
  getAcademyCatalog: vi.fn(),
}));

function catalog(locale: AcademyLocale): FinSenseAcademyCatalog {
  const title = { tr: "Test bütçesi", en: "Test budget", de: "Testbudget" }[locale];
  const lesson = {
    concept_id: "budgeting",
    locale,
    version: 2,
    status: "independent_reviews",
    level: "beginner" as const,
    jurisdiction: ["GLOBAL"],
    title,
    learning_objectives: ["Identify planned income and spending."],
    body_md: "A budget is a plan for expected income and spending.",
    claims: [{
      id: "c1",
      text: "A budget organizes planned income and spending.",
      type: "conceptual" as const,
      source_ids: ["src-test-primary"],
    }],
    quiz: [{
      id: "q1",
      question: "What does a budget organize?",
      options: ["Planned income and spending", "The weather", "A person's age"],
      correct_index: 0,
      explanation: "It records planned income and spending.",
      claim_ids: ["c1"],
    }],
  };
  return {
    catalog_schema_version: "1.0.0",
    locale,
    manifest_sha256: "a".repeat(64),
    manifest: {
      release_id: "rel-2026-10-17-budgeting",
      manifest_schema_version: "2.0.0",
      content_schema_version: "1.0.0",
      policy_version: "autonomous-content-v1.0.0",
      release_gate: { decision: "PASS", publisher: "central-release-gate" },
    },
    lessons: [{
      lesson,
      manifest_entry: {
        concept_id: "budgeting",
        locale,
        version: 2,
        sha256: "b".repeat(64),
        content_hash: "c".repeat(64),
      },
      sources: [{
        id: "src-test-primary",
        title: "Test financial education reference",
        publisher: "Test institution",
        url: "https://example.edu/finance-basics",
        published: "2024",
        accessed: "2026-10-17",
        authority: "primary_official",
        jurisdiction: ["GLOBAL"],
      }],
    }],
  };
}

afterEach(() => cleanup());

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(getAcademyCatalog).mockImplementation(async (locale) => catalog(locale));
});

describe("FinSense canonical Academy catalog", () => {
  it("renders release-backed lesson fields and citations", async () => {
    render(<AcademyPage />);

    const lessonButton = await screen.findByRole("button", { name: /Test bütçesi/ });
    expect(vi.mocked(getAcademyCatalog)).toHaveBeenCalledWith("tr");
    expect(screen.getByText(/release rel-2026-10-17-budgeting/)).toBeTruthy();

    fireEvent.click(lessonButton);
    expect(screen.getByText("A budget is a plan for expected income and spending.")).toBeTruthy();
    expect(screen.getByText("Identify planned income and spending.")).toBeTruthy();
    expect(screen.getByRole("link", { name: /Test financial education reference/ }).getAttribute("href"))
      .toBe("https://example.edu/finance-basics");

    fireEvent.click(screen.getByText("What does a budget organize?"));
    expect(screen.getByText("Yanıtı ve açıklamayı göster")).toBeTruthy();
  });

  it("reloads the selected locale and filters by canonical level", async () => {
    render(<AcademyPage />);
    await screen.findByRole("button", { name: /Test bütçesi/ });

    fireEvent.change(screen.getByRole("combobox", { name: "Dil" }), {
      target: { value: "en" },
    });
    await screen.findByRole("button", { name: /Test budget/ });
    await waitFor(() => expect(vi.mocked(getAcademyCatalog)).toHaveBeenLastCalledWith("en"));

    fireEvent.change(screen.getByRole("combobox", { name: "Seviye" }), {
      target: { value: "advanced" },
    });
    expect(screen.getByText(/0 \/ 1 ders/)).toBeTruthy();
  });
});