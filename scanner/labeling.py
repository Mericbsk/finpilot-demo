"""Triple-barrier labeling — measurement foundation (P0).

From the scanner research review: the system cannot claim a signal has *edge*
until each signal's outcome is labeled by which barrier it hit FIRST —
take-profit, stop-loss, or the time limit — rather than a single fixed-horizon
return (which ignores path dependency). This is the López de Prado triple-barrier
method, simplified for FinPilot's daily/bar OHLC data.

Pure functions, no I/O. Feed it a forward price path (closes, and optionally
highs/lows for precise intrabar touch) and the barriers; it returns the label,
bars-to-hit, realised return, and the MFE/MAE path statistics needed for
honest edge measurement (e.g. the weekly Edge Report).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass
class BarrierLabel:
    label: str  # "tp" | "sl" | "time"
    bars_to_hit: int  # bars from entry to the touch (or horizon on "time")
    entry_price: float
    exit_price: float
    ret_pct: float  # realised return at exit, signed (% as fraction)
    mfe_pct: float  # max favourable excursion over the holding window
    mae_pct: float  # max adverse excursion over the holding window

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "bars_to_hit": self.bars_to_hit,
            "entry_price": round(self.entry_price, 6),
            "exit_price": round(self.exit_price, 6),
            "ret_pct": round(self.ret_pct, 6),
            "mfe_pct": round(self.mfe_pct, 6),
            "mae_pct": round(self.mae_pct, 6),
        }


def triple_barrier_label(
    forward_closes: Sequence[float],
    *,
    entry_price: float,
    tp_pct: float,
    sl_pct: float,
    max_horizon: int | None = None,
    side: str = "long",
    forward_highs: Sequence[float] | None = None,
    forward_lows: Sequence[float] | None = None,
) -> BarrierLabel:
    """Label a trade by the first barrier touched.

    Args:
        forward_closes: close prices AFTER entry (bar 0 = first bar after entry).
        entry_price:    fill price at entry.
        tp_pct:         take-profit distance as a fraction (e.g. 0.10 = +10%).
        sl_pct:         stop-loss distance as a fraction, POSITIVE (e.g. 0.05 = -5%).
        max_horizon:    time barrier in bars; defaults to len(forward_closes).
        side:           "long" or "short".
        forward_highs/forward_lows: optional, for precise intrabar touch detection.
                        When omitted, closes are used for both barrier checks.

    Returns:
        BarrierLabel. If neither price barrier is touched within the horizon,
        label == "time" and exit is the last available close.

    Conservative tie-breaking: if BOTH barriers are touchable within the same
    bar (using high/low), the stop is assumed to hit first (worst case).
    """
    if tp_pct <= 0 or sl_pct <= 0:
        raise ValueError("tp_pct and sl_pct must be positive fractions")
    if side not in ("long", "short"):
        raise ValueError("side must be 'long' or 'short'")
    if entry_price <= 0:
        raise ValueError("entry_price must be positive")

    closes = list(forward_closes)
    n = len(closes)
    horizon = n if max_horizon is None else min(max_horizon, n)
    if horizon == 0:
        return BarrierLabel("time", 0, entry_price, entry_price, 0.0, 0.0, 0.0)

    highs = list(forward_highs) if forward_highs is not None else closes
    lows = list(forward_lows) if forward_lows is not None else closes

    if side == "long":
        tp_price = entry_price * (1.0 + tp_pct)
        sl_price = entry_price * (1.0 - sl_pct)
    else:
        tp_price = entry_price * (1.0 - tp_pct)
        sl_price = entry_price * (1.0 + sl_pct)

    def _ret(px: float) -> float:
        r = (px - entry_price) / entry_price
        return r if side == "long" else -r

    mfe = 0.0
    mae = 0.0
    for i in range(horizon):
        hi, lo = float(highs[i]), float(lows[i])
        # Update path excursions (favourable/adverse in trade terms).
        if side == "long":
            mfe = max(mfe, _ret(hi))
            mae = min(mae, _ret(lo))
            tp_touch = hi >= tp_price
            sl_touch = lo <= sl_price
        else:
            mfe = max(mfe, _ret(lo))
            mae = min(mae, _ret(hi))
            tp_touch = lo <= tp_price
            sl_touch = hi >= sl_price

        if sl_touch:  # conservative: stop wins same-bar ties
            return BarrierLabel("sl", i + 1, entry_price, sl_price, _ret(sl_price), mfe, mae)
        if tp_touch:
            return BarrierLabel("tp", i + 1, entry_price, tp_price, _ret(tp_price), mfe, mae)

    exit_px = float(closes[horizon - 1])
    return BarrierLabel("time", horizon, entry_price, exit_px, _ret(exit_px), mfe, mae)


def summarize_labels(labels: Sequence[BarrierLabel]) -> dict:
    """Aggregate a batch of labels into edge statistics for the Edge Report.

    Returns hit-rate (tp share), stop-rate, time-rate, average realised return,
    and a simple expectancy (mean ret_pct). Empty input → zeros.
    """
    n = len(labels)
    if n == 0:
        return {
            "n": 0,
            "tp_rate": 0.0,
            "sl_rate": 0.0,
            "time_rate": 0.0,
            "avg_ret_pct": 0.0,
            "avg_mfe_pct": 0.0,
            "avg_mae_pct": 0.0,
            "expectancy": 0.0,
        }
    tp = sum(1 for x in labels if x.label == "tp")
    sl = sum(1 for x in labels if x.label == "sl")
    tm = sum(1 for x in labels if x.label == "time")
    avg_ret = sum(x.ret_pct for x in labels) / n
    return {
        "n": n,
        "tp_rate": round(tp / n, 4),
        "sl_rate": round(sl / n, 4),
        "time_rate": round(tm / n, 4),
        "avg_ret_pct": round(avg_ret, 6),
        "avg_mfe_pct": round(sum(x.mfe_pct for x in labels) / n, 6),
        "avg_mae_pct": round(sum(x.mae_pct for x in labels) / n, 6),
        "expectancy": round(avg_ret, 6),
    }
