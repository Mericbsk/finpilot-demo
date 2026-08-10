import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, it, expect } from "vitest";

/**
 * Compliance guard (YONERGE §12): forbidden promissory / fabricated language must
 * NEVER appear on the PUBLIC surface or in shared metadata. This test fails the
 * build if it reappears — so a live regression like the "buy/hold/sell signals"
 * meta description or a fake aggregateRating cannot silently ship again.
 *
 * Note: legitimate DISCLAIMERS ("not buy/sell advice", "never buy/sell
 * recommendations") are intentionally NOT matched — we forbid the promise, not
 * the disclaimer. Dashboard (auth-gated, frozen) is out of scope here.
 */
const ROOT = process.cwd();

const PUBLIC_FILES = [
  "src/app/layout.tsx",
  "src/app/page.tsx",
  "src/app/demo/page.tsx",
  "src/app/methodology/page.tsx",
  "src/app/premium/page.tsx",
  "src/app/academy/page.tsx",
  "src/components/ledger/HowItsMade.tsx",
  "src/components/ledger/EditorialStance.tsx",
  "src/components/ledger/Newsroom.tsx",
  "src/components/ledger/ClassroomPreview.tsx",
];

// Promissory / fabricated phrases that must never appear publicly.
const FORBIDDEN: { label: string; re: RegExp }[] = [
  { label: "buy/hold/sell signals (promise)", re: /buy\s*\/\s*hold\s*\/\s*sell\s+signals/i },
  { label: "clear buy/hold/sell (promise)", re: /clear\s+buy\s*\/\s*hold\s*\/\s*sell/i },
  { label: "stock picks", re: /stock\s+picks/i },
  { label: "price target", re: /price\s+target/i },
  { label: "hedef fiyat", re: /hedef\s+fiyat/i },
  { label: "fabricated rating (aggregateRating)", re: /aggregateRating/i },
  { label: "fabricated rating (ratingValue)", re: /ratingValue/i },
  { label: "fabricated rating (ratingCount)", re: /ratingCount/i },
  { label: "guaranteed return", re: /guaranteed\s+return/i },
];

function read(rel: string): string {
  try {
    return readFileSync(join(ROOT, rel), "utf-8");
  } catch {
    return "";
  }
}

describe("public compliance surface", () => {
  for (const rel of PUBLIC_FILES) {
    it(`${rel} contains no forbidden promissory/fabricated language`, () => {
      const src = read(rel);
      const hits = FORBIDDEN.filter((f) => f.re.test(src)).map((f) => f.label);
      expect(hits, `Forbidden language in ${rel}: ${hits.join(", ")}`).toEqual([]);
    });
  }

  it("all public ledger components are clean", () => {
    // Spot-check the ledger family that renders the landing body.
    const files = [
      "src/components/ledger/Masthead.tsx",
      "src/components/ledger/TheWire.tsx",
      "src/components/ledger/EditionArticle.tsx",
      "src/components/ledger/DailyDouble.tsx",
      "src/components/ledger/EditorialBoard.tsx",
      "src/components/ledger/FactCheckingDesk.tsx",
    ];
    for (const rel of files) {
      const src = read(rel);
      const hits = FORBIDDEN.filter((f) => f.re.test(src)).map((f) => f.label);
      expect(hits, `Forbidden language in ${rel}: ${hits.join(", ")}`).toEqual([]);
    }
  });

  it("does not publish an unsupported DRL model count in the masthead", () => {
    const src = read("src/components/ledger/Masthead.tsx");
    expect(/(?:\d+\s+DRL|DRL\s+models?\s*[:=]?\s*\d+)/i.test(src)).toBe(false);
  });

  it("describes DRL as three research models validated before use", () => {
    const src = read("src/app/methodology/page.tsx");
    expect(src).toMatch(/Three PPO research models/i);
    expect(src).toMatch(/momentum, trend and conservative/i);
    expect(src).toMatch(/validated before use/i);
  });

  it("keeps production Grade and research model claims separate", () => {
    const sources = [
      read("src/components/ledger/HowItsMade.tsx"),
      read("src/components/ledger/EditorialStance.tsx"),
      read("src/components/ledger/Newsroom.tsx"),
    ].join("\n");
    expect(sources).toMatch(/published scanner rules and eligibility checks/i);
    expect(sources).toMatch(/research artifacts/i);
    expect(sources).toMatch(/validated before (?:any )?future use/i);
    expect(sources).not.toMatch(/three (?:independent )?(?:computer )?models .*vote/i);
    expect(sources).not.toMatch(/specialised agents vote/i);
  });

  it("labels the static newsroom data as illustrative", () => {
    expect(read("src/components/ledger/Newsroom.tsx")).toMatch(/Illustrative process example/i);
  });

  it("uses the daily market reasoning positioning in shared metadata", () => {
    const src = read("src/app/layout.tsx");
    expect(src).toMatch(/FinPilot — Daily Market Reasoning/);
    expect(src).toMatch(/daily market research edition/i);
    expect(src).not.toMatch(/AI-Powered Stock Intelligence/i);
  });
});

describe("public research pages carry the required disclaimer", () => {
  // Positive guard: the "not investment advice" disclaimer must never be
  // accidentally removed from a public research page.
  const REQUIRED: Record<string, RegExp> = {
    "src/app/methodology/page.tsx": /not[^.]{0,40}investment\s+advice/i,
    "src/app/premium/page.tsx": /not[^.]{0,40}investment\s+advice/i,
    "src/app/demo/page.tsx": /not[^.]{0,40}investment\s+advice/i,
  };
  for (const [rel, re] of Object.entries(REQUIRED)) {
    it(`${rel} contains an investment-advice disclaimer`, () => {
      expect(re.test(read(rel)), `Missing disclaimer in ${rel}`).toBe(true);
    });
  }
});
