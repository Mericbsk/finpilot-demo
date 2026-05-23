"""Tests for Sprint 5 closed-loop modules.

Covers: quality_gate, calibration, paper_portfolio, outcome_reconciler.
All tests run in pure in-memory mode (no Redis, no yfinance).
"""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.slow


# ---------------------------------------------------------------------------
# Isolation: every test gets fresh module state
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _reset_loop_state(tmp_path, monkeypatch):
    """Wipe in-memory state of every Sprint 5 module and disable Redis."""
    from core import calibration, paper_portfolio, quality_gate

    # Force the Redis-unavailable path so tests don't depend on a live Redis.
    for mod in (quality_gate, calibration, paper_portfolio):
        mod._redis_client = None
        mod._redis_unavailable = True

    quality_gate._mem_flag = None
    calibration._mem_model = None
    paper_portfolio._mem_open = {}
    paper_portfolio._mem_closed = []
    paper_portfolio._mem_equity = []

    # Redirect disk persistence to tmp_path so tests are hermetic
    monkeypatch.setattr(calibration, "_DISK_PATH", tmp_path / "calibration.json")
    monkeypatch.setattr(paper_portfolio, "_SNAPSHOT", tmp_path / "paper.json")
    yield


# ---------------------------------------------------------------------------
# Quality Gate
# ---------------------------------------------------------------------------
def test_quality_gate_default_not_degraded():
    from core.quality_gate import get_status, is_degraded

    assert is_degraded() is False
    assert get_status()["degraded"] is False


def test_quality_gate_set_and_clear():
    from core.quality_gate import clear_degraded, is_degraded, set_degraded

    set_degraded("test reason", eval_report={"overall_pass": False, "metrics": {}})
    assert is_degraded() is True

    status = clear_degraded()
    assert status is True
    assert is_degraded() is False


def test_quality_gate_set_idempotent():
    from core.quality_gate import get_status, set_degraded

    set_degraded("first")
    set_degraded("second")
    s = get_status()
    assert s["degraded"] is True
    assert s["reason"] == "second"


# ---------------------------------------------------------------------------
# Calibration
# ---------------------------------------------------------------------------
def test_calibration_default_returns_half_when_unfitted():
    from core.calibration import calibrated_probability

    assert calibrated_probability(7.0) == 0.5


def test_calibration_refit_with_samples():
    from core.calibration import calibrated_probability, refit_calibration

    # 10 losses in low band, 10 wins in high band — clear monotonic signal
    samples = [(2.0, False)] * 10 + [(13.0, True)] * 10
    model = refit_calibration(samples=samples, min_samples_per_band=3)

    assert model["n_samples"] == 20
    # Low band -> low p; high band -> high p; monotonic
    p_low = calibrated_probability(2.0)
    p_high = calibrated_probability(13.0)
    assert p_low < p_high
    assert p_high >= 0.9


def test_calibration_enforces_monotonic():
    from core.calibration import refit_calibration

    # Inverse signal: ensure the monotonic guard kicks in
    samples = [(13.0, False)] * 10 + [(2.0, True)] * 10
    model = refit_calibration(samples=samples, min_samples_per_band=3)
    probs = [b["p"] for b in model["bands"]]
    assert probs == sorted(probs), f"non-monotonic: {probs}"


def test_calibration_falls_back_to_global_for_sparse_bands():
    from core.calibration import refit_calibration

    samples = [(2.0, True), (2.0, False), (2.0, True)]  # 3 samples, default min=5
    model = refit_calibration(samples=samples, min_samples_per_band=5)
    # All bands should fall back to global rate
    global_p = model["global_win_rate"]
    for band in model["bands"]:
        assert band["raw_p"] == global_p


# ---------------------------------------------------------------------------
# Paper Portfolio
# ---------------------------------------------------------------------------
def test_paper_open_position_creates_entry():
    from core.paper_portfolio import get_open_positions, open_position

    open_position("sig1", "AAPL", "BUY", entry_price=100.0)
    positions = get_open_positions()
    assert len(positions) == 1
    assert positions[0]["symbol"] == "AAPL"
    assert positions[0]["entry_price"] == 100.0


def test_paper_open_position_idempotent():
    from core.paper_portfolio import get_open_positions, open_position

    open_position("sig1", "AAPL", "BUY", 100.0)
    open_position("sig1", "AAPL", "BUY", 999.0)  # ignored
    positions = get_open_positions()
    assert len(positions) == 1
    assert positions[0]["entry_price"] == 100.0


