"""
FinPilot Monitoring & Observability
===================================

Merkezi monitoring altyapısı:
- Prometheus metrikleri
- Sentry error tracking
- MLflow entegrasyonu
- Performance tracking
- Health checks

Kullanım:
    from core.monitoring import metrics, health_check, sentry_client

    # Metrik kaydet
    metrics.signals_generated.inc()
    metrics.scan_duration.observe(1.23)

    # Error tracking
    sentry_client.capture_exception(error)

    # Health check
    status = health_check.run()

Author: FinPilot Team
Version: 1.1.0
"""

from __future__ import annotations

import functools
import os
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, ParamSpec, TypeVar

P = ParamSpec("P")
T = TypeVar("T")


# =============================================================================
# SENTRY ERROR TRACKING
# =============================================================================


class SentryClient:
    """
    Sentry error tracking integration.

    Initializes Sentry SDK if SENTRY_DSN environment variable is set.
    Provides methods for capturing exceptions and messages.

    Usage:
        from core.monitoring import sentry_client

        # Initialize (call once at app startup)
        sentry_client.init()

        # Capture exception
        try:
            risky_operation()
        except Exception as e:
            sentry_client.capture_exception(e)

        # Capture message
        sentry_client.capture_message("User logged in", level="info")

        # Set user context
        sentry_client.set_user({"id": "123", "email": "user@example.com"})

        # Add breadcrumb
        sentry_client.add_breadcrumb(
            category="scan",
            message="Started scanning AAPL",
            level="info"
        )
    """

    def __init__(self) -> None:
        self._initialized = False
        self._enabled = False
        self._sentry = None

    def init(
        self,
        dsn: Optional[str] = None,
        environment: Optional[str] = None,
        release: Optional[str] = None,
        traces_sample_rate: float = 0.1,
        profiles_sample_rate: float = 0.1,
    ) -> bool:
        """
        Initialize Sentry SDK.

        Args:
            dsn: Sentry DSN. If not provided, reads from SENTRY_DSN env var.
            environment: Environment name (production, staging, development).
            release: Release version string.
            traces_sample_rate: Performance monitoring sample rate (0.0 to 1.0).
            profiles_sample_rate: Profiling sample rate (0.0 to 1.0).

        Returns:
            True if initialization succeeded, False otherwise.
        """
        if self._initialized:
            return self._enabled

        self._initialized = True
        dsn = dsn or os.getenv("SENTRY_DSN")

        if not dsn:
            self._enabled = False
            import logging

            logging.getLogger(__name__).info(
                "Sentry DSN not configured. Error tracking disabled. "
                "Set SENTRY_DSN environment variable to enable."
            )
            return False

        try:
            import sentry_sdk
            from sentry_sdk.integrations.logging import LoggingIntegration

            # Configure logging integration
            logging_integration = LoggingIntegration(
                level=None,  # Capture info and above as breadcrumbs
                event_level=None,  # Don't send logs as events (use capture_* methods)
            )

            sentry_sdk.init(
                dsn=dsn,
                environment=environment or os.getenv("SENTRY_ENVIRONMENT", "development"),
                release=release or os.getenv("SENTRY_RELEASE", "finpilot@1.1.0"),
                traces_sample_rate=traces_sample_rate,
                profiles_sample_rate=profiles_sample_rate,
                integrations=[logging_integration],
                # Performance monitoring
                enable_tracing=True,
                # Attach stack locals for better debugging
                attach_stacktrace=True,
                # Send PII (personally identifiable information)
                send_default_pii=False,
            )

            self._sentry = sentry_sdk
            self._enabled = True
            return True

        except ImportError:
            self._enabled = False
            return False
        except Exception:
            self._enabled = False
            return False

    def is_enabled(self) -> bool:
        """Check if Sentry is enabled."""
        return self._enabled

    def capture_exception(
        self,
        error: Optional[BaseException] = None,
        **kwargs: Any,
    ) -> Optional[str]:
        """
        Capture an exception and send to Sentry.

        Args:
            error: Exception to capture. If None, captures current exception.
            **kwargs: Additional context to attach.

        Returns:
            Event ID if captured, None otherwise.
        """
        if not self._enabled or not self._sentry:
            return None

        with self._sentry.push_scope() as scope:
            for key, value in kwargs.items():
                scope.set_extra(key, value)
            return self._sentry.capture_exception(error)

    def capture_message(
        self,
        message: str,
        level: str = "info",
        **kwargs: Any,
    ) -> Optional[str]:
        """
        Capture a message and send to Sentry.

        Args:
            message: Message to capture.
            level: Log level (debug, info, warning, error, fatal).
            **kwargs: Additional context to attach.

        Returns:
            Event ID if captured, None otherwise.
        """
        if not self._enabled or not self._sentry:
            return None

        with self._sentry.push_scope() as scope:
            for key, value in kwargs.items():
                scope.set_extra(key, value)
            return self._sentry.capture_message(message, level=level)  # type: ignore[arg-type]

    def set_user(self, user_info: Dict[str, Any]) -> None:
        """
        Set user context for Sentry events.

        Args:
            user_info: Dict with user info (id, email, username, etc.)
        """
        if not self._enabled or not self._sentry:
            return

        self._sentry.set_user(user_info)

    def set_tag(self, key: str, value: str) -> None:
        """Set a tag that will be attached to all events."""
        if not self._enabled or not self._sentry:
            return

        self._sentry.set_tag(key, value)

    def set_context(self, name: str, context: Dict[str, Any]) -> None:
        """Set additional context for events."""
        if not self._enabled or not self._sentry:
            return

        self._sentry.set_context(name, context)

    def add_breadcrumb(
        self,
        message: str,
        category: str = "default",
        level: str = "info",
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a breadcrumb for debugging.

        Breadcrumbs are stored and attached to the next event.

        Args:
            message: Breadcrumb message.
            category: Category (e.g., "scan", "auth", "api").
            level: Level (debug, info, warning, error).
            data: Additional data to attach.
        """
        if not self._enabled or not self._sentry:
            return

        self._sentry.add_breadcrumb(
            message=message,
            category=category,
            level=level,
            data=data or {},
        )

    @contextmanager
    def start_transaction(
        self,
        name: str,
        op: str = "task",
        **kwargs: Any,
    ):
        """
        Start a performance transaction.

        Usage:
            with sentry_client.start_transaction("scan_portfolio", op="scan"):
                # Long running operation
                perform_scan()
        """
        if not self._enabled or not self._sentry:
            yield None
            return

        with self._sentry.start_transaction(name=name, op=op, **kwargs) as transaction:
            yield transaction

    def flush(self, timeout: float = 2.0) -> None:
        """Flush pending events to Sentry."""
        if not self._enabled or not self._sentry:
            return

        self._sentry.flush(timeout=timeout)


# Global Sentry client instance
sentry_client = SentryClient()


# =============================================================================
# ERROR TRACKING DECORATOR
# =============================================================================


def track_errors_sentry(
    capture: bool = True,
    reraise: bool = True,
    tags: Optional[Dict[str, str]] = None,
):
    """
    Decorator to automatically capture exceptions to Sentry.

    Args:
        capture: Whether to capture the exception to Sentry.
        reraise: Whether to re-raise the exception after capturing.
        tags: Additional tags to attach to the event.

    Usage:
        @track_errors_sentry(tags={"component": "scanner"})
        def risky_function():
            ...
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if capture and sentry_client.is_enabled() and sentry_client._sentry is not None:
                    with sentry_client._sentry.push_scope() as scope:
                        scope.set_extra("function", func.__name__)
                        scope.set_extra("args", str(args)[:500])
                        scope.set_extra("kwargs", str(kwargs)[:500])
                        if tags:
                            for key, value in tags.items():
                                scope.set_tag(key, value)
                        sentry_client.capture_exception(e)

                if reraise:
                    raise
                return None  # type: ignore

        return wrapper

    return decorator


# =============================================================================
# METRICS TYPES (Prometheus-compatible)
# =============================================================================


class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricValue:
    """Single metric value with labels."""

    value: float
    labels: dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class Counter:
    """
    Prometheus-style counter metric.
    Only goes up (or resets).
    """

    def __init__(self, name: str, description: str, labels: Optional[list[str]] = None):
        self.name = name
        self.description = description
        self.label_names = labels or []
        self._values: dict[tuple, float] = {}
        self._lock = threading.Lock()

    def _key(self, labels: dict[str, str]) -> tuple:
        return tuple(sorted(labels.items()))

    def inc(self, value: float = 1, **labels: str) -> None:
        """Increment counter."""
        with self._lock:
            key = self._key(labels)
            self._values[key] = self._values.get(key, 0) + value

    def get(self, **labels: str) -> float:
        """Get current counter value."""
        with self._lock:
            key = self._key(labels)
            return self._values.get(key, 0)

    def reset(self) -> None:
        """Reset all values."""
        with self._lock:
            self._values.clear()

    def collect(self) -> list[MetricValue]:
        """Collect all metric values."""
        with self._lock:
            return [MetricValue(value=v, labels=dict(k)) for k, v in self._values.items()]


class Gauge:
    """
    Prometheus-style gauge metric.
    Can go up and down.
    """

    def __init__(self, name: str, description: str, labels: Optional[list[str]] = None):
        self.name = name
        self.description = description
        self.label_names = labels or []
        self._values: dict[tuple, float] = {}
        self._lock = threading.Lock()

    def _key(self, labels: dict[str, str]) -> tuple:
        return tuple(sorted(labels.items()))

    def set(self, value: float, **labels: str) -> None:
        """Set gauge value."""
        with self._lock:
            key = self._key(labels)
            self._values[key] = value

    def inc(self, value: float = 1, **labels: str) -> None:
        """Increment gauge."""
        with self._lock:
            key = self._key(labels)
            self._values[key] = self._values.get(key, 0) + value

    def dec(self, value: float = 1, **labels: str) -> None:
        """Decrement gauge."""
        with self._lock:
            key = self._key(labels)
            self._values[key] = self._values.get(key, 0) - value

    def get(self, **labels: str) -> float:
        """Get current gauge value."""
        with self._lock:
            key = self._key(labels)
            return self._values.get(key, 0)

    def collect(self) -> list[MetricValue]:
        """Collect all metric values."""
        with self._lock:
            return [MetricValue(value=v, labels=dict(k)) for k, v in self._values.items()]


class Histogram:
    """
    Prometheus-style histogram metric.
    Tracks distributions of values.
    """

    DEFAULT_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, float("inf"))

    def __init__(
        self,
        name: str,
        description: str,
        buckets: Optional[tuple[float, ...]] = None,
        labels: Optional[list[str]] = None,
    ):
        self.name = name
        self.description = description
        self.buckets = buckets or self.DEFAULT_BUCKETS
        self.label_names = labels or []
        self._values: dict[tuple, list[float]] = {}
        self._lock = threading.Lock()

    def _key(self, labels: dict[str, str]) -> tuple:
        return tuple(sorted(labels.items()))

    def observe(self, value: float, **labels: str) -> None:
        """Observe a value."""
        with self._lock:
            key = self._key(labels)
            if key not in self._values:
                self._values[key] = []
            self._values[key].append(value)

    @contextmanager
    def time(self, **labels: str):
        """Context manager to measure execution time."""
        start = time.perf_counter()
        try:
            yield
        finally:
            self.observe(time.perf_counter() - start, **labels)

    def get_stats(self, **labels: str) -> dict[str, float]:
        """Get histogram statistics."""
        with self._lock:
            key = self._key(labels)
            values = self._values.get(key, [])

            if not values:
                return {"count": 0}

            import statistics

            return {
                "count": len(values),
                "sum": sum(values),
                "min": min(values),
                "max": max(values),
                "mean": statistics.mean(values),
                "median": statistics.median(values),
            }

    def collect(self) -> list[dict[str, Any]]:
        """Collect histogram data."""
        result = []
        with self._lock:
            for key, values in self._values.items():
                bucket_counts = {}
                for bucket in self.buckets:
                    bucket_counts[bucket] = sum(1 for v in values if v <= bucket)

                result.append(
                    {
                        "labels": dict(key),
                        "buckets": bucket_counts,
                        "count": len(values),
                        "sum": sum(values),
                    }
                )
        return result


