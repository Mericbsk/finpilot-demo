"""Explicit data-quality and execution policy for scanner selection."""

from __future__ import annotations

import os
from typing import Any

MAX_POSITION_ADV_FRACTION = 0.005
EXIT_PROFILES: dict[str, dict[str, float | int | str]] = {
    "legacy_quality": {
        "strategy_id": "legacy_quality",
        "tp_atr": 2.0,
        "sl_atr": 1.0,
        "horizon_bars": 5,
    },
    "v2": {
        "strategy_id": "v2",
        "tp_atr": 5.0,
        "sl_atr": 1.0,
        "horizon_bars": 5,
    },
    "v2_atr4_rvol2": {
        "strategy_id": "v2_atr4_rvol2",
        "tp_atr": 5.0,
        "sl_atr": 1.0,
        "horizon_bars": 5,
    },
}


def execution_policy_enabled() -> bool:
    return os.environ.get("FINPILOT_ENABLE_EXECUTION_POLICY", "0") == "1"


def portfolio_adv_limit_enabled() -> bool:
    return os.environ.get("FINPILOT_ENABLE_PORTFOLIO_ADV_LIMIT", "1") == "1"


def max_position_notional(dollar_adv: object) -> float | None:
    """Return the point-in-time notional cap, or None when ADV is unavailable."""
    try:
        value = float(dollar_adv)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if value <= 0:
        return None
    try:
        fraction = float(
            os.environ.get("FINPILOT_MAX_POSITION_ADV_FRACTION", MAX_POSITION_ADV_FRACTION)
        )
    except ValueError:
        fraction = MAX_POSITION_ADV_FRACTION
    if fraction <= 0:
        return None
    return round(value * fraction, 2)


def execution_contract(data_quality: dict[str, Any]) -> dict[str, Any]:
    """Classify data quality and execution readiness without zero-filling."""
    available = data_quality.get("available", {})
    missing = list(data_quality.get("missing_fields", []))
    adv_available = bool(available.get("dollar_adv", False))
    feasible = adv_available or not execution_policy_enabled()
    reasons = [] if feasible else ["missing_dollar_adv"]
    warnings = []
    if not adv_available:
        warnings.append("portfolio_capacity_unknown")
    if not available.get("spread_bps", False):
        warnings.append("missing_spread")
    return {
        "execution_confidence": "Tier 2"
        if all(
            available.get(field, False)
            for field in ("spread_bps", "dollar_adv", "short_interest_timestamp")
        )
        else "Tier 1"
        if adv_available
        else "Tier 0",
        "data_quality_tier": "Tier 2"
        if all(
            available.get(field, False)
            for field in ("spread_bps", "dollar_adv", "short_interest_timestamp")
        )
        else "Tier 1"
        if adv_available
        else "Tier 0",
        "data_quality_status": "complete" if not missing else "partial",
        "execution_feasible": feasible,
        "execution_reject_reason": reasons,
        "execution_warning": warnings,
        "missing_fields": missing,
    }


def position_cap(dollar_adv: object, requested_notional: object) -> dict[str, Any]:
    cap = max_position_notional(dollar_adv)
    try:
        requested = max(0.0, float(requested_notional))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        requested = 0.0
    if not portfolio_adv_limit_enabled() or cap is None:
        return {
            "position_cap_notional": cap,
            "position_cap_applied": False,
            "position_cap_reject_reason": "portfolio_capacity_unknown" if cap is None else None,
            "position_notional": requested,
        }
    return {
        "position_cap_notional": cap,
        "position_cap_applied": requested > cap,
        "position_cap_reject_reason": "adv_position_cap" if requested > cap else None,
        "position_notional": round(min(requested, cap), 2),
    }


def exit_profile(strategy_id: str) -> dict[str, float | int | str]:
    """Return a copy so callers cannot mutate the locked shadow profile."""
    return dict(EXIT_PROFILES.get(strategy_id, EXIT_PROFILES["legacy_quality"]))
