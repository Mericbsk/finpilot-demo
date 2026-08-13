"""Research-only manifest and gate evaluator for the 2026-08-11 program.

The program records 220 predeclared tests as phase budgets. It does not run
arbitrary alpha searches and cannot change production behavior. A phase can be
completed only when its prerequisite gate is satisfied; missing data produces
BLOCKED or NOT_OPENED rather than a fabricated result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Phase:
    phase_id: str
    name: str
    test_count: int
    prerequisite: str | None
    purpose: str


PHASES: tuple[Phase, ...] = (
    Phase(
        "P0",
        "Research protocol",
        12,
        None,
        "Pre-registration, splits, leakage and canonicalization",
    ),
    Phase(
        "P1",
        "Data reliability",
        30,
        "P0",
        "PIT universe, corporate actions, immutable prices and provenance",
    ),
    Phase(
        "P2",
        "Label and execution",
        26,
        "P1",
        "Fill ordering, costs, intraday labels and capacity inputs",
    ),
    Phase(
        "P3",
        "Baselines and target semantics",
        20,
        "P2",
        "Benchmarks, random controls and target definitions",
    ),
    Phase(
        "P4", "Score decomposition", 28, "P3", "Feature-level score, calibration and replay tests"
    ),
    Phase("P5", "Entry setup families", 30, "P4", "Pre-registered economic setup families only"),
    Phase(
        "P6",
        "Entry eligibility decomposition",
        18,
        "P5",
        "Entry veto ablation and adverse-selection tests",
    ),
    Phase("P7", "Exit, holding and risk", 20, "P6", "Limited pre-registered exit comparisons"),
    Phase(
        "P8",
        "Portfolio, risk and capacity",
        16,
        "P7",
        "Sizing, concentration, turnover and participation",
    ),
    Phase(
        "P9",
        "Robustness and locked validation",
        20,
        "P8",
        "Walk-forward, stress, stability and locked OOS",
    ),
)

PRIORITY_25: tuple[str, ...] = (
    "immutable_cache_snapshot",
    "corporate_action_classification",
    "pit_universe_delisting",
    "adjusted_raw_reconciliation",
    "score_replay_equivalence",
    "feature_timestamp",
    "next_open_intraday_fill",
    "adv_spread_slippage_model",
    "random_baseline",
    "benchmark_relative_baseline",
    "top_n_score_baseline",
    "entry_ok_disabled_baseline",
    "entry_ok_ablation",
    "forward_return_1_2_5d",
    "mfe_c2c_capture",
    "score_feature_ablation",
    "feature_age_missingness",
    "signal_count_quality",
    "regime_conditioning",
    "sector_concentration",
    "pullback_entry",
    "gap_reversal",
    "rvol_inversion",
    "atr_parity_risk",
    "locked_oos_preregistration",
)

BLOCKERS = {
    "P1": "PIT listing/delisting universe, corporate-action feed and immutable prior cache snapshot are unavailable",
    "P2": "observed spread/slippage/impact, ADV and intraday bars are unavailable",
    "P9": "locked OOS must not open before all prior data and execution gates pass",
}


def program_manifest() -> dict[str, Any]:
    total = sum(phase.test_count for phase in PHASES)
    return {
        "program_id": "finpilot-gated-research-2026-08-11",
        "status": "pre_registered",
        "scope": "research_only",
        "production_change": False,
        "phase_count": len(PHASES),
        "planned_test_count": total,
        "priority_test_count": len(PRIORITY_25),
        "phases": [asdict(phase) for phase in PHASES],
        "priority_25": list(PRIORITY_25),
        "success_contract": {
            "net_expected_value_positive": True,
            "median_net_outcome_non_negative": True,
            "benchmark_excess_positive": True,
            "cvar_and_drawdown_within_limits": True,
            "stable_in_at_least_two_regimes": True,
            "survives_realistic_cost_and_fill_stress": True,
        },
        "rule": "A phase cannot open unless its prerequisite is passed; insufficient data is not a finding.",
    }


def evaluate_gates(
    *,
    source_csv: Path,
    existing_artifacts: dict[str, Path] | None = None,
) -> dict[str, Any]:
    """Evaluate phase availability without opening locked OOS or fabricating results."""
    existing_artifacts = existing_artifacts or {}
    source_hash = (
        hashlib.sha256(source_csv.read_bytes()).hexdigest() if source_csv.exists() else None
    )
    statuses: dict[str, str] = {}
    for phase in PHASES:
        if phase.phase_id == "P0":
            statuses[phase.phase_id] = "COMPLETED" if source_hash else "BLOCKED"
        elif phase.phase_id in BLOCKERS:
            statuses[phase.phase_id] = "BLOCKED"
        else:
            prerequisite_status = statuses.get(phase.prerequisite or "")
            statuses[phase.phase_id] = (
                "NOT_OPENED" if prerequisite_status != "COMPLETED" else "AVAILABLE"
            )

    artifacts = {
        name: {"path": str(path), "exists": path.exists()}
        for name, path in existing_artifacts.items()
    }
    return {
        **program_manifest(),
        "status": "evaluated",
        "evaluated_at": datetime.now(UTC).isoformat(),
        "source_csv": str(source_csv),
        "source_sha256": source_hash,
        "phase_status": statuses,
        "blockers": BLOCKERS,
        "artifacts": artifacts,
        "locked_oos": "NOT_OPENED",
        "production_boundary": "UNCHANGED",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv", type=Path, default=Path("data/backtest_out/full_universe_enriched.csv")
    )
    parser.add_argument(
        "--out", type=Path, default=Path("data/backtest_out/gated_research_program_2026-08-11.json")
    )
    args = parser.parse_args()
    result = evaluate_gates(
        source_csv=args.csv,
        existing_artifacts={
            "v2": Path("data/backtest_out/scanner_battery_v2_2026-08-11.json"),
            "integrity_raw": Path(
                "data/backtest_out/price_cache_integrity_audit_2026-08-11_e2e.json"
            ),
            "negative_controls": Path(
                "data/backtest_out/negative_controls_current_2026-08-11.json"
            ),
        },
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"OK -> {args.out}")
    print(
        json.dumps(
            {
                "planned_test_count": result["planned_test_count"],
                "phase_status": result["phase_status"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
