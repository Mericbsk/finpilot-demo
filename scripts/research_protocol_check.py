"""Validate the FinPilot research protocol and write an auditable report."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.protocol import CostModel, FERRecord, ProtocolError, TemporalSplit
from scripts.research_input_manifest import DEFAULT_INPUTS, build_manifest

OPTIONAL_RESEARCH_MODULES = (
    "scipy",
    "statsmodels",
    "sklearn",
    "lightgbm",
    "hmmlearn",
    "mlfinlab",
    "alphalens",
    "optuna",
)


def _check(label: str, callback) -> dict[str, Any]:
    try:
        callback()
    except ProtocolError as exc:
        return {"name": label, "status": "insufficient_data", "reason": str(exc)}
    return {"name": label, "status": "ok"}


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    root = args.root.resolve()
    inputs = tuple(root / path for path in DEFAULT_INPUTS)
    split = TemporalSplit(args.train_end, args.validation_end, args.locked_oos_end)
    cost = CostModel(
        args.cost_model_version,
        args.commission_bps,
        args.spread_bps,
        args.slippage_bps,
        args.impact_bps,
    )
    fer = FERRecord(
        experiment_id=args.experiment_id,
        hypothesis=args.hypothesis,
        economic_rationale=args.economic_rationale,
        data_snapshot=args.data_snapshot,
        date_range=args.date_range,
        split=split,
        factors=tuple(args.factor),
        pairwise_tests=args.pairwise_tests,
        triple_tests=args.triple_tests,
        max_interaction_order=args.max_interaction_order,
        cost_model=cost,
        n_trials=args.n_trials,
        status=args.status,
    )
    gates = [
        _check("temporal_split", split.validate),
        _check("cost_model", cost.validate),
        _check("fer", fer.validate),
    ]
    return {
        "research_only": True,
        "experiment_id": args.experiment_id,
        "generated_for_date": args.report_date,
        "gates": gates,
        "inputs": build_manifest(inputs),
        "optional_dependencies": {
            name: bool(importlib.util.find_spec(name)) for name in OPTIONAL_RESEARCH_MODULES
        },
        "fer": fer.as_dict() if all(gate["status"] == "ok" for gate in gates) else None,
        "locked_holdout": {
            "status": "not_opened",
            "reason": "control check never opens the locked holdout",
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Research Protocol Check",
        "",
        f"- Experiment: `{report['experiment_id']}`",
        f"- Report date: `{report['generated_for_date']}`",
        "- Scope: research-only; no scanner, score, risk, or publication change",
        "",
        "## Gates",
        "",
        "| Gate | Status | Reason |",
        "| --- | --- | --- |",
    ]
    for gate in report["gates"]:
        lines.append(f"| {gate['name']} | {gate['status']} | {gate.get('reason', '')} |")
    lines.extend(
        [
            "",
            "## Locked Holdout",
            "",
            f"Status: `{report['locked_holdout']['status']}`. {report['locked_holdout']['reason']}.",
            "",
            "## Optional Dependencies",
            "",
        ]
    )
    for name, available in report["optional_dependencies"].items():
        lines.append(f"- `{name}`: {'available' if available else 'missing'}")
    lines.extend(
        [
            "",
            "## Input Manifest",
            "",
            "The JSON companion contains SHA-256 hashes and CSV missingness summaries.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--report-date", required=True)
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--hypothesis", required=True)
    parser.add_argument("--economic-rationale", required=True)
    parser.add_argument("--data-snapshot", required=True)
    parser.add_argument("--date-range", required=True)
    parser.add_argument("--train-end", required=True)
    parser.add_argument("--validation-end", required=True)
    parser.add_argument("--locked-oos-end", required=True)
    parser.add_argument("--factor", action="append", required=True)
    parser.add_argument("--pairwise-tests", type=int, default=0)
    parser.add_argument("--triple-tests", type=int, default=0)
    parser.add_argument("--max-interaction-order", type=int, default=1)
    parser.add_argument("--n-trials", type=int, default=1)
    parser.add_argument("--status", default="proposed")
    parser.add_argument("--cost-model-version", required=True)
    parser.add_argument("--commission-bps", type=float)
    parser.add_argument("--spread-bps", type=float)
    parser.add_argument("--slippage-bps", type=float)
    parser.add_argument("--impact-bps", type=float)
    args = parser.parse_args()

    report = build_report(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render_markdown(report), encoding="utf-8")
    json_out = args.json_out or args.out.with_suffix(".json")
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"report={args.out}")
    print(f"json={json_out}")


if __name__ == "__main__":
    main()
