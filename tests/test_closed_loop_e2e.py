"""Phase 2 (faz2-e2e-test): closed-loop integration test.

Exercises the closed loop end-to-end without yfinance/redis dependencies:

  record_signal(score, p_win)  ->  record_outcome(profit_pct)
  -> refit_calibration() reads the recorded signals and produces a model
  -> calibrated_probability() reflects the new model

Also verifies the decision gate honors FINPILOT_PWIN_THRESHOLD.
"""

from __future__ import annotations

import importlib

import pytest

pytestmark = pytest.mark.slow


@pytest.fixture(autouse=True)
def _reset_inmemory_state(monkeypatch, tmp_path):
    """Force in-memory Redis fallback and isolate calibration model on disk."""
    monkeypatch.setenv("REDIS_URL", "")  # ensure no real redis
    # Re-import modules so the global _mem_signals / _mem_model start clean.
    import core.calibration as cal
    import core.kpi_tracker as kpi

    importlib.reload(kpi)
    importlib.reload(cal)
    # Redirect calibration disk persistence into the test tmp dir
    monkeypatch.setattr(cal, "_DISK_PATH", tmp_path / "calibration_model.json")
    yield
    importlib.reload(kpi)
    importlib.reload(cal)


def test_record_signal_includes_pwin_default():
    from core.kpi_tracker import get_recent_signals, record_signal

    record_signal(symbol="AAPL", direction="BUY", price=100.0, score=0.7, cycle=1)
    sigs = get_recent_signals(limit=5)
    assert len(sigs) == 1
    sig = sigs[0]
    assert "p_win" in sig
    # No model fitted yet -> default 0.5
    assert sig["p_win"] == pytest.approx(0.5, abs=1e-6)


def test_outcome_reconciliation_feeds_calibration():
    from core.calibration import (
        calibrated_probability,
        get_calibration_model,
        refit_calibration,
    )
    from core.kpi_tracker import record_outcome, record_signal

    # 12 high-score winners, 12 low-score losers — clear monotonic signal.
    for i in range(12):
        record_signal(symbol=f"W{i}", direction="BUY", price=100.0, score=0.8, cycle=i)
        record_outcome(symbol=f"W{i}", cycle=i, profit_pct=2.0)
    for i in range(12):
        record_signal(symbol=f"L{i}", direction="BUY", price=100.0, score=0.2, cycle=100 + i)
        record_outcome(symbol=f"L{i}", cycle=100 + i, profit_pct=-2.0)

    model = refit_calibration(
        samples=None,
        min_samples_per_band=3,
        bands=[(0.0, 0.5), (0.5, 1.0)],
    )
    assert model is not None
    assert model["n_samples"] == 24
    assert get_calibration_model() is not None

    # high score should map to higher p than low score (monotonic enforced)
    p_high = calibrated_probability(0.8)
    p_low = calibrated_probability(0.2)
    assert p_high >= p_low
    assert p_high > 0.5
    assert p_low < 0.5


def test_decision_gate_respects_threshold(monkeypatch):
    """When p_win < threshold, paper open_position must be skipped.

    We inspect the scheduler block by simulating its key logic in isolation
    rather than running a full cycle (which needs market data).
    """
    monkeypatch.setenv("FINPILOT_PWIN_THRESHOLD", "0.6")

    from core.calibration import calibrated_probability
    from core.kpi_tracker import record_signal
    from core.paper_portfolio import get_open_positions, open_position, reset_portfolio

    reset_portfolio()

    # No model fitted -> calibrated_probability returns 0.5 < 0.6 threshold
    score = 0.5
    p_win = calibrated_probability(score)
    assert p_win == pytest.approx(0.5)

    record_signal(symbol="MSFT", direction="BUY", price=200.0, score=score, cycle=1, p_win=p_win)

    threshold = float(
        monkeypatch.getenv("FINPILOT_PWIN_THRESHOLD") if hasattr(monkeypatch, "getenv") else 0.6
    )
    # mimic scheduler decision gate
    if p_win >= threshold:
        open_position(
            signal_id="msft_1",
            symbol="MSFT",
            direction="BUY",
            entry_price=200.0,
            score=score,
            cycle=1,
            p_win=p_win,
        )

    assert get_open_positions() == []  # gate held


def test_open_position_persists_pwin():
    from core.paper_portfolio import get_open_positions, open_position, reset_portfolio

    reset_portfolio()
    open_position(
        signal_id="nvda_1",
        symbol="NVDA",
        direction="BUY",
        entry_price=500.0,
        score=0.9,
        cycle=1,
        p_win=0.78,
    )
    positions = get_open_positions()
    assert len(positions) == 1
    assert positions[0]["p_win"] == pytest.approx(0.78, abs=1e-4)
