"""Scanner Position Sizer — Task 3: Dynamic Risk Management

Dynamic position sizing that incorporates:
  - Fixed-fractional (% of account equity at risk per trade)
  - Kelly criterion (fractional)
  - Regime-adaptive scaling (reduce size in high-volatility regimes)
  - Volatility-normalised sizing (scale by inverse vol)
  - Portfolio heat limit (max concurrent exposure)

Entry point
-----------
calculate_dynamic_position(price, stop_loss, account_equity, ...)
"""

from __future__ import annotations

from typing import Any

# ── Default account config ────────────────────────────────────────────────────
DEFAULT_EQUITY = 10_000.0  # Fallback account equity if none provided
MAX_RISK_PCT = 0.02  # Maximum 2% of equity at risk per trade
MIN_RISK_PCT = 0.005  # Minimum 0.5% of equity at risk per trade
MAX_POSITION_PCT = 0.15  # Max 15% of equity in a single position
PORTFOLIO_HEAT_MAX = 0.06  # Stop adding positions once >6% total portfolio at risk
DEFAULT_KELLY_FRAC = 0.25  # Conservative half-Kelly fraction


def _clamp(val: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, val))


def _regime_scale(composite_score: int, is_bull_regime: bool) -> float:
    """Return a position-size multiplier based on market regime and score quality.

    Logic (from barrier audit 2026-06-12):
    - Bull + high score (>62):  suppress ×0.75 (false-positive zone)
    - Bear + mid score (30-55): boost ×1.30 (contrarian edge zone)
    - All other:                neutral ×1.00
    """
    if is_bull_regime and composite_score > 62:
        return 0.75
    if not is_bull_regime and 30 <= composite_score <= 55:
        return 1.30
    return 1.00


def _kelly_size(
    win_rate: float,
    avg_win_r: float,
    avg_loss_r: float,
    fraction: float = DEFAULT_KELLY_FRAC,
) -> float:
    """Fractional Kelly position size as a fraction of equity.

    Kelly fraction = (p·b - q) / b   where b = avg_win / avg_loss

    Args:
        win_rate:   Estimated probability of winning trade (0–1).
        avg_win_r:  Average winning trade size (in R multiples, e.g. 1.5 = 1.5R).
        avg_loss_r: Average losing trade size (in R multiples, typically 1.0).
        fraction:   Fractional Kelly multiplier (0.25 = quarter-Kelly).

    Returns:
        Fractional Kelly size as fraction of equity [0.0, 0.20].
    """
    if avg_loss_r <= 0 or avg_win_r <= 0:
        return 0.02  # fallback: 2% of equity
    q = 1.0 - win_rate
    b = avg_win_r / avg_loss_r
    full_kelly = (win_rate * b - q) / b
    fractional = full_kelly * fraction
    return _clamp(fractional, 0.005, 0.20)


