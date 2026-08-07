"""Research-only no-trade, rejection and model-disagreement experiments.

The experiments describe candidate states and counterfactual outcomes. They do
not alter scanner gates, ranking, portfolio construction or execution.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from research.full_universe_barrier_backtest import (
    dedup_rows,
    label_rows,
    load_rows,
    resolve_paths,
)

VETO_NAMES = (
    "missing_entry_eligibility",
    "weak_trend",
    "high_volatility",
    "gap_risk",
    "near_52w_high",
    "low_relative_volume",
)


def _bool(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _read_fields(path: Path) -> dict[tuple[str, str], dict[str, Any]]:
    """Read descriptive fields not retained by the barrier loader."""
    fields: dict[tuple[str, str], dict[str, Any]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            key = ((row.get("symbol") or "").strip(), (row.get("scan_date") or "").strip())
            fields.setdefault(
                key,
                {
                    "liquidity_ok": _bool(row.get("liquidity_ok")),
                    "score": float(row.get("score") or 0.0),
                    "finpilot_score": float(row.get("finpilot_score") or 0.0),
                    "tier": (row.get("tier") or "").strip(),
                },
            )
    return fields


def veto_reasons(row: dict[str, Any], extra: dict[str, Any] | None = None) -> list[str]:
    """Return predeclared descriptive veto reasons for one candidate."""
    extra = extra or {}
    reasons: list[str] = []
    if not row.get("entry_ok", False):
        reasons.append("missing_entry_eligibility")
    if not row.get("regime", False) or not row.get("direction", False):
        reasons.append("weak_trend")
    if row.get("atr_pct", 0.0) >= 8.0:
        reasons.append("high_volatility")
    if row.get("gap") is not None and row["gap"] >= 5.0:
        reasons.append("gap_risk")
    if row.get("dist52") is not None and row["dist52"] >= 0.95:
        reasons.append("near_52w_high")
    if row.get("rvol") is not None and row["rvol"] < 1.0:
        reasons.append("low_relative_volume")
    if extra and not extra.get("liquidity_ok", False):
        reasons.append("missing_liquidity_eligibility")
    return reasons


def model_views(row: dict[str, Any], extra: dict[str, Any] | None = None) -> dict[str, str]:
    """Produce independent descriptive views, not a composite recommendation."""
    extra = extra or {}
    return {
        "trend": "support" if row.get("regime") and row.get("direction") else "reject",
        "momentum": "support"
        if (row.get("rvol") or 0.0) >= 1.5 and (row.get("gap") or 0.0) >= 0.0
        else "reject",
        "risk": "support"
        if (row.get("atr_pct") or 0.0) < 8.0 and (row.get("dist52") or 0.0) < 0.95
        else "reject",
        "liquidity": "support" if extra.get("liquidity_ok", False) else "reject",
    }


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"status": "insufficient_data", "n": 0}
    wins = sum(row["target"] for row in rows)
    returns = [row["net_return_pct"] for row in rows]
    return {
        "status": "ok",
        "n": len(rows),
        "positive_net_rate": round(wins / len(rows), 6),
        "mean_net_return_pct": round(sum(returns) / len(returns), 6),
        "median_net_return_pct": round(sorted(returns)[len(returns) // 2], 6),
    }


def run(
    csv_path: Path,
    cache_path: Path,
    cost_pct: float = 0.55,
    tp_mult: float = 2.0,
    sl_mult: float = 1.0,
    horizon: int = 5,
) -> dict[str, Any]:
    raw_rows = load_rows(str(csv_path))
    extra_fields = _read_fields(csv_path)
    resolved, inventory = resolve_paths(
        dedup_rows(raw_rows), str(cache_path), horizon=horizon, max_entry_drift=0.5
    )
    veto_rows: list[dict[str, Any]] = []
    losses: list[dict[str, Any]] = []
    disagreements: list[dict[str, Any]] = []
    for row, result in label_rows(resolved, tp_mult=tp_mult, sl_mult=sl_mult, horizon=horizon):
        key = (row["symbol"], row["scan_date"])
        extra = extra_fields.get(key, {})
        reasons = veto_reasons(row, extra)
        views = model_views(row, extra)
        net_return = result.ret_pct * 100.0 - cost_pct
        observation = {
            "event": f"{row['symbol']}:{row['scan_date']}",
            "scan_date": row["scan_date"],
            "net_return_pct": round(net_return, 6),
            "target": int(net_return > 0),
            "veto_reasons": reasons,
            "model_views": views,
            "disagreement": sum(value == "support" for value in views.values()),
        }
        veto_rows.append(observation)
        if net_return < 0:
            loss_reasons = []
            if row.get("atr_pct", 0.0) >= 8.0:
                loss_reasons.append("high_volatility")
            if row.get("gap") is not None and row["gap"] >= 5.0:
                loss_reasons.append("gap_risk")
            if not row.get("regime", False) or not row.get("direction", False):
                loss_reasons.append("weak_trend")
            if row.get("dist52") is not None and row["dist52"] >= 0.95:
                loss_reasons.append("near_52w_high")
            losses.append({**observation, "loss_reasons": loss_reasons or ["unclassified"]})
        disagreements.append(observation)

    rejected = [row for row in veto_rows if row["veto_reasons"]]
    eligible = [row for row in veto_rows if not row["veto_reasons"]]
    veto_summary: dict[str, Any] = {}
    for name in VETO_NAMES:
        rejected_by_reason = [row for row in veto_rows if name in row["veto_reasons"]]
        avoided_loss = sum(row["target"] == 0 for row in rejected_by_reason)
        false_rejection = sum(row["target"] == 1 for row in rejected_by_reason)
        veto_summary[name] = {
            "n": len(rejected_by_reason),
            "counterfactual_loss_rate": round(avoided_loss / len(rejected_by_reason), 6)
            if rejected_by_reason
            else None,
            "counterfactual_positive_rate": round(false_rejection / len(rejected_by_reason), 6)
            if rejected_by_reason
            else None,
            "status": "ok" if len(rejected_by_reason) >= 30 else "insufficient_data",
        }

    disagreement_summary = {}
    for support_count in range(5):
        subset = [row for row in disagreements if row["disagreement"] == support_count]
        disagreement_summary[str(support_count)] = _summary(subset)

    return {
        "methodology": {
            "target": "5-day triple-barrier net return > 0",
            "tp_mult": tp_mult,
            "sl_mult": sl_mult,
            "horizon": horizon,
            "cost_pct": cost_pct,
            "vetoes": list(VETO_NAMES),
            "veto_status": "descriptive_research_only",
            "model_views": ["trend", "momentum", "risk", "liquidity"],
        },
        "inventory": inventory,
        "candidate_summary": {
            "all": _summary(veto_rows),
            "rejected": _summary(rejected),
            "eligible": _summary(eligible),
        },
        "veto_quality": veto_summary,
        "loss_taxonomy": {
            "n_losses": len(losses),
            "reason_counts": Counter(reason for row in losses for reason in row["loss_reasons"]),
        },
        "model_disagreement": disagreement_summary,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv", type=Path, default=Path("data/backtest_out/full_universe_enriched.csv")
    )
    parser.add_argument("--cache", type=Path, default=Path("data/price_cache"))
    parser.add_argument(
        "--out", type=Path, default=Path("data/backtest_out/decision_quality_2026-08-06.json")
    )
    parser.add_argument("--cost-pct", type=float, default=0.55)
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    output = run(args.csv, args.cache, cost_pct=args.cost_pct)
    args.out.write_text(json.dumps(output, indent=2, default=dict), encoding="utf-8")
    print(f"OK -> {args.out}")


if __name__ == "__main__":
    main()