# =============================================================================
# METRICS REGISTRY
# =============================================================================


class MetricsRegistry:
    """
    Central metrics registry.

    Pre-defined metrics for FinPilot:
    - Scanner metrics
    - DRL metrics
    - Auth metrics
    - System metrics
    """

    def __init__(self):
        self._enabled = False
        self._metrics: dict[str, Counter | Gauge | Histogram] = {}

        # =====================================================================
        # SCANNER METRICS
        # =====================================================================

        self.scans_total = self._register(
            Counter(
                "finpilot_scans_total",
                "Total number of scans performed",
                labels=["scan_type"],
            )
        )

        self.signals_generated = self._register(
            Counter(
                "finpilot_signals_generated_total",
                "Total signals generated",
                labels=["signal_type", "ticker"],
            )
        )

        self.scan_duration = self._register(
            Histogram(
                "finpilot_scan_duration_seconds",
                "Scan duration in seconds",
                buckets=(0.1, 0.5, 1, 2, 5, 10, 30, 60, 120),
                labels=["scan_type"],
            )
        )

        self.tickers_scanned = self._register(
            Gauge(
                "finpilot_tickers_scanned",
                "Number of tickers scanned in last run",
            )
        )

        # =====================================================================
        # DRL METRICS
        # =====================================================================

        self.training_episodes = self._register(
            Counter(
                "finpilot_training_episodes_total",
                "Total training episodes",
                labels=["algorithm"],
            )
        )

        self.training_reward = self._register(
            Gauge(
                "finpilot_training_reward",
                "Latest training reward",
                labels=["algorithm", "ticker"],
            )
        )

        self.model_inference_duration = self._register(
            Histogram(
                "finpilot_model_inference_seconds",
                "Model inference duration",
                buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1),
                labels=["model_name"],
            )
        )

        self.backtest_sharpe = self._register(
            Gauge(
                "finpilot_backtest_sharpe_ratio",
                "Backtest Sharpe ratio",
                labels=["ticker", "strategy"],
            )
        )

        self.backtest_return = self._register(
            Gauge(
                "finpilot_backtest_total_return",
                "Backtest total return percentage",
                labels=["ticker", "strategy"],
            )
        )

        # =====================================================================
        # AUTH METRICS
        # =====================================================================

        self.login_attempts = self._register(
            Counter(
                "finpilot_login_attempts_total",
                "Total login attempts",
                labels=["status"],  # success, failure
            )
        )

        self.active_sessions = self._register(
            Gauge(
                "finpilot_active_sessions",
                "Number of active user sessions",
            )
        )

        self.registrations = self._register(
            Counter(
                "finpilot_registrations_total",
                "Total user registrations",
            )
        )

        # =====================================================================
        # API METRICS
        # =====================================================================

        self.api_requests = self._register(
            Counter(
                "finpilot_api_requests_total",
                "Total API requests",
                labels=["endpoint", "status_code"],
            )
        )

        self.api_latency = self._register(
            Histogram(
                "finpilot_api_latency_seconds",
                "API request latency",
                labels=["endpoint"],
            )
        )

        self.external_api_calls = self._register(
            Counter(
                "finpilot_external_api_calls_total",
                "External API calls (polygon, yfinance)",
                labels=["provider", "status"],
            )
        )

        # =====================================================================
        # CACHE METRICS
        # =====================================================================

        self.cache_hits = self._register(
            Counter(
                "finpilot_cache_hits_total",
                "Cache hits",
                labels=["cache_layer"],  # l1, l2
            )
        )

        self.cache_misses = self._register(
            Counter(
                "finpilot_cache_misses_total",
                "Cache misses",
                labels=["cache_layer"],
            )
        )

        self.cache_size = self._register(
            Gauge(
                "finpilot_cache_size",
                "Number of items in cache",
                labels=["cache_layer"],
            )
        )

        # =====================================================================
        # SYSTEM METRICS
        # =====================================================================

        self.errors_total = self._register(
            Counter(
                "finpilot_errors_total",
                "Total errors",
                labels=["error_type", "module"],
            )
        )

        self.memory_usage = self._register(
            Gauge(
                "finpilot_memory_usage_bytes",
                "Memory usage in bytes",
            )
        )

        self.startup_time = self._register(
            Gauge(
                "finpilot_startup_time_seconds",
                "Application startup time",
            )
        )

    def _register(self, metric: Counter | Gauge | Histogram) -> Counter | Gauge | Histogram:
        """Register a metric."""
        self._metrics[metric.name] = metric
        return metric

    @property
    def enabled(self) -> bool:
        return self._enabled

    def enable(self) -> None:
        """Enable metrics collection."""
        self._enabled = True

    def disable(self) -> None:
        """Disable metrics collection."""
        self._enabled = False

    def collect_all(self) -> dict[str, Any]:
        """Collect all metrics for export."""
        result = {}
        for name, metric in self._metrics.items():
            if isinstance(metric, (Counter, Gauge)):
                result[name] = metric.collect()
            elif isinstance(metric, Histogram):
                result[name] = metric.collect()
        return result

    def reset_all(self) -> None:
        """Reset all metrics."""
        for metric in self._metrics.values():
            if hasattr(metric, "reset") and callable(getattr(metric, "reset", None)):
                getattr(metric, "reset")()

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus text format."""
        lines = []

        for name, metric in self._metrics.items():
            lines.append(f"# HELP {name} {metric.description}")

            if isinstance(metric, Counter):
                lines.append(f"# TYPE {name} counter")
                for mv in metric.collect():
                    labels_str = ",".join(f'{k}="{v}"' for k, v in mv.labels.items())
                    label_part = f"{{{labels_str}}}" if labels_str else ""
                    lines.append(f"{name}{label_part} {mv.value}")

            elif isinstance(metric, Gauge):
                lines.append(f"# TYPE {name} gauge")
                for mv in metric.collect():
                    labels_str = ",".join(f'{k}="{v}"' for k, v in mv.labels.items())
                    label_part = f"{{{labels_str}}}" if labels_str else ""
                    lines.append(f"{name}{label_part} {mv.value}")

            elif isinstance(metric, Histogram):
                lines.append(f"# TYPE {name} histogram")
                for data in metric.collect():
                    labels_str = ",".join(f'{k}="{v}"' for k, v in data["labels"].items())
                    base_labels = f"{{{labels_str}}}" if labels_str else ""

                    for bucket, count in data["buckets"].items():
                        bucket_label = f'le="{bucket}"'
                        full_labels = (
                            f"{{{labels_str},{bucket_label}}}"
                            if labels_str
                            else f"{{{bucket_label}}}"
                        )
                        lines.append(f"{name}_bucket{full_labels} {count}")

                    lines.append(f"{name}_sum{base_labels} {data['sum']}")
                    lines.append(f"{name}_count{base_labels} {data['count']}")

            lines.append("")

        return "\n".join(lines)


# =============================================================================
# HEALTH CHECK
# =============================================================================


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    name: str
    status: HealthStatus
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)


class HealthChecker:
    """
    Application health checker.

    Usage:
        health = HealthChecker()

        @health.register("database")
        def check_db():
            # Returns True/False or HealthCheckResult
            return db.ping()

        result = health.run()
    """

    def __init__(self):
        self._checks: dict[str, Callable[[], bool | HealthCheckResult]] = {}

    def register(self, name: str) -> Callable[[Callable], Callable]:
        """Register a health check."""

        def decorator(func: Callable[[], bool | HealthCheckResult]) -> Callable:
            self._checks[name] = func
            return func

        return decorator

    def add_check(self, name: str, check: Callable[[], bool | HealthCheckResult]) -> None:
        """Add a health check function."""
        self._checks[name] = check

    def run(self, checks: Optional[list[str]] = None) -> dict[str, Any]:
        """Run health checks."""
        results: list[HealthCheckResult] = []
        check_names = checks or list(self._checks.keys())

        for name in check_names:
            if name not in self._checks:
                continue

            start = time.perf_counter()
            try:
                result = self._checks[name]()
                duration = (time.perf_counter() - start) * 1000

                if isinstance(result, HealthCheckResult):
                    result.duration_ms = duration
                    results.append(result)
                elif result:
                    results.append(
                        HealthCheckResult(
                            name=name,
                            status=HealthStatus.HEALTHY,
                            duration_ms=duration,
                        )
                    )
                else:
                    results.append(
                        HealthCheckResult(
                            name=name,
                            status=HealthStatus.UNHEALTHY,
                            duration_ms=duration,
                        )
                    )
            except Exception as e:
                duration = (time.perf_counter() - start) * 1000
                results.append(
                    HealthCheckResult(
                        name=name,
                        status=HealthStatus.UNHEALTHY,
                        message=str(e),
                        duration_ms=duration,
                    )
                )

        # Calculate overall status
        statuses = [r.status for r in results]
        if all(s == HealthStatus.HEALTHY for s in statuses):
            overall = HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            overall = HealthStatus.UNHEALTHY
        else:
            overall = HealthStatus.DEGRADED

        return {
            "status": overall.value,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": [
                {
                    "name": r.name,
                    "status": r.status.value,
                    "message": r.message,
                    "duration_ms": round(r.duration_ms, 2),
                    "details": r.details,
                }
                for r in results
            ],
        }


# =============================================================================
# MLFLOW INTEGRATION
# =============================================================================


class MLflowTracker:
    """
    MLflow experiment tracking wrapper.

    Usage:
        tracker = MLflowTracker("finpilot-drl")

        with tracker.start_run(run_name="ppo_training"):
            tracker.log_params({"learning_rate": 0.001})
            tracker.log_metrics({"reward": 100.5})
            tracker.log_artifact("model.zip")
    """

    def __init__(self, experiment_name: str, tracking_uri: Optional[str] = None):
        self.experiment_name = experiment_name
        self.tracking_uri = tracking_uri
        self._enabled = False
        self._mlflow = None
        self._active_run = None

        self._setup()

    def _setup(self) -> None:
        """Initialize MLflow."""
        try:
            import mlflow  # type: ignore[import-not-found]

            self._mlflow = mlflow

            if self.tracking_uri:
                mlflow.set_tracking_uri(self.tracking_uri)

            mlflow.set_experiment(self.experiment_name)
            self._enabled = True
        except ImportError:
            self._enabled = False

    @property
    def enabled(self) -> bool:
        return self._enabled

    @contextmanager
    def start_run(self, run_name: Optional[str] = None, **kwargs):
        """Start an MLflow run."""
        if not self._enabled or self._mlflow is None:
            yield None
            return

        with self._mlflow.start_run(run_name=run_name, **kwargs) as run:
            self._active_run = run
            try:
                yield run
            finally:
                self._active_run = None

    def log_params(self, params: dict[str, Any]) -> None:
        """Log parameters."""
        if self._enabled and self._active_run and self._mlflow is not None:
            for key, value in params.items():
                self._mlflow.log_param(key, value)

    def log_metrics(self, metrics_dict: dict[str, float], step: Optional[int] = None) -> None:
        """Log metrics."""
        if self._enabled and self._active_run and self._mlflow is not None:
            for key, value in metrics_dict.items():
                self._mlflow.log_metric(key, value, step=step)

    def log_artifact(self, path: str) -> None:
        """Log an artifact file."""
        if self._enabled and self._active_run and self._mlflow is not None:
            self._mlflow.log_artifact(path)

    def log_model(self, model: Any, artifact_path: str) -> None:
        """Log a model."""
        if self._enabled and self._active_run and self._mlflow is not None:
            # For sklearn, pytorch, etc.
            try:
                self._mlflow.sklearn.log_model(model, artifact_path)
            except Exception:
                pass


# =============================================================================
# DECORATORS
# =============================================================================


def track_time(metric: Histogram, **labels: str) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator to track function execution time.

    Usage:
        @track_time(metrics.scan_duration, scan_type="full")
        def run_scan():
            ...
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            with metric.time(**labels):
                return func(*args, **kwargs)

        return wrapper

    return decorator


def count_calls(metric: Counter, **labels: str) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator to count function calls.

    Usage:
        @count_calls(metrics.scans_total, scan_type="quick")
        def quick_scan():
            ...
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            metric.inc(**{k: v for k, v in labels.items()})  # type: ignore[arg-type]
            return func(*args, **kwargs)

        return wrapper

    return decorator


def track_errors(metric: Counter, module: str) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator to track errors.

    Usage:
        @track_errors(metrics.errors_total, module="scanner")
        def risky_operation():
            ...
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                metric.inc(error_type=type(e).__name__, module=module)
                raise

        return wrapper

    return decorator


# =============================================================================
# GLOBAL INSTANCES
# =============================================================================

# Metrics registry
metrics = MetricsRegistry()

# Health checker
health_check = HealthChecker()


# Default health checks
@health_check.register("database")
def _check_database() -> bool:
    """Check database connectivity."""
    try:
        import sqlite3

        from core.config import settings

        conn = sqlite3.connect(settings.database.sqlite_path)
        conn.execute("SELECT 1")
        conn.close()
        return True
    except Exception:
        return False


@health_check.register("cache")
def _check_cache() -> bool:
    """Check cache system."""
    try:
        from core.cache import cache_manager

        test_key = "__health_check__"
        cache_manager.set(test_key, "ok", ttl=10)
        result = cache_manager.get(test_key)
        cache_manager.delete(test_key)
        return result == "ok"
    except Exception:
        return False


@health_check.register("memory")
def _check_memory() -> HealthCheckResult:
    """Check memory usage."""
    try:
        import psutil  # type: ignore[import-not-found]

        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024

        # Update gauge (metrics.memory_usage is a Gauge)
        if hasattr(metrics.memory_usage, "set"):
            metrics.memory_usage.set(process.memory_info().rss)  # type: ignore[union-attr]

        if memory_mb > 1000:  # >1GB warning
            return HealthCheckResult(
                name="memory",
                status=HealthStatus.DEGRADED,
                message=f"High memory usage: {memory_mb:.0f}MB",
                details={"memory_mb": memory_mb},
            )

        return HealthCheckResult(
            name="memory",
            status=HealthStatus.HEALTHY,
            details={"memory_mb": memory_mb},
        )
    except ImportError:
        return HealthCheckResult(
            name="memory",
            status=HealthStatus.HEALTHY,
            message="psutil not installed",
        )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Sentry
    "sentry_client",
    "SentryClient",
    "track_errors_sentry",
    # Metrics
    "metrics",
    "MetricsRegistry",
    "Counter",
    "Gauge",
    "Histogram",
    "MetricType",
    # Health
    "health_check",
    "HealthChecker",
    "HealthStatus",
    "HealthCheckResult",
    # MLflow
    "MLflowTracker",
    # Decorators
    "track_time",
    "count_calls",
    "track_errors",
]
