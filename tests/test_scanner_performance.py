from __future__ import annotations

from scanner import performance


def test_stage_timing_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("FINPILOT_SCAN_STAGE_TIMING", raising=False)
    performance.reset()

    with performance.timer("test.stage", count=1):
        pass

    assert performance.snapshot() == []


def test_stage_timing_records_opt_in_events(monkeypatch):
    monkeypatch.setenv("FINPILOT_SCAN_STAGE_TIMING", "1")
    performance.reset()

    with performance.timer("test.stage", count=3, timeframe="1d", path="fixture"):
        pass

    events = performance.snapshot()
    assert len(events) == 1
    assert events[0]["stage"] == "test.stage"
    assert events[0]["count"] == 3
    assert events[0]["timeframe"] == "1d"
    assert events[0]["path"] == "fixture"
    assert events[0]["outcome"] == "ok"
    assert events[0]["elapsed_s"] >= 0


def test_stage_timing_records_error_outcome(monkeypatch):
    monkeypatch.setenv("FINPILOT_SCAN_STAGE_TIMING", "1")
    performance.reset()

    try:
        with performance.timer("test.error"):
            raise ValueError("fixture")
    except ValueError:
        pass

    assert performance.snapshot()[0]["outcome"] == "error"
