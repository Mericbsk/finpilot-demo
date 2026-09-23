"""RESEARCH GOVERNANCE CONTROLLER — v0.2 READ-ONLY implementation.

Spec: docs/governance/research_governance_controller_spec_v1.md (APPROVED/LOCKED,
Level B, SHA a3ea327b...). This tool is READ-ONLY. It is NOT a decision maker and
NOT a governance authority. It reconciles evidence; it does not resolve conflict.

Design sentence (locked): Controller state üretir; authority üretmez. Evidence'ı
reconcile eder; conflict'i çözmez. Geçmişin provenance'ını varsaymaz; mevcut
provenance'ı korur.

Authority precedence (locked):
  SCIENTIFIC TRUTH  <- locked prereg / result artifact / verification artifact
  GOVERNANCE TRUTH  <- decision-log / explicit human approval
  DERIVED STATE     <- this controller (registry + report)  [never overrides]

Scope (locked, two tiers):
  FULL-STATE lines: H4 (A/B/C/D-def/D-measure), NS-1, RX-CAPTURE-1 — modeled and
    verified against on-disk artifacts.
  POINTER-ONLY lines: known_status carried as documented, NOT controller-verified.

Invariants (locked): UNKNOWN never -> FALSE; NOT_FOUND never == NOT_PERFORMED;
scientific verdict never -> production authorization; derived state never
overrides locked evidence; conflict is surfaced not resolved; locked research
never mutated; missing provenance reduces certainty, never creates a negative
finding; READ-ONLY execution produces no governance mutation.

Usage:  python scripts/research_governance_controller.py [--json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECISION_LOG = ROOT / "docs" / "governance" / "decision-log.md"


def sha256_file(p: Path) -> str | None:
    if not p.exists():
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest()


def file_exists(rel: str) -> bool:
    return (ROOT / rel).exists()


# ---------------------------------------------------------------------------
# FULL-STATE lines: declared artifact paths. State is DERIVED from what exists
# on disk and what decision-log records — never hardcoded verdicts here.
# ---------------------------------------------------------------------------
FULL_STATE = {
    "NS-1": {
        "prereg": "reports/research_x_ns1_negative_screen_preregistration_2026-09-22.md",
        "runner": "research/research_x_ns1_negative_screen_2026_09_22.py",
        "result_json": "data/backtest_out/research_x_ns1_negative_screen_2026-09-22.json",
        "report": "reports/research_x_ns1_negative_screen_2026-09-22.md",
        "verification": "data/backtest_out/ns1_independent_verification_2026-09-22.json",
    },
    "RX-CAPTURE-1": {
        "prereg": "reports/research_x_capture_1_preregistration_2026-09-22.md",
        "runner": "research/research_x_capture_1_2026_09_22.py",
        "result_json": "data/backtest_out/research_x_capture_1_2026-09-22.json",
        "report": "reports/research_x_capture_1_2026-09-22.md",
        "verification": "data/backtest_out/rx_capture_1_independent_verification_2026-09-22.json",
    },
    "H4A": {
        "prereg": None,  # H4A had no standalone prereg file (structural audit)
        "runner": "research/research_x_h4a_resolution_compression_2026_09_21.py",
        "result_json": "data/backtest_out/research_x_h4a_resolution_compression_2026-09-21.json",
        "report": "reports/research_x_h4a_resolution_compression_2026-09-21.md",
        "verification": None,
    },
    "H4B": {
        "prereg": None,
        "runner": "research/research_x_h4b_ranking_mapping_2026_09_21.py",
        "result_json": "data/backtest_out/research_x_h4b_ranking_mapping_2026-09-21.json",
        "report": "reports/research_x_h4b_ranking_mapping_2026-09-21.md",
        "verification": None,
    },
    "H4C": {
        "prereg": "reports/research_x_h4c_information_loss_preregistration_2026-09-22.md",
        "runner": "research/research_x_h4c_information_loss_2026_09_22.py",
        "result_json": "data/backtest_out/research_x_h4c_information_loss_2026-09-22.json",
        "report": "reports/research_x_h4c_information_loss_2026-09-22.md",
        "verification": None,
    },
    "H4D-definition": {
        "prereg": "reports/research_x_h4d_ranking_resolution_definition_2026-09-22.md",
        "runner": None,  # definition-only
        "result_json": None,
        "report": "reports/research_x_h4d_ranking_resolution_definition_2026-09-22.md",
        "verification": None,
    },
    "H4D-measure": {
        "prereg": "reports/research_x_h4d_measure_preregistration_2026-09-22.md",
        "runner": "research/research_x_h4d_measure_2026_09_22.py",
        "result_json": "data/backtest_out/research_x_h4d_measure_2026-09-22.json",
        "report": "reports/research_x_h4d_measure_2026-09-22.md",
        "verification": None,
    },
}

POINTER_ONLY = [
    "RX-H2 score-direction",
    "Direction prediction battery",
    "S1 Short Interest",
    "High-RVOL line",
    "TP/SL grid",
    "Reverse-ranking / extension-cap",
    "Ranking-score backtest",
    "V2 path-aware locked-OOS",
]


def read_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def derive_line_state(name: str, spec: dict) -> dict:
    """Derive lifecycle/verdict/verification from on-disk artifacts. NEVER infer
    a verdict that is not present in the artifact; absence -> UNKNOWN."""
    out = {"experiment_id": name}
    missing = []
    for key, rel in spec.items():
        if rel is None:
            out[key] = None
            continue
        p = ROOT / rel
        if not p.exists():
            missing.append(key)
            out[key] = None
        else:
            out[key] = {"path": rel, "sha256": sha256_file(p)}

    # lifecycle: artifact presence (prereg/result) — lock ORDER is derived from
    # decision-log separately (provenance, not file mtime).
    out["lifecycle_state"] = (
        "CLOSED" if out.get("result_json") or name == "H4D-definition" else "UNKNOWN"
    )

    # scientific verdict: read from the result JSON / report — never invented.
    # H4D-definition is definition-only BY DESIGN: no result JSON exists, so its
    # verdict is the locked label DEFINITION_LOCKED, not UNKNOWN.
    if name == "H4D-definition" and out.get("report"):
        verdict = "DEFINITION_LOCKED"
        out["scientific_verdict"] = verdict
        out["lifecycle_state"] = "CLOSED"
        ver = out.get("verification")
        out["verification_state"] = "NONE"
        out["missing_artifacts"] = missing
        return out

    # Try common locked-schema keys in order; absence -> UNKNOWN (never FALSE).
    verdict = None
    rj = out.get("result_json")
    if rj:
        data = read_json(ROOT / rj["path"])
        if isinstance(data, dict):
            # direct keys
            verdict = data.get("verdict") or data.get("overall")
            # NS-1 style: verdicts dict
            if verdict is None and isinstance(data.get("verdicts"), dict):
                verdict = data.get("overall") or data["verdicts"].get("overall")
            # RX-CAPTURE-1 style: candidates dict with per-candidate verdicts
            if verdict is None and isinstance(data.get("candidates"), dict):
                cands = data["candidates"]
                verdict = {k: v.get("verdict") for k, v in cands.items() if isinstance(v, dict)}
            # H4D-measure style: endpoint verdicts + gate
            if verdict is None and isinstance(data.get("endpoints"), dict):
                verdict = data.get("reconstructability_gate") or {
                    k: v.get("verdict") for k, v in data["endpoints"].items() if isinstance(v, dict)
                }
    out["scientific_verdict"] = verdict if verdict is not None else "UNKNOWN"

    # verification state: from the verification artifact if present.
    ver = out.get("verification")
    if ver:
        vdata = read_json(ROOT / ver["path"])
        v = vdata.get("verification") if isinstance(vdata, dict) else None
        out["verification_state"] = v if v else "UNKNOWN"
    else:
        out["verification_state"] = "NONE"

    out["missing_artifacts"] = missing
    return out


def decision_log_state(log_text: str) -> dict:
    """Derive decision-log integrity signals. READ-ONLY."""
    entries = re.findall(r"^\[(\d{4}-\d{2}-\d{2})\]", log_text, flags=re.M)
    pending = [line for line in log_text.splitlines() if "pending" in line.lower()]
    return {
        "decision_log_present": DECISION_LOG.exists(),
        "total_entries": len(entries),
        "pending_mentions": len(pending),
        "has_h4_freeze": ("FROZEN" in log_text and "H4" in log_text),
        "has_controller_lock": "Research Governance Controller spec v0.2 locked" in log_text,
    }


def conflict_scan(state: dict) -> list[dict]:
    """Surface conflicts; NEVER resolve. A conflict is reported as CONFLICT with
    RESOLUTION_REQUIRED and AUTHORITY_ACTION=NONE."""
    conflicts = []
    for name, s in state["lines"].items():
        # artifact-derived lifecycle vs verification expectation
        if s.get("lifecycle_state") == "UNKNOWN":
            conflicts.append(
                {
                    "line": name,
                    "type": "INSUFFICIENT_PROVENANCE",
                    "detail": "lifecycle could not be derived from on-disk artifacts",
                    "state": "CONFLICT",
                    "resolution": "REQUIRED",
                    "authority_action": "NONE",
                }
            )
        if s.get("missing_artifacts"):
            conflicts.append(
                {
                    "line": name,
                    "type": "SHA_MISSING",
                    "detail": f"missing artifact slots: {s['missing_artifacts']}",
                    "state": "CONFLICT",
                    "resolution": "REQUIRED",
                    "authority_action": "NONE",
                }
            )
    return conflicts


def build_state() -> dict:
    log_text = DECISION_LOG.read_text(encoding="utf-8") if DECISION_LOG.exists() else ""
    lines = {name: derive_line_state(name, spec) for name, spec in FULL_STATE.items()}
    state = {
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "controller_version": "v0.2-READONLY",
        "authority": "DERIVED_STATE (never overrides locked evidence)",
        "lines": lines,
        "pointer_only_lines": [
            {
                "experiment_id": n,
                "controller_state": "POINTER_ONLY",
                "known_status": "as documented",
                "verified": False,
            }
            for n in POINTER_ONLY
        ],
        "decision_log": decision_log_state(log_text),
    }
    state["conflicts"] = conflict_scan(state)
    return state


def program_state_block(state: dict) -> str:
    # Derived from artifact state where possible; conservative defaults otherwise.
    h4 = "FROZEN_CLOSED"
    ns1 = state["lines"].get("NS-1", {})
    cap = state["lines"].get("RX-CAPTURE-1", {})
    ns1_ver = ns1.get("verification_state", "UNKNOWN")
    cap_ver = cap.get("verification_state", "UNKNOWN")
    return "\n".join(
        [
            "PROGRAM_STATE:",
            "SELECTION_PREDICTIVE_EDGE = NOT_ESTABLISHED",
            "DIRECTION_PREDICTION = CLOSED_NOT_SUPPORTED",
            f"H4 = {h4}",
            f"NS1 = CLOSED / verification={ns1_ver}",
            f"RX_CAPTURE = CLOSED / verification={cap_ver}",
            "RX_CAPTURE_PRODUCTION = NOT_APPROVED",
            "LOCKED_OOS = NOT_OPENED",
            "PRODUCTION_IMPACT = NONE",
        ]
    )


def print_report(state: dict) -> None:
    print("RESEARCH GOVERNANCE CONTROLLER — READ-ONLY state report")
    print(f"generated_at: {state['generated_at']}  |  authority: {state['authority']}")
    print("=" * 72)
    print("FULL-STATE LINES (derived from artifacts):")
    for name, s in state["lines"].items():
        print(
            f"  {name:16} lifecycle={s.get('lifecycle_state')}"
            f"  verdict={json.dumps(s.get('scientific_verdict'))[:40]}"
            f"  verification={s.get('verification_state')}"
            + (f"  MISSING={s['missing_artifacts']}" if s.get("missing_artifacts") else "")
        )
    print("-" * 72)
    print("POINTER-ONLY LINES (not controller-verified):")
    for p in state["pointer_only_lines"]:
        print(
            f"  {p['experiment_id']:34} state={p['controller_state']} known_status={p['known_status']}"
        )
    print("-" * 72)
    dl = state["decision_log"]
    print(
        f"DECISION-LOG: present={dl['decision_log_present']} entries={dl['total_entries']}"
        f" pending_mentions={dl['pending_mentions']} h4_freeze={dl['has_h4_freeze']}"
        f" controller_lock={dl['has_controller_lock']}"
    )
    print("-" * 72)
    if state["conflicts"]:
        print("CONFLICTS (surfaced, NOT resolved):")
        for c in state["conflicts"]:
            print(f"  [{c['type']}] {c['line']}: {c['detail']} -> {c['state']}/{c['resolution']}")
    else:
        print("CONFLICTS: none detected among full-state lines.")
    print("-" * 72)
    print(program_state_block(state))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = ap.parse_args()
    state = build_state()
    if args.json:
        print(json.dumps(state, indent=2, sort_keys=True, default=str))
    else:
        print_report(state)


if __name__ == "__main__":
    main()
