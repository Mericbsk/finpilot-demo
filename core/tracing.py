"""FinPilot Tracing — lightweight OpenTelemetry-compatible span wrapper.

Wraps agent execution with structured spans for observability.
Falls back to simple logging when OpenTelemetry is not installed.

Usage::

    from core.tracing import trace_agent, get_tracer

    # As a context manager
    with trace_agent("scanner", symbols=["AAPL"]) as span:
        result = ScannerAgent().run(ctx)
        span.set_attribute("symbols_found", len(result.data or {}))

    # As a decorator
    @trace_agent_call("scanner")
    def run_scanner(ctx):
        return ScannerAgent().run(ctx)
"""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from typing import Any, Generator

logger = logging.getLogger(__name__)

# Try to import OpenTelemetry — graceful fallback if not installed
_otel_available = False
_tracer = None

try:
    from opentelemetry import trace as otel_trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

    _provider = TracerProvider()
    _provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    otel_trace.set_tracer_provider(_provider)
    _tracer = otel_trace.get_tracer("finpilot.agents")
    _otel_available = True
    logger.info("Tracing: OpenTelemetry initialized (ConsoleSpanExporter)")
except ImportError:
    logger.debug("Tracing: OpenTelemetry not available — using log-based fallback")


class _FallbackSpan:
    """No-op span used when OpenTelemetry is unavailable."""

    def __init__(self, name: str, **attrs: Any) -> None:
        self.name = name
        self._attrs = dict(attrs)
        self._start = time.perf_counter()

    def set_attribute(self, key: str, value: Any) -> None:
        self._attrs[key] = value

    def set_status_ok(self) -> None:
        pass

    def set_status_error(self, description: str) -> None:
        self._attrs["error"] = description

    def end(self) -> None:
        dur = (time.perf_counter() - self._start) * 1000
        logger.debug(
            "SPAN [%s] %.1fms attrs=%s",
            self.name,
            dur,
            self._attrs,
        )


@contextmanager
def trace_agent(
    agent_name: str,
    task: str = "",
    symbols: list[str] | None = None,
    **extra_attrs: Any,
) -> Generator[Any, None, None]:
    """Context manager that wraps an agent execution in a trace span.

    Example::
        with trace_agent("scanner", task="full", symbols=["AAPL"]) as span:
            result = ScannerAgent().run(ctx)
            span.set_attribute("result_count", len(result.data or {}))
    """
    attrs: dict[str, Any] = {
        "agent": agent_name,
        "task": task,
        "symbols": ",".join(symbols or []),
        **extra_attrs,
    }

    if _otel_available and _tracer is not None:
        from opentelemetry import trace as otel_trace

        with _tracer.start_as_current_span(f"agent.{agent_name}") as span:
            for k, v in attrs.items():
                span.set_attribute(k, str(v))
            t0 = time.perf_counter()
            try:
                yield span
                span.set_attribute("duration_ms", round((time.perf_counter() - t0) * 1000, 1))
            except Exception as exc:
                span.set_attribute("error", str(exc))
                span.set_status(otel_trace.StatusCode.ERROR, str(exc))
                raise
    else:
        span = _FallbackSpan(f"agent.{agent_name}", **attrs)
        t0 = time.perf_counter()
        try:
            yield span
            span.set_attribute("duration_ms", round((time.perf_counter() - t0) * 1000, 1))
        except Exception as exc:
            span.set_status_error(str(exc))
            raise
        finally:
            span.end()


def record_cycle_trace(
    cycle_num: int,
    step: str,
    status: str,
    duration_ms: float,
    details: str = "",
) -> None:
    """Record a scheduler cycle step as a trace event (log-level)."""
    logger.info(
        "CYCLE[%d] %s → %s (%.1fms) %s",
        cycle_num,
        step,
        status,
        duration_ms,
        details,
    )


def get_tracer() -> Any:
    """Return the OpenTelemetry tracer if available, else None."""
    return _tracer
