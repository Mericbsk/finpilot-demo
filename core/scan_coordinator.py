"""Process-local, opt-in scan jobs with bounded admission and waiter ownership."""

from __future__ import annotations

import hashlib
import inspect
import json
import os
import threading
import time
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from contextvars import ContextVar
from copy import deepcopy
from dataclasses import dataclass, field
from functools import wraps
from typing import Any
from uuid import uuid4

from core import scan_observability


class ScanBusy(RuntimeError):
    """Admission or queue wait exceeds the scan's bounded budget."""


class ScanCancelled(RuntimeError):
    """All waiters left and the job reached a cancellation boundary."""


def enabled() -> bool:
    return os.getenv("FINPILOT_SCAN_COORDINATOR", "0") == "1"


@dataclass
class ScanJob:
    key: str
    function: Callable[[], Any]
    observation: scan_observability.ScanObservation | None = None
    prepare: Callable[[], None] | None = None
    job_id: str = field(default_factory=lambda: uuid4().hex)
    future: Future = field(default_factory=Future)
    cancelled: threading.Event = field(default_factory=threading.Event)
    cancellation_lock: Any = field(default_factory=threading.RLock)
    cancellation_committed: bool = False
    waiters: set[str] = field(default_factory=set)
    created: float = field(default_factory=lambda: time.monotonic())
    started: float | None = None
    queue_deadline: float = 0


_CURRENT_JOB: ContextVar[ScanJob | None] = ContextVar("coordinated_scan_job", default=None)


def current_job() -> ScanJob | None:
    return _CURRENT_JOB.get()


def check_cancelled(job: ScanJob | None = None) -> None:
    job = job if job is not None else current_job()
    if job is not None:
        with job.cancellation_lock:
            if job.cancelled.is_set():
                job.cancellation_committed = True
                raise ScanCancelled("Scan has no remaining waiters")


class ScanHandle:
    def __init__(self, coordinator: ScanCoordinator, job: ScanJob, waiter_id: str) -> None:
        self.coordinator = coordinator
        self.job = job
        self.waiter_id = waiter_id

    @property
    def future(self) -> Future:
        return self.job.future

    def detach(self) -> None:
        self.coordinator.detach(self.job, self.waiter_id)

    def result(self, timeout: float | None = None) -> Any:
        try:
            return deepcopy(self.future.result(timeout=timeout))
        finally:
            self.detach()


class ScanCoordinator:
    def __init__(
        self,
        max_concurrent: int = 1,
        queue_capacity: int = 1,
        queue_wait_seconds: float = 120,
        estimated_job_seconds: float = 480,
        dedupe: bool = True,
        cooperative_cancel: bool = True,
    ) -> None:
        if not 1 <= max_concurrent <= 16 or not 0 <= queue_capacity <= 16:
            raise ValueError("Invalid scan slot/queue capacity")
        if not 0 <= queue_wait_seconds <= 120 or not 0 < estimated_job_seconds <= 600:
            raise ValueError("Invalid scan queue/estimate budget")
        self.max_concurrent = max_concurrent
        self.queue_capacity = queue_capacity
        self.queue_wait_seconds = queue_wait_seconds
        self.estimated_job_seconds = estimated_job_seconds
        self.dedupe = dedupe
        self.cooperative_cancel = cooperative_cancel
        self._lock = threading.RLock()
        self._jobs: dict[str, ScanJob] = {}
        self._by_key: dict[str, ScanJob] = {}
        self._closed = False
        self._pool = ThreadPoolExecutor(max_workers=max_concurrent, thread_name_prefix="scan-job")

    def _estimated_wait(self, now: float) -> float:
        remaining = [
            max(0, self.estimated_job_seconds - (now - job.started))
            for job in self._jobs.values()
            if job.started is not None
        ]
        remaining.extend([0] * (self.max_concurrent - len(remaining)))
        for job in self._jobs.values():
            if job.started is None:
                first = remaining.index(min(remaining))
                remaining[first] += self.estimated_job_seconds
        return min(remaining)

    def submit(
        self,
        key: str,
        function: Callable[[], Any],
        *,
        budget_seconds: float = 600,
        observation: scan_observability.ScanObservation | None = None,
        prepare: Callable[[], None] | None = None,
    ) -> ScanHandle:
        with self._lock:
            if self._closed:
                raise ScanBusy("Scan coordinator is closed")
            existing = self._by_key.get(key) if self.dedupe else None
            if existing is not None:
                with existing.cancellation_lock:
                    if existing.cancellation_committed:
                        existing = None
                    else:
                        existing.cancelled.clear()
            new_job = existing is None
            if existing is not None:
                job = existing
            else:
                if len(self._jobs) >= self.max_concurrent + self.queue_capacity:
                    raise ScanBusy("Scan queue is full; retry later")
                wait = self._estimated_wait(time.monotonic())
                if wait > self.queue_wait_seconds or wait + self.estimated_job_seconds > min(
                    600, budget_seconds
                ):
                    raise ScanBusy("Scan queue exceeds time budget; retry later")
                job_observation = (
                    scan_observability.ScanObservation(observation.caller, observation.symbols)
                    if observation is not None
                    else None
                )
                job = ScanJob(key, function, observation=job_observation, prepare=prepare)
                if job_observation is not None:
                    job.job_id = job_observation.job_id
                    job_observation.coordinator_version = 1
                job.queue_deadline = (
                    job.created
                    + min(
                        self.queue_wait_seconds, max(0, budget_seconds - self.estimated_job_seconds)
                    )
                    if len(self._jobs) >= self.max_concurrent
                    else float("inf")
                )
                self._jobs[job.job_id] = job
                self._by_key[key] = job
            if observation is not None and job.observation is not None:
                observation.shared_job = job.observation
                observation.job_id = job.job_id
            waiter_id = uuid4().hex
            job.waiters.add(waiter_id)
            handle = ScanHandle(self, job, waiter_id)
            if new_job:
                self._pool.submit(self._run, job)
            return handle

    def detach(self, job: ScanJob, waiter_id: str) -> None:
        with self._lock:
            job.waiters.discard(waiter_id)
            if self.cooperative_cancel and not job.waiters:
                with job.cancellation_lock:
                    job.cancelled.set()

    def _run(self, job: ScanJob) -> None:
        token = _CURRENT_JOB.set(job)
        result = None
        error = None
        observation_token = None
        try:
            with self._lock:
                job.started = time.monotonic()
            if job.observation is not None:
                job.observation.queue_wait_s = round(job.started - job.created, 6)
            if job.started > job.queue_deadline:
                raise ScanBusy("Scan queue wait expired; retry later")
            check_cancelled()
            if job.prepare is not None:
                job.prepare()
            if job.observation is not None:
                observation_token = scan_observability._CURRENT_SCAN.set(job.observation)
                job.observation.start_job()
            result = job.function()
            check_cancelled()
        except BaseException as exc:
            error = exc
        finally:
            if job.observation is not None:
                outcome = (
                    "client_gone"
                    if isinstance(error, ScanCancelled)
                    else (
                        "error"
                        if error is not None or getattr(result, "success", True) is False
                        else "ok"
                    )
                )
                job.observation.end_job(
                    outcome,
                    type(error).__name__ if error else None,
                    event="job_finished"
                    if job.observation.job_started is not None
                    else "job_skipped",
                )
            if observation_token is not None:
                scan_observability._CURRENT_SCAN.reset(observation_token)
            _CURRENT_JOB.reset(token)
            with self._lock:
                self._jobs.pop(job.job_id, None)
                if self._by_key.get(job.key) is job:
                    self._by_key.pop(job.key, None)
        if error is None:
            job.future.set_result(result)
        else:
            job.future.set_exception(error)

    def shutdown(self) -> None:
        with self._lock:
            self._closed = True
        self._pool.shutdown(wait=True)


