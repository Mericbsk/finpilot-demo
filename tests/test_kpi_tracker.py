"""Tests for core.kpi_tracker — in-memory path only (no Redis required).

Covers: record_signal, record_outcome, mark_signal_auto_approved,
        _recompute_kpis, get_kpis, get_recent_signals, self_evaluate,
        get_cycle_scores.
"""

from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Fixture: reset in-memory state and force Redis-unavailable for every test
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _reset_kpi_state():
    import core.kpi_tracker as kt

    kt._redis_client = None
    kt._redis_unavailable = True
    kt._mem_signals.clear()
    kt._mem_kpis = {
        "win_rate": 0.0,
        "profit_factor": 0.0,
        "avg_rr": 0.0,
        "total_signals": 0,
        "total_wins": 0,
        "total_losses": 0,
        "total_profit_pct": 0.0,
        "total_loss_pct": 0.0,
        "last_updated": None,
    }
    kt._mem_cycle_scores.clear()
    yield


# ---------------------------------------------------------------------------
# record_signal
# ---------------------------------------------------------------------------
class TestRecordSignal:
    def test_basic_signal_stored(self):
        from core.kpi_tracker import record_signal, get_recent_signals

        record_signal("AAPL", "BUY", price=150.0, score=72, cycle=1)
        sigs = get_recent_signals(10)
        assert len(sigs) == 1
        s = sigs[0]
        assert s["symbol"] == "AAPL"
        assert s["direction"] == "BUY"
        assert s["price"] == 150.0
        assert s["score"] == 72.0
        assert s["cycle"] == 1
        assert s["outcome"] is None

    def test_multiple_signals_stored_newest_first(self):
        from core.kpi_tracker import record_signal, get_recent_signals

        record_signal("AAPL", "BUY", price=150.0, cycle=1)
        record_signal("MSFT", "SELL", price=300.0, cycle=2)
        sigs = get_recent_signals(5)
        assert len(sigs) == 2
        assert sigs[0]["symbol"] == "MSFT"  # newest first

    def test_signal_id_format(self):
        from core.kpi_tracker import record_signal, get_recent_signals

        record_signal("NVDA", "BUY", price=500.0, cycle=99)
        sig = get_recent_signals(1)[0]
        assert sig["id"].startswith("NVDA_99_")

    def test_explicit_p_win_stored(self):
        from core.kpi_tracker import record_signal, get_recent_signals

        record_signal("AAPL", "BUY", price=100.0, p_win=0.72)
        sig = get_recent_signals(1)[0]
        assert sig["p_win"] == 0.72

    def test_p_win_defaults_to_half_when_calibration_unavailable(self, monkeypatch):
        from core import kpi_tracker as kt
        monkeypatch.setattr(kt, "_redis_unavailable", True)
        # No calibration model fitted → falls back to 0.5
        from core.kpi_tracker import record_signal, get_recent_signals

        record_signal("AAPL", "BUY", price=100.0, score=50, p_win=None)
        sig = get_recent_signals(1)[0]
        assert sig["p_win"] == 0.5

    def test_max_signals_cap(self):
        from core.kpi_tracker import MAX_SIGNALS, record_signal, get_recent_signals

        for i in range(MAX_SIGNALS + 10):
            record_signal("AAPL", "BUY", price=float(i), cycle=i)
        sigs = get_recent_signals(MAX_SIGNALS + 20)
        assert len(sigs) <= MAX_SIGNALS

    def test_rr_and_stop_loss_stored(self):
        from core.kpi_tracker import record_signal, get_recent_signals

        record_signal("TSLA", "BUY", price=200.0, rr=2.5, stop_loss=190.0, take_profit=220.0)
        sig = get_recent_signals(1)[0]
        assert sig["rr"] == 2.5
        assert sig["stop_loss"] == 190.0
        assert sig["take_profit"] == 220.0


