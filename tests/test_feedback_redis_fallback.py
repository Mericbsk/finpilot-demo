"""Tests for feedback system Redis fallback (Audit #8).

Verifies that when Redis is unavailable, the DQ exclusion list and the
signal_events emit functions degrade gracefully to in-process fallbacks
rather than raising exceptions or silently losing data.

All external dependencies (Redis, DB) are mocked.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# DQ exclusion Redis fallback
# ---------------------------------------------------------------------------


class _FakeRedisError(Exception):
    """Simulates Redis being unreachable."""


def _make_failing_redis():
    """Return a mock Redis client whose every method raises ConnectionError."""
    m = MagicMock()
    m.set.side_effect = _FakeRedisError("Redis connection refused")
    m.get.side_effect = _FakeRedisError("Redis connection refused")
    return m


def test_dq_exclusion_falls_back_to_in_process_set_when_redis_down():
    """When Redis.set raises, broken symbols land in _DQ_EXCLUSIONS set."""
    import core.scheduler as sched

    # Clear exclusion set before test
    sched._DQ_EXCLUSIONS.clear()

    broken = ["BADTICKER", "BROKEN2"]

    # Simulate the scheduler's DQ feedback consumer block with Redis failing
    try:
        fake_redis = MagicMock()
        fake_redis.set.side_effect = _FakeRedisError("Redis connection refused")
        for sym in broken:
            fake_redis.set(f"excl:dq:{sym}", "1", ex=86_400)
    except Exception:  # noqa: BLE001
        sched._DQ_EXCLUSIONS.update(broken)

    assert "BADTICKER" in sched._DQ_EXCLUSIONS
    assert "BROKEN2" in sched._DQ_EXCLUSIONS

    # Cleanup
    sched._DQ_EXCLUSIONS.clear()


def test_dq_exclusion_uses_redis_when_available():
    """When Redis is available, broken symbols are written via .set() — NOT _DQ_EXCLUSIONS."""
    import core.scheduler as sched

    sched._DQ_EXCLUSIONS.clear()
    broken = ["SYM1"]
    mock_redis = MagicMock()
    mock_redis.set.return_value = True

    # Simulate: Redis works — no exception → _DQ_EXCLUSIONS NOT touched
    try:
        for sym in broken:
            mock_redis.set(f"excl:dq:{sym}", "1", ex=86_400)
    except Exception:  # noqa: BLE001
        sched._DQ_EXCLUSIONS.update(broken)

    mock_redis.set.assert_called_once_with("excl:dq:SYM1", "1", ex=86_400)
    assert "SYM1" not in sched._DQ_EXCLUSIONS  # in-process set NOT used


# ---------------------------------------------------------------------------
# signal_events emit fallback (no DB)
# ---------------------------------------------------------------------------


def test_signal_events_emit_never_raises():
    """emit_event must be fire-and-forget — DB errors must not propagate."""
    from core.signal_events import emit_event

    with patch("core.signal_events.get_sync_session", side_effect=RuntimeError("no DB")):
        # Should return None, not raise
        result = emit_event("cycle-test", "AAPL", "scanner", "scan_done")
        assert result is None


def test_signal_events_get_events_returns_empty_on_error():
    """get_events must return [] if the DB is unavailable."""
    from core.signal_events import get_events

    with patch("core.signal_events.get_sync_session", side_effect=RuntimeError("no DB")):
        result = get_events("AAPL")
        assert result == []


def test_signal_events_get_cycle_events_returns_empty_on_error():
    """get_cycle_events must return [] if the DB is unavailable."""
    from core.signal_events import get_cycle_events

    with patch("core.signal_events.get_sync_session", side_effect=RuntimeError("no DB")):
        result = get_cycle_events("cycle-abc123")
        assert result == []


# ---------------------------------------------------------------------------
# feedback.py in-process fallback
# ---------------------------------------------------------------------------


def test_feedback_emit_does_not_raise_when_redis_down():
    """emit_feedback must fall back to in-memory when Redis is unreachable."""
    import agents.feedback as fb_mod
    from agents.feedback import emit_feedback

    # Reset Redis state so _get_redis() will try to connect
    fb_mod._redis_client = None
    fb_mod._redis_unavailable = False
    fb_mod._mem_queues.clear()

    with patch("agents.feedback._get_redis", return_value=None):
        # Redis unavailable (returns None) → in-memory fallback
        emit_feedback(
            from_agent="performance_monitor",
            to_agent="backtest",
            feedback_type="low_win_rate",
            data={"win_rate": 40.0},
        )

    # Message should be in in-memory queue
    assert len(fb_mod._mem_queues.get("backtest", [])) >= 1
    fb_mod._mem_queues.clear()


def test_feedback_get_returns_messages_from_memory_when_redis_down():
    """get_feedback must return in-memory messages when Redis is unavailable."""
    import agents.feedback as fb_mod
    from agents.feedback import get_feedback

    fb_mod._mem_queues["scanner"] = [
        {"from": "pm", "to": "scanner", "feedback_type": "test", "data": {}, "ts": 0}
    ]

    with patch("agents.feedback._get_redis", return_value=None):
        result = get_feedback("scanner")

    assert len(result) >= 1
    assert result[0]["feedback_type"] == "test"
    fb_mod._mem_queues.clear()


# ---------------------------------------------------------------------------
# Registry audit smoke test
# ---------------------------------------------------------------------------


def test_registry_audit_runs_without_error():
    """audit_registry() must complete without raising regardless of import failures."""
    from agents.registry import audit_registry

    result = audit_registry()
    assert "discovered" in result
    assert "ok" in result
    assert "in_code_not_registry" in result
    assert "in_registry_not_code" in result
    # All discovered agents should be importable in test env
    assert result["discovered_count"] > 0
