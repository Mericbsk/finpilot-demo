from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

REQUIRED_COLUMNS = {
    "symbol",
    "price",
    "score",
    "regime",
    "direction",
    "entry_ok",
    "timestamp",
    "filter_score",
    "alignment_ratio",
    "momentum_ratio",
}


@dataclass(frozen=True)
class ComparisonProfile:
    name: str
    min_signal_score: int
    min_alignment_ratio: float
    min_momentum_ratio: float
    min_filter_score: int
    min_price: float


@dataclass(frozen=True)
class HistoricalComparisonResult:
    summary: dict[str, Any]
    changes: pd.DataFrame
    per_file: pd.DataFrame
    rows: pd.DataFrame


OPTIMIZED_CANDIDATE = ComparisonProfile(
    name="optimized_candidate",
    min_signal_score=2,
    min_alignment_ratio=0.60,
    min_momentum_ratio=0.40,
    min_filter_score=1,
    min_price=2.0,
)


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _shortlist_root() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "shortlists"


def load_rich_shortlists(
    shortlist_dir: Path | None = None,
) -> tuple[pd.DataFrame, list[str], list[str]]:
    shortlist_dir = shortlist_dir or _shortlist_root()
    frames: list[pd.DataFrame] = []
    used_files: list[str] = []
    skipped_files: list[str] = []

    for csv_path in sorted(shortlist_dir.glob("shortlist_*.csv")):
        try:
            df = pd.read_csv(csv_path)
        except Exception:
            skipped_files.append(csv_path.name)
            continue

        if not REQUIRED_COLUMNS.issubset(df.columns):
            skipped_files.append(csv_path.name)
            continue

        normalized = df.copy()
        normalized["source_file"] = csv_path.name
        normalized["timestamp"] = pd.to_datetime(normalized["timestamp"], errors="coerce")
        normalized = normalized.dropna(subset=["timestamp", "symbol"])

        for bool_col in ["regime", "direction", "entry_ok", "liquidity_ok"]:
            if bool_col in normalized.columns:
                normalized[bool_col] = normalized[bool_col].map(_to_bool)

        for numeric_col in [
            "price",
            "score",
            "filter_score",
            "alignment_ratio",
            "momentum_ratio",
            "risk_reward",
        ]:
            if numeric_col in normalized.columns:
                normalized[numeric_col] = pd.to_numeric(normalized[numeric_col], errors="coerce")

        frames.append(normalized)
        used_files.append(csv_path.name)

    if not frames:
        raise ValueError(f"No rich shortlist files found under {shortlist_dir}")

    return pd.concat(frames, ignore_index=True), used_files, skipped_files


def apply_candidate_profile(
    rows: pd.DataFrame,
    profile: ComparisonProfile = OPTIMIZED_CANDIDATE,
) -> pd.Series:
    candidate = (
        rows["regime"].map(_to_bool)
        & rows["direction"].map(_to_bool)
        & (rows["score"].fillna(-1) >= profile.min_signal_score)
        & (rows["alignment_ratio"].fillna(-1.0) >= profile.min_alignment_ratio)
        & (rows["momentum_ratio"].fillna(-1.0) >= profile.min_momentum_ratio)
        & (rows["filter_score"].fillna(-1.0) >= profile.min_filter_score)
        & (rows["price"].fillna(-1.0) >= profile.min_price)
    )

    if "liquidity_ok" in rows.columns:
        candidate &= rows["liquidity_ok"].map(_to_bool)

    return candidate


def compare_shortlist_history(
    *,
    window_days: int = 365,
    shortlist_dir: Path | None = None,
    candidate_profile: ComparisonProfile = OPTIMIZED_CANDIDATE,
) -> HistoricalComparisonResult:
    rows, used_files, skipped_files = load_rich_shortlists(shortlist_dir)

    end_ts = rows["timestamp"].max()
    start_ts = end_ts - pd.Timedelta(days=window_days - 1)
    windowed = rows.loc[rows["timestamp"] >= start_ts].copy()

    windowed["baseline_entry_ok"] = windowed["entry_ok"].map(_to_bool)
    windowed["candidate_entry_ok"] = apply_candidate_profile(windowed, candidate_profile)

    windowed["change_type"] = "unchanged_false"
    windowed.loc[
        windowed["baseline_entry_ok"] & windowed["candidate_entry_ok"],
        "change_type",
    ] = "unchanged_true"
    windowed.loc[
        (~windowed["baseline_entry_ok"]) & windowed["candidate_entry_ok"],
        "change_type",
    ] = "added_by_candidate"
    windowed.loc[
        windowed["baseline_entry_ok"] & (~windowed["candidate_entry_ok"]),
        "change_type",
    ] = "removed_by_candidate"

    changes = windowed.loc[
        windowed["change_type"].isin(["added_by_candidate", "removed_by_candidate"])
    ].copy()
    changes = changes.sort_values(
        ["timestamp", "source_file", "symbol"], ascending=[True, True, True]
    )

    per_file = (
        windowed.groupby("source_file", as_index=False)
        .agg(
            timestamp=("timestamp", "max"),
            symbols=("symbol", "count"),
            baseline_true=("baseline_entry_ok", "sum"),
            candidate_true=("candidate_entry_ok", "sum"),
        )
        .sort_values(["timestamp", "source_file"])
    )
    per_file["added_by_candidate"] = per_file["candidate_true"] - per_file["baseline_true"]

    baseline_true = int(windowed["baseline_entry_ok"].sum())
    candidate_true = int(windowed["candidate_entry_ok"].sum())
    overlap_true = int((windowed["baseline_entry_ok"] & windowed["candidate_entry_ok"]).sum())
    union_true = int((windowed["baseline_entry_ok"] | windowed["candidate_entry_ok"]).sum())

    summary = {
        "window_days_requested": window_days,
        "coverage_start": windowed["timestamp"].min().strftime("%Y-%m-%d %H:%M"),
        "coverage_end": windowed["timestamp"].max().strftime("%Y-%m-%d %H:%M"),
        "coverage_days_actual": int(
            (windowed["timestamp"].max() - windowed["timestamp"].min()).days
        ),
        "files_used": len(used_files),
        "files_skipped": len(skipped_files),
        "rows_evaluated": int(len(windowed)),
        "baseline_true": baseline_true,
        "candidate_true": candidate_true,
        "added_by_candidate": int(
            (~windowed["baseline_entry_ok"] & windowed["candidate_entry_ok"]).sum()
        ),
        "removed_by_candidate": int(
            (windowed["baseline_entry_ok"] & ~windowed["candidate_entry_ok"]).sum()
        ),
        "unchanged_true": overlap_true,
        "unchanged_false": int(
            (~windowed["baseline_entry_ok"] & ~windowed["candidate_entry_ok"]).sum()
        ),
        "true_signal_overlap_pct": round((overlap_true / union_true) * 100, 2)
        if union_true
        else 100.0,
        "baseline_signal_rate_pct": round((baseline_true / len(windowed)) * 100, 2),
        "candidate_signal_rate_pct": round((candidate_true / len(windowed)) * 100, 2),
        "candidate_profile": asdict(candidate_profile),
        "top_added_symbols": changes.loc[changes["change_type"] == "added_by_candidate", "symbol"]
        .value_counts()
        .head(15)
        .to_dict(),
        "top_removed_symbols": changes.loc[
            changes["change_type"] == "removed_by_candidate", "symbol"
        ]
        .value_counts()
        .head(15)
        .to_dict(),
    }

    return HistoricalComparisonResult(
        summary=summary,
        changes=changes,
        per_file=per_file,
        rows=windowed,
    )
