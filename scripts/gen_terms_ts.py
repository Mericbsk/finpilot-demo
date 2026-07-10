"""E4 — distribution/glossary.py -> web/src/lib/terms.ts üretici.

Kullanım:  python scripts/gen_terms_ts.py [--check]
  --check: dosyayı yazmaz, mevcut terms.ts senkron mu diye bakar (CI için).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from distribution.glossary import GLOSSARY

OUT = Path("web/src/lib/terms.ts")

HEADER = """/**
 * AUTO-GENERATED from distribution/glossary.py — DO NOT EDIT BY HAND.
 * Regenerate with:  python scripts/gen_terms_ts.py
 * Single source of truth for glossary content (E4).
 */

export interface Term {
  slug: string;
  name: string;
  short: string; // plain language, ≤60 words
}

export const TERMS: Record<string, Term> = {
"""

FOOTER = """};

export function termForBadge(badge: string): Term | undefined {
  return TERMS[badge];
}
"""


def _esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def render() -> str:
    body = []
    for e in GLOSSARY:
        body.append(
            f'  "{e["key"]}": {{\n'
            f'    slug: "{_esc(e["slug"])}",\n'
            f'    name: "{_esc(e["name_en"])}",\n'
            f'    short:\n      "{_esc(e["card_en"])}",\n'
            f"  }},"
        )
    return HEADER + "\n".join(body) + "\n" + FOOTER


def main() -> int:
    content = render()
    if "--check" in sys.argv:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != content:
            print("OUT OF SYNC: terms.ts != glossary.py — run: python scripts/gen_terms_ts.py")
            return 1
        print("terms.ts in sync with glossary.py")
        return 0
    OUT.write_text(content, encoding="utf-8")
    print(f"wrote {OUT} ({len(GLOSSARY)} terms)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
