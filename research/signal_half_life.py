"""Signal half-life (Gate 3.2) — research-only, Level A.

Measures how long the signal's predictive power persists, using the honest
close-to-close label (c2c) at multiple horizons. A signal whose edge decays
within a day cannot support a daily-cadence product; one that persists for
days can.

This is a coarse daily-bar approximation — intraday half-life requires
intraday data (Gate 3.3, open). It answers: "at daily resolution, does the
eligible cohort's realized return concentrate in the first day or persist?"
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def signal_half_life(df: pd.DataFrame) -> dict:
    """Cumulative realized return of the eligible cohort by horizon.

    Uses c2c_1d and c2c_5d (the only honest close-to-close fields). The
    half-life question: what share of the 5d move happens on day 1?
    """
    sub = df.dropna(subset=["c2c_1d", "c2c_5d"])
    elig = sub[sub["entry_ok"]]
    if len(elig) < 50:
        return {"status": "insufficient_data", "eligible_n": int(len(elig))}
    day1 = elig["c2c_1d"].to_numpy()
    day5 = elig["c2c_5d"].to_numpy()
    # Share of the 5d move realized on day 1 (only where day5 != 0)
    with np.errstate(divide="ignore", invalid="ignore"):
        share = np.where(np.abs(day5) > 1e-9, day1 / day5, np.nan)
    share = share[np.isfinite(share)]
    return {
        "status": "completed",
        "eligible_n": int(len(elig)),
        "day1_median_pct": round(float(np.median(day1)), 4),
        "day5_median_pct": round(float(np.median(day5)), 4),
        "day1_positive_rate": round(float((day1 > 0).mean()), 4),
        "day5_positive_rate": round(float((day5 > 0).mean()), 4),
        "day1_share_of_day5_median": round(float(np.median(share)), 4) if len(share) else None,
        "interpretation": (
            "edge concentrates on day 1 (fast decay)"
            if len(share) and abs(float(np.median(share))) > 0.5
            else "edge does not concentrate on day 1 (or is absent)"
        ),
        "note": "daily-bar approximation; intraday half-life needs Gate 3.3 data",
    }
