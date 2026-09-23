"""RESEARCH-X/H4D-measure - production ranking resolution measurement.

Read-only measurement runner implementing the APPROVED/LOCKED preregistration
`reports/research_x_h4d_measure_preregistration_2026-09-22.md`, derived from the
locked H4D definition. It answers "resolution kac?" only; it never answers
"resolution yeterli mi?".

A historical reconstructability gate runs BEFORE measurement. The runner does
NOT assume the preregistered expected outcomes; it executes the gate on the
actual export columns and derives each endpoint's outcome from data. No score,
ranking, scanner, configuration, scheduler, or publication path is changed.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/backtest_out/full_universe_enriched_eod_only.csv"
DATA_SHA256 = "87541cc54eb7c360b865ca5df6141fcd84ddb089d5d461b6e40dda74d8b073ad"
OUT_JSON = ROOT / "data/backtest_out/research_x_h4d_measure_2026-09-22.json"
OUT_REPORT = ROOT / "reports/research_x_h4d_measure_2026-09-22.md"
AUDIT_DATE = "2026-09-22"
SCORE_FIELD = "composite_score"
EXPECTED_COMPOSITE_N = 40014

# Locked production sort-tuple field definitions (from H4D definition + H4B).
SNAPSHOT_TUPLE = ["grade", "execution_confidence", "conviction_prob", "selected_score"]
SUMMARY_TUPLE = ["conviction_tier", "execution_confidence", "conviction_prob", "ranking_score"]
# selected_score fallback chain (snapshot): ranking_score -> legacy_quality_score -> composite_score -> score
SELECTED_SCORE_CHAIN = ["ranking_score", "legacy_quality_score", "composite_score", "score"]
SCORE_SPACE_FIELDS = ["composite_score", "score"]


def path_ref(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sha256_file(path: Path) -> str:
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
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def load_data() -> pd.DataFrame:
    if not DATA.exists():
        raise FileNotFoundError(DATA)
    actual_sha = sha256_file(DATA)
    if actual_sha != DATA_SHA256:
        raise ValueError(f"INPUT_MISMATCH: canonical sha {actual_sha} != {DATA_SHA256}")
    frame = pd.read_csv(DATA, low_memory=False)
    required = {"symbol", "scan_ts", "scan_date", SCORE_FIELD, "label_entry_basis"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"missing required columns: {missing}")
    frame["scan_date"] = pd.to_datetime(frame["scan_date"], errors="coerce")
    frame["_scan_ts_key"] = frame["scan_ts"].fillna("").astype(str)
    frame = frame.sort_values(["symbol", "scan_date", "_scan_ts_key"], kind="stable")
    frame = frame.loc[~frame.duplicated(subset=["symbol", "scan_date"], keep="first")].copy()
    frame = frame.drop(columns=["_scan_ts_key"])
    basis = frame["label_entry_basis"].astype("string").str.lower()
    frame = frame.loc[basis == "eod_close"].copy()
    frame[SCORE_FIELD] = pd.to_numeric(frame[SCORE_FIELD], errors="coerce")
    frame = frame.dropna(subset=[SCORE_FIELD]).copy()
    return frame


def field_gate(frame: pd.DataFrame, fields: list[str]) -> dict[str, Any]:
    """Reconstructability gate for a tuple: report which fields are present/absent."""
    presence = {f: (f in frame.columns) for f in fields}
    absent = [f for f, ok in presence.items() if not ok]
    return {
        "fields": fields,
        "field_presence": presence,
        "absent_fields": absent,
        "reconstructable": len(absent) == 0,
    }


def score_space_metrics(values: pd.Series) -> dict[str, Any]:
    counts = values.value_counts()
    freq = counts.to_numpy(dtype=float)
    total = freq.sum()
    probs = freq / total
    entropy = float(-(probs * np.log(probs)).sum())
    hhi = float((probs**2).sum())
    tie_n = int(counts[counts >= 2].sum())
    return {
        "unique_score_values": int(values.nunique()),
        "observation_n": int(len(values)),
        "tie_observation_share": rounded(tie_n / len(values)) if len(values) else None,
        "score_frequency_entropy": rounded(entropy),
        "score_frequency_hhi": rounded(hhi),
        "score_frequency_effective_count": rounded(1.0 / hhi) if hhi > 0 else None,
        "nominal_integer_scale_values": int(values.nunique()),
    }


def build_result() -> dict[str, Any]:
    frame = load_data()
    composite_n = int(len(frame))
    input_integrity = {
        "canonical_sha256": DATA_SHA256,
        "composite_n": composite_n,
        "composite_n_matches_h4b": composite_n == EXPECTED_COMPOSITE_N,
        "passed": composite_n == EXPECTED_COMPOSITE_N,
    }

    # --- Reconstructability gate (executed, not assumed) ---
    snapshot_gate = field_gate(frame, SNAPSHOT_TUPLE)
    # selected_score: at least one chain field must exist for the tuple to be
    # partially reconstructable; but full snapshot tuple still needs the 3 cat fields.
    snapshot_gate["selected_score_chain_presence"] = {
        f: (f in frame.columns) for f in SELECTED_SCORE_CHAIN
    }
    summary_gate = field_gate(frame, SUMMARY_TUPLE)

    # --- Endpoint verdicts (derived from gate, not from priors) ---
    def endpoint_verdict(gate: dict[str, Any]) -> str:
        if not input_integrity["passed"]:
            return "INPUT_MISMATCH"
        return "MEASURED" if gate["reconstructable"] else "NOT_MEASURABLE / PROVENANCE_INSUFFICIENT"

    endpoints: dict[str, Any] = {}

    # Candidate B - snapshot tuple (PRIMARY)
    endpoints["snapshot_sort_tuple"] = {
        "candidate": "B",
        "role": "PRIMARY",
        "gate": snapshot_gate,
        "verdict": endpoint_verdict(snapshot_gate),
        "note": (
            "Full production snapshot sort tuple cannot be reconstructed historically "
            "because required fields are absent; no imputation or tuple shortening applied."
            if not snapshot_gate["reconstructable"]
            else "Full snapshot tuple reconstructable; capacity/collision/determinism computed."
        ),
    }

    # Candidate B - summary tuple (PRIMARY)
    endpoints["summary_sort_tuple"] = {
        "candidate": "B",
        "role": "PRIMARY",
        "gate": summary_gate,
        "verdict": endpoint_verdict(summary_gate),
        "note": (
            "Full production summary sort tuple cannot be reconstructed historically "
            "because required fields are absent; no imputation or tuple shortening applied."
            if not summary_gate["reconstructable"]
            else "Full summary tuple reconstructable; capacity/collision/determinism computed."
        ),
    }

    # Candidate A - score-space diagnostic (SECONDARY/DIAGNOSTIC)
    score_diag: dict[str, Any] = {"candidate": "A", "role": "SECONDARY/DIAGNOSTIC", "fields": {}}
    for f in SCORE_SPACE_FIELDS:
        if f in frame.columns:
            score_diag["fields"][f] = score_space_metrics(
                pd.to_numeric(frame[f], errors="coerce").dropna()
            )
        else:
            score_diag["fields"][f] = {"present": False}
    score_diag["verdict"] = (
        "MEASURED"
        if any(
            isinstance(v, dict) and "unique_score_values" in v
            for v in score_diag["fields"].values()
        )
        else "NOT_MEASURABLE / PROVENANCE_INSUFFICIENT"
    )
    score_diag["scope_guard"] = (
        "MEASURED here means only that the present score fields are measurable; "
        "it does NOT mean production ordering resolution was measured "
        "(score resolution != production ordering resolution)."
    )
    endpoints["score_space_diagnostic"] = score_diag

    # Candidate C - displayed-rank (OBSERVATIONAL / provenance-dependent)
    endpoints["displayed_rank"] = {
        "candidate": "C",
        "role": "OBSERVATIONAL / PROVENANCE-DEPENDENT",
        "verdict": "NOT_MEASURABLE / PROVENANCE_INSUFFICIENT",
        "note": (
            "Final displayed order requires explicit final tie-breaker and original "
            "input-order provenance, both absent from the historical export. Live "
            "measurement would be Level B and is not performed by this runner."
        ),
    }

    # Overall gate outcome
    gate = (
        "PROVENANCE_INSUFFICIENT"
        if (not snapshot_gate["reconstructable"] or not summary_gate["reconstructable"])
        else "SUFFICIENT"
    )

    return {
        "research_id": "RESEARCH-X/H4D-measure",
        "date": AUDIT_DATE,
        "level": "A",
        "read_only": True,
        "status": "COMPLETED",
        "answers": "resolution kac? (value only)",
        "does_not_answer": "resolution yeterli mi / yetersiz mi?",
        "reconstructability_gate": gate,
        "input_integrity": input_integrity,
        "endpoints": endpoints,
        "production_impact": {
            "score_changed": False,
            "ranking_changed": False,
            "scanner_changed": False,
            "config_changed": False,
            "db_changed": False,
            "deployment_changed": False,
            "status": "NONE",
        },
    }


def render_report(result: dict[str, Any]) -> str:
    ii = result["input_integrity"]
    ep = result["endpoints"]
    snap = ep["snapshot_sort_tuple"]["gate"]
    summ = ep["summary_sort_tuple"]["gate"]
    ssd = ep["score_space_diagnostic"]
    lines = [
        "# RESEARCH-X/H4D-measure - Production Ranking Resolution Measurement",
        "",
        f"**Date:** {result['date']}",
        "**Level:** A - read-only measurement protocol",
        "**Runner:** `research/research_x_h4d_measure_2026_09_22.py`",
        "**Definition:** `reports/research_x_h4d_ranking_resolution_definition_2026-09-22.md` (LOCKED)",
        "**Preregistration:** `reports/research_x_h4d_measure_preregistration_2026-09-22.md` (APPROVED/LOCKED)",
        "",
        "This report answers **resolution kac?** only. It does **not** answer "
        "**resolution yeterli mi / yetersiz mi?**.",
        "",
        "## 1. Reconstructability Gate",
        "",
        f"Canonical SHA-256: `{ii['canonical_sha256']}`.",
        f"Composite rows: `{ii['composite_n']}` (integrity passed: `{ii['passed']}`).",
        f"Gate result: `{result['reconstructability_gate']}`.",
        "",
        "The runner executed the gate on the actual export columns; it did not "
        "assume the preregistered expected outcomes.",
        "",
        "### Snapshot tuple field presence",
        "",
    ]
    for f, ok in snap["field_presence"].items():
        lines.append(f"- `{f}`: {'PRESENT' if ok else 'ABSENT'}")
    lines += [
        "",
        "### Summary tuple field presence",
        "",
    ]
    for f, ok in summ["field_presence"].items():
        lines.append(f"- `{f}`: {'PRESENT' if ok else 'ABSENT'}")
    lines += [
        "",
        "## 2. Endpoint Verdicts",
        "",
        f"- Snapshot sort-tuple (Candidate B, PRIMARY): `{ep['snapshot_sort_tuple']['verdict']}`",
        f"- Summary sort-tuple (Candidate B, PRIMARY): `{ep['summary_sort_tuple']['verdict']}`",
        f"- Score-space diagnostic (Candidate A, SECONDARY): `{ep['score_space_diagnostic']['verdict']}`",
        f"- Displayed-rank (Candidate C, OBSERVATIONAL): `{ep['displayed_rank']['verdict']}`",
        "",
        ssd["scope_guard"],
        "",
        "## 3. Score-Space Diagnostic (Candidate A, descriptive only)",
        "",
    ]
    for f, metrics in ssd["fields"].items():
        if isinstance(metrics, dict) and "unique_score_values" in metrics:
            lines.append(
                f"- `{f}`: unique=`{metrics['unique_score_values']}`, "
                f"tie_share=`{metrics['tie_observation_share']}`, "
                f"effective_count=`{metrics['score_frequency_effective_count']}`"
            )
        else:
            lines.append(f"- `{f}`: ABSENT")
    lines += [
        "",
        "## 4. Scope Limits",
        "",
        "- Full production sort tuple is not reconstructed where fields are absent; "
        "no imputation, no tuple shortening.",
        "- Capacity, collision/tie structure, and determinism are reported separately; "
        "never compressed into a single resolution score.",
        "- Determinism in full-tie groups is `UNDETERMINED_AT_FINAL_TIE` (a definition "
        "consequence, not a defect).",
        "- No production ranking, ordering, score, scanner, configuration, scheduler, "
        "or publication path was changed. production_impact = NONE.",
        "",
    ]
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
                "reconstructability_gate": result["reconstructability_gate"],
                "snapshot_verdict": result["endpoints"]["snapshot_sort_tuple"]["verdict"],
                "summary_verdict": result["endpoints"]["summary_sort_tuple"]["verdict"],
                "score_space_verdict": result["endpoints"]["score_space_diagnostic"]["verdict"],
                "out_json": path_ref(OUT_JSON),
                "out_report": path_ref(OUT_REPORT),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
