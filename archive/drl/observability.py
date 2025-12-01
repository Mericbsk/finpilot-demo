"""Observability utilities for FinPilot's DRL stack.

This module centralises optional integrations with MLflow and Prometheus.
Both integrations are designed to degrade gracefully when the respective
packages are unavailable so the rest of the system can continue to operate
without hard dependencies.
"""
from __future__ import annotations

import contextlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional

try:  # pragma: no cover - optional dependency
    import mlflow  # type: ignore
except Exception:  # pragma: no cover - missing MLflow is handled at runtime
    mlflow = None  # type: ignore

try:  # pragma: no cover - optional dependency
    from prometheus_client import Counter, Gauge, Histogram, start_http_server  # type: ignore
except Exception:  # pragma: no cover - missing Prometheus handled via no-op stubs
    Counter = Gauge = Histogram = start_http_server = None  # type: ignore


# ---------------------------------------------------------------------------
# MLflow helpers
# ---------------------------------------------------------------------------
@dataclass
class MLflowSettings:
    """Configuration block describing how MLflow should be initialised."""

    enabled: bool = False
    tracking_uri: Optional[str] = None
    experiment: str = "FinPilot-DRL"
    tags: Dict[str, str] = field(default_factory=dict)


def configure_mlflow(settings: MLflowSettings) -> bool:
    """Initialise MLflow according to the supplied settings.

    Returns ``True`` when MLflow is available and initialisation succeeded; ``False``
    otherwise. The function never raises if the dependency is missing to keep the
    broader application optional-dependency friendly.
    """

    if not settings.enabled or mlflow is None:  # type: ignore[truthy-function]
        return False
    if settings.tracking_uri:
        mlflow.set_tracking_uri(settings.tracking_uri)  # type: ignore[attr-defined]
    mlflow.set_experiment(settings.experiment)  # type: ignore[attr-defined]
    return True


@contextlib.contextmanager
def mlflow_run(
    settings: MLflowSettings,
    *,
    run_name: str,
    tags: Optional[Mapping[str, Any]] = None,
    params: Optional[Mapping[str, Any]] = None,
):
    """Context manager that starts an MLflow run when possible.

    The manager is a no-op when MLflow is unavailable or disabled. Tags and params
    are logged immediately after the run is initialised.
    """

    if not configure_mlflow(settings):
        yield None
        return

    active = mlflow.active_run()  # type: ignore[attr-defined]
    created_run = active is None
    if created_run:
        mlflow.start_run(run_name=run_name)  # type: ignore[attr-defined]
    try:
        if tags:
            mlflow.set_tags({k: str(v) for k, v in tags.items()})  # type: ignore[attr-defined]
        if params:
            mlflow.log_params(_coerce_params(params))  # type: ignore[attr-defined]
        yield mlflow.active_run()  # type: ignore[attr-defined]
    finally:
        if created_run:
            mlflow.end_run()  # type: ignore[attr-defined]


def mlflow_log_metrics(metrics: Mapping[str, float]) -> None:
    """Log numeric metrics to the active MLflow run if possible."""

    if mlflow is None:
        return
    run = mlflow.active_run()  # type: ignore[attr-defined]
    if run is None:
        return
    mlflow.log_metrics({k: float(v) for k, v in metrics.items()})  # type: ignore[attr-defined]


def mlflow_log_params(params: Mapping[str, Any]) -> None:
    """Log parameters to the active MLflow run with safe coercion."""

    if mlflow is None:
        return
    run = mlflow.active_run()  # type: ignore[attr-defined]
    if run is None:
        return
    mlflow.log_params(_coerce_params(params))  # type: ignore[attr-defined]


def mlflow_log_dict(payload: Mapping[str, Any], artifact_file: str) -> None:
    """Persist a JSON artefact under the active MLflow run."""

    if mlflow is None:
        return
    run = mlflow.active_run()  # type: ignore[attr-defined]
    if run is None:
        return
    mlflow.log_dict(dict(payload), artifact_file)  # type: ignore[attr-defined]


def mlflow_log_artifact(path: Path, artifact_path: Optional[str] = None) -> None:
    """Log a local file as an artefact if MLflow is active."""

    if mlflow is None:
        return
    run = mlflow.active_run()  # type: ignore[attr-defined]
    if run is None:
        return
    mlflow.log_artifact(str(path), artifact_path=artifact_path)  # type: ignore[attr-defined]


def _coerce_params(params: Mapping[str, Any]) -> Dict[str, Any]:
    coerced: Dict[str, Any] = {}
    for key, value in params.items():
        if isinstance(value, (str, int, float)) or value is None:
            coerced[key] = value
        else:
            coerced[key] = str(value)
    return coerced


# ---------------------------------------------------------------------------
# Prometheus helpers
# ---------------------------------------------------------------------------
@dataclass
class PrometheusSettings:
    """Configuration block for Prometheus metrics exposure."""

    enabled: bool = False
    host: str = "0.0.0.0"
    port: int = 9000
    namespace: str = "finpilot"
    auto_start: bool = True


class _NoopMetric:
    def labels(self, *_args: Any, **_kwargs: Any) -> "_NoopMetric":
        return self

    def observe(self, *_args: Any, **_kwargs: Any) -> None:
        return None

    def inc(self, *_args: Any, **_kwargs: Any) -> None:
        return None

    def set(self, *_args: Any, **_kwargs: Any) -> None:
        return None


