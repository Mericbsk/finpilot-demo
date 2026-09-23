"""RESEARCH-X/H4B - production ranking mapping reconstruction.

This runner is a read-only forensic audit. It reconstructs the implemented
score-source branch and publication ordering from repository code, then checks
which parts can and cannot be replayed from the canonical historical export.
It does not change a score, ranking, threshold, scanner, configuration, or
publication path.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/backtest_out/full_universe_enriched_eod_only.csv"
OUT_JSON = ROOT / "data/backtest_out/research_x_h4b_ranking_mapping_2026-09-21.json"
OUT_REPORT = ROOT / "reports/research_x_h4b_ranking_mapping_2026-09-21.md"
AUDIT_DATE = "2026-09-21"
SCORE_FIELD = "composite_score"
FLAG = "FINPILOT_ENABLE_LEGACY_COMPOSITE_RANKING"

SOURCE_FILES = {
    "score_engine": ROOT / "scanner/score_engine.py",
    "evaluate": ROOT / "scanner/evaluate.py",
    "snapshot_builder": ROOT / "distribution/snapshot_builder.py",
    "scan_summary": ROOT / "scanner/scan_summary.py",
    "distribution_jobs": ROOT / "distribution/jobs.py",
    "prepublish_gate": ROOT / "distribution/prepublish_gate.py",
}

BASE_PROXY_FIELDS = (
    "regime",
    "direction",
    "score",
    "atr_pct_real",
    "rvol",
)
OPTIONAL_PROXY_FIELDS = (
    "squeeze_factor",
    "lottery_factor",
    "overnight_gap_factor",
)

SECTION_TITLES = (
    "Executive Result",
    "Research Question",
    "Governance and Scope",
    "Dataset and Provenance",
    "Production Path Under Audit",
    "Raw Features to Composite Score",
    "Composite Score Storage",
    "Ranking Score Definition",
    "Configuration and Flag Provenance",
    "Mapping Relationship",
    "Additional Inputs",
    "Ranking Method Provenance",
    "Candidate Eligibility",
    "Public Snapshot Ordering",
    "Summary and Alert Ordering",
    "Tie-Breakers and Stability",
    "Historical Ranking Coverage",
    "Reconstructed Score Diagnostics",
    "Resolution Definition",
    "Evidence vs Interpretation",
    "Limitations and Not Proven",
    "Production Impact and Next Question",
)


def path_ref(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rounded(value: Any, digits: int = 6) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return round(number, digits) if np.isfinite(number) else None


def json_value(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if pd.isna(value):
        return None
    return value


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and np.isfinite(float(value)):
        return bool(value)
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def optional_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if np.isfinite(number) else None


def load_legacy_quality_score() -> Any:
    score_engine_path = ROOT / "scanner/score_engine.py"
    spec = importlib.util.spec_from_file_location("_h4b_score_engine", score_engine_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load score engine from {score_engine_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.compute_legacy_quality_score


def safe_corr(left: pd.Series, right: pd.Series, method: str) -> float | None:
    if len(left) < 3 or left.nunique(dropna=True) < 2 or right.nunique(dropna=True) < 2:
        return None
    try:
        return rounded(left.corr(right, method=method))
    except (TypeError, ValueError):
        return None


def date_range(frame: pd.DataFrame) -> list[str | None]:
    if frame.empty:
        return [None, None]
    return [
        frame["scan_date"].min().date().isoformat(),
        frame["scan_date"].max().date().isoformat(),
    ]


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    if not DATA.exists():
        raise FileNotFoundError(DATA)

    frame = pd.read_csv(DATA, low_memory=False)
    required = {"symbol", "scan_ts", "scan_date", SCORE_FIELD, "label_entry_basis"}
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
    score_frame = frame.dropna(subset=[SCORE_FIELD]).copy()

    contract = {
        "input_csv": path_ref(DATA),
        "input_sha256": sha256(DATA),
        "raw_n": raw_n,
        "deduplicated_n": len(frame),
        "duplicate_rows_removed": duplicate_n,
        "invalid_scan_date_rows": invalid_date_n,
        "invalid_symbol_rows": invalid_symbol_n,
        "non_eod_rows_excluded": non_eod_n,
        "composite_missing_rows": int(frame[SCORE_FIELD].isna().sum()),
        "composite_n": len(score_frame),
        "composite_date_range": date_range(score_frame),
        "composite_unique_dates": int(score_frame["scan_date"].nunique()),
        "label_entry_basis_required": "eod_close",
        "deduplication_rule": (
            "one row per symbol/scan_date, retaining earliest lexical scan_ts; "
            "stable first row on exact ties"
        ),
        "ranking_fields_persisted": {
            field: field in frame.columns
            for field in ("ranking_score", "legacy_quality_score", "ranking_method")
        },
        "historical_columns": list(frame.columns),
    }
    return frame, score_frame, contract


def function_spans(path: Path) -> dict[str, dict[str, int]]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    spans: dict[str, dict[str, int]] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            spans[node.name] = {
                "start_line": int(node.lineno),
                "end_line": int(getattr(node, "end_lineno", node.lineno)),
            }
    return spans


def line_for(path: Path, needle: str) -> int | None:
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if needle in line:
            return line_number
    return None


def source_evidence() -> dict[str, Any]:
    evidence: dict[str, Any] = {}
    for name, path in SOURCE_FILES.items():
        if not path.exists():
            evidence[name] = {"path": path_ref(path), "status": "MISSING"}
            continue
        spans = function_spans(path)
        evidence[name] = {
            "path": path_ref(path),
            "sha256": sha256(path),
            "status": "AVAILABLE",
            "functions": {
                name: spans[name]
                for name in (
                    "compute_legacy_quality_score",
                    "compute_recommendation_score",
                    "compute_recommendation_strength",
                    "legacy_composite_ranking_enabled",
                    "evaluate_symbol",
                    "_sort_key",
                    "_grade_of",
                    "_public_candidate",
                    "build_snapshot",
                    "_rank",
                    "build_candidate_pool",
                    "summarize_full_scan",
                    "_persist_distribution_export",
                )
                if name in spans
            },
        }

    line_checks = {
        "evaluate_score_input": (
            SOURCE_FILES["evaluate"],
            '"_score_input"',
        ),
        "evaluate_composite_assignment": (
            SOURCE_FILES["evaluate"],
            "_composite_score = compute_recommendation_strength",
        ),
        "evaluate_legacy_assignment": (
            SOURCE_FILES["evaluate"],
            "_legacy_quality_score = compute_legacy_quality_score",
        ),
        "evaluate_ranking_selection": (
            SOURCE_FILES["evaluate"],
            "_ranking_score = (",
        ),
        "evaluate_ranking_method": (
            SOURCE_FILES["evaluate"],
            '"ranking_method": "legacy_quality"',
        ),
        "snapshot_sort_key": (SOURCE_FILES["snapshot_builder"], "def _sort_key"),
        "snapshot_score_fallback": (
            SOURCE_FILES["snapshot_builder"],
            'row.get("ranking_score")',
        ),
        "snapshot_sort_call": (
            SOURCE_FILES["snapshot_builder"],
            "graded.sort(key=_sort_key)",
        ),
        "summary_rank_key": (SOURCE_FILES["scan_summary"], "def _rank"),
        "summary_sort_call": (SOURCE_FILES["scan_summary"], "cand.sort(key=_rank)"),
        "jobs_snapshot_caller": (SOURCE_FILES["distribution_jobs"], "snap = build_snapshot"),
    }
    evidence["line_checks"] = {
        name: {"path": path_ref(path), "line": line_for(path, needle)}
        for name, (path, needle) in line_checks.items()
    }
    return evidence


def dotenv_value(key: str) -> str | None:
    dotenv = ROOT / ".env"
    if not dotenv.exists():
        return None
    value: str | None = None
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=\s*(.*?)\s*(?:#.*)?$")
    for line in dotenv.read_text(encoding="utf-8", errors="replace").splitlines():
        match = pattern.match(line)
        if match:
            value = match.group(1).strip().strip('"').strip("'")
    return value


def flag_provenance() -> dict[str, Any]:
    process_value = os.environ.get(FLAG)
    file_value = dotenv_value(FLAG)
    effective_value = process_value if process_value is not None else "0"
    return {
        "flag": FLAG,
        "source_code_default": "0",
        "process_environment_value": process_value,
        "repository_dotenv_value": file_value,
        "runner_effective_value": effective_value,
        "runner_effective_legacy_override_enabled": effective_value == "1",
        "dotenv_implicitly_loaded_by_score_engine": False,
        "live_process_confirmation": "NOT_PERFORMED_BY_THIS_RUNNER",
        "interpretation": (
            "The score engine reads os.environ directly. A repository .env value is recorded "
            "as provenance only unless the caller has loaded it into the process environment."
        ),
    }


def legacy_proxy_diagnostics(score_frame: pd.DataFrame) -> dict[str, Any]:
    compute_legacy_quality_score = load_legacy_quality_score()
    values: list[float | None] = []
    missing_by_field = {field: 0 for field in BASE_PROXY_FIELDS}
    for _, row in score_frame.iterrows():
        parsed: dict[str, Any] = {}
        missing = False
        for field in BASE_PROXY_FIELDS:
            if field in {"regime", "direction"}:
                parsed[field] = parse_bool(row.get(field))
                continue
            parsed[field] = optional_float(row.get(field))
            if parsed[field] is None:
                missing_by_field[field] += 1
                missing = True
        if missing:
            values.append(None)
            continue
        optional = {field: optional_float(row.get(field)) for field in OPTIONAL_PROXY_FIELDS}
        values.append(
            compute_legacy_quality_score(
                regime=parsed["regime"],
                direction=parsed["direction"],
                raw_score=parsed["score"],
                atr_pct=parsed["atr_pct_real"],
                rvol=parsed["rvol"],
                squeeze_factor=optional["squeeze_factor"],
                lottery_factor=optional["lottery_factor"],
                overnight_gap_factor=optional["overnight_gap_factor"],
            )
        )

    proxy = pd.Series(values, index=score_frame.index, dtype="float64")
    both = score_frame.loc[proxy.notna(), [SCORE_FIELD]].copy()
    both["legacy_quality_proxy"] = proxy.loc[proxy.notna()]
    proxy_values = proxy.dropna().to_numpy(dtype=float)
    integer_mask = np.isclose(proxy_values, np.round(proxy_values), atol=1e-12)
    return {
        "field_name": "legacy_quality_score_historical_proxy",
        "formula_source": "scanner/score_engine.py::compute_legacy_quality_score",
        "proxy_is_persisted_ranking": False,
        "calculable_n": int(proxy.notna().sum()),
        "not_calculable_n": int(proxy.isna().sum()),
        "missing_base_input_counts": missing_by_field,
        "unique_values": int(proxy.nunique(dropna=True)),
        "finite_summary": {
            "n": int(len(proxy_values)),
            "min": rounded(np.min(proxy_values)) if len(proxy_values) else None,
            "max": rounded(np.max(proxy_values)) if len(proxy_values) else None,
            "median": rounded(np.median(proxy_values)) if len(proxy_values) else None,
            "integer_valued_fraction": rounded(float(integer_mask.mean()))
            if len(proxy_values)
            else None,
        },
        "comparable_n": int(len(both)),
        "proxy_vs_composite": {
            "pearson": safe_corr(both["legacy_quality_proxy"], both[SCORE_FIELD], "pearson"),
            "spearman": safe_corr(both["legacy_quality_proxy"], both[SCORE_FIELD], "spearman"),
        },
        "interpretation": (
            "This is a historical back-computation from export fields, not proof that the "
            "historical process emitted this exact ranking_score. Current evaluator provenance, "
            "feature timestamps, and persisted ranking_score are absent from the CSV."
        ),
    }


def score_resolution(score_frame: pd.DataFrame, proxy: dict[str, Any]) -> dict[str, Any]:
    scores = pd.to_numeric(score_frame[SCORE_FIELD], errors="coerce").dropna()
    counts = scores.value_counts()
    tie_n = int(counts[counts >= 2].sum())
    return {
        "composite_unique_values": int(scores.nunique()),
        "composite_observation_n": int(len(scores)),
        "composite_tie_observation_share": rounded(tie_n / len(scores)) if len(scores) else None,
        "ranking_unique_values": None,
        "historical_ranking_score_persisted": False,
        "historical_legacy_quality_score_persisted": False,
        "historical_ranking_method_persisted": False,
        "historical_proxy_unique_values": proxy["unique_values"],
        "official_production_definition": None,
        "status": "DEFINITION_REQUIRED",
        "reason": (
            "The export has a composite score but no persisted ranking score, and the code "
            "uses a multi-key publication tuple with no explicit final tie-breaker."
        ),
    }


def build_result() -> dict[str, Any]:
    frame, score_frame, contract = load_data()
    evidence = source_evidence()
    config = flag_provenance()
    proxy = legacy_proxy_diagnostics(score_frame)
    resolution = score_resolution(score_frame, proxy)

    override_enabled = config["runner_effective_legacy_override_enabled"]
    default_source = "composite_score" if override_enabled else "legacy_quality_score"
    mapping = {
        "ranking_score_exists": True,
        "composite_source_identified": True,
        "ranking_source_identified": True,
        "relationship": (
            "ranking_score = composite_score when "
            "FINPILOT_ENABLE_LEGACY_COMPOSITE_RANKING=1; otherwise "
            "ranking_score = legacy_quality_score"
        ),
        "default_or_runner_source": default_source,
        "score_source_deterministic_given_flag": True,
        "deterministic": False,
        "historical_exact_replay": False,
        "additional_inputs": [
            "regime",
            "direction",
            "raw score",
            "daily ATR percentage",
            "raw RVOL / alpha RVOL transformation",
            "squeeze_factor",
            "lottery_factor",
            "overnight_gap_factor",
            "FINPILOT_ENABLE_LEGACY_COMPOSITE_RANKING process value",
        ],
        "monotonic": {
            "status": "DESCRIPTIVE_PROXY_ONLY",
            "historical_proxy_spearman_with_composite": proxy["proxy_vs_composite"]["spearman"],
            "historical_proxy_n": proxy["comparable_n"],
            "production_monotonicity_proven": False,
            "reason": "The default ranking source is a separate score formula, not a declared monotone transform of composite_score.",
        },
    }

    ordering = {
        "sort_keys": {
            "public_snapshot": [
                "grade ascending: A, B, C, then unknown",
                "execution_confidence ascending: Tier 2, Tier 1, Tier 0",
                "conviction_prob descending",
                "selected score descending: ranking_score or legacy_quality_score or composite_score or score",
            ],
            "scan_summary": [
                "conviction_tier ascending: A, B, C, then empty",
                "execution_confidence ascending: Tier 2, Tier 1, Tier 0",
                "conviction_prob descending",
                "ranking_score descending; composite_score is the default only when the key is absent",
            ],
        },
        "tie_breakers": {
            "explicit": [],
            "implicit": ["Python stable sort preserves input order for equal keys"],
            "source_order": [
                "snapshot rows inherit scan export/result insertion order",
                "historical EOD CSV row order is not the production scan result order",
            ],
            "score_fallback_uses_python_or": True,
            "missing_ranking_score_uses_composite": True,
            "falsy_ranking_score_uses_composite": False,
        },
        "reconstructed": False,
        "reconstruction_status": "PARTIAL_CODE_PATH_ONLY",
        "reason": (
            "Sort precedence is visible, but exact displayed order requires all row-level keys "
            "and the original input order; the historical export does not persist the ranking fields."
        ),
    }

    method_provenance = {
        "emitted_field": "ranking_method",
        "evaluate_default_value": "legacy_quality",
        "default_branch_consistent": not override_enabled,
        "override_branch_consistent": False,
        "status": "CONSISTENT_FOR_DEFAULT_BRANCH_ONLY",
        "reason": (
            "evaluate.py emits ranking_method='legacy_quality' unconditionally, while the "
            "feature flag can select composite_score as ranking_score."
        ),
    }

    candidate_path = {
        "snapshot_public_candidate": [
            "grade/conviction label must exist",
            "selection_eligible must be true when present",
            "execution_feasible must be true when present",
            "position_cap_reject_reason must be empty",
        ],
        "scan_summary_candidate_pool": [
            "selection_eligible when present, otherwise entry_ok or conviction tier",
            "position_cap_reject_reason must be empty",
        ],
        "max_public_candidates": 50,
        "max_summary_candidates_default": 25,
    }

    production_impact = {
        "score_changed": False,
        "ranking_changed": False,
        "scanner_changed": False,
        "db_changed": False,
        "config_changed": False,
        "deployment_changed": False,
        "status": "NONE",
    }

    return {
        "research_id": "RESEARCH-X/H4B",
        "date": AUDIT_DATE,
        "level": "A",
        "read_only": True,
        "status": "COMPLETED",
        "verdict": "MAPPING_DEPENDS_ON_ADDITIONAL_INPUTS",
        "mapping": mapping,
        "ordering": ordering,
        "resolution": resolution,
        "production_impact": production_impact,
        "dataset": contract,
        "source_evidence": evidence,
        "configuration": config,
        "composite_path": {
            "raw_features": [
                "regime",
                "direction",
                "score",
                "filter_score",
                "alignment_ratio",
                "momentum_ratio",
                "volume_spike",
                "price_momentum",
                "trend_strength",
                "vol_regime",
                "sentiment_score",
                "optional squeeze/catalyst/lottery/overnight factors",
            ],
            "compute_function": "scanner/score_engine.py::compute_recommendation_strength",
            "stored_field": "composite_score",
            "normalization": "clip(raw_recommendation_score / 16.5 * 100, 0, 100)",
            "final_operation": "int(round(strength))",
        },
        "ranking_path": {
            "legacy_formula": "scanner/score_engine.py::compute_legacy_quality_score",
            "legacy_output_precision": "round(..., 3)",
            "selected_field": "ranking_score",
            "default_selected_source": default_source,
            "snapshot_selected_score_fallback": [
                "ranking_score",
                "legacy_quality_score",
                "composite_score",
                "score",
                "0.0",
            ],
            "summary_selected_score_fallback": ["ranking_score", "composite_score", "0.0"],
        },
        "method_provenance": method_provenance,
        "candidate_path": candidate_path,
        "historical_proxy": proxy,
        "reconstruction": {
            "score_source": "RECONSTRUCTED_FROM_CURRENT_CODE",
            "historical_ranking_value": "NOT_RECONSTRUCTABLE_EXACTLY",
            "final_public_order": "NOT_RECONSTRUCTABLE_EXACTLY",
            "why": [
                "ranking_score is not persisted in the canonical historical CSV",
                "legacy_quality_score and ranking_method are not persisted",
                "required current evaluator provenance is not persisted per row",
                "snapshot sorting has no explicit symbol/timestamp final tie-breaker",
                "the official production resolution definition is not documented in scoped evidence",
            ],
        },
        "evidence_labels": {
            "evidence": [
                "current code computes composite_score, legacy_quality_score, and ranking_score separately",
                "the default code branch selects legacy_quality_score when the override flag is not 1",
                "public snapshot ordering is a multi-key tuple",
                "historical EOD export lacks persisted ranking fields",
            ],
            "interpretation": [
                "composite_score is not the default production ranking field under the observed repository default",
                "compression findings for composite_score cannot be relabeled as official ranking resolution",
            ],
            "not_proven": [
                "the exact historical production ranking order",
                "that ranking_score is a monotone transform of composite_score",
                "that score precision or tie concentration caused predictive/economic failure",
                "that any score, ranking, or publication change would improve outcomes",
            ],
        },
    }


def bullet_list(values: list[Any]) -> str:
    if not values:
        return "- None"
    return "\n".join(f"- {value}" for value in values)


def render_report(result: dict[str, Any]) -> str:
    dataset = result["dataset"]
    mapping = result["mapping"]
    ordering = result["ordering"]
    resolution = result["resolution"]
    proxy = result["historical_proxy"]
    config = result["configuration"]
    evidence = result["source_evidence"]
    production = result["production_impact"]

    lines = [
        "# RESEARCH-X/H4B - Production Ranking Mapping Reconstruction",
        "",
        f"**Date:** {result['date']}",
        f"**Level:** {result['level']} - read-only forensic research",
        "**Runner:** `research/research_x_h4b_ranking_mapping_2026_09_21.py`",
        "**Artifact:** `data/backtest_out/research_x_h4b_ranking_mapping_2026-09-21.json`",
        "",
    ]

    sections = {
        "Executive Result": [
            f"H4B verdict: `{result['verdict']}`.",
            "The implemented score-source branch is identifiable, but exact historical ranking and final public order are not replayable from the canonical CSV.",
            "Official production ranking resolution remains `DEFINITION_REQUIRED`; this is separate from H4A structural compression and does not establish predictive or economic failure.",
        ],
        "Research Question": [
            "Reconstruct the path `raw features -> composite_score -> ? -> ranking_score -> production ordering` without changing the score formula.",
            "The audit separates score-source selection, candidate eligibility, publication ordering, and final tie behavior.",
        ],
        "Governance and Scope": [
            "Research / Level A / READ_ONLY.",
            "No score inversion, refit, threshold tuning, ranking mutation, scanner mutation, configuration mutation, database write, deployment, or locked-OOS opening was permitted.",
            "H2 remains `CLOSED / NOT_SUPPORTED`; H4A remains structural and does not authorize a production score change.",
        ],
        "Dataset and Provenance": [
            f"Input: `{dataset['input_csv']}`",
            f"SHA-256: `{dataset['input_sha256']}`",
            f"Raw rows: `{dataset['raw_n']}`; deduplicated EOD rows: `{dataset['deduplicated_n']}`; composite non-null rows: `{dataset['composite_n']}`.",
            f"Composite date range: `{dataset['composite_date_range']}`; unique dates: `{dataset['composite_unique_dates']}`.",
            f"Deduplication: {dataset['deduplication_rule']}.",
        ],
        "Production Path Under Audit": [
            "`scanner/evaluate.py` builds the score input, computes composite strength, computes legacy quality, selects ranking_score by environment flag, and emits the fields.",
            "`distribution/jobs.py` passes scan export rows to `distribution.snapshot_builder.build_snapshot`.",
            "`scanner/scan_summary.py` separately builds the summary/alert candidate pool with its own rank helper.",
            "`distribution/prepublish_gate.py` requires ranking fields in the export contract; it does not define a ranking resolution metric.",
        ],
        "Raw Features to Composite Score": [
            "The evaluated score input contains regime, direction, raw score, filter score, alignment ratio, momentum ratio, binary filter components, volatility regime, sentiment, and optional feature factors.",
            "The composite path is `compute_recommendation_score` followed by `compute_recommendation_strength`.",
            "This is the composite construction path only; it is not the default ranking source when the legacy override flag is disabled.",
        ],
        "Composite Score Storage": [
            "`composite_score` is the rounded 0-100 strength value: `clip(raw_recommendation_score / 16.5 * 100, 0, 100)` followed by `int(round(strength))`.",
            f"The historical export contains `{resolution['composite_unique_values']}` unique composite values across `{resolution['composite_observation_n']}` observations.",
            "The raw recommendation score and component breakdown are not persisted in the canonical historical CSV.",
        ],
        "Ranking Score Definition": [
            f"Current code: `{mapping['relationship']}`.",
            f"The runner's effective branch is `{result['ranking_path']['default_selected_source']}`; this describes the runner/repository default, not an unverified live process state.",
            "`legacy_quality_score` is a separate 0-100 nominal score rounded to three decimals and uses regime, direction, raw score, ATR, RVOL, squeeze, lottery, and overnight inputs.",
        ],
        "Configuration and Flag Provenance": [
            f"Flag: `{config['flag']}`.",
            f"Source-code default: `{config['source_code_default']}`; repository `.env` value: `{config['repository_dotenv_value']}`; runner process value: `{config['process_environment_value']}`.",
            "The score engine reads `os.environ` directly; a `.env` value is provenance only unless the caller loads it.",
            "This runner did not inspect or mutate a live production process.",
        ],
        "Mapping Relationship": [
            "The ranking path is not a single transform from composite_score. It is a conditional source switch between composite_score and an independently computed legacy_quality_score.",
            f"Code-level source mapping: `{mapping['score_source_deterministic_given_flag']}` given a known flag; historical exact replay: `{mapping['historical_exact_replay']}`.",
            "Therefore structural compression of composite_score must not be presented as official production ranking resolution.",
        ],
        "Additional Inputs": [
            "The default legacy branch requires additional inputs beyond the persisted composite score.",
            bullet_list(mapping["additional_inputs"]),
            "Historical `atr_pct_real` and `rvol` permit a descriptive back-computation, but missing per-row feature timestamps, evaluator provenance, and persisted ranking_score prevent exact production replay.",
        ],
        "Ranking Method Provenance": [
            f"`ranking_method` is emitted as `{result['method_provenance']['evaluate_default_value']}` unconditionally in `evaluate.py`.",
            "That label is consistent with the default legacy branch but would be stale if the composite override flag were enabled.",
            f"Status: `{result['method_provenance']['status']}`.",
        ],
        "Candidate Eligibility": [
            "Public snapshot candidates require a grade/conviction label, selection eligibility when present, execution feasibility when present, and no position-cap rejection.",
            "The summary candidate pool has a separate fallback eligibility rule and does not use exactly the same candidate filter as the public snapshot.",
            f"Snapshot cap: `{result['candidate_path']['max_public_candidates']}`; summary pool default: `{result['candidate_path']['max_summary_candidates_default']}`.",
        ],
        "Public Snapshot Ordering": [
            "`distribution/snapshot_builder._sort_key` orders public candidates by:",
            bullet_list(ordering["sort_keys"]["public_snapshot"]),
            "The score is therefore the fourth precedence level, not the sole publication ordering field.",
        ],
        "Summary and Alert Ordering": [
            "`scanner/scan_summary._rank` orders its candidate pool separately by conviction tier, execution confidence, conviction probability, and ranking score/composite fallback.",
            bullet_list(ordering["sort_keys"]["scan_summary"]),
            "When `ranking_score` is absent, the mapping expression uses `composite_score`; a present zero or null value is coerced to zero rather than replaced by composite_score.",
            "This path can diverge from the snapshot builder because its tier mapping and score fallback are not identical.",
        ],
        "Tie-Breakers and Stability": [
            "No explicit symbol, timestamp, row id, or deterministic final tie-breaker is present in either inspected sort key.",
            bullet_list(ordering["tie_breakers"]["implicit"]),
            "Equal-key ordering depends on input sequence. The historical CSV row order is not sufficient evidence of the production scan result insertion order.",
            "The Python `or` fallback also treats a zero ranking score as falsy and may select the next score field.",
        ],
        "Historical Ranking Coverage": [
            "Persisted historical ranking fields:",
            bullet_list(
                f"{field}: {present}"
                for field, present in dataset["ranking_fields_persisted"].items()
            ),
            f"A legacy-quality historical proxy is calculable for `{proxy['calculable_n']}` of `{dataset['composite_n']}` composite rows; it is not a persisted ranking_score.",
            "Historical exact ranking order: NOT RECONSTRUCTABLE.",
        ],
        "Reconstructed Score Diagnostics": [
            f"Historical legacy-quality proxy unique values: `{proxy['unique_values']}`; range: `{proxy['finite_summary']['min']}` to `{proxy['finite_summary']['max']}`.",
            f"Comparable proxy/composite rows: `{proxy['comparable_n']}`; descriptive Pearson: `{proxy['proxy_vs_composite']['pearson']}`; descriptive Spearman: `{proxy['proxy_vs_composite']['spearman']}`.",
            "These are proxy diagnostics only. They do not prove a historical production ranking value, monotonicity, predictive quality, or economic value.",
        ],
        "Resolution Definition": [
            f"Composite unique values: `{resolution['composite_unique_values']}`.",
            "Historical ranking unique values: `NOT AVAILABLE` because ranking_score is not persisted.",
            f"Historical proxy unique values: `{resolution['historical_proxy_unique_values']}`; this is not the official production metric.",
            "Official production ranking resolution: `DEFINITION_REQUIRED` because the scoped evidence does not choose between score values, complete sort-key tuples, and final displayed ranks.",
        ],
        "Evidence vs Interpretation": [
            "**EVIDENCE**",
            bullet_list(result["evidence_labels"]["evidence"]),
            "**INTERPRETATION**",
            bullet_list(result["evidence_labels"]["interpretation"]),
            "**NOT PROVEN**",
            bullet_list(result["evidence_labels"]["not_proven"]),
        ],
        "Limitations and Not Proven": [
            "The canonical EOD export lacks ranking_score, legacy_quality_score, ranking_method, complete evaluator feature provenance, and original production input ordering.",
            "The proxy uses available historical columns and the current legacy formula; it is not a point-in-time replay of the live evaluator.",
            "Mapping reconstruction does not test a new score and does not authorize changing any production rule.",
        ],
        "Production Impact and Next Question": [
            f"Production impact: `{production['status']}`. All mutation flags are false.",
            "H4B closes the code-level source question only partially: the ranking field and sort precedence are visible, while exact historical final order and official resolution remain unresolved.",
            "Next question: define the official production ranking resolution metric and, only after that, decide whether an H4C information-loss audit is warranted. Compression is not ranking failure, and mapping ambiguity is not predictive/economic failure.",
            "Guardrail: no score formula, ranking source, scanner, configuration, database, scheduler, publication behavior, or user-facing surface was changed.",
        ],
    }

    for index, title in enumerate(SECTION_TITLES, start=1):
        lines.append(f"## {index}. {title}")
        lines.extend(sections[title])
        lines.append("")

    lines.extend(
        [
            "## Source Evidence Index",
            "",
            "| Surface | Path | SHA-256 | Relevant symbols/lines |",
            "|---|---|---|---|",
        ]
    )
    for key in (
        "score_engine",
        "evaluate",
        "snapshot_builder",
        "scan_summary",
        "distribution_jobs",
        "prepublish_gate",
    ):
        item = evidence[key]
        functions = ", ".join(
            f"{name}:{span['start_line']}-{span['end_line']}"
            for name, span in item.get("functions", {}).items()
        )
        lines.append(
            f"| {key} | `{item['path']}` | `{item.get('sha256', 'MISSING')}` | {functions or 'n/a'} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_artifacts(result: dict[str, Any]) -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True, default=json_value) + "\n",
        encoding="utf-8",
    )
    OUT_REPORT.write_text(render_report(result), encoding="utf-8")


def main() -> None:
    result = build_result()
    write_artifacts(result)
    print(
        json.dumps(
            {
                "status": result["status"],
                "verdict": result["verdict"],
                "mapping_source": result["ranking_path"]["default_selected_source"],
                "historical_exact_replay": result["mapping"]["historical_exact_replay"],
                "ordering_reconstructed": result["ordering"]["reconstructed"],
                "resolution_status": result["resolution"]["status"],
                "out_json": path_ref(OUT_JSON),
                "out_report": path_ref(OUT_REPORT),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
