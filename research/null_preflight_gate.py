"""Null-preflight gate (Gate 2.3) — research-only, Level A.

Makes the matched-null control a mandatory preflight instead of an optional
check. A candidate result is only a "finding" if it separates from its null
distribution; otherwise it is a "discovery signal" (keşif sinyali).

This module does NOT run the nulls itself (that is `negative_control.py`'s
job); it evaluates a candidate result against a precomputed null distribution
and returns a gate verdict.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NullGateVerdict:
    status: str  # "finding" | "discovery_signal" | "insufficient_data"
    candidate_value: float | None
    null_n: int
    candidate_percentile: float | None
    reason: str


def null_preflight_gate(
    candidate_value: float | None,
    null_distribution: list[float],
    *,
    min_null_n: int = 100,
    percentile_lo: float = 0.025,
    percentile_hi: float = 0.975,
) -> NullGateVerdict:
    """Evaluate a candidate against its null distribution.

    A candidate is a "finding" only if it falls outside the null's central
    interval [lo, hi]. Inside the interval (or with too few nulls) it is a
    discovery signal — not a finding.
    """
    if candidate_value is None:
        return NullGateVerdict(
            "insufficient_data", None, len(null_distribution), None, "candidate value is None"
        )
    if len(null_distribution) < min_null_n:
        return NullGateVerdict(
            "insufficient_data",
            candidate_value,
            len(null_distribution),
            None,
            f"null distribution too small (n={len(null_distribution)} < {min_null_n})",
        )
    ordered = sorted(null_distribution)
    lo = ordered[int(len(ordered) * percentile_lo)]
    hi = ordered[min(len(ordered) - 1, int(len(ordered) * percentile_hi))]
    percentile = sum(v <= candidate_value for v in ordered) / len(ordered)
    if candidate_value < lo or candidate_value > hi:
        return NullGateVerdict(
            "finding",
            candidate_value,
            len(ordered),
            round(percentile, 4),
            f"candidate outside null [{lo:.4f}, {hi:.4f}]",
        )
    return NullGateVerdict(
        "discovery_signal",
        candidate_value,
        len(ordered),
        round(percentile, 4),
        f"candidate inside null [{lo:.4f}, {hi:.4f}] — not a finding",
    )
