"""Authority-map guard (Level A — CORE-009 minimal, read-only, isolated).

Purpose: prevent the "dynamic authority map" model (AGENTS.md -> 00-core.md
-> docs/INDEX.md -> decision-log.md -> authority doc) from silently drifting
away from the real repository tree, the way the old numbered-folder
(`00-strategy/`, `01-product/`, ...) references drifted (see
docs/2026-07-29-otorite-haritasi-gocu-plani.md and the 2026-07-29
decision-log entry).

This script does NOT modify any file. It only reports. Wire it into
pre-commit / CI as a guard; a non-zero exit should block merge.

Checks:
  1. docs/INDEX.md contains a machine-readable ```json manifest block.
  2. Every manifest entry's `authority_path` (if set) exists on disk.
     - status == "active"  -> missing path is an ERROR.
     - status in {draft, gap, external} -> missing path is a WARNING only.
  3. Every manifest entry's `applies_to` glob patterns match at least one
     real path on disk (same active/non-active severity rule).
  4. Every `.github/instructions/*.instructions.md` file's `applyTo`
     frontmatter glob(s) match at least one real path on disk. This is
     always an ERROR if it matches nothing, regardless of manifest status,
     because these files are live tool-facing config, not documentation.

Usage:
    python scripts/lint_authority_map.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_MD = REPO_ROOT / "docs" / "INDEX.md"
INSTRUCTIONS_DIR = REPO_ROOT / ".github" / "instructions"

MANIFEST_HEADING = "## Makine-okunur otorite manifesti"
NON_BLOCKING_STATUS = {"draft", "gap", "external", "superseded"}


def _extract_manifest(text: str) -> dict:
    if MANIFEST_HEADING not in text:
        raise ValueError(f"{INDEX_MD}: manifest heading not found ('{MANIFEST_HEADING}')")
    after_heading = text.split(MANIFEST_HEADING, 1)[1]
    match = re.search(r"```json\s*\n(.*?)```", after_heading, re.DOTALL)
    if not match:
        raise ValueError(f"{INDEX_MD}: no fenced ```json manifest block found after heading")
    return json.loads(match.group(1))


def _glob_matches(pattern: str) -> bool:
    if not pattern:
        return False
    try:
        return any(REPO_ROOT.glob(pattern))
    except (re.error, ValueError, NotImplementedError):
        return False


def _extract_apply_to(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8")
    match = re.search(r'^applyTo:\s*"([^"]*)"', text, re.MULTILINE)
    return match.group(1) if match else None


def _check_manifest(errors: list[str], warnings: list[str]) -> None:
    if not INDEX_MD.exists():
        errors.append(f"{INDEX_MD} does not exist")
        return

    manifest = _extract_manifest(INDEX_MD.read_text(encoding="utf-8"))
    entries = manifest.get("entries", [])
    if not entries:
        errors.append("docs/INDEX.md manifest has no entries")
        return

    for entry in entries:
        entry_id = entry.get("id", "<no-id>")
        status = entry.get("status", "active")
        blocking = status not in NON_BLOCKING_STATUS
        authority_path = entry.get("authority_path")
        applies_to = entry.get("applies_to", [])

        if authority_path:
            if not (REPO_ROOT / authority_path).exists():
                msg = f"[{entry_id}] authority_path does not exist: {authority_path}"
                (errors if blocking else warnings).append(msg)
        elif blocking:
            errors.append(f"[{entry_id}] status={status!r} but authority_path is null")

        for pattern in applies_to:
            if not _glob_matches(pattern):
                msg = f"[{entry_id}] applies_to glob matches nothing on disk: {pattern}"
                (errors if blocking else warnings).append(msg)


def _check_instructions_dir(errors: list[str]) -> None:
    if not INSTRUCTIONS_DIR.exists():
        return
    for path in sorted(INSTRUCTIONS_DIR.glob("*.instructions.md")):
        apply_to = _extract_apply_to(path)
        if not apply_to:
            errors.append(f".github/instructions/{path.name}: no applyTo frontmatter found")
            continue
        patterns = [p.strip() for p in apply_to.split(",") if p.strip()]
        if not patterns:
            errors.append(f".github/instructions/{path.name}: applyTo is empty")
            continue
        if not any(_glob_matches(p) for p in patterns):
            errors.append(
                f".github/instructions/{path.name}: applyTo matches nothing on disk: {apply_to}"
            )


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    try:
        _check_manifest(errors, warnings)
    except ValueError as exc:
        errors.append(str(exc))

    _check_instructions_dir(errors)

    for w in warnings:
        print(f"WARN: {w}")
    for e in errors:
        print(f"ERROR: {e}")

    if errors:
        print(f"\nlint_authority_map: FAILED ({len(errors)} error(s), {len(warnings)} warning(s))")
        return 1

    print(f"lint_authority_map: OK (0 errors, {len(warnings)} warning(s) - known gaps)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
