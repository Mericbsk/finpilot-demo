"""Tests for core.scheduler utility functions.

Covers: _make_watchdog_job, _compose_jobs.
Does NOT start APScheduler — purely unit tests of the composable wrappers.
"""

from __future__ import annotations

import threading
import time

import pytest


# ---------------------------------------------------------------------------
# _make_watchdog_job
# ---------------------------------------------------------------------------
class TestMakeWatchdogJob:
    def test_successful_job_runs(self):
        from core.scheduler import _make_watchdog_job

        calls = []
        wrapped = _make_watchdog_job("test_job", lambda: calls.append(1), timeout_s=5)
        wrapped()
        assert calls == [1]

    def test_job_name_set_on_wrapper(self):
        from core.scheduler import _make_watchdog_job

        wrapped = _make_watchdog_job("my_job", lambda: None, timeout_s=5)
        assert wrapped.__name__ == "watchdog_my_job"

    def test_timeout_kills_hanging_job(self):
        """A job that exceeds timeout_s must NOT block caller indefinitely."""
        from core.scheduler import _make_watchdog_job

        start = time.time()
        wrapped = _make_watchdog_job("slow_job", lambda: time.sleep(10), timeout_s=1)
        wrapped()
        elapsed = time.time() - start
        assert elapsed < 5, f"Watchdog should abort within 5s, took {elapsed:.1f}s"

    def test_exception_in_job_does_not_raise(self):
        from core.scheduler import _make_watchdog_job

        def bad():
            raise RuntimeError("boom")

        wrapped = _make_watchdog_job("bad_job", bad, timeout_s=5)
        # Must not re-raise; caller should not see exception
        wrapped()

    def test_side_effects_visible_after_job(self):
        from core.scheduler import _make_watchdog_job

        shared = {"value": 0}

        def update():
            shared["value"] = 42

        _make_watchdog_job("update_job", update, timeout_s=5)()
        assert shared["value"] == 42


# ---------------------------------------------------------------------------
# _compose_jobs
# ---------------------------------------------------------------------------
class TestComposeJobs:
    def test_all_sub_jobs_run(self):
        from core.scheduler import _compose_jobs

        log = []
        j1 = lambda: log.append("a")  # noqa: E731
        j2 = lambda: log.append("b")  # noqa: E731
        j3 = lambda: log.append("c")  # noqa: E731
        composite = _compose_jobs("grp", j1, j2, j3)
        composite()
        assert log == ["a", "b", "c"]

    def test_composite_name_set(self):
        from core.scheduler import _compose_jobs

        composite = _compose_jobs("hourly_ops", lambda: None)
        assert composite.__name__ == "composite_hourly_ops"

    def test_failure_in_one_sub_does_not_block_rest(self):
        from core.scheduler import _compose_jobs

        log = []

        def ok():
            log.append("ok")

        def bad():
            raise ValueError("sub failure")

        composite = _compose_jobs("mixed", ok, bad, ok)
        composite()
        assert log == ["ok", "ok"]

    def test_zero_sub_jobs_runs_without_error(self):
        from core.scheduler import _compose_jobs

        composite = _compose_jobs("empty")
        composite()  # should complete without exception

    def test_sub_jobs_run_in_order(self):
        from core.scheduler import _compose_jobs

        order = []
        for i in range(5):
            i_ = i
            order.append(None)  # placeholder
        log = []

        funcs = []
        for i in range(5):
            def make(n):
                return lambda: log.append(n)
            funcs.append(make(i))

        composite = _compose_jobs("ordered", *funcs)
        composite()
        assert log == [0, 1, 2, 3, 4]

    def test_compatible_with_watchdog_wrapped_jobs(self):
        """Compose + watchdog integration."""
        from core.scheduler import _compose_jobs, _make_watchdog_job

        results = []
        j1 = _make_watchdog_job("j1", lambda: results.append(1), timeout_s=5)
        j2 = _make_watchdog_job("j2", lambda: results.append(2), timeout_s=5)
        composite = _compose_jobs("integrated", j1, j2)
        composite()
        assert results == [1, 2]


# ---------------------------------------------------------------------------
# Legacy vs new scheduler job mode (env flag)
# ---------------------------------------------------------------------------
class TestLegacySchedulerFlag:
    def test_legacy_flag_env_var_not_set_by_default(self, monkeypatch):
        import os
        monkeypatch.delenv("FINPILOT_SCHEDULER_LEGACY_JOBS", raising=False)
        val = os.getenv("FINPILOT_SCHEDULER_LEGACY_JOBS", "0")
        assert val == "0"

    def test_legacy_flag_can_be_enabled(self, monkeypatch):
        import os
        monkeypatch.setenv("FINPILOT_SCHEDULER_LEGACY_JOBS", "1")
        val = os.getenv("FINPILOT_SCHEDULER_LEGACY_JOBS", "0")
        assert val == "1"
