from __future__ import annotations

from research.scanner_battery_v2 import (
    _summary,
    cost_sensitivity,
    feature_ablation,
    matched_selection,
    payoff_tail,
    signal_frequency,
)


def _row(date: str, symbol: str, value: float, *, eligible: bool, score: float = 50.0) -> dict:
    return {
        "scan_date": date,
        "symbol": symbol,
        "entry_ok": eligible,
        "fwd_5d_pct": value,
        "finpilot_score": score,
        "composite_score": score,
        "dist_52w_high": 0.5,
        "gap_pct": 0.0,
        "rvol": 1.0,
        "atr_pct_real": 3.0,
        "squeeze_factor": 0.5,
        "lottery_factor": 0.5,
        "overnight_gap_factor": 0.0,
        "catalyst_factor": 0.0,
    }


def test_summary_reports_payoff_and_tail_metrics() -> None:
    result = _summary([-2.0, -1.0, 1.0, 5.0])
    assert result["n"] == 4
    assert result["positive_rate"] == 0.5
    assert result["payoff_ratio"] > 1
    assert result["profit_factor"] > 1


def test_cost_sensitivity_preserves_group_boundaries() -> None:
    rows = [
        _row("2026-01-01", "A", 1.0, eligible=True),
        _row("2026-01-01", "B", -1.0, eligible=False),
    ]
    result = cost_sensitivity(rows)
    assert result["groups"]["eligible"]["0"]["mean_net_pct"] == 1.0
    assert result["groups"]["rejected"]["0"]["mean_net_pct"] == -1.0
    assert result["groups"]["eligible"]["150"]["mean_net_pct"] == -0.5


def test_feature_ablation_detects_monotone_feature() -> None:
    rows = [
        _row("2026-01-01", f"S{i}", float(i), eligible=False, score=float(i)) for i in range(20)
    ]
    result = feature_ablation(rows)
    assert result["features"]["finpilot_score"]["spearman_vs_forward_pct"] > 0.99
    assert result["features"]["finpilot_score"]["top_quintile"]["mean_net_pct"] > 15


def test_frequency_counts_daily_eligible_signals() -> None:
    rows = [
        _row("2026-01-01", "A", 1.0, eligible=True),
        _row("2026-01-01", "B", 2.0, eligible=False),
        _row("2026-01-02", "C", -1.0, eligible=True),
    ]
    result = signal_frequency(rows)
    assert result["days"] == 2
    assert result["daily"][0]["eligible_count"] == 1


def test_matched_selection_matches_same_day_rejected_candidate() -> None:
    rows = [
        _row("2026-01-01", "A", -2.0, eligible=True, score=50),
        _row("2026-01-01", "B", 1.0, eligible=False, score=50.1),
    ]
    result = matched_selection(rows)
    assert result["pairs"] == 1
    assert result["difference"]["mean_net_pct"] == -3.0


def test_payoff_tail_does_not_call_top_winner_invalid() -> None:
    rows = [
        _row("2026-01-01", str(i), value, eligible=True) for i, value in enumerate([-1, -1, 1, 100])
    ]
    result = payoff_tail(rows)
    assert result["groups"]["eligible"]["all"]["max_win_pct"] == 100.0
    assert result["groups"]["eligible"]["without_top_1pct"]["status"] == "COMPLETED"
