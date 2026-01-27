"""Prefect orchestration for alternative data ETL."""

from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, Optional, Tuple

import pandas as pd

from ..data_sources.async_base import AsyncBaseAdapter
from ..data_sources.base import DataSlice
from ..data_sources.exceptions import AdapterError
from ..observability import record_etl_flow
from .quality import QualityReport, build_default_expectation_suite, run_expectation_suite
from .run_key import build_run_key
from .schemas import ValidationReport, validate_dataframe
from .storage import StorageResult, write_partitioned_parquet


def _load_prefect_components() -> Tuple[Optional[Any], Optional[Any], Optional[Any], Optional[Any]]:
    try:  # pragma: no cover
        prefect_module = importlib.import_module("prefect")
        runtime_module = importlib.import_module("prefect.runtime")
    except ImportError:  # pragma: no cover
        return None, None, None, None
    return (
        getattr(prefect_module, "task"),
        getattr(prefect_module, "flow"),
        getattr(prefect_module, "get_run_logger"),
        getattr(runtime_module, "flow_run"),
    )


_PREFECT_TASK, _PREFECT_FLOW, _PREFECT_GET_RUN_LOGGER, _PREFECT_FLOW_RUN = (
    _load_prefect_components()
)
PREFECT_AVAILABLE = _PREFECT_TASK is not None


def _missing_prefect(*_args: Any, **_kwargs: Any) -> None:  # pragma: no cover
    raise RuntimeError(
        "Prefect>=2 is required to use the ETL flow. Install it via requirements-etl.txt."
    )


class _TaskStub:  # pragma: no cover
    def __call__(self, fn: Optional[Any] = None, **_kwargs: Any):
        if fn is None:

            def _decorator(inner_fn: Any) -> Any:
                return self._wrap(inner_fn)

            return _decorator
        return self._wrap(fn)

    def _wrap(self, fn: Any) -> Any:
        def _wrapper(*_args: Any, **_kwargs: Any) -> Any:
            _missing_prefect()

        def _submit(*_args: Any, **_kwargs: Any) -> Any:
            _missing_prefect()

        _wrapper.submit = _submit  # type: ignore[attr-defined]
        return _wrapper


def task(*args: Any, **kwargs: Any):
    if PREFECT_AVAILABLE:
        assert _PREFECT_TASK is not None
        return _PREFECT_TASK(*args, **kwargs)
    return _TaskStub()(*args, **kwargs)


def flow(*args: Any, **kwargs: Any):
    if PREFECT_AVAILABLE:
        assert _PREFECT_FLOW is not None
        return _PREFECT_FLOW(*args, **kwargs)
    return _TaskStub()(*args, **kwargs)


def get_run_logger():  # type: ignore[override]
    if PREFECT_AVAILABLE:
        assert _PREFECT_GET_RUN_LOGGER is not None
        return _PREFECT_GET_RUN_LOGGER()
    return logging.getLogger("prefect-missing")


class _FlowRunStub:  # pragma: no cover
    @staticmethod
    def get_id() -> str:
        _missing_prefect()
        return "missing-prefect"


flow_run = _PREFECT_FLOW_RUN if PREFECT_AVAILABLE else _FlowRunStub()


@dataclass(frozen=True)
class ETLRunContext:
    source: str
    symbol: str
    start: Optional[pd.Timestamp]
    end: Optional[pd.Timestamp]
    base_path: Path
    run_key: str


@dataclass(frozen=True)
class ETLResult:
    run_key: str
    rows_ingested: int
    validation: ValidationReport
    quality: Optional[QualityReport]
    storage: StorageResult
    flow_run_id: str


@task(name="Fetch alternative data", retries=3, retry_delay_seconds=10)
async def fetch_data(context: ETLRunContext, adapter: AsyncBaseAdapter) -> DataSlice:
    logger = get_run_logger()
    logger.info("Fetching %s data for %s", context.source, context.symbol)
    try:
        data = await adapter.fetch_async(context.symbol, start=context.start, end=context.end)
    except AdapterError:
        logger.exception("Adapter failed for %s", context.run_key)
        raise
    logger.info("Fetched %s rows", len(data.frame))
    return data


