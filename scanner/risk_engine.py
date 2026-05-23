"""Scanner Risk Engine — Sprint 5 T3

ATR-based dynamic stop-loss, take-profit, and position sizing extracted
from scanner/evaluate.py so it can be unit-tested and adjusted without
touching the main evaluation pipeline.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

# Portfolio drawdown gate state file (resets daily)
_DD_STATE_PATH = Path(__file__).resolve().parents[1] / "data" / "portfolio_dd_state.json"


def daily_dd_breached(threshold: float = 0.03) -> bool:
    """Return True if today's realised portfolio drawdown >= threshold (fraction).

    Reads data/portfolio_dd_state.json:
        { "date": "YYYY-MM-DD", "start_equity": float, "current_equity": float }

    A missing/stale/malformed file is treated as "not breached" (fail-open so
    the scanner keeps running when state isn't initialised). Stale = date older
    than today (UTC); the file is logically reset on the first read of a new day.
    """
    try:
        if not _DD_STATE_PATH.exists():
            return False
        data = json.loads(_DD_STATE_PATH.read_text(encoding="utf-8"))
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        if str(data.get("date")) != today:
            return False  # stale: new day, no DD yet
        start = float(data.get("start_equity", 0) or 0)
        current = float(data.get("current_equity", 0) or 0)
        if start <= 0:
            return False
        dd = (start - current) / start
        return dd >= float(threshold)
    except Exception:
        return False


def record_equity_snapshot(equity: float) -> None:
    """Update the daily DD state file. Initialises start_equity on first call of the day."""
    try:
        _DD_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        state: dict[str, Any] = {}
        if _DD_STATE_PATH.exists():
            try:
                state = json.loads(_DD_STATE_PATH.read_text(encoding="utf-8"))
            except Exception:
                state = {}
        if state.get("date") != today:
            state = {"date": today, "start_equity": float(equity)}
        state["current_equity"] = float(equity)
        state["updated_at"] = datetime.now(UTC).isoformat()
        _DD_STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception:
        pass


# Suppress unused-import warnings if timedelta gets pruned by ruff later
_ = timedelta


def calculate_risk_management(price: float, atr_val: float, momentum_score: int) -> dict[str, Any]:
    """ATR-based dynamic stop-loss & take-profit.

    Multipliers are chosen by momentum tier:
      - Sniper  (score >= 70): tighter stop, aggressive targets
      - Normal  (50-69):       balanced
      - Defansif (score < 50): wider stop, conservative targets

    Args:
        price:          Current entry price
        atr_val:        Average True Range (same unit as price)
        momentum_score: 0-100 composite momentum score from evaluate_symbol

    Returns:
        Dict with stop_loss, take_profit, tp1/tp2/tp3, risk_reward_ratio,
        stop_loss_percent, position_size, strategy_tag.
    """
    if momentum_score >= 70:
        stop_mult, tp1_mult, tp2_mult, tp3_mult = 1.5, 3.0, 5.0, 8.0
        strategy_tag = "Sniper 🎯"
    elif momentum_score < 50:
        stop_mult, tp1_mult, tp2_mult, tp3_mult = 2.5, 4.5, 6.5, 0
        strategy_tag = "Defansif 🛡️"
    else:
        stop_mult, tp1_mult, tp2_mult, tp3_mult = 2.0, 3.5, 5.5, 7.5
        strategy_tag = "Normal 📈"

    stop_loss = price - (atr_val * stop_mult)
    tp1 = price + (atr_val * tp1_mult)
    tp2 = price + (atr_val * tp2_mult)
    tp3 = price + (atr_val * tp3_mult) if tp3_mult > 0 else 0
    take_profit = tp2
    position_size = 1000
    risk_reward_ratio = (
        (take_profit - price) / (price - stop_loss) if (price - stop_loss) != 0 else 0
    )
    stop_loss_percent = (price - stop_loss) / price * 100 if price != 0 else 0

    return {
        "stop_loss": round(stop_loss, 2),
        "take_profit": round(take_profit, 2),
        "tp1": round(tp1, 2),
        "tp2": round(tp2, 2),
        "tp3": round(tp3, 2) if tp3 > 0 else None,
        "strategy_tag": strategy_tag,
        "position_size": position_size,
        "risk_reward_ratio": round(risk_reward_ratio, 2),
        "stop_loss_percent": round(stop_loss_percent, 2),
    }
