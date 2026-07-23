"""Shared completeness checks for scan-to-distribution handoff."""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from typing import Any


def expected_universe() -> int:
    return int(os.getenv("FINPILOT_FULL_UNIVERSE_SIZE", "1812"))


def minimum_results() -> int:
    ratio = float(os.getenv("FINPILOT_MIN_FULL_SCAN_RATIO", "0.9"))
    return max(1, int(expected_universe() * ratio))


def result_symbols(results: Mapping[str, Any] | Sequence[Mapping[str, Any]]) -> set[str]:
    rows = results.keys() if isinstance(results, Mapping) else results
    symbols: set[str] = set()
    for row in rows:
        if isinstance(results, Mapping):
            symbol = row
        elif isinstance(row, Mapping):
            symbol = row.get("symbol") or row.get("ticker")
        else:
            symbol = None
        if symbol:
            symbols.add(str(symbol).strip().upper())
    return symbols


def full_scan_problems(
    results: Mapping[str, Any] | Sequence[Mapping[str, Any]],
    universe: int | None,
    scan_complete: bool | None = None,
) -> list[str]:
    """Return blocking reasons for publishing a scan as the full universe."""
    if scan_complete is False:
        return ["scan_complete=false"]

    declared_universe = int(universe or 0)
    unique_results = len(result_symbols(results))
    problems: list[str] = []
    if declared_universe < expected_universe():
        problems.append(f"universe={declared_universe} < expected={expected_universe()}")
    if unique_results < minimum_results():
        problems.append(f"unique_results={unique_results} < minimum={minimum_results()}")
    return problems


def is_full_scan(
    results: Mapping[str, Any] | Sequence[Mapping[str, Any]],
    universe: int | None,
    scan_complete: bool | None = None,
) -> bool:
    return not full_scan_problems(results, universe, scan_complete)