@task(name="Validate schema")
def validate_data(context: ETLRunContext, data: DataSlice) -> Tuple[pd.DataFrame, ValidationReport]:
    logger = get_run_logger()
    validated, report = validate_dataframe(data.frame.copy(), context.source)
    if not report.passed:
        logger.warning("Schema validation reported %s issues", len(report.errors))
    else:
        logger.info("Schema validation passed for %s rows", len(validated))
    return validated, report


@task(name="Run quality checks", retries=1, retry_delay_seconds=5)
def run_quality_checks(
    context: ETLRunContext,
    frame: pd.DataFrame,
    *,
    enable_quality: bool,
) -> Optional[QualityReport]:
    logger = get_run_logger()
    if not enable_quality or frame.empty:
        logger.info("Skipping quality checks (enabled=%s, empty=%s)", enable_quality, frame.empty)
        return None

    try:
        suite = build_default_expectation_suite(context.source)
    except RuntimeError as exc:
        logger.warning("Quality suite unavailable: %s", exc)
        return None

    logger.info("Running quality expectations for %s", context.run_key)
    frame_ready = frame.reset_index()
    report = run_expectation_suite(frame_ready, suite)
    if report.passed:
        logger.info("Quality checks passed")
    else:
        logger.warning("Quality checks failed: %s", report.details)
    return report


@task(name="Persist partitioned parquet")
def persist_data(
    context: ETLRunContext,
    frame: pd.DataFrame,
    *,
    timestamp_column: str = "timestamp",
    compression: str = "snappy",
) -> StorageResult:
    logger = get_run_logger()
    storage_result = write_partitioned_parquet(
        frame,
        base_path=context.base_path,
        source=context.source,
        symbol=context.symbol,
        timestamp_column=timestamp_column,
        compression=compression,  # type: ignore[arg-type] - Literal defined in storage module
    )
    logger.info(
        "Persisted %s rows across %s partitions under %s",
        storage_result.rows_written,
        storage_result.partitions,
        storage_result.base_path,
    )
    return storage_result


@flow(name="alternative-data-etl")
async def alternative_data_etl_flow(
    *,
    adapter: AsyncBaseAdapter,
    source: str,
    symbol: str,
    base_path: Path,
    start: Optional[pd.Timestamp] = None,
    end: Optional[pd.Timestamp] = None,
    enable_quality: bool = True,
    timestamp_column: str = "timestamp",
    compression: str = "snappy",
) -> ETLResult:
    started_at = perf_counter()
    rows_ingested = 0
    success = False
    run_key = build_run_key(source, symbol, start=start, end=end)
    context = ETLRunContext(
        source=source,
        symbol=symbol,
        start=start,
        end=end,
        base_path=base_path,
        run_key=run_key,
    )
    logger = get_run_logger()
    logger.info("Starting ETL flow with run key %s", run_key)

    try:
        data_future = fetch_data.submit(context, adapter)
        data_slice = await data_future.result()

        validated_future = validate_data.submit(context, data_slice)
        validated_frame, validation_report = await validated_future.result()

        quality_future = run_quality_checks.submit(
            context,
            validated_frame,
            enable_quality=enable_quality,
        )
        quality_report = await quality_future.result()

        storage_future = persist_data.submit(
            context,
            validated_frame,
            timestamp_column=timestamp_column,
            compression=compression,
        )
        storage_result = await storage_future.result()
        rows_ingested = storage_result.rows_written
        success = True

        flow_id_getter = getattr(flow_run, "get_id", lambda: "unknown")
        flow_id = flow_id_getter()

        return ETLResult(
            run_key=run_key,
            rows_ingested=storage_result.rows_written,
            validation=validation_report,
            quality=quality_report,
            storage=storage_result,
            flow_run_id=str(flow_id),
        )
    finally:
        duration = perf_counter() - started_at
        record_etl_flow(
            source=source,
            symbol=symbol,
            duration_seconds=duration,
            rows_ingested=rows_ingested,
            success=success,
        )


__all__ = ["alternative_data_etl_flow", "ETLRunContext", "ETLResult"]
