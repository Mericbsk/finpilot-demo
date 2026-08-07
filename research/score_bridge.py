"""Research-only bridge between live score telemetry and research scores."""

from __future__ import annotations

from typing import Any

from scanner.score_engine import compute_recommendation_score, score_component_breakdown


def build_score_bridge(
    row: dict[str, Any],
    *,
    research_score: float | None = None,
    sentiment_score: float | None = None,
) -> dict[str, Any]:
    """Return comparable live/research scores and component accounting.

    ``research_score`` is intentionally supplied by the caller. The bridge
    must not silently substitute a different research formula for the live
    scorer, because that would conceal score-contract drift.
    """
    components = score_component_breakdown(row, sentiment_score=sentiment_score)
    live_score = compute_recommendation_score(row, sentiment_score=sentiment_score)
    filter_flags = sum(
        bool(row.get(name, False)) for name in ("volume_spike", "price_momentum", "trend_strength")
    )
    filter_score = float(row.get("filter_score", 0.0) or 0.0)
    return {
        "live_score": live_score,
        "research_score": research_score,
        "score_delta": round(live_score - research_score, 3)
        if research_score is not None
        else None,
        "live_components": components,
        "filter_score": filter_score,
        "filter_flag_count": filter_flags,
        "filter_accounting_delta": round(filter_score - filter_flags, 3),
        "research_score_status": "provided" if research_score is not None else "missing",
    }