_COORDINATOR: ScanCoordinator | None = None
_COORDINATOR_LOCK = threading.Lock()


def get_coordinator() -> ScanCoordinator:
    global _COORDINATOR
    with _COORDINATOR_LOCK:
        if _COORDINATOR is None:
            _COORDINATOR = ScanCoordinator(
                max_concurrent=int(os.getenv("FINPILOT_SCAN_MAX_CONCURRENT", "1")),
                queue_capacity=int(os.getenv("FINPILOT_SCAN_QUEUE_CAPACITY", "1")),
                queue_wait_seconds=float(os.getenv("FINPILOT_SCAN_QUEUE_WAIT_S", "120")),
                estimated_job_seconds=float(os.getenv("FINPILOT_SCAN_ESTIMATED_JOB_S", "480")),
                dedupe=os.getenv("FINPILOT_SCAN_DEDUPE", "1") == "1",
                cooperative_cancel=os.getenv("FINPILOT_SCAN_COOP_CANCEL", "1") == "1",
            )
        return _COORDINATOR


def make_key(operation: str, symbols: list[str], parameters: dict, scope: tuple) -> str:
    from scanner import config, evaluate

    core_settings = config._core_settings
    state = {
        "settings": config.SETTINGS,
        "scanner": core_settings.scanner.model_dump(mode="json") if core_settings else None,
        "drl": core_settings.drl.model_dump(mode="json") if core_settings else None,
        "market": evaluate.CURRENT_MARKET_STATUS,
        "strategies": evaluate.STRATEGY_PARAMS,
    }
    flags = {
        name: value
        for name, value in os.environ.items()
        if name.startswith("FINPILOT_")
        and not any(word in name for word in ("SECRET", "TOKEN", "PASSWORD", "KEY", "CREDENTIAL"))
    }
    payload = {
        "operation": operation,
        "symbols": sorted({symbol.strip().upper() for symbol in symbols}),
        "input_symbols": symbols,
        "parameters": parameters,
        "scope": scope,
        "state": state,
        "flags": flags,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def submit_scan(
    key: str,
    function: Callable[[], Any],
    observation: scan_observability.ScanObservation | None,
    *,
    budget_seconds: float = 600,
) -> ScanHandle:
    from scanner.data_fetcher import reset_yf_fetch_count

    return get_coordinator().submit(
        key,
        function,
        observation=observation,
        prepare=reset_yf_fetch_count,
        budget_seconds=budget_seconds,
    )


def coordinate_scan(function: Callable) -> Callable:
    signature = inspect.signature(function)

    @wraps(function)
    def coordinated(*args, **kwargs):
        if not enabled() or current_job() is not None:
            return function(*args, **kwargs)
        bound = signature.bind(*args, **kwargs)
        bound.apply_defaults()
        symbols = bound.arguments["symbols"]
        parameters = dict(bound.arguments)
        parameters.pop("symbols")
        callback = parameters.get("progress_callback")
        parameters["progress_callback"] = id(callback) if callback is not None else None
        observation = scan_observability.current_scan()
        if observation is None and scan_observability.enabled():
            observation = scan_observability.ScanObservation("script", len(symbols))
        caller = observation.caller if observation else "script"
        key = make_key("evaluate", symbols, parameters, (caller,))
        handle = submit_scan(key, lambda: function(*args, **kwargs), observation)
        return handle.result(timeout=600)

    return coordinated
