"""Tests for core.pipeline.run_cycle — LangGraph-free CEO workflow.

All agent calls are mocked so tests run without network/Redis/LLM.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_agent_result(success: bool = True, data: dict | None = None, error: str = ""):
    r = MagicMock()
    r.success = success
    r.data = data or {}
    r.error = error
    return r


SCAN_DATA = {
    "AAPL": {"finpilot_score": 0.9, "entry_ok": True},
    "NVDA": {"finpilot_score": 0.8, "entry_ok": True},
    "MSFT": {"finpilot_score": 0.7, "entry_ok": False},
}


@pytest.fixture(autouse=True)
def _reset_imports():
    """Ensure pipeline module is freshly importable each test."""
    import importlib
    import core.pipeline  # noqa: F401  (just ensure it's loadable)

    importlib.reload(__import__("core.pipeline", fromlist=["run_cycle"]))
    yield


# ---------------------------------------------------------------------------
# Task "scan"
# ---------------------------------------------------------------------------


def test_scan_task_returns_scan_results():
    from core.pipeline import run_cycle

    mock_result = _make_agent_result(data=SCAN_DATA)
    with patch("agents.scanner_agent.ScannerAgent") as MockScanner:
        MockScanner.return_value.run.return_value = mock_result
        state = run_cycle(["AAPL", "NVDA", "MSFT"], task="scan")

    assert state["scan_results"] == SCAN_DATA
    assert state["top_symbols"][0] == "AAPL"  # highest finpilot_score first
    assert len(state["top_symbols"]) <= 5
    assert state["errors"] == []


def test_scan_task_top5_cap():
    """Top symbols must be capped at 5 even with 6 inputs."""
    from core.pipeline import run_cycle

    many = {f"SYM{i}": {"finpilot_score": float(i)} for i in range(6)}
    mock_result = _make_agent_result(data=many)
    with patch("agents.scanner_agent.ScannerAgent") as MockScanner:
        MockScanner.return_value.run.return_value = mock_result
        state = run_cycle(list(many.keys()), task="scan")

    assert len(state["top_symbols"]) == 5
    assert state["top_symbols"][0] == "SYM5"  # highest score


def test_scan_failure_returns_early():
    from core.pipeline import run_cycle

    mock_result = _make_agent_result(success=False, error="market closed")
    with patch("agents.scanner_agent.ScannerAgent") as MockScanner:
        MockScanner.return_value.run.return_value = mock_result
        state = run_cycle(["AAPL"], task="scan")

    assert "scan: market closed" in state["errors"]
    assert state["scan_results"] == {}
    assert state["top_symbols"] == []


def test_scan_exception_returns_early():
    from core.pipeline import run_cycle

    with patch("agents.scanner_agent.ScannerAgent") as MockScanner:
        MockScanner.return_value.run.side_effect = RuntimeError("timeout")
        state = run_cycle(["AAPL"], task="scan")

    assert any("scan:" in e for e in state["errors"])
    assert state["scan_results"] == {}


def test_scan_task_does_not_call_analysis():
    from core.pipeline import run_cycle

    mock_scan = _make_agent_result(data=SCAN_DATA)
    with (
        patch("agents.scanner_agent.ScannerAgent") as MockScanner,
        patch("agents.analysis_agent.AnalysisAgent") as MockAnalysis,
    ):
        MockScanner.return_value.run.return_value = mock_scan
        state = run_cycle(["AAPL"], task="scan")

    MockAnalysis.assert_not_called()
    assert state["analysis_results"] == {}


# ---------------------------------------------------------------------------
# Task "full"
# ---------------------------------------------------------------------------


def test_full_task_calls_all_agents():
    from core.pipeline import run_cycle

    mock_scan = _make_agent_result(data=SCAN_DATA)
    mock_analysis = _make_agent_result(data={"AAPL": {"recommendation": "BUY"}})
    mock_risk = _make_agent_result(data={"AAPL": {"risk": "low"}})
    mock_alert = _make_agent_result(data=["AAPL"])

    with (
        patch("agents.scanner_agent.ScannerAgent") as MS,
        patch("agents.analysis_agent.AnalysisAgent") as MA,
        patch("agents.risk_agent.RiskAgent") as MR,
        patch("agents.alert_agent.AlertAgent") as MAl,
    ):
        MS.return_value.run.return_value = mock_scan
        MA.return_value.run.return_value = mock_analysis
        MR.return_value.run.return_value = mock_risk
        MAl.return_value.run.return_value = mock_alert

        state = run_cycle(["AAPL", "NVDA", "MSFT"], task="full")

    assert state["scan_results"] == SCAN_DATA
    assert len(state["analysis_results"]) > 0
    assert state["risk_results"] == {"AAPL": {"risk": "low"}}
    assert state["alerts_sent"] == ["AAPL"]
    assert state["errors"] == []


def test_full_task_partial_analysis_failure():
    """Analysis failure for one symbol appends error but continues."""
    from core.pipeline import run_cycle

    scan_data = {
        "AAPL": {"finpilot_score": 0.9},
        "NVDA": {"finpilot_score": 0.8},
    }
    mock_scan = _make_agent_result(data=scan_data)
    mock_analysis_fail = _make_agent_result(success=False, error="rate limited")
    mock_risk = _make_agent_result(data={})
    mock_alert = _make_agent_result(data=[])

    with (
        patch("agents.scanner_agent.ScannerAgent") as MS,
        patch("agents.analysis_agent.AnalysisAgent") as MA,
        patch("agents.risk_agent.RiskAgent") as MR,
        patch("agents.alert_agent.AlertAgent") as MAl,
    ):
        MS.return_value.run.return_value = mock_scan
        MA.return_value.run.return_value = mock_analysis_fail
        MR.return_value.run.return_value = mock_risk
        MAl.return_value.run.return_value = mock_alert

        state = run_cycle(["AAPL", "NVDA"], task="full")

    assert any("analyze/" in e for e in state["errors"])
    assert state["risk_results"] == {}
    assert state["alerts_sent"] == []


# ---------------------------------------------------------------------------
# Task "risk"
# ---------------------------------------------------------------------------


def test_risk_task_skips_alert():
    from core.pipeline import run_cycle

    mock_scan = _make_agent_result(data=SCAN_DATA)
    mock_risk = _make_agent_result(data={"AAPL": {"risk": "medium"}})

    with (
        patch("agents.scanner_agent.ScannerAgent") as MS,
        patch("agents.risk_agent.RiskAgent") as MR,
        patch("agents.alert_agent.AlertAgent") as MAl,
    ):
        MS.return_value.run.return_value = mock_scan
        MR.return_value.run.return_value = mock_risk

        state = run_cycle(["AAPL"], task="risk")

    MAl.assert_not_called()
    assert state["risk_results"] == {"AAPL": {"risk": "medium"}}
    assert state["alerts_sent"] == []


# ---------------------------------------------------------------------------
# State dict structure
# ---------------------------------------------------------------------------


def test_state_always_has_all_keys():
    from core.pipeline import run_cycle

    mock_scan = _make_agent_result(success=False, error="no data")
    with patch("agents.scanner_agent.ScannerAgent") as MS:
        MS.return_value.run.return_value = mock_scan
        state = run_cycle(["AAPL"], task="full")

    required_keys = {"task", "symbols", "scan_results", "top_symbols",
                     "analysis_results", "risk_results", "alerts_sent", "errors"}
    assert required_keys.issubset(state.keys())


def test_empty_symbols_returns_scan_results():
    """run_cycle with empty list should not crash."""
    from core.pipeline import run_cycle

    mock_scan = _make_agent_result(data={})
    with patch("agents.scanner_agent.ScannerAgent") as MS:
        MS.return_value.run.return_value = mock_scan
        state = run_cycle([], task="scan")

    assert state["top_symbols"] == []
    assert state["errors"] == []
