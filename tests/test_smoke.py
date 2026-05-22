"""Smoke tests — Sprint 1 S1-8.

Verifies three critical axis:
  1. Redis on/off  — KPI tracker & agent_state degrade gracefully without Redis.
  2. Auth on/off   — POST /scan/run returns 401 without a token, 200 with one.
  3. Pipeline      — run_cycle("scan") with a mocked ScannerAgent completes and
                     returns the expected keys.
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# 1. Redis unavailable — KPI tracker stays functional
# ---------------------------------------------------------------------------

class TestRedisUnavailable:
    def setup_method(self):
        import core.kpi_tracker as kt
        kt._redis_client = None
        kt._redis_unavailable = True
        kt._mem_signals.clear()
        kt._mem_kpis = {
            "win_rate": 0.0, "profit_factor": 0.0, "avg_rr": 0.0,
            "total_signals": 0, "total_wins": 0, "total_losses": 0,
            "total_profit_pct": 0.0, "total_loss_pct": 0.0, "last_updated": None,
        }

    def test_record_and_get_kpis_without_redis(self):
        from core.kpi_tracker import get_kpis, record_outcome, record_signal

        record_signal("AAPL", "BUY", price=180.0, score=70.0, rr=2.0, cycle=1, p_win=0.6)
        record_outcome("AAPL", cycle=1, profit_pct=3.0)
        kpis = get_kpis()
        assert kpis["total_signals"] == 1
        assert kpis["total_wins"] == 1
        assert kpis["win_rate"] == 100.0  # stored as percentage (0-100)

    def test_agent_state_fallback_without_redis(self):
        import core.agent_state as ag

        ag._redis = None
        ag._mem_store.clear()
        from core.agent_state import get_agent_result, save_agent_result

        save_agent_result("scan", ["AAPL"], {"AAPL": {"score": 88}})
        result = get_agent_result("scan", ["AAPL"])
        assert result is not None
        assert result["AAPL"]["score"] == 88

    def test_feedback_fallback_without_redis(self):
        import agents.feedback as fb

        fb._redis_client = None
        fb._redis_unavailable = True
        fb._mem_queues.clear()
        from agents.feedback import emit_feedback, get_feedback

        emit_feedback("monitor", "backtest", "low_win_rate", {"win_rate": 38.0})
        msgs = get_feedback("backtest", limit=5)
        assert len(msgs) == 1
        assert msgs[0]["feedback_type"] == "low_win_rate"


# ---------------------------------------------------------------------------
# 2. Auth middleware — require_auth dependency
# ---------------------------------------------------------------------------

class TestAuthMiddleware:
    def _make_token(self) -> str:
        from auth.core import AuthConfig
        from auth.tokens import JWTHandler

        cfg = AuthConfig()
        handler = JWTHandler(secret_key=cfg.secret_key, algorithm=cfg.algorithm)
        now = int(time.time())
        payload = {
            "sub": "user-smoke-test",
            "exp": now + 3600,
            "iat": now,
            "jti": "smoke-jti",
            "type": "access",
            "role": "user",
        }
        return handler.encode(payload)

    def test_require_auth_raises_without_token(self):
        from fastapi import HTTPException
        from api.middleware.auth import require_auth

        class _NoCreds:
            credentials = None

        import pytest
        with pytest.raises(HTTPException) as exc_info:
            require_auth(None)
        assert exc_info.value.status_code == 401

    def test_require_auth_passes_with_valid_token(self):
        from fastapi.security import HTTPAuthorizationCredentials
        from api.middleware.auth import require_auth

        token = self._make_token()
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        payload = require_auth(creds)
        assert payload.sub == "user-smoke-test"
        assert payload.type == "access"


# ---------------------------------------------------------------------------
# 3. Pipeline run_cycle — mocked ScannerAgent
# ---------------------------------------------------------------------------

class TestPipelineRunCycle:
    def _make_scan_result(self):
        return {
            "AAPL": {"finpilot_score": 80, "composite_score": 75, "entry_ok": True},
            "NVDA": {"finpilot_score": 85, "composite_score": 80, "entry_ok": True},
            "MSFT": {"finpilot_score": 60, "composite_score": 55, "entry_ok": False},
        }

    def test_run_cycle_scan_task(self):
        from agents.base import AgentResult

        mock_result = AgentResult(
            agent="scanner",
            success=True,
            data=self._make_scan_result(),
        )

        with patch("agents.scanner_agent.ScannerAgent.run", return_value=mock_result):
            from core.pipeline import run_cycle

            state = run_cycle(["AAPL", "NVDA", "MSFT"], task="scan")

        assert state["task"] == "scan"
        assert "AAPL" in state["scan_results"]
        assert "NVDA" in state["scan_results"]
        assert len(state["top_symbols"]) <= 5
        assert state["errors"] == []

    def test_run_cycle_returns_early_on_scan_failure(self):
        from agents.base import AgentResult

        mock_result = AgentResult(agent="scanner", success=False, error="no data")

        with patch("agents.scanner_agent.ScannerAgent.run", return_value=mock_result):
            from core.pipeline import run_cycle

            state = run_cycle(["AAPL"], task="full")

        assert len(state["errors"]) > 0
        assert "scan" in state["errors"][0]
        assert state["scan_results"] == {}

    def test_run_cycle_top_symbols_ranked_by_score(self):
        from agents.base import AgentResult

        scan = {
            "A": {"finpilot_score": 50},
            "B": {"finpilot_score": 90},
            "C": {"finpilot_score": 70},
        }
        mock_result = AgentResult(agent="scanner", success=True, data=scan)

        with patch("agents.scanner_agent.ScannerAgent.run", return_value=mock_result):
            from core.pipeline import run_cycle

            state = run_cycle(["A", "B", "C"], task="scan")

        assert state["top_symbols"][0] == "B"
        assert state["top_symbols"][1] == "C"
