"""RESEARCH-X/H2 — frozen score-direction test runner.

This runner implements the pre-registration in
reports/research_x_h2_score_direction_preregistration_2026-09-21.md.
It is research-only: it does not change production scoring, ranking, flags,
source data, or user-facing behavior.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

DATA = Path("data/backtest_out/full_universe_enriched_eod_only.csv")
OUT_JSON = Path("data/backtest_out/research_x_h2_score_direction_2026-09-21.json")
OUT_REPORT = Path("reports/research_x_h2_score_direction_2026-09-21.md")

SEED = 20260921
BOOT_B = 2_000
MATCHED_R = 1_000
QUANTILES = (0.2, 0.4, 0.6, 0.8)
ANALYSIS_START = pd.Timestamp("2026-05-01")
ANALYSIS_END = pd.Timestamp("2026-07-31")

FOLDS = (
    {
        "name": "F1",
        "train_start": pd.Timestamp("2026-05-01"),
        "train_end": pd.Timestamp("2026-05-31"),
        "test_start": pd.Timestamp("2026-06-01"),
        "test_end": pd.Timestamp("2026-06-30"),
    },
    {
        "name": "F2",
        "train_start": pd.Timestamp("2026-05-01"),
        "train_end": pd.Timestamp("2026-06-30"),
        "test_start": pd.Timestamp("2026-07-01"),
        "test_end": pd.Timestamp("2026-07-31"),
    },
)


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


def round_or_none(value: Any, digits: int = 6) -> float | None:
    if value is None or not np.isfinite(float(value)):
        return None
    return round(float(value), digits)


def date_range(frame: pd.DataFrame) -> list[str | None]:
    if frame.empty:
        return [None, None]
    return [
        frame["scan_date"].min().date().isoformat(),
        frame["scan_date"].max().date().isoformat(),
    ]


def load_data() -> tuple[pd.DataFrame, dict[str, Any]]:
    required = {"symbol", "scan_date", "composite_score", "c2c_5d", "label_entry_basis"}
    frame = pd.read_csv(DATA, low_memory=False)
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"missing required columns: {missing}")

    raw_n = len(frame)
    frame["scan_date"] = pd.to_datetime(frame["scan_date"], errors="coerce")
    frame = frame.sort_values(["scan_date", "symbol"], kind="stable")
    duplicate_n = int(frame.duplicated(subset=["symbol", "scan_date"], keep="first").sum())
    frame = frame.drop_duplicates(subset=["symbol", "scan_date"], keep="first").copy()
    deduplicated_n = len(frame)

    basis = frame["label_entry_basis"].astype("string").str.lower()
    non_eod_n = int((basis != "eod_close").fillna(True).sum())
    frame = frame[basis == "eod_close"].copy()
    missing_value_n = int(
        frame[["scan_date", "symbol", "composite_score", "c2c_5d"]].isna().any(axis=1).sum()
    )
    frame = frame.dropna(subset=["scan_date", "symbol", "composite_score", "c2c_5d"]).copy()

    outside = frame[(frame["scan_date"] < ANALYSIS_START) | (frame["scan_date"] > ANALYSIS_END)]
    frame = frame[
        (frame["scan_date"] >= ANALYSIS_START) & (frame["scan_date"] <= ANALYSIS_END)
    ].copy()
    frame["composite_score"] = pd.to_numeric(frame["composite_score"], errors="coerce")
    frame["c2c_5d"] = pd.to_numeric(frame["c2c_5d"], errors="coerce")
    frame = frame.dropna(subset=["composite_score", "c2c_5d"]).copy()

    contract = {
        "input_csv": str(DATA).replace("\\", "/"),
        "raw_n": raw_n,
        "deduplicated_n": deduplicated_n,
        "duplicate_rows_removed": duplicate_n,
        "non_eod_rows_excluded": non_eod_n,
        "missing_value_rows_excluded": missing_value_n,
        "outside_preregistered_window_excluded": len(outside),
        "analysis_n": len(frame),
        "analysis_range": date_range(frame),
        "label_entry_basis_required": "eod_close",
        "score_field": "composite_score",
        "outcome_field": "c2c_5d",
    }
    return frame, contract


def assign_bands(scores: np.ndarray, cutpoints: np.ndarray) -> np.ndarray:
    """Assign tie-preserving train-derived bands; no random tie-break is used."""
    bands = np.full(len(scores), -1, dtype=int)
    q20, q40, q60, q80 = cutpoints
    bands[scores <= q20] = 0
    bands[(scores > q20) & (scores <= q40)] = 1
    bands[(scores > q40) & (scores <= q60)] = 2
    bands[(scores > q60) & (scores <= q80)] = 3
    bands[scores > q80] = 4
    return bands


def rate(values: np.ndarray, predicate) -> float | None:
    if len(values) == 0:
        return None
    return float(predicate(values).mean())


def metric_table(values: np.ndarray, bands: np.ndarray) -> list[dict[str, Any]]:
    table = []
    for band in range(5):
        selected = values[bands == band]
        table.append(
            {
                "quantile": f"Q{band + 1}",
                "quantile_index": band + 1,
                "n": int(len(selected)),
                "median_c2c_5d": round_or_none(np.median(selected)) if len(selected) else None,
                "mean_c2c_5d": round_or_none(np.mean(selected)) if len(selected) else None,
                "p_return_lt_0": round_or_none(rate(selected, lambda x: x < 0)),
                "p_big_loser_le_minus_10": round_or_none(rate(selected, lambda x: x <= -10)),
                "p_big_winner_ge_plus_10": round_or_none(rate(selected, lambda x: x >= 10)),
            }
        )
    return table


def spearman_quantile_medians(table: list[dict[str, Any]]) -> float | None:
    valid = [row for row in table if row["median_c2c_5d"] is not None]
    if len(valid) < 3:
        return None
    medians = np.array([row["median_c2c_5d"] for row in valid], dtype=float)
    ordinal = np.array([row["quantile_index"] for row in valid], dtype=float)
    if np.std(medians) == 0:
        return 0.0
    median_ranks = pd.Series(medians).rank(method="average").to_numpy(dtype=float)
    return round_or_none(np.corrcoef(ordinal, median_ranks)[0, 1])


def contrasts(table: list[dict[str, Any]]) -> dict[str, float | None]:
    first = table[0]
    last = table[4]
    fields = (
        "median_c2c_5d",
        "mean_c2c_5d",
        "p_return_lt_0",
        "p_big_loser_le_minus_10",
        "p_big_winner_ge_plus_10",
    )
    result = {}
    for field in fields:
        left, right = first[field], last[field]
        result[f"q1_minus_q5_{field}"] = (
            round_or_none(left - right) if left is not None and right is not None else None
        )
    medians = [row["median_c2c_5d"] for row in table]
    result["adjacent_inverse_pairs"] = int(
        sum(
            medians[i] is not None and medians[i + 1] is not None and medians[i] >= medians[i + 1]
            for i in range(4)
        )
    )
    result["adjacent_pairs"] = 4
    result["spearman_quantile_vs_median"] = spearman_quantile_medians(table)
    return result


def summarize(values: np.ndarray) -> dict[str, Any]:
    clean = values[np.isfinite(values)]
    if len(clean) == 0:
        return {"n": 0, "mean": None, "ci_95": [None, None]}
    lo, hi = np.percentile(clean, [2.5, 97.5])
    return {
        "n": int(len(clean)),
        "mean": round_or_none(np.mean(clean)),
        "ci_95": [round_or_none(lo), round_or_none(hi)],
    }


def bootstrap_contrasts(
    values_by_date: list[np.ndarray], bands_by_date: list[np.ndarray], seed: int
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    date_count = len(values_by_date)
    fields = (
        "median_c2c_5d",
        "mean_c2c_5d",
        "p_return_lt_0",
        "p_big_loser_le_minus_10",
        "p_big_winner_ge_plus_10",
    )
    samples = {field: [] for field in fields}
    if date_count == 0:
        return {field: summarize(np.array([])) for field in fields}

    for _ in range(BOOT_B):
        selected_dates = rng.integers(0, date_count, size=date_count)
        values = np.concatenate([values_by_date[index] for index in selected_dates])
        bands = np.concatenate([bands_by_date[index] for index in selected_dates])
        table = metric_table(values, bands)
        q1, q5 = table[0], table[4]
        for field in fields:
            left, right = q1[field], q5[field]
            samples[field].append(
                left - right if left is not None and right is not None else np.nan
            )

    return {field: summarize(np.asarray(sample, dtype=float)) for field, sample in samples.items()}


def matched_random_control(
    values_by_date: list[np.ndarray],
    bands_by_date: list[np.ndarray],
    observed_contrasts: dict[str, float | None],
    seed: int,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    median_contrasts = []
    winner_contrasts = []
    loser_contrasts = []
    negative_contrasts = []

    for _ in range(MATCHED_R):
        random_values = []
        random_bands = []
        for values, observed_bands in zip(values_by_date, bands_by_date, strict=True):
            counts = np.bincount(observed_bands, minlength=5)
            labels = np.repeat(np.arange(5), counts)
            random_bands.append(rng.permutation(labels))
            random_values.append(values)
        table = metric_table(np.concatenate(random_values), np.concatenate(random_bands))
        q1, q5 = table[0], table[4]
        median_contrasts.append(q1["median_c2c_5d"] - q5["median_c2c_5d"])
        winner_contrasts.append(q1["p_big_winner_ge_plus_10"] - q5["p_big_winner_ge_plus_10"])
        loser_contrasts.append(q1["p_big_loser_le_minus_10"] - q5["p_big_loser_le_minus_10"])
        negative_contrasts.append(q1["p_return_lt_0"] - q5["p_return_lt_0"])

    def p_upper(observed: float | None, null: list[float]) -> float | None:
        if observed is None or not null:
            return None
        clean = np.asarray(null, dtype=float)
        return round_or_none((1 + np.sum(clean >= observed)) / (len(clean) + 1), 6)

    return {
        "repetitions": MATCHED_R,
        "median_q1_minus_q5": summarize(np.asarray(median_contrasts, dtype=float)),
        "big_winner_q1_minus_q5": summarize(np.asarray(winner_contrasts, dtype=float)),
        "big_loser_q1_minus_q5": summarize(np.asarray(loser_contrasts, dtype=float)),
        "negative_rate_q1_minus_q5": summarize(np.asarray(negative_contrasts, dtype=float)),
        "primary_p_value": p_upper(
            observed_contrasts.get("q1_minus_q5_median_c2c_5d"), median_contrasts
        ),
        "big_winner_p_value": p_upper(
            observed_contrasts.get("q1_minus_q5_p_big_winner_ge_plus_10"), winner_contrasts
        ),
    }


def fold_result(frame: pd.DataFrame, spec: dict[str, Any], fold_index: int) -> dict[str, Any]:
    train = frame[
        (frame["scan_date"] >= spec["train_start"]) & (frame["scan_date"] <= spec["train_end"])
    ].copy()
    test = frame[
        (frame["scan_date"] >= spec["test_start"]) & (frame["scan_date"] <= spec["test_end"])
    ].copy()
    if train.empty or test.empty:
        return {
            "fold": spec["name"],
            "status": "INSUFFICIENT_DATA",
            "train_n": len(train),
            "test_n": len(test),
            "train_range": date_range(train),
            "test_range": date_range(test),
            "reason": "empty train or test window",
        }

    train_scores = train["composite_score"].to_numpy(dtype=float)
    cutpoints = np.quantile(train_scores, QUANTILES, method="linear")
    test_scores = test["composite_score"].to_numpy(dtype=float)
    test["quantile_index"] = assign_bands(test_scores, cutpoints)
    values = test["c2c_5d"].to_numpy(dtype=float)
    bands = test["quantile_index"].to_numpy(dtype=int)
    table = metric_table(values, bands)
    distinct_test_dates = int(test["scan_date"].nunique())
    bin_counts = [row["n"] for row in table]
    duplicate_boundaries = bool(np.any(np.diff(cutpoints) == 0))
    boundary_share = {
        f"q{int(q * 100)}": round_or_none(float(np.mean(np.isclose(test_scores, cutpoint))), 6)
        for q, cutpoint in zip(QUANTILES, cutpoints, strict=True)
    }

    values_by_date = []
    bands_by_date = []
    for _, group in test.sort_values(["scan_date", "symbol"], kind="stable").groupby(
        "scan_date", sort=True
    ):
        values_by_date.append(group["c2c_5d"].to_numpy(dtype=float))
        bands_by_date.append(group["quantile_index"].to_numpy(dtype=int))

    tie_resolution_ok = all(count > 0 for count in bin_counts)
    enough_dates = distinct_test_dates >= 5
    status = "OK" if tie_resolution_ok and enough_dates else "INSUFFICIENT_DATA"
    reason = None
    if not tie_resolution_ok:
        status = "INSUFFICIENT_TIE_RESOLUTION"
        reason = "at least one train-derived quantile band is empty in test"
    elif not enough_dates:
        reason = "fewer than 5 distinct test scan dates"

    result: dict[str, Any] = {
        "fold": spec["name"],
        "status": status,
        "reason": reason,
        "train_window": [
            spec["train_start"].date().isoformat(),
            spec["train_end"].date().isoformat(),
        ],
        "test_window": [spec["test_start"].date().isoformat(), spec["test_end"].date().isoformat()],
        "train_n": len(train),
        "test_n": len(test),
        "train_range": date_range(train),
        "test_range": date_range(test),
        "test_distinct_scan_dates": distinct_test_dates,
        "train_unique_score_count": int(train["composite_score"].nunique()),
        "test_unique_score_count": int(test["composite_score"].nunique()),
        "train_quantile_cutpoints": [round_or_none(value) for value in cutpoints],
        "duplicate_train_boundaries": duplicate_boundaries,
        "test_boundary_score_share": boundary_share,
        "test_bin_counts": bin_counts,
        "quantile_metrics": table,
        "contrasts": contrasts(table),
        "controls": None,
    }
    result["_test_values"] = values
    result["_test_bands"] = bands
    if status == "OK":
        result["controls"] = {
            "date_block_bootstrap": bootstrap_contrasts(
                values_by_date, bands_by_date, SEED + fold_index * 10
            ),
            "matched_random_ordering": matched_random_control(
                values_by_date,
                bands_by_date,
                result["contrasts"],
                SEED + fold_index * 10 + 1,
            ),
        }
    return result


def primary_pass(result: dict[str, Any]) -> bool:
    if result.get("status") != "OK" or not result.get("controls"):
        return False
    contrast = result["contrasts"].get("q1_minus_q5_median_c2c_5d")
    ci = result["controls"]["date_block_bootstrap"]["median_c2c_5d"]["ci_95"]
    observed_p = result["controls"]["matched_random_ordering"].get("primary_p_value")
    return bool(
        contrast is not None
        and contrast > 0
        and ci[0] is not None
        and ci[0] > 0
        and observed_p is not None
        and observed_p < 0.05
        and result["contrasts"].get("adjacent_inverse_pairs", 0) >= 3
    )


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# RESEARCH-X/H2 — Score-Direction Test Result",
        "",
        "**Tarih:** 2026-09-21  ",
        "**Status:** historical split-sample; true future-OOS değil  ",
        "**Pre-registration:** `reports/research_x_h2_score_direction_preregistration_2026-09-21.md`  ",
        "**Runner:** `research/research_x_h2_score_direction_2026_09_21.py`",
        "",
        f"**Overall H2a verdict:** `{result['verdicts']['h2a']}`",
        "",
        "Bu rapor yalnızca preregistered `composite_score` quantile/outcome ölçümünü verir. `ranking_score` eşdeğerliği, reverse score veya production kuralı sonucu çıkarılmaz.",
        "",
        "## Fold sonuçları",
        "",
    ]
    for fold in result["folds"]:
        lines.extend(
            [
                f"### {fold['fold']} — `{fold['status']}`",
                "",
                f"Train: `{fold.get('train_window')}` · Test: `{fold.get('test_window')}` · n={fold.get('test_n')}",
                "",
            ]
        )
        if fold.get("reason"):
            lines.extend([f"Reason: {fold['reason']}", ""])
        lines.extend(
            [
                "| Quantile | n | Median c2c_5d | Mean | P(<0) | P(<=-10) | P(>=+10) |",
                "|---|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for row in fold.get("quantile_metrics", []):
            lines.append(
                f"| {row['quantile']} | {row['n']} | {row['median_c2c_5d']} | {row['mean_c2c_5d']} | "
                f"{row['p_return_lt_0']} | {row['p_big_loser_le_minus_10']} | {row['p_big_winner_ge_plus_10']} |"
            )
        lines.extend(
            [
                "",
                f"Q1−Q5 median: `{fold.get('contrasts', {}).get('q1_minus_q5_median_c2c_5d')}` · "
                f"adjacent inverse pairs: `{fold.get('contrasts', {}).get('adjacent_inverse_pairs')}/4` · "
                f"Spearman: `{fold.get('contrasts', {}).get('spearman_quantile_vs_median')}`",
                "",
                f"Secondary Q1−Q5 contrasts: big-winner `{fold.get('contrasts', {}).get('q1_minus_q5_p_big_winner_ge_plus_10')}` · "
                f"big-loser `{fold.get('contrasts', {}).get('q1_minus_q5_p_big_loser_le_minus_10')}` · "
                f"negative-rate `{fold.get('contrasts', {}).get('q1_minus_q5_p_return_lt_0')}`",
                "",
                f"Train unique scores: `{fold.get('train_unique_score_count')}` · "
                f"cutpoints: `{fold.get('train_quantile_cutpoints')}` · "
                f"test bin counts: `{fold.get('test_bin_counts')}` · "
                f"boundary shares: `{fold.get('test_boundary_score_share')}`",
                "",
            ]
        )
        controls = fold.get("controls")
        if controls:
            bootstrap = controls["date_block_bootstrap"]
            random_control = controls["matched_random_ordering"]
            lines.extend(
                [
                    "**Date-block bootstrap (B=2,000) Q1−Q5 CI:**",
                    f"median `{bootstrap['median_c2c_5d']['ci_95']}` · "
                    f"mean `{bootstrap['mean_c2c_5d']['ci_95']}` · "
                    f"P(<0) `{bootstrap['p_return_lt_0']['ci_95']}` · "
                    f"P(<=-10) `{bootstrap['p_big_loser_le_minus_10']['ci_95']}` · "
                    f"P(>=+10) `{bootstrap['p_big_winner_ge_plus_10']['ci_95']}`",
                    "",
                    "**Matched-date randomized ordering (R=1,000):** "
                    f"primary median raw one-sided p=`{random_control['primary_p_value']}` · "
                    f"big-winner raw one-sided p=`{random_control['big_winner_p_value']}` · "
                    f"null median CI=`{random_control['median_q1_minus_q5']['ci_95']}` · "
                    f"big-winner CI=`{random_control['big_winner_q1_minus_q5']['ci_95']}` · "
                    f"big-loser CI=`{random_control['big_loser_q1_minus_q5']['ci_95']}` · "
                    f"negative-rate CI=`{random_control['negative_rate_q1_minus_q5']['ci_95']}`",
                    "",
                ]
            )
    pooled = result.get("pooled")
    if pooled and pooled.get("status") == "OK":
        lines.extend(
            [
                "## Pooled diagnostic",
                "",
                "Fold-specific train cutpoints remain primary. This pooled table is a predeclared diagnostic for whether the inverse pattern is driven by one endpoint bin.",
                "",
                "| Quantile | n | Median c2c_5d | Mean | P(<0) | P(<=-10) | P(>=+10) |",
                "|---|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for row in pooled["quantile_metrics"]:
            lines.append(
                f"| {row['quantile']} | {row['n']} | {row['median_c2c_5d']} | {row['mean_c2c_5d']} | "
                f"{row['p_return_lt_0']} | {row['p_big_loser_le_minus_10']} | {row['p_big_winner_ge_plus_10']} |"
            )
        lines.extend(
            [
                "",
                f"Pooled Q1−Q5 median: `{pooled['contrasts']['q1_minus_q5_median_c2c_5d']}` · "
                f"adjacent inverse pairs: `{pooled['contrasts']['adjacent_inverse_pairs']}/4` · "
                f"Spearman: `{pooled['contrasts']['spearman_quantile_vs_median']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Guardrails",
            "",
            "- Score field: `composite_score`; no score refit, inversion, flag change or production change.",
            "- Fold design is chronological but historical; it is not true future-OOS.",
            "- Empty bins or insufficient dates remain explicit blockers; no post-hoc quantile/threshold repair was applied.",
            "- H2d remains deferred until H2a-c, tie-resolution and `ranking_score` mapping are separately resolved.",
            "",
            "## Governance",
            "",
            "Read-only research artifact. Negative, mixed or insufficient results are valid outcomes; no production promotion follows from this report.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    frame, contract = load_data()
    folds = [fold_result(frame, spec, index) for index, spec in enumerate(FOLDS)]

    pooled_parts = [
        (fold["_test_values"], fold["_test_bands"])
        for fold in folds
        if "_test_values" in fold and "_test_bands" in fold
    ]
    if len(pooled_parts) == len(FOLDS):
        pooled_values = np.concatenate([part[0] for part in pooled_parts])
        pooled_bands = np.concatenate([part[1] for part in pooled_parts])
        pooled_table = metric_table(pooled_values, pooled_bands)
        pooled = {
            "status": "OK",
            "quantile_metrics": pooled_table,
            "contrasts": contrasts(pooled_table),
        }
    else:
        pooled = {"status": "INSUFFICIENT_DATA"}
    for fold in folds:
        fold.pop("_test_values", None)
        fold.pop("_test_bands", None)

    valid_folds = [fold for fold in folds if fold.get("status") == "OK"]
    pooled_primary_ok = (
        pooled.get("status") == "OK" and pooled["contrasts"].get("adjacent_inverse_pairs", 0) >= 3
    )
    if len(valid_folds) < len(FOLDS):
        h2a_verdict = "INSUFFICIENT_DATA"
    elif all(primary_pass(fold) for fold in valid_folds) and pooled_primary_ok:
        h2a_verdict = "SUPPORTED"
    elif any(primary_pass(fold) for fold in valid_folds):
        h2a_verdict = "PARTIAL"
    else:
        h2a_verdict = "NOT_SUPPORTED"

    result = {
        "preregistration": "reports/research_x_h2_score_direction_preregistration_2026-09-21.md",
        "seed": SEED,
        "bootstrap_repetitions": BOOT_B,
        "matched_random_repetitions": MATCHED_R,
        "analysis_window": [ANALYSIS_START.date().isoformat(), ANALYSIS_END.date().isoformat()],
        "future_oos": False,
        "data_contract": contract,
        "folds": folds,
        "pooled": pooled,
        "verdicts": {
            "h2a": h2a_verdict,
            "h2b": "REPORTED_AS_SECONDARY",
            "h2c": "REPORTED_AS_DIRECTIONLESS_SECONDARY",
        },
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(result, indent=2, default=json_value), encoding="utf-8")
    OUT_REPORT.write_text(render_report(result), encoding="utf-8")
    print(json.dumps(result, indent=2, default=json_value))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
