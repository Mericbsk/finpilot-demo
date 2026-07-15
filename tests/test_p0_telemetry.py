from scanner.labeling import triple_barrier_label
from scanner.score_engine import compute_recommendation_score
from scanner.telemetry import decision_telemetry, score_component_breakdown


def test_score_component_breakdown_matches_production_score(monkeypatch):
    for name in (
        "FINPILOT_ENABLE_SQUEEZE_FACTOR",
        "FINPILOT_ENABLE_EDGAR_CATALYST",
        "FINPILOT_ENABLE_LOTTERY_FADE",
        "FINPILOT_ENABLE_OVERNIGHT_GAP",
    ):
        monkeypatch.setenv(name, "1")
    row = {
        "regime": True,
        "direction": True,
        "score": 3,
        "filter_score": 2,
        "alignment_ratio": 0.8,
        "momentum_ratio": 0.7,
        "vol_regime": 1,
        "volume_spike": True,
        "price_momentum": False,
        "trend_strength": True,
        "squeeze_factor": 0.8,
        "catalyst_factor": 0.6,
        "lottery_factor": 0.7,
        "overnight_gap_factor": 0.4,
    }
    expected = compute_recommendation_score(row)
    actual = score_component_breakdown(row)["total"]
    assert actual == expected


def test_decision_telemetry_deduplicates_reject_reasons():
    telemetry = decision_telemetry(
        reject_reasons=["liquidity_gate", "liquidity_gate", "score_threshold"],
        score=5.25,
        components={"total": 5.25, "regime": 2.0},
    )
    assert telemetry["telemetry_version"] == "p0.v1"
    assert telemetry["point_in_time"] is True
    assert telemetry["reject_reason"] == ["liquidity_gate", "score_threshold"]
    assert telemetry["score_component_breakdown"]["total"] == 5.25


def test_decision_telemetry_preserves_data_quality_contract():
    telemetry = decision_telemetry(
        reject_reasons=[],
        score=4.0,
        components={"total": 4.0},
        data_quality={"spread_bps": 12.5, "missing_fields": ["short_interest_timestamp"]},
    )
    assert telemetry["data_quality"]["spread_bps"] == 12.5
    assert telemetry["data_quality"]["missing_fields"] == ["short_interest_timestamp"]


def test_barrier_execution_has_path_dependent_result():
    result = triple_barrier_label(
        [100.0, 103.0, 102.0],
        entry_price=100.0,
        tp_pct=0.02,
        sl_pct=0.01,
        max_horizon=3,
        forward_highs=[101.0, 103.0, 102.0],
        forward_lows=[100.0, 101.0, 101.0],
    )
    assert result.label == "tp"
    assert result.bars_to_hit == 2
