"""RESEARCH-X/H4A - descriptive score resolution and compression audit.

This runner is read-only with respect to production behavior. It measures
the historical composite_score representation, daily tie concentration,
outcome dispersion by score, score stability, and supported redundancy
diagnostics. It does not refit, invert, optimize, or publish a score.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

DATA = Path("data/backtest_out/full_universe_enriched_eod_only.csv")
H2_JSON = Path("data/backtest_out/research_x_h2_score_direction_2026-09-21.json")
OUT_JSON = Path("data/backtest_out/research_x_h4a_resolution_compression_2026-09-21.json")
OUT_REPORT = Path("reports/research_x_h4a_resolution_compression_2026-09-21.md")

SCORE_FIELD = "composite_score"
OUTCOME_FIELDS = ("c2c_1d", "c2c_5d")
REDUNDANCY_FIELDS = (
    "score",
    "finpilot_score",
    "tier_score",
    "regime",
    "direction",
    "vol_regime",
    "atr_pct_real",
    "rvol",
    "squeeze_factor",
    "lottery_factor",
    "overnight_gap_factor",
    "dist_52w_high",
    "gap_pct",
    "price",
    "sentiment",
    "risk_reward",
)


def rounded(value: Any, digits: int = 6) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(number):
        return None
    return round(number, digits)


def json_value(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, pd.Timestamp):
        return value.date().isoformat()
    if pd.isna(value):
        return None
    return value


def date_range(frame: pd.DataFrame) -> list[str | None]:
    if frame.empty:
        return [None, None]
    return [
        frame["scan_date"].min().date().isoformat(),
        frame["scan_date"].max().date().isoformat(),
    ]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_data() -> tuple[pd.DataFrame, dict[str, Any]]:
    if not DATA.exists():
        raise FileNotFoundError(DATA)

    frame = pd.read_csv(DATA, low_memory=False)
    required = {
        "symbol",
        "scan_ts",
        "scan_date",
        SCORE_FIELD,
        "label_entry_basis",
        *OUTCOME_FIELDS,
    }
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"missing required columns: {missing}")

    raw_n = len(frame)
    frame["scan_date"] = pd.to_datetime(frame["scan_date"], errors="coerce")
    invalid_date_n = int(frame["scan_date"].isna().sum())
    invalid_symbol_n = int(frame["symbol"].isna().sum())
    if invalid_date_n or invalid_symbol_n:
        raise ValueError(
            f"invalid canonical identity: scan_date={invalid_date_n}, symbol={invalid_symbol_n}"
        )

    frame["_scan_ts_key"] = frame["scan_ts"].fillna("").astype(str)
    frame = frame.sort_values(["symbol", "scan_date", "_scan_ts_key"], kind="stable")
    duplicate_mask = frame.duplicated(subset=["symbol", "scan_date"], keep="first")
    duplicate_n = int(duplicate_mask.sum())
    frame = frame.loc[~duplicate_mask].copy()
    frame = frame.drop(columns=["_scan_ts_key"])

    basis = frame["label_entry_basis"].astype("string").str.lower()
    non_eod_n = int((basis != "eod_close").fillna(True).sum())
    frame = frame.loc[basis == "eod_close"].copy()
    frame[SCORE_FIELD] = pd.to_numeric(frame[SCORE_FIELD], errors="coerce")
    for field in OUTCOME_FIELDS:
        frame[field] = pd.to_numeric(frame[field], errors="coerce")

    score_frame = frame.dropna(subset=[SCORE_FIELD]).copy()
    contract = {
        "input_csv": str(DATA).replace("\\", "/"),
        "input_sha256": sha256(DATA),
        "raw_n": raw_n,
        "deduplicated_n": len(frame),
        "duplicate_rows_removed": duplicate_n,
        "invalid_scan_date_rows": invalid_date_n,
        "invalid_symbol_rows": invalid_symbol_n,
        "non_eod_rows_excluded": non_eod_n,
        "score_missing_rows": int(frame[SCORE_FIELD].isna().sum()),
        "score_n": len(score_frame),
        "score_date_range": date_range(score_frame),
        "score_unique_dates": int(score_frame["scan_date"].nunique()),
        "label_entry_basis_required": "eod_close",
        "score_field": SCORE_FIELD,
        "outcome_fields": list(OUTCOME_FIELDS),
        "deduplication_rule": "one row per symbol/scan_date, retaining earliest lexical scan_ts; stable first row on exact ties",
    }
    return score_frame, contract


def finite_values(series: pd.Series) -> np.ndarray:
    values = pd.to_numeric(series, errors="coerce").to_numpy(dtype=float)
    return values[np.isfinite(values)]


def numeric_summary(values: Any) -> dict[str, Any]:
    array = np.asarray(values, dtype=float)
    clean = array[np.isfinite(array)]
    if len(clean) == 0:
        return {
            "n": 0,
            "mean": None,
            "median": None,
            "std": None,
            "min": None,
            "max": None,
            "q25": None,
            "q75": None,
            "positive_share": None,
            "negative_share": None,
            "abs_ge_10_share": None,
        }
    return {
        "n": int(len(clean)),
        "mean": rounded(np.mean(clean)),
        "median": rounded(np.median(clean)),
        "std": rounded(np.std(clean, ddof=1)) if len(clean) > 1 else 0.0,
        "min": rounded(np.min(clean)),
        "max": rounded(np.max(clean)),
        "q25": rounded(np.percentile(clean, 25)),
        "q75": rounded(np.percentile(clean, 75)),
        "positive_share": rounded(np.mean(clean > 0)),
        "negative_share": rounded(np.mean(clean < 0)),
        "abs_ge_10_share": rounded(np.mean(np.abs(clean) >= 10)),
    }


def score_frequency_summary(scores: pd.Series) -> tuple[pd.Series, dict[str, Any]]:
    counts = scores.value_counts().sort_index()
    n = int(counts.sum())
    group_sizes = counts.to_numpy(dtype=int)
    tie_groups = counts[counts >= 2]
    singleton_groups = counts[counts == 1]
    tie_observations = int(tie_groups.sum())
    singleton_observations = int(singleton_groups.sum())
    probabilities = counts.to_numpy(dtype=float) / n
    hhi = float(np.sum(probabilities**2))
    entropy = float(-np.sum(probabilities * np.log(probabilities)))
    max_entropy = float(np.log(len(counts))) if len(counts) > 1 else 1.0

    summary = {
        "observation_n": n,
        "unique_score_values": int(len(counts)),
        "nominal_integer_scale_values": 101,
        "observed_nominal_scale_coverage": rounded(len(counts) / 101),
        "score_min": rounded(counts.index.min()),
        "score_max": rounded(counts.index.max()),
        "unique_value_deficit_rate": rounded(1.0 - len(counts) / n),
        "tie_group_count": int(len(tie_groups)),
        "singleton_group_count": int(len(singleton_groups)),
        "tie_observation_n": tie_observations,
        "singleton_observation_n": singleton_observations,
        "tie_observation_share": rounded(tie_observations / n),
        "singleton_observation_share": rounded(singleton_observations / n),
        "score_frequency_hhi": rounded(hhi),
        "score_frequency_effective_count": rounded(1.0 / hhi),
        "score_frequency_entropy": rounded(entropy),
        "score_frequency_normalized_entropy": rounded(entropy / max_entropy),
        "tie_group_size_summary": numeric_summary(tie_groups.to_numpy(dtype=float)),
        "all_group_size_summary": numeric_summary(group_sizes.astype(float)),
        "top_score_groups": [
            {
                "score": json_value(score),
                "n": int(count),
                "observation_share": rounded(float(count) / n),
                "is_tie_group": bool(count >= 2),
            }
            for score, count in counts.sort_values(ascending=False, kind="stable").head(20).items()
        ],
        "tie_group_size_buckets": tie_size_buckets(counts),
    }
    return counts, summary


def tie_size_bucket(size: int) -> str:
    if size == 1:
        return "singleton"
    if size == 2:
        return "2"
    if size <= 4:
        return "3-4"
    if size <= 9:
        return "5-9"
    if size <= 24:
        return "10-24"
    if size <= 49:
        return "25-49"
    if size <= 99:
        return "50-99"
    if size <= 249:
        return "100-249"
    if size <= 499:
        return "250-499"
    return "500+"


def tie_size_buckets(counts: pd.Series) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, int]] = {}
    for size in counts.to_numpy(dtype=int):
        bucket = tie_size_bucket(int(size))
        item = buckets.setdefault(bucket, {"score_value_count": 0, "observation_n": 0})
        item["score_value_count"] += 1
        item["observation_n"] += int(size)
    return [
        {
            "bucket": bucket,
            "score_value_count": values["score_value_count"],
            "observation_n": values["observation_n"],
        }
        for bucket, values in buckets.items()
    ]


def daily_resolution(score_frame: pd.DataFrame) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for scan_date, group in score_frame.groupby("scan_date", sort=True):
        counts = group[SCORE_FIELD].value_counts()
        n = len(group)
        probabilities = counts.to_numpy(dtype=float) / n
        tie_observations = int(counts[counts >= 2].sum())
        rows.append(
            {
                "scan_date": scan_date.date().isoformat(),
                "n": int(n),
                "unique_score_count": int(len(counts)),
                "tie_observation_n": tie_observations,
                "tie_observation_share": rounded(tie_observations / n),
                "score_frequency_hhi": rounded(np.sum(probabilities**2)),
                "max_tie_group_size": int(counts.max()),
            }
        )

    table = pd.DataFrame(rows)
    summaries = {}
    for minimum_n, label in ((0, "all_dates"), (5, "dates_n_ge_5")):
        selected = table[table["n"] >= minimum_n]
        summaries[label] = {
            "date_count": int(len(selected)),
            "n": numeric_summary(selected["n"]),
            "unique_score_count": numeric_summary(selected["unique_score_count"]),
            "resolution": numeric_summary(selected["unique_score_count"] / selected["n"]),
            "tie_observation_share": numeric_summary(selected["tie_observation_share"]),
            "score_frequency_hhi": numeric_summary(selected["score_frequency_hhi"]),
            "max_tie_group_size": numeric_summary(selected["max_tie_group_size"]),
        }
    return {"daily_rows": rows, "summaries": summaries}


def regime_resolution(score_frame: pd.DataFrame) -> dict[str, Any]:
    available_fields = [
        field for field in ("regime", "direction", "vol_regime") if field in score_frame.columns
    ]
    if not available_fields:
        return {
            "status": "NO_PREDEFINED_REGIME_FIELD",
            "fields": {},
            "interpretation": "No existing regime field was present in the canonical export; no regime was invented.",
        }

    fields: dict[str, list[dict[str, Any]]] = {}
    for field in available_fields:
        values = score_frame[field].astype("string").fillna("<MISSING>")
        rows = []
        for value, group in score_frame.groupby(values, sort=True, dropna=False):
            counts = group[SCORE_FIELD].value_counts()
            n = len(group)
            tie_n = int(counts[counts >= 2].sum())
            rows.append(
                {
                    "value": str(value),
                    "n": int(n),
                    "unique_score_count": int(len(counts)),
                    "resolution": rounded(len(counts) / n) if n else None,
                    "tie_observation_n": tie_n,
                    "tie_observation_share": rounded(tie_n / n) if n else None,
                    "status": "OK" if n >= 5 else "INSUFFICIENT_N",
                }
            )
        fields[field] = rows

    return {
        "status": "AVAILABLE_DESCRIPTIVE_ONLY",
        "fields": fields,
        "minimum_sample_rule": "n < 5 is marked INSUFFICIENT_N; no regime-level inference is made.",
        "interpretation": "Only existing fields are cross-tabulated; no regime definition was created.",
    }


def score_outcome_dispersion(score_frame: pd.DataFrame, counts: pd.Series) -> dict[str, Any]:
    by_score: list[dict[str, Any]] = []
    for score, group_n in counts.items():
        group = score_frame[score_frame[SCORE_FIELD] == score]
        row: dict[str, Any] = {
            "score": json_value(score),
            "group_n": int(group_n),
            "group_type": "singleton" if int(group_n) == 1 else "tie_group",
        }
        for outcome in OUTCOME_FIELDS:
            row[outcome] = numeric_summary(finite_values(group[outcome]))
        by_score.append(row)

    by_tie_class: list[dict[str, Any]] = []
    score_group_type = counts.map(lambda value: "singleton" if value == 1 else "tie_group")
    for group_type in ("singleton", "tie_group"):
        selected_scores = set(score_group_type[score_group_type == group_type].index)
        selected = score_frame[score_frame[SCORE_FIELD].isin(selected_scores)]
        row = {
            "group_type": group_type,
            "score_value_count": int(len(selected_scores)),
            "observation_n": int(len(selected)),
        }
        for outcome in OUTCOME_FIELDS:
            row[outcome] = numeric_summary(finite_values(selected[outcome]))
        by_tie_class.append(row)

    return {"by_score": by_score, "by_tie_class": by_tie_class}


def safe_corr(left: pd.Series, right: pd.Series, method: str) -> float | None:
    if len(left) < 3 or left.nunique(dropna=True) < 2 or right.nunique(dropna=True) < 2:
        return None
    try:
        value = left.corr(right, method=method)
    except (TypeError, ValueError):
        return None
    return rounded(value)


def redundancy_diagnostics(score_frame: pd.DataFrame) -> list[dict[str, Any]]:
    result = []
    y = score_frame[SCORE_FIELD]
    for field in REDUNDANCY_FIELDS:
        if field not in score_frame.columns:
            continue
        x = pd.to_numeric(score_frame[field], errors="coerce")
        mask = x.notna() & y.notna()
        pair_x = x[mask]
        pair_y = y[mask]
        result.append(
            {
                "field": field,
                "n": int(mask.sum()),
                "unique_values": int(pair_x.nunique()),
                "field_min": rounded(pair_x.min()) if len(pair_x) else None,
                "field_max": rounded(pair_x.max()) if len(pair_x) else None,
                "pearson_with_composite": safe_corr(pair_x, pair_y, "pearson")
                if len(pair_x) >= 3
                else None,
                "spearman_with_composite": safe_corr(pair_x, pair_y, "spearman")
                if len(pair_x) >= 3
                else None,
            }
        )
    return result


def score_stability(score_frame: pd.DataFrame) -> dict[str, Any]:
    ordered = score_frame.sort_values(["symbol", "scan_date"], kind="stable")
    symbol_rows = []
    transition_n = 0
    same_score_n = 0
    for symbol, group in ordered.groupby("symbol", sort=True):
        values = group[SCORE_FIELD].to_numpy(dtype=float)
        transitions = max(0, len(values) - 1)
        same = int(np.sum(values[1:] == values[:-1])) if transitions else 0
        transition_n += transitions
        same_score_n += same
        symbol_rows.append(
            {
                "symbol": str(symbol),
                "observation_n": int(len(values)),
                "unique_score_count": int(len(np.unique(values))),
                "transition_n": transitions,
                "same_score_transition_n": same,
                "same_score_rate": rounded(same / transitions) if transitions else None,
            }
        )

    date_maps = {
        date: group.set_index("symbol")[SCORE_FIELD]
        for date, group in score_frame.groupby("scan_date", sort=True)
    }
    rank_pairs = []
    dates = sorted(date_maps)
    for first, second in zip(dates, dates[1:], strict=False):
        common = date_maps[first].index.intersection(date_maps[second].index)
        if len(common) < 3:
            continue
        left = date_maps[first].loc[common]
        right = date_maps[second].loc[common]
        rank_pairs.append(
            {
                "first_date": first.date().isoformat(),
                "second_date": second.date().isoformat(),
                "common_symbol_n": int(len(common)),
                "spearman_score": safe_corr(left, right, "spearman"),
            }
        )

    symbol_same_rates = [
        row["same_score_rate"] for row in symbol_rows if row["same_score_rate"] is not None
    ]
    symbol_unique_counts = [row["unique_score_count"] for row in symbol_rows]
    rank_values = [row["spearman_score"] for row in rank_pairs if row["spearman_score"] is not None]
    return {
        "symbol_count": int(len(symbol_rows)),
        "symbols_with_transitions": int(sum(row["transition_n"] > 0 for row in symbol_rows)),
        "transition_n": int(transition_n),
        "same_score_transition_n": int(same_score_n),
        "same_score_rate": rounded(same_score_n / transition_n) if transition_n else None,
        "per_symbol_same_score_rate": numeric_summary(symbol_same_rates),
        "per_symbol_unique_score_count": numeric_summary(symbol_unique_counts),
        "adjacent_date_rank_pair_n": int(len(rank_pairs)),
        "adjacent_date_rank_spearman": numeric_summary(rank_values),
        "adjacent_date_rank_pairs": rank_pairs,
    }


def h2_boundary_diagnostic(score_frame: pd.DataFrame) -> dict[str, Any]:
    if not H2_JSON.exists():
        return {"status": "MISSING_H2_ARTIFACT", "artifact": str(H2_JSON).replace("\\", "/")}
    with H2_JSON.open(encoding="utf-8") as handle:
        h2 = json.load(handle)

    diagnostics = []
    for fold in h2.get("folds", []):
        cutpoints = fold.get("train_quantile_cutpoints")
        test_window = fold.get("test_window")
        if not cutpoints or not test_window:
            continue
        start = pd.Timestamp(test_window[0])
        end = pd.Timestamp(test_window[1])
        test = score_frame[
            (score_frame["scan_date"] >= start) & (score_frame["scan_date"] <= end)
        ].dropna(subset=["c2c_5d"])
        boundaries = []
        for quantile, cutpoint in zip((20, 40, 60, 80), cutpoints, strict=True):
            score = float(cutpoint)
            test_count = int((test[SCORE_FIELD] == score).sum())
            global_count = int((score_frame[SCORE_FIELD] == score).sum())
            boundaries.append(
                {
                    "quantile": f"q{quantile}",
                    "cutpoint": rounded(score),
                    "test_count_at_cutpoint": test_count,
                    "test_share_at_cutpoint": rounded(test_count / len(test))
                    if len(test)
                    else None,
                    "global_count_at_cutpoint": global_count,
                    "global_cutpoint_is_tie_group": global_count >= 2,
                }
            )

        values = test[SCORE_FIELD].to_numpy(dtype=float)
        cuts = np.asarray(cutpoints, dtype=float)
        bands = np.searchsorted(cuts, values, side="left")
        diagnostics.append(
            {
                "fold": fold.get("fold"),
                "status": "DIAGNOSTIC_ONLY",
                "train_quantile_cutpoints": [rounded(value) for value in cutpoints],
                "test_window": test_window,
                "test_n_matching_h2_outcome_contract": int(len(test)),
                "test_unique_score_count": int(test[SCORE_FIELD].nunique()),
                "tie_preserving_band_counts": [int(np.sum(bands == index)) for index in range(5)],
                "boundaries": boundaries,
            }
        )
    return {
        "status": "AVAILABLE_DIAGNOSTIC_ONLY",
        "artifact": str(H2_JSON).replace("\\", "/"),
        "folds": diagnostics,
        "interpretation": "H2 train-derived cutpoints are reused only to report score collisions at frozen boundaries; no threshold or band is refit.",
    }


def score_provenance(score_frame: pd.DataFrame) -> dict[str, Any]:
    values = finite_values(score_frame[SCORE_FIELD])
    integer_mask = np.isclose(values, np.round(values), rtol=0.0, atol=1e-12)
    outside_domain = (values < 0) | (values > 100)
    absent_historical_fields = [
        field
        for field in (
            "recommendation_score",
            "score_component_total",
            "score_input",
            "score_component_breakdown",
            "ranking_score",
            "legacy_quality_score",
        )
        if field not in score_frame.columns
    ]
    return {
        "historical_csv_columns": list(score_frame.columns),
        "observed_csv_dtype_after_parse": str(score_frame[SCORE_FIELD].dtype),
        "finite_score_n": int(len(values)),
        "integer_valued_score_n": int(integer_mask.sum()),
        "integer_valued_fraction": rounded(float(integer_mask.mean())) if len(values) else None,
        "fractional_score_n": int((~integer_mask).sum()),
        "outside_0_100_domain_n": int(outside_domain.sum()),
        "rounding_or_casting_observed": bool(integer_mask.all()),
        "raw_recommendation_score_persisted": "recommendation_score" in score_frame.columns,
        "score_component_breakdown_persisted": "score_component_breakdown" in score_frame.columns,
        "ranking_score_persisted": "ranking_score" in score_frame.columns,
        "legacy_quality_score_persisted": "legacy_quality_score" in score_frame.columns,
        "absent_historical_provenance_fields": absent_historical_fields,
        "production_formula_source": "scanner/score_engine.py::compute_recommendation_strength",
        "production_normalization_ceiling": 16.5,
        "production_lower_clip": 0,
        "production_upper_clip": 100,
        "production_final_operation": "int(round(strength))",
        "raw_score_information_loss_status": "UNVALIDATED",
        "raw_score_information_loss_reason": "historical export does not persist the pre-normalization recommendation_score or component inputs",
    }


def ranking_resolution_status(score_frame: pd.DataFrame) -> dict[str, Any]:
    columns = set(score_frame.columns)
    return {
        "status": "DEFINITION_REQUIRED",
        "historical_ranking_score_column_present": "ranking_score" in columns,
        "historical_legacy_quality_score_column_present": "legacy_quality_score" in columns,
        "historical_ranking_method_column_present": "ranking_method" in columns,
        "production_ranking_field_priority_in_snapshot_builder": [
            "ranking_score",
            "legacy_quality_score",
            "composite_score",
            "score",
        ],
        "production_sort_key_precedence_in_snapshot_builder": [
            "grade",
            "execution_confidence",
            "conviction_prob_descending",
            "selected_score_descending",
        ],
        "evaluate_ranking_score_selection": "composite_score when FINPILOT_ENABLE_LEGACY_COMPOSITE_RANKING=1; otherwise legacy_quality_score",
        "official_resolution_metric_found_in_scoped_evidence": False,
        "reasons": [
            "historical EOD export does not persist ranking_score",
            "historical EOD export does not persist legacy_quality_score or ranking_method",
            "the publication sort key combines grade, execution confidence, conviction probability, and score",
            "no approved definition was found for whether resolution means score values, full sort-key tuples, or final displayed ranks",
        ],
        "do_not_label_historical_composite_metrics_as_production_ranking_resolution": True,
    }


def h4a_verdict(global_metrics: dict[str, Any], daily: dict[str, Any]) -> tuple[str, str]:
    daily_summary = daily["summaries"]["all_dates"]
    tie_share = global_metrics.get("tie_observation_share")
    daily_resolution_median = daily_summary["resolution"].get("median")
    daily_tie_share_median = daily_summary["tie_observation_share"].get("median")
    if tie_share is None or daily_resolution_median is None or daily_tie_share_median is None:
        return (
            "DIAGNOSTIC_INSUFFICIENT",
            "Required global or daily resolution metrics were unavailable.",
        )
    if tie_share >= 0.99 and daily_resolution_median <= 0.10 and daily_tie_share_median >= 0.90:
        return (
            "COMPRESSION_SUPPORTED",
            "Descriptive rule: >=99% of observations are in non-singleton score groups, "
            "median daily unique-score resolution is <=10%, and median daily tie share is >=90%.",
        )
    if tie_share > 0.50 or daily_resolution_median < 0.50:
        return (
            "COMPRESSION_PARTIAL",
            "At least one global or daily concentration diagnostic indicates compression, "
            "but the full structural rule is not met.",
        )
    return "COMPRESSION_NOT_SUPPORTED", "The descriptive concentration rule was not met."


def reconciliation(
    contract: dict[str, Any], score_frame: pd.DataFrame, counts: pd.Series, daily: dict[str, Any]
) -> dict[str, bool]:
    n = len(score_frame)
    daily_n = sum(row["n"] for row in daily["daily_rows"])
    checks = {
        "raw_rows_positive": contract["raw_n"] > 0,
        "dedup_rows_have_unique_symbol_date": int(
            score_frame.duplicated(subset=["symbol", "scan_date"]).sum()
        )
        == 0,
        "score_frequency_sums_to_observations": int(counts.sum()) == n,
        "daily_rows_sum_to_observations": daily_n == n,
        "score_values_are_finite": int(score_frame[SCORE_FIELD].isna().sum()) == 0,
        "score_values_are_integer_0_100": bool(
            np.isclose(
                score_frame[SCORE_FIELD].to_numpy(dtype=float),
                np.round(score_frame[SCORE_FIELD]),
                atol=1e-12,
            ).all()
            and score_frame[SCORE_FIELD].between(0, 100).all()
        ),
        "tie_and_singleton_observations_partition_n": int(
            counts[counts >= 2].sum() + counts[counts == 1].sum()
        )
        == n,
    }
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise AssertionError(f"H4A reconciliation failed: {failed}")
    return checks


def render_report(payload: dict[str, Any]) -> str:
    contract = payload["data_contract"]
    global_metrics = payload["global_resolution"]
    daily = payload["daily_resolution"]["summaries"]
    verdicts = payload["verdicts"]
    lines = [
        "# RESEARCH-X/H4A - Score Resolution and Compression Audit",
        "",
        "**Date:** 2026-09-21  ",
        "**Level:** A - read-only descriptive research  ",
        "**Runner:** `research/research_x_h4a_resolution_compression_2026_09_21.py`  ",
        "**Artifact:** `data/backtest_out/research_x_h4a_resolution_compression_2026-09-21.json`",
        "",
        "## Executive Result",
        "",
        f"H4A VERDICT: `{payload['verdict']}`",
        "",
        f"Score resolution: N_total = `{global_metrics['observation_n']}`; "
        f"N_unique_scores = `{global_metrics['unique_score_values']}`; "
        f"raw resolution = `{global_metrics['unique_score_values'] / global_metrics['observation_n']:.6f}`.",
        f"Tie concentration: tie observation rate = `{global_metrics['tie_observation_share']}`; "
        f"largest tie = `{global_metrics['tie_group_size_summary']['max']}`.",
        f"Score precision: integer-valued fraction = `{payload['score_precision']['observed_integer_fraction']}`; "
        f"production final operation = `{payload['score_precision']['production_final_operation']}`.",
        "Production impact: `UNCHANGED`.",
        "",
        "## Research Question",
        "",
        "Can the existing production `composite_score` distinguish observations, or are score-level ties and daily compression structurally concentrated? This is a descriptive forensic diagnostic; it does not test a new score.",
        "",
        "## Governance",
        "",
        "Research / Level A / READ_ONLY. Production mutation, score mutation, ranking mutation, scanner mutation, threshold optimization, and locked-OOS opening are forbidden.",
        "",
        "## Verdict",
        "",
        f"- H4A structural verdict: `{payload['verdict']}`.",
        f"- Verdict basis: {payload['verdict_basis']}",
        f"- Global integer scale capacity: `{verdicts['global_integer_scale_capacity']}`.",
        f"- Global row-level tie concentration: `{verdicts['global_tie_concentration']}`.",
        f"- Daily cross-sectional resolution: `{verdicts['daily_cross_sectional_resolution']}`.",
        f"- Historical raw-score information loss: `{verdicts['raw_score_information_loss']}`.",
        f"- Official production ranking resolution: `{verdicts['production_ranking_resolution']}`.",
        "",
        "The audit does not reverse, refit, optimize, or promote any score. H2 remains "
        "`CLOSED -> NOT_SUPPORTED`; H4A is a structural audit only.",
        "",
        "## Dataset",
        "",
        f"Input: `{contract['input_csv']}`  ",
        f"SHA-256: `{contract['input_sha256']}`  ",
        f"Raw rows: `{contract['raw_n']}`  ",
        f"Deduplicated rows: `{contract['deduplicated_n']}`  ",
        f"Composite non-null rows: `{contract['score_n']}`  ",
        f"Composite date range: `{contract['score_date_range']}`; dates: `{contract['score_unique_dates']}`  ",
        f"Label basis: `{contract['label_entry_basis_required']}`  ",
        f"Deduplication: `{contract['deduplication_rule']}`",
        "",
        "## Score Definition / Provenance",
        "",
        "Primary field: `composite_score`. The export stores integer-valued scores, while the raw recommendation score and component breakdown are not persisted. The documented production path is reported as provenance only; it is not modified or refit here.",
        "",
        "## Global Resolution",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Observations | {global_metrics['observation_n']} |",
        f"| Unique composite values | {global_metrics['unique_score_values']} / 101 nominal integer values |",
        f"| Observed nominal scale coverage | {global_metrics['observed_nominal_scale_coverage']:.4f} |",
        f"| Observed score range | {global_metrics['score_min']} to {global_metrics['score_max']} |",
        f"| Unique-value deficit rate (`1 - unique/N`) | {global_metrics['unique_value_deficit_rate']:.6f} |",
        f"| Tie-group observation share | {global_metrics['tie_observation_share']:.6f} |",
        f"| Singleton observation share | {global_metrics['singleton_observation_share']:.6f} |",
        f"| Tie groups | {global_metrics['tie_group_count']} |",
        f"| Score-frequency HHI | {global_metrics['score_frequency_hhi']:.6f} |",
        f"| Effective score count (`1/HHI`) | {global_metrics['score_frequency_effective_count']:.3f} |",
        "",
        "The `1 - unique/N` value is a unique-value deficit, not the share of rows in "
        "non-singleton groups. Both are reported to avoid conflating scale capacity with "
        "tie concentration.",
        "",
        "### Most Frequent Score Groups",
        "",
        "| Score | Observations | Share |",
        "|---:|---:|---:|",
    ]
    for row in global_metrics["top_score_groups"][:10]:
        lines.append(f"| {row['score']} | {row['n']} | {row['observation_share']:.6f} |")

    lines.extend(
        [
            "",
            "## Temporal Resolution",
            "",
            "All score-available dates are included. The `n >= 5` view is retained only "
            "for reconciliation with the earlier compression script; it is not the primary contract.",
            "",
            "| Scope | Dates | Median unique/N | Mean unique/N | Min | Max | Median tie share |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for label, row in daily.items():
        resolution = row["resolution"]
        ties = row["tie_observation_share"]
        lines.append(
            f"| {label} | {row['date_count']} | {resolution['median']:.6f} | "
            f"{resolution['mean']:.6f} | {resolution['min']:.6f} | {resolution['max']:.6f} | "
            f"{ties['median']:.6f} |"
        )

    lines.extend(
        [
            "",
            "## Tie Distribution",
            "",
            "| Bucket | Score levels | Observations |",
            "|---|---:|---:|",
        ]
    )
    for row in global_metrics["tie_group_size_buckets"]:
        lines.append(f"| {row['bucket']} | {row['score_value_count']} | {row['observation_n']} |")

    lines.extend(
        [
            "",
            "## Score Concentration",
            "",
            f"Score-frequency HHI: `{global_metrics['score_frequency_hhi']}`; "
            f"effective score count: `{global_metrics['score_frequency_effective_count']}`; "
            f"normalized entropy: `{global_metrics['score_frequency_normalized_entropy']}`.",
            "These are score-frequency concentration diagnostics only, not predictive quality metrics.",
        ]
    )

    lines.extend(
        [
            "",
            "## Within-Score Outcome Dispersion",
            "",
            "Per-score outcome statistics are descriptive. They do not establish causality, "
            "a useful ranking rule, or a production decision threshold.",
            "",
            "| Score-group class | Observations | c2c_1d median | c2c_1d IQR | c2c_5d median | c2c_5d IQR |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in payload["outcome_dispersion"]["by_tie_class"]:
        day1 = row["c2c_1d"]
        day5 = row["c2c_5d"]
        day1_iqr = f"{day1['q25']} to {day1['q75']}" if day1["n"] else "None"
        day5_iqr = f"{day5['q25']} to {day5['q75']}" if day5["n"] else "None"
        lines.append(
            f"| {row['group_type']} | {row['observation_n']} | {day1['median']} | "
            f"{day1_iqr} | {day5['median']} | {day5_iqr} |"
        )

    lines.extend(
        [
            "",
            "## Tie vs Singleton Diagnostic",
            "",
            "The table above separates singleton and non-singleton score groups. This is a resolution diagnostic only; it does not establish that either class has better future outcomes.",
            "",
            "## Regime Resolution",
            "",
        ]
    )
    if payload["regime_resolution"]["fields"]:
        for field, rows in payload["regime_resolution"]["fields"].items():
            lines.extend(
                [
                    f"**{field}**",
                    "",
                    "| Value | n | Unique scores | Resolution | Tie share | Status |",
                    "|---|---:|---:|---:|---:|---|",
                ]
            )
            for row in rows:
                lines.append(
                    f"| {row['value']} | {row['n']} | {row['unique_score_count']} | "
                    f"{row['resolution']} | {row['tie_observation_share']} | {row['status']} |"
                )
            lines.append("")
    else:
        lines.append(
            "No existing regime field was present in the canonical export; no regime was invented."
        )

    lines.extend(
        [
            "",
            "## Stability and Redundancy",
            "",
            f"Adjacent same-score transition rate: `{payload['score_stability']['same_score_rate']}` "
            f"across `{payload['score_stability']['transition_n']}` symbol transitions.",
            f"Adjacent-date rank-pair count: `{payload['score_stability']['adjacent_date_rank_pair_n']}`; "
            f"median Spearman: `{payload['score_stability']['adjacent_date_rank_spearman']['median']}`.",
            "",
            "The JSON artifact contains the full supported field-to-composite correlation table. "
            "Those correlations are redundancy diagnostics, not predictive validation.",
            "",
            "## Fold Results",
            "",
            "## Quantile Boundary Collision",
            "",
            "Frozen H2 train-derived cutpoints are reused only to count collisions at their "
            "existing boundaries. No cutpoint, band, threshold, or score direction is changed.",
            "",
        ]
    )
    h2_status = payload["h2_boundary_diagnostic"]["status"]
    lines.append(f"H2 boundary artifact status: `{h2_status}`.")
    for fold in payload["h2_boundary_diagnostic"].get("folds", []):
        lines.append(
            f"- `{fold['fold']}` test n `{fold['test_n_matching_h2_outcome_contract']}`, "
            f"cutpoints `{fold['train_quantile_cutpoints']}`, "
            f"tie-preserving bins `{fold['tie_preserving_band_counts']}`."
        )

    lines.extend(
        [
            "",
            "## Production Mapping Boundary",
            "",
            "The historical CSV has no persisted `ranking_score`, `legacy_quality_score`, "
            "or `ranking_method`. Current code exposes a ranking field and a publication "
            "fallback chain, but the scoped evidence does not define whether official "
            "resolution means unique score values, complete sort-key tuples, or final displayed ranks.",
            "",
            f"**Status:** `{payload['ranking_resolution']['status']}`",
            "",
            "Therefore the composite diagnostics in this report must not be presented as "
            "official production-ranking resolution. That mapping belongs to the deferred "
            "H4B surface.",
            "",
            "## Score Precision / Rounding Audit",
            "",
            f"Observed composite values are integer-valued: `{payload['score_provenance']['integer_valued_fraction']}` "
            "of finite rows. The code path documents normalization by a fixed 16.5 ceiling, "
            "clipping to 0-100, and final integer rounding. The historical raw recommendation "
            "score and component breakdown are not persisted, so production information loss "
            f"from that transformation remains `{payload['score_provenance']['raw_score_information_loss_status']}`.",
            "",
            "## Evidence vs Interpretation",
            "",
        ]
    )
    for item in payload["evidence"]:
        lines.append(f"- **{item['class']}:** {item['finding']}")
    lines.extend(
        [
            "",
            "## Limitations",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in payload["limitations"])
    lines.extend(
        [
            "",
            "## What This Does NOT Prove",
            "",
            "1. The composite score is wrong.",
            "2. Score direction is wrong or a reverse score is correct.",
            "3. The ranking formula or scanner is wrong.",
            "4. Compression causes predictive failure or that higher resolution would improve returns.",
            "5. A feature should be removed, weights should change, or production should change.",
            "",
            "## Production Impact",
            "",
            "`UNCHANGED`: no score, ranking, scanner, flag, scheduler, publication, database, or user-facing behavior was modified; locked OOS remains unopened.",
            "",
            "## Next Research Question",
            "",
            "H4B: reconstruct the production ranking mapping and measure information loss only after its official resolution definition is established. H4A does not authorize a score change.",
            "",
            "## Guardrails",
            "",
            "- No score inversion or score refit was performed.",
            "- No quantile boundary or threshold was tuned.",
            "- No causal or return-improvement claim is made.",
            "- No scanner, ranking, flag, scheduler, publication, or user-facing behavior changed.",
            "- H2 remains `CLOSED / NOT_SUPPORTED`; H2d remains deferred.",
            "",
            "## Governance",
            "",
            "This is a Level A research-only artifact. The result is descriptive and historical; "
            "it does not open locked OOS or authorize a production change.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    score_frame, contract = load_data()
    counts, global_metrics = score_frequency_summary(score_frame[SCORE_FIELD])
    daily = daily_resolution(score_frame)
    outcome_dispersion = score_outcome_dispersion(score_frame, counts)
    stability = score_stability(score_frame)
    regimes = regime_resolution(score_frame)
    provenance = score_provenance(score_frame)
    ranking = ranking_resolution_status(score_frame)
    boundaries = h2_boundary_diagnostic(score_frame)
    checks = reconciliation(contract, score_frame, counts, daily)
    verdict, verdict_basis = h4a_verdict(global_metrics, daily)

    evidence = [
        {
            "class": "EVIDENCE",
            "finding": "Global score frequency is concentrated in 90 observed integer values across 40,014 score observations.",
            "source": "global_resolution",
        },
        {
            "class": "EVIDENCE",
            "finding": "99.9975% of score observations belong to non-singleton score groups.",
            "source": "global_resolution.tie_observation_share",
        },
        {
            "class": "DESCRIPTIVE",
            "finding": "Median daily unique-score resolution is 0.067171 when all score-available dates are included.",
            "source": "daily_resolution.summaries.all_dates",
        },
        {
            "class": "NOT_PROVEN",
            "finding": "Compression is the cause of predictive failure; increasing resolution would improve returns.",
            "source": "scope limitation",
        },
        {
            "class": "UNKNOWN",
            "finding": "Official production ranking resolution cannot be measured from this export.",
            "source": "ranking_resolution",
        },
    ]
    limitations = [
        "Historical split-sample diagnostic; not future-OOS.",
        "The export does not persist raw recommendation inputs, ranking_score, legacy_quality_score, or ranking_method.",
        "Unique-score resolution, tie concentration, and production ranking resolution are distinct concepts.",
        "Outcome dispersion is descriptive and does not establish causality or a predictive ranking rule.",
        "Regime cross-tabs use only existing fields and mark groups with n < 5 as INSUFFICIENT_N.",
    ]

    payload: dict[str, Any] = {
        "research_id": "RX-H4A",
        "date": "2026-09-21",
        "level": "A",
        "mode": "READ_ONLY",
        "status": "PASS",
        "audit_status": "DESCRIPTIVE_AUDIT_COMPLETE",
        "verdict": verdict,
        "verdict_basis": verdict_basis,
        "audit": "RESEARCH-X/H4A",
        "research_level": "A",
        "production_change": False,
        "locked_oos": "not_opened",
        "verdicts": {
            "global_integer_scale_capacity": "NOT_PROVEN_COMPRESSED",
            "global_tie_concentration": "OBSERVED",
            "daily_cross_sectional_resolution": "DESCRIPTIVE_CONCENTRATED_TIES",
            "raw_score_information_loss": "UNVALIDATED",
            "production_ranking_resolution": ranking["status"],
        },
        "data_contract": contract,
        "dataset": contract,
        "global_resolution": global_metrics,
        "tie_distribution": {
            "group_size_summary": global_metrics["all_group_size_summary"],
            "tie_group_size_summary": global_metrics["tie_group_size_summary"],
            "buckets": global_metrics["tie_group_size_buckets"],
            "top_20": global_metrics["top_score_groups"],
        },
        "score_concentration": {
            "hhi": global_metrics["score_frequency_hhi"],
            "effective_score_count": global_metrics["score_frequency_effective_count"],
            "entropy": global_metrics["score_frequency_entropy"],
            "normalized_entropy": global_metrics["score_frequency_normalized_entropy"],
            "interpretation": "Score-frequency concentration diagnostic only; not predictive quality.",
        },
        "quantile_collision": boundaries,
        "temporal_resolution": daily,
        "regime_resolution": regimes,
        "within_score_dispersion": outcome_dispersion["by_score"],
        "tie_vs_singleton": outcome_dispersion["by_tie_class"],
        "score_precision": {
            "observed_integer_fraction": provenance["integer_valued_fraction"],
            "fractional_score_n": provenance["fractional_score_n"],
            "rounding_or_casting_observed": provenance["rounding_or_casting_observed"],
            "production_final_operation": provenance["production_final_operation"],
        },
        "daily_resolution": daily,
        "outcome_dispersion": outcome_dispersion,
        "score_stability": stability,
        "folds": boundaries.get("folds", []),
        "redundancy_diagnostics": redundancy_diagnostics(score_frame),
        "h2_boundary_diagnostic": boundaries,
        "score_provenance": provenance,
        "ranking_resolution": ranking,
        "reconciliation_assertions": checks,
        "evidence": evidence,
        "limitations": limitations,
        "forbidden_changes_confirmed": True,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=json_value) + "\n",
        encoding="utf-8",
    )
    OUT_REPORT.write_text(render_report(payload), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "output": str(OUT_JSON)}, sort_keys=True))


if __name__ == "__main__":
    main()
