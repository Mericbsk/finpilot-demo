"""Scanner Risk Engine — Sprint 5 T3

ATR-based dynamic stop-loss, take-profit, and position sizing extracted
from scanner/evaluate.py so it can be unit-tested and adjusted without
touching the main evaluation pipeline.
"""

from __future__ import annotations

from typing import Any


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
