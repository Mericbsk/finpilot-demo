"""Back-compute legacy_quality_score (= ranking_score when LEGACY_COMPOSITE_RANKING=0)
and re-test all key negative score findings against it.

Research-only; Level A diagnostic. No production change.

Formula source: scanner/score_engine.py::compute_legacy_quality_score (read from code).
Flag source: .env FINPILOT_ENABLE_LEGACY_COMPOSITE_RANKING=0 (repo file).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

COST_PCT = 0.55
RNG_SEED = 20260812


def _normalized(value: float | None, scale: float) -> float:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return 0.0
    return max(0.0, min(1.0, float(value) / scale))


def compute_legacy_quality_score_row(
    regime: bool,
    direction: bool,
    raw_score: float,
    atr_pct: float | None,
    rvol: float | None,
    squeeze_factor: float | None = None,
    lottery_factor: float | None = None,
    overnight_gap_factor: float | None = None,
) -> float:
    """Mirror of scanner/score_engine.py::compute_legacy_quality_score."""
    base = 2.0 * float(regime) + 2.0 * float(direction) + 1.5 * _normalized(raw_score, 3.0)
    atr = _normalized(atr_pct, 6.0)
    relative_volume = _normalized(
        (float(rvol) - 1.0) if rvol is not None and not np.isnan(float(rvol)) else None, 2.0
    )
    squeeze = max(0.0, min(1.0, float(squeeze_factor or 0.0)))
    lottery = max(0.0, min(1.0, float(lottery_factor or 0.0)))
    overnight = max(0.0, min(1.0, float(overnight_gap_factor or 0.0)))
    return round(
        (base + 1.5 * atr + 1.5 * relative_volume + 0.5 * squeeze - 1.5 * lottery - overnight)
        / 10.0
        * 100.0,
        3,
    )


def backtest_score(df: pd.DataFrame, score_col: str) -> dict[str, Any]:
    """Re-run the key negative findings against a given score column."""
    d = df[df[score_col].notna() & df["c2c_5d"].notna()].copy()
    if len(d) < 100:
        return {"status": "insufficient_data", "n": len(d)}

    out: dict[str, Any] = {"score_col": score_col, "n": len(d)}

    # R1: backward vs forward Spearman
    if "past_5d_proxy" in d.columns:
        out["spearman_past"] = float(d[score_col].corr(d["past_5d_proxy"], method="spearman"))
    out["spearman_fwd_5d"] = float(d[score_col].corr(d["c2c_5d"], method="spearman"))
    out["spearman_fwd_1d"] = float(d[score_col].corr(d["c2c_1d"], method="spearman"))

    # L4: top-quintile eligible vs not-eligible
    try:
        d["q"] = pd.qcut(d[score_col], 5, labels=False, duplicates="drop")
        top = d[d["q"] == d["q"].max()]
        out["top_quintile_median_eligible"] = float(top[top["entry_ok"]]["c2c_5d"].median())
        out["top_quintile_median_not_eligible"] = float(top[~top["entry_ok"]]["c2c_5d"].median())
        out["top_quintile_gap_pp"] = (
            out["top_quintile_median_eligible"] - out["top_quintile_median_not_eligible"]
        )
        out["top_quintile_n_eligible"] = int(top["entry_ok"].sum())
        out["top_quintile_n_not"] = int((~top["entry_ok"]).sum())
    except ValueError:
        out["top_quintile"] = "insufficient_distinct_scores"

    # Decile monotonicity
    try:
        d["decile"] = pd.qcut(d[score_col], 10, labels=False, duplicates="drop")
        dec_medians = d.groupby("decile")["c2c_5d"].median()
        out["decile_medians"] = {int(k): round(float(v), 4) for k, v in dec_medians.items()}
        out["decile_monotonicity_spearman"] = float(
            pd.Series(range(len(dec_medians))).corr(
                dec_medians.reset_index(drop=True), method="spearman"
            )
        )
    except ValueError:
        out["decile"] = "insufficient_distinct_scores"

    # P1-style: eligible vs same-date random rejected
    rng = np.random.default_rng(RNG_SEED)
    diffs = []
    for date, eg in d[d["entry_ok"]].groupby("scan_date"):
        ev = eg["c2c_5d"].dropna().to_numpy(float)
        if len(ev) == 0:
            continue
        rv = d[(~d["entry_ok"]) & (d["scan_date"] == date)]["c2c_5d"].dropna().to_numpy(float)
        if len(rv) < len(ev):
            continue
        e_med = float(np.median(ev))
        rand_meds = [
            float(np.median(rng.choice(rv, size=len(ev), replace=False))) for _ in range(200)
        ]
        diffs.append(e_med - float(np.mean(rand_meds)))
    if diffs:
        arr = np.array(diffs)
        out["p1_matched"] = {
            "matched_dates": len(diffs),
            "median_diff_pp": float(np.median(arr)),
            "share_dates_positive": float((arr > 0).mean()),
        }

    # Eligible overall median/mean
    el = d[d["entry_ok"]]
    out["eligible_median_5d"] = float(el["c2c_5d"].median())
    out["eligible_mean_5d"] = float(el["c2c_5d"].mean())

    return out


def main() -> None:
    df = pd.read_csv("data/backtest_out/full_universe_enriched.csv", low_memory=False)
    df = df.drop_duplicates(["symbol", "scan_date"], keep="first")
    df["entry_ok"] = df["entry_ok"].astype(bool)

    # Back-compute past_5d return proxy from dist_52w_high (approximation)
    # We don't have past_5d directly, so we skip backward-looking test for ranking_score.
    # Instead, we compute ranking_score and compare its forward correlation.

    # Compute legacy_quality_score row by row
    df["ranking_score_backtest"] = df.apply(
        lambda r: compute_legacy_quality_score_row(
            regime=bool(r.get("regime", False)),
            direction=bool(r.get("direction", False)),
            raw_score=float(r.get("score", 0)),
            atr_pct=r.get("atr_pct_real"),
            rvol=r.get("rvol"),
            squeeze_factor=r.get("squeeze_factor"),
            lottery_factor=r.get("lottery_factor"),
            overnight_gap_factor=r.get("overnight_gap_factor"),
        ),
        axis=1,
    )

    print(f"ranking_score computed: {df['ranking_score_backtest'].notna().sum()} rows")
    print(
        f"ranking_score range: {df['ranking_score_backtest'].min():.1f} - {df['ranking_score_backtest'].max():.1f}"
    )

    results = {}

    # Test ranking_score (the live one)
    results["ranking_score"] = backtest_score(df, "ranking_score_backtest")

    # Test composite_score (what we tested before)
    results["composite_score"] = backtest_score(df, "composite_score")

    # Test finpilot_score (also tested before)
    results["finpilot_score"] = backtest_score(df, "finpilot_score")

    # Correlation between the three scores
    scored = df[df["ranking_score_backtest"].notna() & df["composite_score"].notna()]
    results["score_correlations"] = {
        "ranking_vs_composite": float(
            scored["ranking_score_backtest"].corr(scored["composite_score"], method="spearman")
        ),
        "ranking_vs_finpilot": float(
            df[df["ranking_score_backtest"].notna() & df["finpilot_score"].notna()][
                "ranking_score_backtest"
            ].corr(
                df[df["ranking_score_backtest"].notna() & df["finpilot_score"].notna()][
                    "finpilot_score"
                ],
                method="spearman",
            )
        ),
    }

    payload = {
        "status": "exploratory",
        "production_change": False,
        "locked_oos": "not_opened",
        "formula_source": "scanner/score_engine.py::compute_legacy_quality_score",
        "flag_source": ".env FINPILOT_ENABLE_LEGACY_COMPOSITE_RANKING=0",
        "caveat": "Cannot verify live server env; only repo .env confirmed",
        "results": results,
    }

    out_path = Path("data/backtest_out/ranking_score_backtest_2026-08-12.json")
    out_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    # Print key findings
    for score_name, res in results.items():
        if score_name == "score_correlations":
            print("\n=== Score correlations ===")
            for k, v in res.items():
                print(f"  {k}: {v:.4f}")
            continue
        print(f"\n=== {score_name} (n={res['n']}) ===")
        print(f"  spearman fwd_5d: {res.get('spearman_fwd_5d', 'N/A'):.4f}")
        print(f"  spearman fwd_1d: {res.get('spearman_fwd_1d', 'N/A'):.4f}")
        if "top_quintile_gap_pp" in res:
            print(
                f"  top-quintile gap: {res['top_quintile_gap_pp']:.2f}pp (elig={res['top_quintile_median_eligible']:.2f} vs not={res['top_quintile_median_not_eligible']:.2f})"
            )
        if "p1_matched" in res:
            print(
                f"  P1 matched: {res['p1_matched']['median_diff_pp']:.2f}pp ({res['p1_matched']['share_dates_positive']:.0%} positive dates)"
            )
        print(f"  eligible median 5d: {res.get('eligible_median_5d', 'N/A'):.2f}%")
        if "decile_monotonicity_spearman" in res:
            print(f"  decile monotonicity: {res['decile_monotonicity_spearman']:.4f}")
            print(f"  decile medians: {res['decile_medians']}")


if __name__ == "__main__":
    main()