def test_paper_close_position_buy_win():
    from core.paper_portfolio import close_position, get_summary, open_position

    open_position("sig1", "AAPL", "BUY", 100.0)
    closed = close_position("sig1", 110.0)
    assert closed is not None
    assert closed["pnl"] > 0
    summary = get_summary()
    assert summary["closed_count"] == 1
    assert summary["win_count"] == 1
    assert summary["equity"] > summary["initial_equity"]


def test_paper_close_position_sell_win():
    from core.paper_portfolio import close_position, open_position

    open_position("sig1", "AAPL", "SELL", 100.0)
    closed = close_position("sig1", 90.0)  # price down = SELL wins
    assert closed["pnl"] > 0


def test_paper_close_position_missing_returns_none():
    from core.paper_portfolio import close_position

    assert close_position("nonexistent", 50.0) is None


def test_paper_summary_with_no_trades():
    from core.paper_portfolio import get_summary

    s = get_summary()
    assert s["equity"] == s["initial_equity"]
    assert s["closed_count"] == 0
    assert s["win_rate"] == 0.0


def test_paper_open_position_rejects_invalid_price():
    from core.paper_portfolio import open_position

    with pytest.raises(ValueError):
        open_position("sig1", "AAPL", "BUY", entry_price=0.0)


# ---------------------------------------------------------------------------
# Outcome Reconciler
# ---------------------------------------------------------------------------
def test_reconciler_skips_young_signals(monkeypatch):
    from core import outcome_reconciler

    fake_signal = {
        "id": "AAPL_1_999",
        "symbol": "AAPL",
        "direction": "BUY",
        "price": 100.0,
        "cycle": 1,
        "outcome": None,
        "ts": int(time.time() * 1000),  # just now
    }
    monkeypatch.setattr("core.kpi_tracker._load_all_signals", lambda: [fake_signal])
    summary = outcome_reconciler.reconcile_open_signals(min_age_hours=24)
    assert summary["reconciled"] == 0
    assert summary["skipped_age"] == 1


def test_reconciler_records_outcome_when_close_available(monkeypatch):
    from core import outcome_reconciler

    # Aged signal (10 days old)
    fake_signal = {
        "id": "AAPL_1_111",
        "symbol": "AAPL",
        "direction": "BUY",
        "price": 100.0,
        "cycle": 1,
        "outcome": None,
        "ts": int((time.time() - 10 * 86400) * 1000),
    }
    monkeypatch.setattr("core.kpi_tracker._load_all_signals", lambda: [fake_signal])

    # Mock yfinance close lookup to a win
    monkeypatch.setattr(outcome_reconciler, "_fetch_close_after", lambda *a, **kw: 110.0)

    recorded: list[tuple] = []

    def fake_record(symbol, cycle, profit_pct):
        recorded.append((symbol, cycle, profit_pct))

    monkeypatch.setattr("core.kpi_tracker.record_outcome", fake_record)

    summary = outcome_reconciler.reconcile_open_signals()
    assert summary["reconciled"] == 1
    assert recorded == [("AAPL", 1, pytest.approx(10.0, abs=0.01))]


def test_reconciler_handles_no_close_data(monkeypatch):
    from core import outcome_reconciler

    fake_signal = {
        "id": "AAPL_1_111",
        "symbol": "AAPL",
        "direction": "BUY",
        "price": 100.0,
        "cycle": 1,
        "outcome": None,
        "ts": int((time.time() - 10 * 86400) * 1000),
    }
    monkeypatch.setattr("core.kpi_tracker._load_all_signals", lambda: [fake_signal])
    monkeypatch.setattr(outcome_reconciler, "_fetch_close_after", lambda *a, **kw: None)

    summary = outcome_reconciler.reconcile_open_signals()
    assert summary["reconciled"] == 0
    assert summary["skipped_data"] == 1


# ---------------------------------------------------------------------------
# AlertAgent quality-gate gating
# ---------------------------------------------------------------------------
def test_alert_agent_suppressed_when_degraded(monkeypatch):
    from agents.alert_agent import AlertAgent
    from agents.base import AgentContext

    from core.quality_gate import set_degraded

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "fake")
    set_degraded("test")

    ctx = AgentContext(symbols=["AAPL"], scan_results={"AAPL": {"entry_ok": True, "price": 100}})
    with patch("requests.post") as mock_post:
        result = AlertAgent().run(ctx)
    assert result.success
    assert result.data == []
    assert mock_post.call_count == 0


# ---------------------------------------------------------------------------
# Weekly report — smoke
# ---------------------------------------------------------------------------
def test_weekly_report_renders_with_empty_state(monkeypatch, tmp_path):
    from scripts import weekly_report

    monkeypatch.setattr(weekly_report, "REPORT_DIR", tmp_path)
    md, path = weekly_report.generate_weekly_report(write=True)
    assert "FinPilot Weekly Report" in md
    assert path is not None
    assert path.exists()