# ---------------------------------------------------------------------------
# record_outcome
# ---------------------------------------------------------------------------
class TestRecordOutcome:
    def test_win_updates_outcome(self):
        from core.kpi_tracker import record_signal, record_outcome, get_recent_signals

        record_signal("AAPL", "BUY", price=100.0, cycle=1)
        record_outcome("AAPL", cycle=1, profit_pct=5.0)
        sig = get_recent_signals(1)[0]
        assert sig["outcome"] == "win"
        assert sig["profit_pct"] == 5.0

    def test_loss_updates_outcome(self):
        from core.kpi_tracker import record_signal, record_outcome, get_recent_signals

        record_signal("AAPL", "BUY", price=100.0, cycle=2)
        record_outcome("AAPL", cycle=2, profit_pct=-3.0)
        sig = get_recent_signals(1)[0]
        assert sig["outcome"] == "loss"
        assert sig["profit_pct"] == -3.0

    def test_outcome_not_overwritten_for_different_cycle(self):
        from core.kpi_tracker import record_signal, record_outcome, get_recent_signals

        record_signal("AAPL", "BUY", price=100.0, cycle=1)
        record_signal("AAPL", "BUY", price=105.0, cycle=2)
        record_outcome("AAPL", cycle=1, profit_pct=4.0)
        sigs = get_recent_signals(5)
        cycle1 = next(s for s in sigs if s["cycle"] == 1)
        cycle2 = next(s for s in sigs if s["cycle"] == 2)
        assert cycle1["outcome"] == "win"
        assert cycle2["outcome"] is None

    def test_outcome_not_set_for_wrong_symbol(self):
        from core.kpi_tracker import record_signal, record_outcome, get_recent_signals

        record_signal("AAPL", "BUY", price=100.0, cycle=1)
        record_outcome("MSFT", cycle=1, profit_pct=5.0)
        sig = get_recent_signals(1)[0]
        assert sig["outcome"] is None

    def test_kpis_updated_after_outcome(self):
        from core.kpi_tracker import record_signal, record_outcome, get_kpis

        record_signal("AAPL", "BUY", price=100.0, cycle=1)
        record_outcome("AAPL", cycle=1, profit_pct=10.0)
        kpis = get_kpis()
        assert kpis["total_wins"] == 1
        assert kpis["win_rate"] == 100.0

    def test_profit_factor_computed(self):
        from core.kpi_tracker import record_signal, record_outcome, get_kpis

        record_signal("A", "BUY", price=100.0, cycle=1)
        record_signal("B", "BUY", price=100.0, cycle=2)
        record_outcome("A", cycle=1, profit_pct=10.0)
        record_outcome("B", cycle=2, profit_pct=-5.0)
        kpis = get_kpis()
        assert kpis["profit_factor"] == 2.0
        assert kpis["win_rate"] == 50.0
        assert kpis["total_wins"] == 1
        assert kpis["total_losses"] == 1

    def test_avg_rr_computed_from_signals_with_rr(self):
        from core.kpi_tracker import record_signal, record_outcome, get_kpis

        record_signal("A", "BUY", price=100.0, rr=2.0, cycle=1)
        record_signal("B", "BUY", price=100.0, rr=3.0, cycle=2)
        record_outcome("A", cycle=1, profit_pct=5.0)
        record_outcome("B", cycle=2, profit_pct=-2.0)
        kpis = get_kpis()
        assert kpis["avg_rr"] == 2.5

    def test_only_resolved_contribute_to_kpis(self):
        from core.kpi_tracker import record_signal, record_outcome, get_kpis

        record_signal("A", "BUY", price=100.0, cycle=1)
        record_signal("B", "BUY", price=100.0, cycle=2)  # no outcome
        record_outcome("A", cycle=1, profit_pct=5.0)
        kpis = get_kpis()
        assert kpis["total_signals"] == 2
        assert kpis["total_wins"] == 1

    def test_profit_factor_infinity_when_no_losses(self):
        from core.kpi_tracker import record_signal, record_outcome, get_kpis

        record_signal("A", "BUY", price=100.0, cycle=1)
        record_outcome("A", cycle=1, profit_pct=10.0)
        kpis = get_kpis()
        assert kpis["profit_factor"] == 999.0  # sentinel for inf


# ---------------------------------------------------------------------------
# mark_signal_auto_approved
# ---------------------------------------------------------------------------
class TestMarkSignalAutoApproved:
    def test_returns_true_on_success(self):
        from core.kpi_tracker import record_signal, mark_signal_auto_approved

        record_signal("AAPL", "BUY", price=100.0, cycle=5)
        result = mark_signal_auto_approved("AAPL", cycle=5, p_win=0.72)
        assert result is True

    def test_flag_persisted(self):
        from core.kpi_tracker import record_signal, mark_signal_auto_approved, get_recent_signals

        record_signal("AAPL", "BUY", price=100.0, cycle=5)
        mark_signal_auto_approved("AAPL", cycle=5, p_win=0.72)
        sig = get_recent_signals(1)[0]
        assert sig["auto_approved"] is True
        assert sig["auto_approve_p_win"] == 0.72

    def test_idempotent_returns_false_on_second_call(self):
        from core.kpi_tracker import record_signal, mark_signal_auto_approved

        record_signal("AAPL", "BUY", price=100.0, cycle=5)
        mark_signal_auto_approved("AAPL", cycle=5, p_win=0.72)
        result2 = mark_signal_auto_approved("AAPL", cycle=5, p_win=0.80)
        assert result2 is False

    def test_idempotent_does_not_overwrite_p_win(self):
        from core.kpi_tracker import record_signal, mark_signal_auto_approved, get_recent_signals

        record_signal("AAPL", "BUY", price=100.0, cycle=5)
        mark_signal_auto_approved("AAPL", cycle=5, p_win=0.72)
        mark_signal_auto_approved("AAPL", cycle=5, p_win=0.99)
        sig = get_recent_signals(1)[0]
        assert sig["auto_approve_p_win"] == 0.72  # original retained

    def test_returns_false_for_missing_symbol(self):
        from core.kpi_tracker import mark_signal_auto_approved

        result = mark_signal_auto_approved("NONEXISTENT", cycle=999, p_win=0.9)
        assert result is False

    def test_cycle_mismatch_not_updated(self):
        from core.kpi_tracker import record_signal, mark_signal_auto_approved, get_recent_signals

        record_signal("AAPL", "BUY", price=100.0, cycle=1)
        result = mark_signal_auto_approved("AAPL", cycle=99, p_win=0.8)
        assert result is False
        sig = get_recent_signals(1)[0]
        assert not sig.get("auto_approved")

    def test_multiple_signals_only_matching_approved(self):
        from core.kpi_tracker import record_signal, mark_signal_auto_approved, get_recent_signals

        record_signal("AAPL", "BUY", price=100.0, cycle=1)
        record_signal("MSFT", "BUY", price=300.0, cycle=1)
        mark_signal_auto_approved("AAPL", cycle=1, p_win=0.75)
        sigs = get_recent_signals(5)
        aapl = next(s for s in sigs if s["symbol"] == "AAPL")
        msft = next(s for s in sigs if s["symbol"] == "MSFT")
        assert aapl["auto_approved"] is True
        assert not msft.get("auto_approved")


