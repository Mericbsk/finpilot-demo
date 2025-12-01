"""Great Expectations helpers for alternative data ETL."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

import pandas as pd

try:  # pragma: no cover
    import great_expectations as ge
except ImportError:  # pragma: no cover
    ge = None  # type: ignore[assignment]

ExpectationSuiteType = Any


@dataclass
class QualityReport:
    passed: bool
    details: Dict[str, object]


def _require_ge() -> None:
    if ge is None:  # pragma: no cover
        raise RuntimeError(
            "great-expectations>=0.18 is required to run data quality checks. Install it via requirements-etl.txt."
        )


def build_default_expectation_suite(source: str) -> ExpectationSuiteType:
    _require_ge()
    assert ge is not None
    suite = ge.core.ExpectationSuite(expectation_suite_name=f"altdata_{source.lower()}_suite")
    return suite


def run_expectation_suite(frame: pd.DataFrame, suite: ExpectationSuiteType) -> QualityReport:
    _require_ge()
    assert ge is not None
    dataset = ge.dataset.PandasDataset(frame.copy())
    dataset._set_expectation_suite(suite)

    if "sentiment_score" in frame.columns:
        dataset.expect_column_values_to_be_between("sentiment_score", -1.0, 1.0)
    if "news_volume" in frame.columns:
        dataset.expect_column_values_to_be_greater_than_or_equal_to("news_volume", 0.0)
    if "onchain_active_addresses" in frame.columns:
        dataset.expect_column_values_to_be_greater_than_or_equal_to("onchain_active_addresses", 0.0)
    if "onchain_tx_volume" in frame.columns:
        dataset.expect_column_values_to_be_greater_than_or_equal_to("onchain_tx_volume", 0.0)

    result = dataset.validate(return_only_failures=False)
    success = result.get("success", False)
    return QualityReport(passed=bool(success), details=result)


__all__ = ["QualityReport", "build_default_expectation_suite", "run_expectation_suite"]
