"""Observation-only scan lifecycle records; coordination remains unchanged."""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import UTC, datetime
from functools import wraps
from pathlib import Path
from typing import Any, ParamSpec, TypeVar
from uuid import uuid4

_JOB_LOCK = threading.Lock()
_LOG_LOCK = threading.Lock()
_ACTIVE_JOBS: dict[str, ScanObservation] = {}
_COUNTER_GENERATION = 0
_Parameters = ParamSpec("_Parameters")
_ReturnT = TypeVar("_ReturnT")
logger = logging.getLogger(__name__)


def enabled() -> bool:
    return os.getenv("FINPILOT_SCAN_OBSERVABILITY", "1") == "1"


def note_counter_reset() -> None:
    global _COUNTER_GENERATION
    with _JOB_LOCK:
        _COUNTER_GENERATION += 1
        for observation in _ACTIVE_JOBS.values():
            observation.counters_unreliable = True


class ScanObservation:
    """Track actual worker lifetime independently from its HTTP waiter."""

    def __init__(self, caller: str, symbols: int, request_id: str | None = None) -> None:
        self.job_id = uuid4().hex
        self.request_id = request_id
        self.caller = caller
        self.symbols = symbols
        self.started = time.perf_counter()
        self.job_started: float | None = None
        self.job_finished = False
        self.active_jobs_at_start: int | None = None
        self.active_jobs_at_end: int | None = None
        self.peak_active_jobs = 0
        self.counters_unreliable = False
        self.counter_generation = 0
        self.client_gone = False
        self.request_outcome: str | None = None
        self.job_outcome: str | None = None
        self.timing: dict[str, Any] = {}
        self.shared_job: ScanObservation | None = None
        self.coordinator_version: int | None = None
        self.queue_wait_s: float | None = None

    def start_job(self) -> None:
        global _COUNTER_GENERATION
        with _JOB_LOCK:
            _COUNTER_GENERATION += 1
            self.job_started = time.perf_counter()
            self.counter_generation = _COUNTER_GENERATION
            _ACTIVE_JOBS[self.job_id] = self
            self.active_jobs_at_start = len(_ACTIVE_JOBS)
            for observation in _ACTIVE_JOBS.values():
                observation.peak_active_jobs = max(observation.peak_active_jobs, len(_ACTIVE_JOBS))
        append_scan_timing_log(self.fields("job_started"), self.symbols)

    def end_job(
        self, outcome: str, error_type: str | None = None, *, event: str = "job_finished"
    ) -> None:
        with _JOB_LOCK:
            self.active_jobs_at_end = len(_ACTIVE_JOBS)
            self.job_finished = True
            self.job_outcome = outcome
            _ACTIVE_JOBS.pop(self.job_id, None)
        record = {**self.timing, **self.fields(event, outcome)}
        record["job_s"] = round(time.perf_counter() - (self.job_started or self.started), 6)
        record["error_type"] = error_type
        append_scan_timing_log(record, self.symbols)

    def fields(self, event: str, outcome: str | None = None) -> dict[str, Any]:
        if self.shared_job is not None:
            record = self.shared_job.fields(event, outcome)
            record.update(
                request_id=self.request_id, caller=self.caller, request_outcome=self.request_outcome
            )
            return record
        with _JOB_LOCK:
            return {
                "observation_version": 1,
                "coordinator_version": self.coordinator_version,
                "queue_wait_s": self.queue_wait_s,
                "process_id": os.getpid(),
                "active_jobs_scope": "process",
                "job_id": self.job_id,
                "request_id": self.request_id,
                "caller": self.caller,
                "event": event,
                "outcome": outcome,
                "request_outcome": self.request_outcome,
                "job_outcome": self.job_outcome,
                "symbols": self.symbols,
                "active_jobs_at_start": self.active_jobs_at_start,
                "active_jobs_at_end": self.active_jobs_at_end,
                "active_jobs_at_event": len(_ACTIVE_JOBS),
                "peak_active_jobs": self.peak_active_jobs,
                "worker_started": self.job_started is not None,
                "worker_finished": self.job_finished,
                "counters_unreliable": (
                    self.job_started is None
                    or self.counters_unreliable
                    or self.peak_active_jobs > 1
                    or self.counter_generation != _COUNTER_GENERATION
                ),
            }

    def mark_client_gone(self) -> None:
        with _JOB_LOCK:
            self.client_gone = True
        append_scan_timing_log(self.fields("request_disconnected", "client_gone"), self.symbols)

    def finish_request(
        self, outcome: str, error_type: str | None = None, *, event: str = "request_finished"
    ) -> None:
        with _JOB_LOCK:
            self.request_outcome = "client_gone" if self.client_gone else outcome
        record = dict(self.shared_job.timing if self.shared_job is not None else self.timing)
        record.update(self.fields(event, self.request_outcome))
        record["request_s"] = round(time.perf_counter() - self.started, 6)
        record["error_type"] = error_type
        append_scan_timing_log(record, self.symbols)


_CURRENT_SCAN: ContextVar[ScanObservation | None] = ContextVar("scan_observation", default=None)


@contextmanager
def scan_context(observation: ScanObservation) -> Iterator[None]:
    token = _CURRENT_SCAN.set(observation)
    try:
        yield
    finally:
        _CURRENT_SCAN.reset(token)


def current_scan() -> ScanObservation | None:
    return _CURRENT_SCAN.get()


def call_with_context(
    observation: ScanObservation | None,
    function: Callable[_Parameters, _ReturnT],
    *args: _Parameters.args,
    **kwargs: _Parameters.kwargs,
) -> _ReturnT:
    if observation is None:
        return function(*args, **kwargs)
    with scan_context(observation):
        return function(*args, **kwargs)


def observe_scan(
    function: Callable[_Parameters, _ReturnT],
) -> Callable[_Parameters, _ReturnT]:
    """Observe every evaluator caller without changing work or exceptions."""

    @wraps(function)
    def observed(*args: _Parameters.args, **kwargs: _Parameters.kwargs) -> _ReturnT:
        from core.scan_coordinator import current_job

        if current_job() is not None:
            return function(*args, **kwargs)
        if not enabled():
            return function(*args, **kwargs)
        observation = current_scan()
        if observation is None:
            symbols = kwargs.get("symbols", args[0] if args else [])
            observation = ScanObservation("script", len(symbols))
        with scan_context(observation):
            observation.start_job()
            outcome = "ok"
            error_type = None
            try:
                return function(*args, **kwargs)
            except BaseException as exc:
                outcome = "error"
                error_type = type(exc).__name__
                raise
            finally:
                observation.end_job(outcome, error_type)

    return observed


def append_scan_timing_log(timing: dict[str, Any], universe: int) -> None:
    """Share the existing best-effort JSONL writer across all scanner callers."""
    try:
        export_dir = Path(os.getenv("FINPILOT_DIST_DIR", "data/distribution"))
        export_dir.mkdir(parents=True, exist_ok=True)
        now = datetime.now(tz=UTC)
        record = {
            "ts": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
            "universe": universe,
            **timing,
        }
        with _LOG_LOCK, (export_dir / "scan_timing.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    except Exception as exc:
        logger.debug("scan timing log skipped: %s", type(exc).__name__)