def calculate_dynamic_position(
    price: float,
    stop_loss: float,
    account_equity: float = DEFAULT_EQUITY,
    composite_score: int = 50,
    is_bull_regime: bool = True,
    risk_reward: float = 2.0,
    ann_vol_pct: float = 20.0,
    kelly_fraction: float = DEFAULT_KELLY_FRAC,
    portfolio_current_risk_pct: float = 0.0,
) -> dict[str, Any]:
    """Calculate dynamic position size for a single trade.

    Combines four layers:
    1. Fixed-fractional: risk MAX_RISK_PCT of equity per trade
    2. Kelly criterion: scale by win-probability-adjusted optimal size
    3. Regime scaling: shrink in high-false-positive regimes
    4. Volatility normalisation: wider stop → smaller size

    Args:
        price:                      Entry price.
        stop_loss:                  Stop-loss price.
        account_equity:             Total account equity (dollars). Defaults to $10k.
        composite_score:            Scanner composite score (0–100).
        is_bull_regime:             True if market is in bull regime.
        risk_reward:                Target risk/reward ratio.
        ann_vol_pct:                Annualised volatility % from risk_metrics.
        kelly_fraction:             Fractional Kelly multiplier (default 0.25).
        portfolio_current_risk_pct: Sum of risk% already committed in open positions.

    Returns:
        Dictionary with:
            shares           – Suggested share count (integer)
            notional         – Suggested notional value ($)
            risk_amount      – $ at risk (price - stop_loss) × shares
            risk_pct         – risk_amount / account_equity as %
            position_pct     – notional / account_equity as %
            kelly_pct        – Kelly-only sizing as % of equity
            regime_scale     – Regime multiplier applied (0.75 / 1.0 / 1.30)
            portfolio_ok     – True if portfolio heat limit not exceeded
            sizing_method    – Description of sizing approach used
    """
    out: dict[str, Any] = {
        "shares": 0,
        "notional": 0.0,
        "risk_amount": 0.0,
        "risk_pct": 0.0,
        "position_pct": 0.0,
        "kelly_pct": 0.0,
        "regime_scale": 1.0,
        "portfolio_ok": True,
        "sizing_method": "fixed-fractional",
    }

    try:
        if price <= 0 or stop_loss <= 0 or price <= stop_loss:
            # stop_loss above/equal price: invalid
            return out

        risk_per_share = price - stop_loss
        if risk_per_share <= 0:
            return out

        # ── Portfolio heat gate ───────────────────────────────────────────
        remaining_heat = PORTFOLIO_HEAT_MAX - portfolio_current_risk_pct / 100.0
        if remaining_heat <= 0:
            out["portfolio_ok"] = False
            return out

        # ── Fixed-fractional baseline ─────────────────────────────────────
        base_risk_pct = _clamp(MAX_RISK_PCT, MIN_RISK_PCT, MAX_RISK_PCT)
        base_risk_pct = min(base_risk_pct, remaining_heat)

        # ── Kelly sizing ──────────────────────────────────────────────────
        # Approximate win_rate and avg_win_r from composite_score and R/R
        # score 0-100 → win_rate mapped linearly 30-65% (based on historical data)
        win_rate = _clamp(0.30 + (composite_score / 100.0) * 0.35, 0.30, 0.65)
        avg_win_r = max(risk_reward, 1.0)
        kelly_sz = _kelly_size(win_rate, avg_win_r, 1.0, kelly_fraction)
        out["kelly_pct"] = round(kelly_sz * 100, 2)

        # ── Blend fixed-fractional + Kelly ───────────────────────────────
        # Take minimum of: base_risk_pct × regime_scale, kelly_sz
        reg_scale = _regime_scale(composite_score, is_bull_regime)
        out["regime_scale"] = reg_scale
        adjusted_risk_pct = min(base_risk_pct * reg_scale, kelly_sz)
        adjusted_risk_pct = _clamp(adjusted_risk_pct, MIN_RISK_PCT, MAX_RISK_PCT)

        # ── Volatility normalisation ──────────────────────────────────────
        # Higher vol → smaller size. Normalise to 20% baseline vol.
        # If vol = 40% → scale = 20/40 = 0.5 (half position)
        baseline_vol = 20.0
        if ann_vol_pct > 0:
            vol_scale = _clamp(baseline_vol / ann_vol_pct, 0.4, 2.0)
        else:
            vol_scale = 1.0

        final_risk_pct = _clamp(adjusted_risk_pct * vol_scale, MIN_RISK_PCT, MAX_RISK_PCT)

        # ── Compute shares ────────────────────────────────────────────────
        risk_dollars = account_equity * final_risk_pct
        raw_shares = risk_dollars / risk_per_share
        shares = max(1, int(raw_shares))

        # Cap by position size limit
        max_notional = account_equity * MAX_POSITION_PCT
        if shares * price > max_notional:
            shares = max(1, int(max_notional / price))

        notional = shares * price
        actual_risk = shares * risk_per_share

        out.update(
            {
                "shares": shares,
                "notional": round(notional, 2),
                "risk_amount": round(actual_risk, 2),
                "risk_pct": round(actual_risk / account_equity * 100, 3),
                "position_pct": round(notional / account_equity * 100, 2),
                "sizing_method": "kelly+regime+vol-norm",
            }
        )

    except Exception:
        pass

    return out


def calculate_portfolio_metrics(
    positions: list[dict[str, Any]],
    account_equity: float = DEFAULT_EQUITY,
) -> dict[str, Any]:
    """Compute aggregate portfolio risk metrics from a list of open positions.

    Each position dict should have: price, stop_loss, shares (or notional).

    Returns:
        total_notional, total_risk_amount, total_risk_pct,
        avg_risk_per_trade_pct, position_count, heat_remaining_pct,
        diversification_score (0-100, higher = more diversified)
    """
    if not positions:
        return {
            "total_notional": 0.0,
            "total_risk_amount": 0.0,
            "total_risk_pct": 0.0,
            "avg_risk_per_trade_pct": 0.0,
            "position_count": 0,
            "heat_remaining_pct": round(PORTFOLIO_HEAT_MAX * 100, 1),
            "diversification_score": 100,
        }

    total_notional = 0.0
    total_risk = 0.0

    for p in positions:
        price = float(p.get("price", 0) or 0)
        stop = float(p.get("stop_loss", 0) or 0)
        shares = int(p.get("shares", 0) or 0)
        notional = float(p.get("notional", 0) or shares * price)
        risk = max(0.0, (price - stop) * shares) if stop > 0 and shares > 0 else 0.0
        total_notional += notional
        total_risk += risk

    n = len(positions)
    total_risk_pct = total_risk / account_equity * 100 if account_equity > 0 else 0.0
    heat_rem = max(0.0, PORTFOLIO_HEAT_MAX * 100 - total_risk_pct)

    # Diversification score: 100 if single position, decreases with concentration
    # Simple Herfindahl-Hirschman Index (HHI) proxy
    if total_notional > 0:
        weights = [(float(p.get("notional", 0) or 0) / total_notional) ** 2 for p in positions]
        hhi = sum(weights)  # 1/N = perfect diversification
        divers_score = int(_clamp((1 - hhi) * 100, 0, 100))
    else:
        divers_score = 0

    return {
        "total_notional": round(total_notional, 2),
        "total_risk_amount": round(total_risk, 2),
        "total_risk_pct": round(total_risk_pct, 2),
        "avg_risk_per_trade_pct": round(total_risk_pct / n if n > 0 else 0, 2),
        "position_count": n,
        "heat_remaining_pct": round(heat_rem, 1),
        "diversification_score": divers_score,
    }
