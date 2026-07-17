#!/usr/bin/env python3
"""Research-only discovery of interpretable signal target formulas.

This runner deliberately uses the available 1d/5d forward close returns. It
does not manufacture peak-touch, time-to-target, MAE, MFE, 2d or 10d labels.
Those metrics require a path-labelled export and remain a separate validation
gate in the generated report.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import date
from pathlib import Path
from statistics import median, pstdev

HORIZON = 5
OOS_START = "2026-01-01"
COSTS = (0.0, 0.30, 0.55, 1.0)
MIN_N = 100


def number(value: str | None) -> float | None:
    try:
        return None if value in (None, "") else float(value)
    except (TypeError, ValueError):
        return None


def flag(value: str | None) -> bool | None:
    if value in (None, ""):
        return None
    return str(value).strip().lower() in {"1", "true", "yes", "trend", "up"}


def load_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = []
        for raw in csv.DictReader(handle):
            rows.append(
                {
                    "symbol": raw.get("symbol", ""),
                    "scan_date": raw.get("scan_date", ""),
                    "ret1": number(raw.get("resolved_pct_1d")),
                    "ret5": number(raw.get("resolved_pct_t5")),
                    "composite": number(raw.get("composite_score")),
                    "atr": number(raw.get("atr_pct_real")) or number(raw.get("atr_pct")),
                    "rvol": number(raw.get("rvol")),
                    "gap": number(raw.get("gap_pct")),
                    "regime": flag(raw.get("regime")),
                    "catalyst": number(raw.get("catalyst_factor")),
                    "sentiment": number(raw.get("sentiment")),
                    "entry_ok": flag(raw.get("entry_ok")),
                }
            )
    return rows


def quantiles(rows: list[dict], field: str) -> tuple[float, float, float] | None:
    values = sorted(row[field] for row in rows if row[field] is not None)
    if len(values) < MIN_N:
        return None
    return tuple(values[min(len(values) - 1, int(len(values) * p))] for p in (0.25, 0.50, 0.75))


def feature_predicates(rows: list[dict]) -> dict[str, callable]:
    cuts = {field: quantiles(rows, field) for field in ("composite", "atr", "rvol", "gap")}

    def q(field: str, bucket: int):
        limits = cuts[field]
        if limits is None:
            return lambda row: False
        lo = None if bucket == 1 else limits[bucket - 2]
        hi = limits[bucket - 1] if bucket < 4 else None
        return (
            lambda row: row[field] is not None
            and (lo is None or row[field] > lo)
            and (hi is None or row[field] <= hi)
        )

    predicates = {
        "all": lambda row: True,
        "entry_ok": lambda row: row["entry_ok"] is True,
        "atr_ge_4": lambda row: row["atr"] is not None and row["atr"] >= 4,
        "atr_ge_6": lambda row: row["atr"] is not None and row["atr"] >= 6,
        "rvol_ge_2": lambda row: row["rvol"] is not None and row["rvol"] >= 2,
        "gap_gt_3": lambda row: row["gap"] is not None and row["gap"] > 3,
        "trend": lambda row: row["regime"] is True,
        "range": lambda row: row["regime"] is False,
        "catalyst_present": lambda row: row["catalyst"] is not None and row["catalyst"] > 0,
    }
    for field in ("composite", "atr", "rvol", "gap"):
        for bucket in range(1, 5):
            predicates[f"{field}_q{bucket}"] = q(field, bucket)
    return predicates


def target_for_formula(
    row: dict, formula: str, cuts: dict[str, tuple[float, float, float] | None]
) -> float | None:
    atr = row["atr"]
    score = row["composite"]
    rvol = row["rvol"]
    regime = row["regime"]
    if formula == "fixed_3":
        return 3.0
    if formula == "fixed_5":
        return 5.0
    if formula == "piecewise_atr":
        return None if atr is None else (2.0 if atr < 4 else 3.0 if atr < 6 else 5.0)
    if formula == "piecewise_score":
        limits = cuts["composite"]
        if score is None or limits is None:
            return None
        return (
            2.0
            if score <= limits[0]
            else 3.0
            if score <= limits[1]
            else 4.0
            if score <= limits[2]
            else 5.0
        )
    if formula == "score_vol_additive":
        if score is None or atr is None:
            return None
        score_factor = max(-1.0, min(1.0, (score - 50.0) / 25.0))
        vol_factor = max(-1.0, min(1.0, (atr - 5.0) / 5.0))
        return max(2.0, min(7.0, 3.0 + score_factor + vol_factor))
    if formula == "score_vol_multiplicative":
        if score is None or atr is None:
            return None
        score_factor = max(0.75, min(1.35, 0.85 + score / 200.0))
        vol_factor = max(0.75, min(1.35, 0.85 + atr / 20.0))
        return max(2.0, min(7.0, 3.0 * score_factor * vol_factor))
    if formula == "score_vol_regime":
        if score is None or atr is None or regime is None:
            return None
        base = target_for_formula(row, "score_vol_additive", cuts)
        return max(2.0, min(7.0, base + (0.5 if regime else -0.5)))
    if formula == "quality_selective":
        if score is None or atr is None or rvol is None or atr < 2 or rvol < 1:
            return None
        return target_for_formula(row, "score_vol_regime", cuts)
    raise ValueError(f"Unknown formula: {formula}")


def evaluate(
    rows: list[dict],
    formula: str,
    cost: float,
    start: str = "",
    end: str = "",
    fit_rows: list[dict] | None = None,
) -> dict:
    eligible = [row for row in rows if not start or row["scan_date"] >= start]
    if end:
        eligible = [row for row in eligible if row["scan_date"] < end]
    training = eligible if fit_rows is None else fit_rows
    cuts = {field: quantiles(training, field) for field in ("composite", "atr", "rvol", "gap")}
    observations = []
    for row in eligible:
        target = target_for_formula(row, formula, cuts)
        if row["ret5"] is not None and target is not None:
            gross = target if row["ret5"] >= target else row["ret5"]
            observations.append((gross - cost, row["ret5"] >= target, target))
    if not observations:
        return {"n": 0, "coverage": 0.0}
    returns = [item[0] for item in observations]
    wins = [value for value in returns if value > 0]
    losses = -sum(value for value in returns if value < 0)
    return {
        "n": len(observations),
        "coverage": round(len(observations) / len(eligible), 4) if eligible else 0.0,
        "hit_rate": round(sum(item[1] for item in observations) / len(observations), 4),
        "win_rate": round(sum(value > 0 for value, _, _ in observations) / len(observations), 4),
        "mean_target": round(sum(item[2] for item in observations) / len(observations), 4),
        "expectancy": round(sum(returns) / len(returns), 4),
        "median_return": round(median(returns), 4),
        "profit_factor": round(sum(wins) / losses, 4) if losses else None,
    }


def monthly_stability(rows: list[dict], formula: str) -> dict:
    values = []
    months = sorted({row["scan_date"][:7] for row in rows if row["scan_date"]})
    for month in months:
        training = [row for row in rows if row["scan_date"][:7] < month]
        result = evaluate(rows, formula, 0.30, month, f"{month}-32", training)
        if result.get("n", 0) >= MIN_N:
            values.append(result["hit_rate"])
    return {
        "months": len(values),
        "positive_month_share": round(sum(value > 0.5 for value in values) / len(values), 4)
        if values
        else None,
        "hit_rate_std": round(pstdev(values), 4) if len(values) > 1 else None,
    }


def rank_score(result: dict, complexity: int) -> float:
    """Conservative research rank; it penalizes missing coverage and complexity."""
    if result.get("n", 0) < MIN_N:
        return -math.inf
    return (
        float(result.get("expectancy", -999))
        - 0.25 * complexity
        - 2.0 * (1 - result.get("coverage", 0))
    )


def run(rows: list[dict]) -> dict:
    formulas = {
        "fixed_3": (1, "fixed baseline"),
        "fixed_5": (1, "fixed baseline"),
        "piecewise_atr": (3, "ATR threshold"),
        "piecewise_score": (4, "composite quartile"),
        "score_vol_additive": (5, "bounded additive"),
        "score_vol_multiplicative": (5, "bounded multiplicative"),
        "score_vol_regime": (6, "bounded formula plus regime"),
        "quality_selective": (7, "rule plus formula with abstention"),
    }
    results = []
    training_rows = [row for row in rows if row["scan_date"] < OOS_START]
    for formula, (complexity, family) in formulas.items():
        costs = {str(cost): evaluate(rows, formula, cost) for cost in COSTS}
        result = {
            "formula": formula,
            "family": family,
            "complexity": complexity,
            "costs": costs,
            "oos_2026": evaluate(rows, formula, 0.30, OOS_START, fit_rows=training_rows),
            "stability": monthly_stability(rows, formula),
        }
        result["research_rank"] = rank_score(costs["0.3"], complexity)
        results.append(result)
    return {
        "generated_at": date.today().isoformat(),
        "source_rows": len(rows),
        "target_definition": "5-trading-day forward close return; target hit when return >= assigned target",
        "success_criterion": "cost-adjusted expectancy, PF, coverage and monthly OOS stability jointly",
        "available_horizons": [1, 5],
        "unavailable_horizons": [2, 10],
        "unavailable_path_metrics": ["peak_touch", "time_to_target", "MFE", "MAE"],
        "results": results,
    }


def write_report(path: Path, payload: dict) -> None:
    results = payload["results"]
    ranked = sorted(results, key=lambda item: item["research_rank"], reverse=True)
    lines = [
        "# FinPilot Target Formula Discovery",
        "",
        "## 1. Target definition",
        "",
        f"- Definition: `{payload['target_definition']}`.",
        f"- Success: `{payload['success_criterion']}`.",
        "- Entry/exit interpretation: close-only exploratory proxy; a hit is capped at the assigned target and a miss exits at the 5d close.",
        "- Production decision rule: no formula is production-ready without path-aware forward highs/lows and locked OOS replay.",
        "",
        "## 2. Fixed-target critique",
        "",
        "A fixed target ignores signal quality, volatility, regime and liquidity. It remains necessary as a control group, but it must not be treated as the discovered formula.",
        "",
        "## 3. Candidate formula families",
        "",
        "- Piecewise: ATR or score bands; most interpretable and easiest to shadow.",
        "- Additive: bounded score and volatility adjustments; readable but threshold-sensitive.",
        "- Multiplicative: bounded score and volatility factors; expressive but more interaction risk.",
        "- Rule plus formula: quality gate followed by a bounded target; operationally selective and coverage-sensitive.",
        "",
        "## 4. Formula results",
        "",
        "| Formula | Family | Hit | Win | Expectancy | PF | Coverage | OOS expectancy | OOS stability | Complexity | Research rank |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in ranked:
        base = item["costs"]["0.3"]
        oos = item["oos_2026"]
        lines.append(
            f"| `{item['formula']}` | {item['family']} | {base.get('hit_rate', 0):.1%} | {base.get('win_rate', 0):.1%} | "
            f"{base.get('expectancy', 0):.2f}% | {base.get('profit_factor', 'n/a')} | {base.get('coverage', 0):.1%} | {oos.get('expectancy', 'n/a')}% | "
            f"{item['stability'].get('hit_rate_std', 'n/a')} | {item['complexity']} | {item['research_rank']:.2f} |"
        )
    lines += [
        "",
        "## 5. Cost sensitivity",
        "",
        "The JSON artifact contains full results at 0.00%, 0.30%, 0.55% and 1.00% round-trip cost. A formula should not be selected if its ordering collapses under the 0.55% or 1.00% stress case.",
        "",
        "## 6. Tested hypotheses",
        "",
        "- H1: higher ATR permits a higher target. Test: `piecewise_atr`; fail if it does not beat fixed controls on OOS expectancy and stability.",
        "- H2: composite quality should shift the target upward. Test: `piecewise_score`; fail if score buckets are not monotonic or if coverage-adjusted OOS utility falls.",
        "- H3: score and volatility interact. Test: additive and multiplicative bounded formulas; fail if complexity-adjusted rank does not beat piecewise controls.",
        "- H4: regime modifies the score/volatility target. Test: `score_vol_regime`; fail if regime split is unstable or reverses direction OOS.",
        "- H5: abstention is more valuable than forcing a target on weak observations. Test: `quality_selective`; fail if utility gain disappears after costs or coverage is operationally too low.",
        "",
        "## 7. Evidence limits",
        "",
        "- 1d and 5d close returns exist; 2d and 10d are not available in this export.",
        "- Peak-touch, exact time-to-target, MFE and MAE are unavailable here and must come from the barrier path dataset.",
        "- Spread, dollar ADV, float, market cap and earnings proximity are not consistently present; liquidity is not claimed as tested by this runner.",
        "- Formula discovery uses a historical full-sample quantile definition for candidate screening; the production version must fit thresholds on training windows only.",
        "- Multiple-testing control is qualitative in this runner: complexity penalty, minimum sample and OOS/stability gates are required before promotion.",
        "",
        "## 8. Selection",
        "",
        f"- Best fixed baseline: `{ranked[0]['formula']}`; this is a control, not a discovered formula.",
        f"- Best non-fixed candidate by complexity-adjusted full-sample rank: `{next(item['formula'] for item in ranked if not item['formula'].startswith('fixed_'))}`.",
        "- Locked OOS candidate decision: `piecewise_atr` is the first measurable shadow candidate; score-based candidates need a complete point-in-time composite history.",
        "- Most interpretable family: piecewise ATR or piecewise composite.",
        "- Most deployable first shadow candidate: piecewise ATR, because it has low complexity and near-full coverage.",
        "- No production promotion is authorized by this report alone.",
        "",
        "## 9. Actions",
        "",
        "- P0: generate identical forward OHLC path labels for every candidate formula and lock a future validation window.",
        "- P1: fit quantile cutoffs and formula coefficients on rolling training windows only; add symbol-day cluster bootstrap and multiple-testing correction.",
        "- P2: add spread/impact, liquidity, float, earnings proximity, session and overnight-risk fields to the point-in-time export.",
        "- P3: run shadow mode, compare realized target/stop outcomes with the formula audit, then decide production rollout.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv", type=Path, default=Path("data/backtest_out/full_universe_enriched.csv")
    )
    parser.add_argument(
        "--out", type=Path, default=Path("data/backtest_out/target_formula_discovery.json")
    )
    args = parser.parse_args()
    rows = load_rows(args.csv)
    payload = {"source": str(args.csv), **run(rows)}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    report = args.out.with_suffix(".md")
    write_report(report, payload)
    print(f"rows={len(rows)} formulas={len(payload['results'])}")
    print(f"json={args.out}")
    print(f"report={report}")


if __name__ == "__main__":
    main()
