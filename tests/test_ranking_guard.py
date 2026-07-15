from api.routers import scan as scan_router
from scanner.evaluate import _execution_contract
from scanner.execution_policy import (
    execution_contract,
    exit_profile,
    max_position_notional,
    position_cap,
)
from scanner.features import compute_conviction
from scanner.scan_summary import build_candidate_pool
from scanner.score_engine import (
    compute_legacy_quality_score,
    compute_recommendation_score,
    legacy_composite_ranking_enabled,
    regime_gate_mult,
)


def test_legacy_quality_guard_changes_ranking_only(monkeypatch):
    row = {
        "regime": True,
        "direction": True,
        "score": 3,
        "filter_score": 2,
        "alignment_ratio": 0.8,
        "momentum_ratio": 0.7,
        "vol_regime": 1,
        "volume_spike": True,
        "price_momentum": True,
        "trend_strength": True,
    }
    composite = compute_recommendation_score(row)
    quality = compute_legacy_quality_score(
        regime=True,
        direction=True,
        raw_score=3,
        atr_pct=5.0,
        rvol=2.5,
        squeeze_factor=0.4,
        lottery_factor=0.1,
        overnight_gap_factor=0.0,
    )
    expected_gate = regime_gate_mult(True, round(composite / 16.5 * 100))
    monkeypatch.setenv("FINPILOT_ENABLE_LEGACY_COMPOSITE_RANKING", "0")
    assert not legacy_composite_ranking_enabled()
    assert compute_recommendation_score(row) == composite
    assert regime_gate_mult(True, round(composite / 16.5 * 100)) == expected_gate
    assert quality != round(composite / 16.5 * 100)
    monkeypatch.setenv("FINPILOT_ENABLE_LEGACY_COMPOSITE_RANKING", "1")
    assert legacy_composite_ranking_enabled()


def test_scan_summary_prefers_ranking_score():
    out = {
        "AAA": {
            "entry_ok": True,
            "ranking_score": 82,
            "composite_score": 20,
            "conviction_prob": 0.52,
        },
        "BBB": {
            "entry_ok": True,
            "ranking_score": 61,
            "composite_score": 95,
            "conviction_prob": 0.52,
        },
    }
    assert [symbol for symbol, _ in build_candidate_pool(out, 2)] == ["AAA", "BBB"]


def test_scan_summary_orders_tier_then_execution_then_probability():
    out = {
        "B_T2": {
            "entry_ok": True,
            "selection_eligible": True,
            "conviction_tier": "B",
            "execution_confidence": "Tier 2",
            "conviction_prob": 0.59,
            "ranking_score": 99,
        },
        "A_T1": {
            "entry_ok": True,
            "selection_eligible": True,
            "conviction_tier": "A",
            "execution_confidence": "Tier 1",
            "conviction_prob": 0.73,
            "ranking_score": 70,
        },
        "A_T2": {
            "entry_ok": True,
            "selection_eligible": True,
            "conviction_tier": "A",
            "execution_confidence": "Tier 2",
            "conviction_prob": 0.73,
            "ranking_score": 65,
        },
    }
    assert [symbol for symbol, _ in build_candidate_pool(out, 3)] == ["A_T2", "A_T1", "B_T2"]


def test_conviction_probabilities_are_calibrated(monkeypatch):
    monkeypatch.setenv("FINPILOT_ENABLE_CONVICTION_TIERS", "1")
    assert compute_conviction(0.7, 0.7, 0.0, 0.0) == ("A", 0.73)
    assert compute_conviction(0.7, 0.0, 0.0, 4.0) == ("B", 0.59)
    assert compute_conviction(0.0, 0.2, 0.25, 0.0) == ("C", 0.52)


def test_execution_contract_does_not_fabricate_missing_data():
    assert _execution_contract(
        {"available": {"dollar_adv": True, "spread_bps": False, "short_interest_timestamp": False}}
    ) == {"execution_confidence": "Tier 1", "data_quality_tier": "Tier 1"}
    assert _execution_contract(
        {"available": {"dollar_adv": False, "spread_bps": False, "short_interest_timestamp": False}}
    ) == {"execution_confidence": "Tier 0", "data_quality_tier": "Tier 0"}
    assert _execution_contract(
        {"available": {"dollar_adv": True, "spread_bps": True, "short_interest_timestamp": True}}
    ) == {"execution_confidence": "Tier 2", "data_quality_tier": "Tier 2"}


def test_execution_policy_rejects_missing_adv_without_zero_fill(monkeypatch):
    monkeypatch.setenv("FINPILOT_ENABLE_EXECUTION_POLICY", "1")
    result = execution_contract(
        {
            "available": {
                "dollar_adv": False,
                "spread_bps": False,
                "short_interest_timestamp": False,
            },
            "missing_fields": ["dollar_adv", "spread_bps"],
        }
    )
    assert result["execution_feasible"] is False
    assert result["data_quality_status"] == "partial"
    assert "missing_dollar_adv" in result["execution_reject_reason"]
    assert max_position_notional(None) is None


def test_position_cap_and_locked_exit_profiles(monkeypatch):
    monkeypatch.setenv("FINPILOT_ENABLE_PORTFOLIO_ADV_LIMIT", "1")
    capped = position_cap(1_000_000, 6_000)
    assert capped["position_cap_notional"] == 5_000.0
    assert capped["position_cap_applied"] is True
    assert capped["position_notional"] == 5_000.0
    assert exit_profile("legacy_quality")["tp_atr"] == 2.0
    assert exit_profile("v2")["tp_atr"] == 5.0


def test_candidate_pool_excludes_ineligible_and_cap_rejected_rows():
    out = {
        "AAA": {"entry_ok": True, "selection_eligible": True, "ranking_score": 90},
        "BBB": {"entry_ok": True, "selection_eligible": False, "ranking_score": 99},
        "CCC": {
            "entry_ok": True,
            "selection_eligible": True,
            "position_cap_reject_reason": "adv_position_cap",
            "ranking_score": 98,
        },
    }
    assert [symbol for symbol, _ in build_candidate_pool(out, 10)] == ["AAA"]

    def test_shadow_ledger_persists_rejected_rows(tmp_path, monkeypatch):
        monkeypatch.setattr(scan_router, "_SHADOW_DIR", tmp_path)
        scan_router._persist_shadow_ledger(
            {
                "BAD": {
                    "entry_ok": False,
                    "selection_eligible": False,
                    "reject_reason": ["missing_dollar_adv"],
                    "execution_feasible": False,
                    "strategy_scores": {},
                }
            },
            universe=1,
        )
        lines = (tmp_path / "scan_shadow.jsonl").read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1
        assert '"symbol": "BAD"' in lines[0]
        assert '"missing_dollar_adv"' in lines[0]
