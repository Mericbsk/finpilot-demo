"""Component Ablation — zero out each scoring component, recompute hit rate.

Reads resolved signals from data/signal_archive/*.json (and optionally live
KPI tracker), parses available components from each record, then for each
component "ablates" it (forces neutral value) and recomputes hit rate.

Output: data/component_ablation.json
"""

from __future__ import annotations

import json
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.profitcore_audit import (  # noqa: E402
    extract_outcome_pct,
    load_archive_signals,
    load_live_signals,
    resolve_outcomes_yf,
)

OUT = ROOT / "data" / "component_ablation.json"

_ALIGN_RE = re.compile(r"Z(\d+)%/M(\d+)%")
_FILTRE_RE = re.compile(r"Filtre\s*(\d+)/(\d+)")


def parse_components(s: dict) -> dict:
    """Extract numeric components per signal."""
    expl = str(s.get("explanation", "") or "")
    align_z = align_m = filt_n = filt_d = None
    m = _ALIGN_RE.search(expl)
    if m:
        align_z, align_m = int(m.group(1)), int(m.group(2))
    m = _FILTRE_RE.search(expl)
    if m:
        filt_n, filt_d = int(m.group(1)), int(m.group(2))

    regime = str(s.get("regime", "") or "").lower()
    regime_trend = 1.0 if "trend" in regime else 0.0

    sent = str(s.get("sentiment", "") or "").lower()
    sent_bull = 1.0 if "bull" in sent else (-1.0 if "bear" in sent else 0.0)

    rr = float(s.get("risk_reward", 0) or 0)

    return {
        "score": float(s.get("score", 0) or 0),
        "align_z": float(align_z) if align_z is not None else 0.0,
        "align_m": float(align_m) if align_m is not None else 0.0,
        "filter_ratio": (filt_n / filt_d) if filt_n and filt_d else 0.0,
        "regime_trend": regime_trend,
        "sentiment": sent_bull,
        "risk_reward": rr,
    }


# Weights (linear proxy for the composite score)
_W = {
    "score": 1.0,
    "align_z": 0.1,
    "align_m": 0.1,
    "filter_ratio": 10.0,
    "regime_trend": 5.0,
    "sentiment": 3.0,
    "risk_reward": 2.0,
}


def composite(c: dict, ablate: str | None = None) -> float:
    return sum(_W[k] * (0.0 if k == ablate else c[k]) for k in _W)


def hit_rate_top_decile(rows: list[tuple[float, float]]) -> tuple[float, int]:
    if not rows:
        return 0.0, 0
    rows = sorted(rows, key=lambda r: r[0])
    top = rows[-max(1, len(rows) // 10) :]
    wins = sum(1 for _, p in top if p > 0)
    return round(wins / len(top), 3), len(top)


def overall_hit_rate(rows: list[tuple[float, float]]) -> float:
    if not rows:
        return 0.0
    wins = sum(1 for _, p in rows if p > 0)
    return round(wins / len(rows), 3)


def expectancy(rows: list[tuple[float, float]]) -> float:
    if not rows:
        return 0.0
    return round(statistics.mean(p for _, p in rows), 3)


def main(days: int = 60, resolve: bool = True) -> dict:
    signals = load_archive_signals(days) + load_live_signals()
    if resolve:
        resolve_outcomes_yf(signals, horizon_days=5)
    records = []
    for s in signals:
        pct = extract_outcome_pct(s)
        if pct is None:
            continue
        comp = parse_components(s)
        records.append((comp, float(pct)))

    if not records:
        out = {"error": "no resolved signals", "n": 0}
        OUT.write_text(json.dumps(out, indent=2))
        return out

    baseline = [(composite(c), p) for c, p in records]
    base_top_hr, top_n = hit_rate_top_decile(baseline)
    base_hr = overall_hit_rate(baseline)
    base_exp = expectancy(baseline)

    table = []
    for comp_name in _W:
        rows = [(composite(c, ablate=comp_name), p) for c, p in records]
        top_hr, _ = hit_rate_top_decile(rows)
        hr = overall_hit_rate(rows)
        exp = expectancy(rows)
        table.append(
            {
                "component": comp_name,
                "weight": _W[comp_name],
                "top_decile_hit_rate": top_hr,
                "delta_top_hr_vs_base": round(top_hr - base_top_hr, 3),
                "overall_hit_rate": hr,
                "delta_overall_hr": round(hr - base_hr, 3),
                "expectancy_pct": exp,
                "delta_expectancy": round(exp - base_exp, 3),
            }
        )

    table.sort(key=lambda r: r["delta_top_hr_vs_base"], reverse=True)

    out = {
        "n_records": len(records),
        "top_decile_n": top_n,
        "baseline": {
            "top_decile_hit_rate": base_top_hr,
            "overall_hit_rate": base_hr,
            "expectancy_pct": base_exp,
        },
        "ablations": table,
        "note": (
            "delta_top_hr_vs_base > 0 means removing the component IMPROVED "
            "top-decile hit rate (i.e. the component is harmful)."
        ),
    }
    OUT.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=60)
    p.add_argument("--no-resolve", action="store_true")
    args = p.parse_args()
    main(days=args.days, resolve=not args.no_resolve)
