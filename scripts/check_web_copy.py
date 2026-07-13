"""Lightweight banned-word scan for the web Ledger landing/demo copy.

There's no existing scanner for TSX copy (`distribution/lint.py` only
checks Telegram brief text). This is a minimal stand-in: greps the ledger
landing/demo source files for guarantee/certainty/FOMO language patterns
that would violate FinPilot's "probability, not advice" editorial stance.

Usage: python scripts/check_web_copy.py
Exit code 1 if any match is found (usable in CI later).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

TARGET_FILES = [
    "web/src/app/page.tsx",
    "web/src/app/demo/page.tsx",
    *sorted(Path("web/src/components/ledger").glob("*.tsx")),
    "web/src/components/Waitlist.tsx",
    "web/src/components/Navbar.tsx",
    "web/src/components/Footer.tsx",
]

# Case-insensitive; word-boundary regex fragments.
BANNED_PATTERNS = [
    r"\bguarantee[sd]?\b",
    r"\brisk[- ]free\b",
    r"\bcan'?t lose\b",
    r"\bsure thing\b",
    r"\b100% (win|accurate|certain)\b",
    r"\bget rich\b",
    r"\bact now\b",
    r"\blimited time\b",
    r"\bonly \d+ spots?\b",
    r"\bbuy now\b",
    r"\bsell now\b",
    r"\bnever loses?\b",
    r"\bfinancial advice\b",
]

# Disclaimer sentences ("does not guarantee", "not financial advice", "not a
# guarantee") are the compliant, EXPECTED use of these words — skip a line if
# it contains an explicit negation anywhere.
_NEGATION = re.compile(r"\bnot\b|\bn't\b|\bno\b", re.IGNORECASE)

_COMPILED = [re.compile(p, re.IGNORECASE) for p in BANNED_PATTERNS]


def scan_file(path: Path) -> list[str]:
    hits = []
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return hits
    for i, line in enumerate(text.splitlines(), start=1):
        if _NEGATION.search(line):
            continue
        for pat in _COMPILED:
            if pat.search(line):
                hits.append(f"{path}:{i}: {line.strip()[:120]}")
    return hits


def main() -> int:
    all_hits: list[str] = []
    for f in TARGET_FILES:
        p = Path(f)
        all_hits.extend(scan_file(p))

    if all_hits:
        print(f"Found {len(all_hits)} banned-phrase match(es):")
        for h in all_hits:
            print(f"  {h}")
        return 1

    print(f"Clean — scanned {len(TARGET_FILES)} files, no banned phrases found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
