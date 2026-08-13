"""Validate the generated ten-product educational content series."""

from __future__ import annotations

import re
from pathlib import Path

CONTENT_DIR = Path("reports/content_series")
EXPECTED_FILES = 10
PAGE_PATTERN = re.compile(r"^## Page (\d+) — (.+)$", re.MULTILINE)
FORBIDDEN_PATTERNS = (
    r"garantili\s+getiri",
    r"getiri\s+garantisi",
    r"kesin\s+kazan",
    r"hedef\s+fiyat",
    r"buy\s+now",
    r"sell\s+now",
)
REQUIRED_MARKERS = (
    "Status: Original educational manuscript",
    "This content is educational material and is not investment advice.",
    "## Sources and rights",
    "## Pre-publication checklist",
)


def validate_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    pages = PAGE_PATTERN.findall(text)
    numbers = [int(number) for number, _ in pages]
    topics = [topic.strip() for _, topic in pages]

    if numbers != list(range(1, 41)):
        errors.append(f"{path.name}: page sequence is not 1..40")
    if len(pages) != 40:
        errors.append(f"{path.name}: expected 40 pages, found {len(pages)}")
    if len(set(topics)) != len(topics):
        errors.append(f"{path.name}: duplicate page topic")
    for marker in REQUIRED_MARKERS:
        if marker not in text:
            errors.append(f"{path.name}: missing marker: {marker}")
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            errors.append(f"{path.name}: forbidden commercial language: {pattern}")
    return errors


def main() -> int:
    paths = sorted(
        path
        for path in CONTENT_DIR.glob("*.md")
        if path.name != "source_rights_register_2026-08-10.md"
    )
    errors: list[str] = []
    if len(paths) != EXPECTED_FILES:
        errors.append(f"expected {EXPECTED_FILES} manuscripts, found {len(paths)}")
    for path in paths:
        errors.extend(validate_file(path))

    if errors:
        print("CONTENT_SERIES_FAIL")
        print("\n".join(f"- {error}" for error in errors))
        return 1

    print(f"CONTENT_SERIES_OK: {len(paths)} manuscripts x 40 pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
