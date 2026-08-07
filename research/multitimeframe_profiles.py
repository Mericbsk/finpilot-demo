"""Research-only multi-timeframe profile classification.

These labels are descriptive experiment cohorts. They do not change
``entry_ok``, ranking, risk, or execution behavior.
"""

from __future__ import annotations


def classify_multitimeframe_profile(
    *, alignment_ratio: float, momentum_ratio: float, momentum_confluence: bool
) -> str:
    """Classify a row into confirmatory, early, or insufficient-data cohorts."""
    alignment = max(0.0, min(1.0, float(alignment_ratio)))
    momentum = max(0.0, min(1.0, float(momentum_ratio)))

    if momentum < 0.5 or not momentum_confluence:
        return "insufficient_data"
    if alignment >= 1.0:
        return "confirmatory"
    return "early"