@dataclass
class PrometheusRegistry:
    etl_flow_duration: Any = _NoopMetric()
    etl_flow_success_total: Any = _NoopMetric()
    etl_flow_failure_total: Any = _NoopMetric()
    etl_rows_ingested_total: Any = _NoopMetric()
    inference_latency: Any = _NoopMetric()
    inference_requests_total: Any = _NoopMetric()
    feature_cache_hit_ratio: Any = _NoopMetric()
    fallback_activation_total: Any = _NoopMetric()


_PROMETHEUS_SETTINGS: Optional[PrometheusSettings] = None
_PROMETHEUS_REGISTRY = PrometheusRegistry()
_PROMETHEUS_STARTED = False


def configure_prometheus(settings: PrometheusSettings) -> bool:
    """Initialise Prometheus metrics according to the provided settings."""

    global _PROMETHEUS_SETTINGS, _PROMETHEUS_REGISTRY, _PROMETHEUS_STARTED

    _PROMETHEUS_SETTINGS = settings
    if not settings.enabled or any(obj is None for obj in (Counter, Gauge, Histogram)):
        _PROMETHEUS_REGISTRY = PrometheusRegistry()
        return False

    if settings.auto_start and start_http_server is not None and not _PROMETHEUS_STARTED:  # type: ignore[truthy-function]
        start_http_server(settings.port, addr=settings.host)  # type: ignore[attr-defined]
        _PROMETHEUS_STARTED = True

    def _counter(name: str, documentation: str, labels: Iterable[str]):
        return Counter(  # type: ignore[call-arg]
            name,
            documentation,
            tuple(labels),
            namespace=settings.namespace,
        )

    def _histogram(name: str, documentation: str, labels: Iterable[str]):
        return Histogram(  # type: ignore[call-arg]
            name,
            documentation,
            tuple(labels),
            namespace=settings.namespace,
        )

    def _gauge(name: str, documentation: str, labels: Iterable[str]):
        return Gauge(  # type: ignore[call-arg]
            name,
            documentation,
            tuple(labels),
            namespace=settings.namespace,
        )

    _PROMETHEUS_REGISTRY = PrometheusRegistry(
        etl_flow_duration=_histogram(
            "etl_flow_duration_seconds",
            "Duration of ETL flow executions in seconds",
            ("source",),
        ),
        etl_flow_success_total=_counter(
            "etl_flow_success_total",
            "Number of successful ETL flow executions",
            ("source",),
        ),
        etl_flow_failure_total=_counter(
            "etl_flow_failure_total",
            "Number of failed ETL flow executions",
            ("source",),
        ),
        etl_rows_ingested_total=_counter(
            "etl_rows_ingested_total",
            "Total rows ingested by ETL flows",
            ("source",),
        ),
        inference_latency=_histogram(
            "inference_latency_seconds",
            "Latency of inference requests in seconds",
            ("model",),
        ),
        inference_requests_total=_counter(
            "inference_requests_total",
            "Total inference requests processed",
            ("model",),
        ),
        feature_cache_hit_ratio=_gauge(
            "feature_cache_hit_ratio",
            "Cache hit ratio for inference feature lookups",
            ("model",),
        ),
        fallback_activation_total=_counter(
            "fallback_activation_total",
            "Number of times the inference fallback was triggered",
            ("model",),
        ),
    )
    return True


def prometheus_registry() -> PrometheusRegistry:
    """Return the active Prometheus registry (falls back to no-op metrics)."""

    return _PROMETHEUS_REGISTRY


def record_etl_flow(
    *,
    source: str,
    symbol: str,
    duration_seconds: float,
    rows_ingested: int,
    success: bool,
) -> None:
    """Record an ETL execution event in Prometheus when enabled."""

    registry = prometheus_registry()
    registry.etl_flow_duration.labels(source=source).observe(duration_seconds)
    if success:
        registry.etl_flow_success_total.labels(source=source).inc()
        if rows_ingested:
            registry.etl_rows_ingested_total.labels(source=source).inc(rows_ingested)
    else:
        registry.etl_flow_failure_total.labels(source=source).inc()


def record_inference_event(
    *,
    model: str,
    latency_seconds: float,
    cache_hit: Optional[bool] = None,
    fallback_triggered: bool = False,
) -> None:
    """Record an inference request in Prometheus when enabled."""

    registry = prometheus_registry()
    registry.inference_latency.labels(model=model).observe(latency_seconds)
    registry.inference_requests_total.labels(model=model).inc()
    if cache_hit is not None:
        registry.feature_cache_hit_ratio.labels(model=model).set(1.0 if cache_hit else 0.0)
    if fallback_triggered:
        registry.fallback_activation_total.labels(model=model).inc()


__all__ = [
    "MLflowSettings",
    "PrometheusSettings",
    "configure_mlflow",
    "configure_prometheus",
    "mlflow_run",
    "mlflow_log_metrics",
    "mlflow_log_params",
    "mlflow_log_dict",
    "mlflow_log_artifact",
    "record_etl_flow",
    "record_inference_event",
    "prometheus_registry",
]
