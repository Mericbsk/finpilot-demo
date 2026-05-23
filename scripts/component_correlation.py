"""Component Correlation — Pearson correlation matrix between scoring components.

Reuses the same parse_components() extraction as component_ablation.py.
Flags any pair with |r| > 0.7 as highly correlated (redundant).

Output: data/component_correlation.json
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.component_ablation import parse_components  # noqa: E402
from scripts.profitcore_audit import (  # noqa: E402
    extract_outcome_pct,
    load_archive_signals,
    load_live_signals,
    resolve_outcomes_yf,
)

OUT = ROOT / "data" / "component_correlation.json"

_COMPONENTS = [
    "score",
    "align_z",
    "align_m",
    "filter_ratio",
    "regime_trend",
    "sentiment",
    "risk_reward",
]


def _pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=False))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return 0.0
    return num / (dx * dy)


def main(days: int = 60, resolve: bool = False) -> dict:
    signals = load_archive_signals(days) + load_live_signals()
    if resolve:
        resolve_outcomes_yf(signals, horizon_days=5)

    series: dict[str, list[float]] = {k: [] for k in _COMPONENTS}
    outcomes: list[float] = []

    for s in signals:
        comp = parse_components(s)
        for k in _COMPONENTS:
            series[k].append(float(comp.get(k, 0.0) or 0.0))
        pct = extract_outcome_pct(s)
        outcomes.append(float(pct) if pct is not None else float("nan"))

    n = len(signals)
    if n < 2:
        out = {"error": "not enough signals", "n": n}
        OUT.write_text(json.dumps(out, indent=2))
        return out

    matrix: dict[str, dict[str, float]] = {}
    for a in _COMPONENTS:
        matrix[a] = {}
        for b in _COMPONENTS:
            matrix[a][b] = round(_pearson(series[a], series[b]), 3)

    flagged = []
    for i, a in enumerate(_COMPONENTS):
        for b in _COMPONENTS[i + 1 :]:
            r = matrix[a][b]
            if abs(r) > 0.7:
                flagged.append({"a": a, "b": b, "r": r})

    # Correlation with outcome (only where outcome resolved)
    outcome_corr = {}
    resolved_idx = [i for i, v in enumerate(outcomes) if not math.isnan(v)]
    if len(resolved_idx) >= 2:
        ys = [outcomes[i] for i in resolved_idx]
        for k in _COMPONENTS:
            xs = [series[k][i] for i in resolved_idx]
            outcome_corr[k] = round(_pearson(xs, ys), 3)

    out = {
        "n_signals": n,
        "n_resolved": len(resolved_idx),
        "components": _COMPONENTS,
        "matrix": matrix,
        "high_correlation_pairs": flagged,
        "correlation_with_outcome_pct": outcome_corr,
        "threshold": 0.7,
        "note": (
            "Pairs with |r| > 0.7 are redundant — one can likely be dropped. "
            "correlation_with_outcome_pct shows how well each component predicts "
            "the T+5 forward return."
        ),
    }
    OUT.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=60)
    p.add_argument("--resolve", action="store_true")
    args = p.parse_args()
    main(days=args.days, resolve=args.resolve)