# ---------------------------------------------------------------------------
# get_kpis — edge cases
# ---------------------------------------------------------------------------
class TestGetKpis:
    def test_returns_zeros_when_no_signals(self):
        from core.kpi_tracker import get_kpis

        kpis = get_kpis()
        assert kpis["win_rate"] == 0.0
        assert kpis["total_signals"] == 0

    def test_returns_zeros_when_no_resolved_signals(self):
        from core.kpi_tracker import record_signal, get_kpis

        record_signal("AAPL", "BUY", price=100.0, cycle=1)
        kpis = get_kpis()
        assert kpis["win_rate"] == 0.0

    def test_get_recent_signals_limit(self):
        from core.kpi_tracker import record_signal, get_recent_signals

        for i in range(10):
            record_signal(f"S{i}", "BUY", price=float(i), cycle=i)
        sigs = get_recent_signals(3)
        assert len(sigs) == 3


# ---------------------------------------------------------------------------
# self_evaluate
# ---------------------------------------------------------------------------
class TestSelfEvaluate:
    def test_grade_a_on_healthy_system(self):
        from core.kpi_tracker import record_signal, record_outcome, self_evaluate

        for i in range(10):
            record_signal("A", "BUY", price=100.0, cycle=i)
            record_outcome("A", cycle=i, profit_pct=5.0)  # all wins

        result = self_evaluate(
            {
                "market_intel": "ok",
                "research": "ok",
                "backtest": "ok",
                "monitor": "ok",
                "errors": [],
            }
        )
        assert result["grade"] in ("A", "B")
        assert result["score"] >= 60

    def test_grade_d_with_errors_and_failures(self):
        from core.kpi_tracker import self_evaluate

        result = self_evaluate(
            {
                "errors": ["err1", "err2", "err3", "err4", "err5", "err6"],
            }
        )
        assert result["grade"] in ("C", "D")
        assert result["score"] < 70

    def test_score_clipped_to_0_100(self):
        from core.kpi_tracker import self_evaluate

        result = self_evaluate({"errors": []})
        assert 0 <= result["score"] <= 100

    def test_recommendations_generated_for_low_win_rate(self):
        from core.kpi_tracker import record_signal, record_outcome, self_evaluate

        for i in range(5):
            record_signal("A", "BUY", price=100.0, cycle=i)
            record_outcome("A", cycle=i, profit_pct=-5.0)  # all losses

        result = self_evaluate({"errors": []})
        assert any("win rate" in r.lower() or "win_rate" in r.lower() or "oran" in r.lower()
                   for r in result["recommendations"])

    def test_evaluation_stored_in_cycle_scores(self):
        from core.kpi_tracker import self_evaluate, get_cycle_scores

        self_evaluate({"errors": []})
        scores = get_cycle_scores(5)
        assert len(scores) == 1
        assert "score" in scores[0]
        assert "grade" in scores[0]

    def test_breakdown_keys_present(self):
        from core.kpi_tracker import self_evaluate

        result = self_evaluate({"market_intel": "ok", "errors": []})
        bd = result["breakdown"]
        assert "kpi_health" in bd
        assert "error_penalty" in bd
        assert "coverage" in bd
        assert "momentum" in bd


# ---------------------------------------------------------------------------
# get_cycle_scores
# ---------------------------------------------------------------------------
class TestGetCycleScores:
    def test_empty_initially(self):
        from core.kpi_tracker import get_cycle_scores

        assert get_cycle_scores() == []

    def test_scores_stored_newest_first(self):
        from core.kpi_tracker import self_evaluate, get_cycle_scores

        self_evaluate({"errors": []})
        self_evaluate({"errors": ["e1"]})
        scores = get_cycle_scores(10)
        assert len(scores) == 2
        # newest first — last evaluated (with error) scored lower
        assert scores[0]["ts"] >= scores[1]["ts"]

    def test_limit_respected(self):
        from core.kpi_tracker import self_evaluate, get_cycle_scores

        for _ in range(5):
            self_evaluate({"errors": []})
        scores = get_cycle_scores(3)
        assert len(scores) == 3
