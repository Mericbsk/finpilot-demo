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
      "src/components/ledger/TheWire.tsx",
      "src/components/ledger/EditionArticle.tsx",
      "src/components/ledger/DailyDouble.tsx",
    ];
    for (const rel of files) {
      const src = read(rel);
      const hits = FORBIDDEN.filter((f) => f.re.test(src)).map((f) => f.label);
      expect(hits, `Forbidden language in ${rel}: ${hits.join(", ")}`).toEqual([]);
    }
  });
});
