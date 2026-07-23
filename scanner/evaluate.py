"""Scanner Evaluation Module — Sprint 2 B3 Refactoring

evaluate_symbol() ve evaluate_symbols_parallel() fonksiyonları
artık scanner package'ı içinde yaşıyor.  Eski scanner.py dosyası
geriye dönük uyumluluk için bu modülü import eder.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import pandas as pd

from .config import DELISTED_SYMBOLS_SET, get_setting
from .data_fetcher import (
    fetch_multi_timeframe,
    prefetch_symbols_multi_timeframe,
)
from .execution_policy import execution_contract, position_cap
from .position_sizer import calculate_dynamic_position
from .risk_engine import (
    calculate_risk_management,
    calculate_risk_management_yz,
    daily_dd_breached,
)
from .risk_metrics import calculate_risk_adjusted_metrics
from .score_engine import (
    compute_legacy_quality_score,
    compute_recommendation_score,
    compute_recommendation_strength,
    compute_v2_score,
    decision_telemetry,
    legacy_composite_ranking_enabled,
    regime_gate_mult,
    score_component_breakdown,
)
from .signals import (
    analyze_price_momentum,
    check_momentum_confluence,
    check_timeframe_alignment,
    check_trend_strength,
    check_volume_spike,
    safe_float,
)

logger = logging.getLogger(__name__)

# Global market status (set at scan-time)
CURRENT_MARKET_STATUS: dict[str, Any] = {"safe": True, "reason": "Varsayılan"}

STRATEGY_PARAMS = {
    "Normal": {"min_score": 1, "rsi_low": 30, "rsi_high": 70},
    "Agresif": {"min_score": 1, "rsi_low": 40, "rsi_high": 60},
    "Defansif": {"min_score": 2, "rsi_low": 25, "rsi_high": 75},
    "Momentum": {"min_score": 1, "rsi_low": 35, "rsi_high": 65},
}

# Faz 6: cost-label thresholds
_COST_FLAT_PCT: float = 0.0020  # 0.20% round-trip cost assumption (retail fallback)
_THIN_EDGE_THRESH: float = 0.003  # net EV < 0.3% → thin edge
_DECAY_EV_THRESH: float = 0.005  # high-vol + net EV < 0.5% → edge_decay warning


def _feature_contract_legacy(
    *,
    df_15m: pd.DataFrame,
    df_1h: pd.DataFrame,
    df_4h: pd.DataFrame,
    df_1d: pd.DataFrame,
    signal_timestamp: str,
) -> dict[str, Any]:
    frames = {"15m": df_15m, "1h": df_1h, "4h": df_4h, "1d": df_1d}
    signal_ts = pd.Timestamp(signal_timestamp)
    if signal_ts.tzinfo is not None:
        signal_ts = signal_ts.tz_localize(None)
    timestamps: dict[str, str | None] = {}
    ages: dict[str, float | None] = {}
    for name, frame in frames.items():
        if frame.empty:
            timestamps[name] = None
            ages[name] = None
            continue
        latest = pd.Timestamp(frame.index[-1])
        if latest.tzinfo is not None:
            latest = latest.tz_localize(None)
        timestamps[name] = latest.isoformat()
        ages[name] = round(max(0.0, (signal_ts - latest).total_seconds() / 60.0), 2)
    dollar_adv = None
    if all(column in df_1d.columns for column in ("Close", "Volume")):
        values = (
            (
                pd.to_numeric(df_1d["Close"], errors="coerce")
                * pd.to_numeric(df_1d["Volume"], errors="coerce")
            )
            .dropna()
            .tail(20)
        )
        if len(values) >= 5:
            dollar_adv = float(values.mean())
    spread_bps = None
    if "spread_bps" in df_15m.columns and pd.notna(df_15m["spread_bps"].iloc[-1]):
        spread_bps = float(df_15m["spread_bps"].iloc[-1])
    short_timestamp = df_1d.attrs.get("short_interest_timestamp")
    if short_timestamp is not None and hasattr(short_timestamp, "isoformat"):
        short_timestamp = short_timestamp.isoformat()
    available = {
        "spread_bps": spread_bps is not None,
        "dollar_adv": dollar_adv is not None,
        "short_interest_timestamp": short_timestamp is not None,
    }
    return {
        "spread_bps": round(spread_bps, 4) if spread_bps is not None else None,
        "spread_source": "spread_bps" if spread_bps is not None else "missing",
        "dollar_adv": round(dollar_adv, 2) if dollar_adv is not None else None,
        "adv_source": "close_volume_20d" if dollar_adv is not None else "missing",
        "short_interest_timestamp": short_timestamp,
        "feature_timestamps": timestamps,
        "feature_age_minutes": ages,
        "available": available,
        "missing_fields": [name for name, present in available.items() if not present],
    }


def _compute_cost_labels(
    ev_per_trade: float,
    ann_vol_pct: float,
    vol_regime: int,
    price: float,
) -> dict[str, object]:
    """Return Faz 6 net-return and edge-decay fields for the signal result dict.

    Uses core.slippage_tracker's real RealisticBacktestCosts model to estimate
    round-trip cost; falls back to _COST_FLAT_PCT (0.20%) if the import/call
    fails for any reason. (Previously imported a non-existent
    `estimate_round_trip_cost` function — every call silently fell back to
    the flat 0.20% one-sided assumption; see tests/test_scanner_fixes.py.)

    Returns keys: net_expected_return (float %), edge_label (str).
    """
    cost_pct = _COST_FLAT_PCT
    try:
        from core.slippage_tracker import RealisticBacktestCosts  # noqa: PLC0415

        cost_pct = RealisticBacktestCosts().round_trip_cost_pct() / 100.0
    except Exception:
        pass

    net_ev = ev_per_trade - cost_pct

    if net_ev <= 0:
        label = "negative"
    elif vol_regime == 2 and net_ev < _DECAY_EV_THRESH:
        label = "edge_decay"
    elif net_ev < _THIN_EDGE_THRESH:
        label = "thin_edge"
    else:
        label = "ok"

    return {
        "net_expected_return": round(net_ev, 4),
        "edge_label": label,
    }


def _execution_contract(data_quality: dict[str, Any]) -> dict[str, str]:
    """Return the compact legacy execution classification used by callers."""
    available = data_quality.get("available", {})
    if all(
        available.get(field, False)
        for field in ("spread_bps", "dollar_adv", "short_interest_timestamp")
    ):
        return {"execution_confidence": "Tier 2", "data_quality_tier": "Tier 2"}
    if available.get("dollar_adv", False):
        return {"execution_confidence": "Tier 1", "data_quality_tier": "Tier 1"}
    return {"execution_confidence": "Tier 0", "data_quality_tier": "Tier 0"}


def _feature_contract_compat(
    *,
    df_15m: pd.DataFrame,
    df_1h: pd.DataFrame,
    df_4h: pd.DataFrame,
    df_1d: pd.DataFrame,
    signal_timestamp: str,
) -> dict[str, Any]:
    frames = {"15m": df_15m, "1h": df_1h, "4h": df_4h, "1d": df_1d}
    feature_timestamps: dict[str, str | None] = {}
    feature_age_minutes: dict[str, float | None] = {}
    signal_ts = pd.Timestamp(signal_timestamp)
    if signal_ts.tzinfo is not None:
        signal_ts = signal_ts.tz_localize(None)
    for name, frame in frames.items():
        if frame.empty:
            feature_timestamps[name] = None
            feature_age_minutes[name] = None
            continue
        latest = pd.Timestamp(frame.index[-1])
        if latest.tzinfo is not None:
            latest = latest.tz_localize(None)
        feature_timestamps[name] = latest.isoformat()
        feature_age_minutes[name] = round(max(0.0, (signal_ts - latest).total_seconds() / 60.0), 2)
    spread_bps = None
    spread_source = "missing"
    for column in ("spread_bps", "spread_pct"):
        if column in df_15m.columns and pd.notna(df_15m[column].iloc[-1]):
            value = float(df_15m[column].iloc[-1])
            spread_bps = value if column == "spread_bps" else value * 100.0
            spread_source = column
            break
    if spread_bps is None and all(column in df_15m.columns for column in ("bid", "ask")):
        bid = float(df_15m["bid"].iloc[-1])
        ask = float(df_15m["ask"].iloc[-1])
        mid = (bid + ask) / 2.0
        if bid > 0 and ask >= bid and mid > 0:
            spread_bps = (ask - bid) / mid * 10_000.0
            spread_source = "bid_ask"
    dollar_adv = None
    adv_source = "missing"
    if all(column in df_1d.columns for column in ("Close", "Volume")):
        dollar_volume = pd.to_numeric(df_1d["Close"], errors="coerce") * pd.to_numeric(
            df_1d["Volume"], errors="coerce"
        )
        dollar_volume = dollar_volume.dropna().tail(20)
        if len(dollar_volume) >= 5:
            dollar_adv = float(dollar_volume.mean())
            adv_source = "close_volume_20d"
    short_interest_timestamp = df_1d.attrs.get("short_interest_timestamp")
    if short_interest_timestamp is not None and hasattr(short_interest_timestamp, "isoformat"):
        short_interest_timestamp = short_interest_timestamp.isoformat()
    available = {
        "spread_bps": spread_bps is not None,
        "dollar_adv": dollar_adv is not None,
        "short_interest_timestamp": short_interest_timestamp is not None,
    }
    return {
        "spread_bps": round(spread_bps, 4) if spread_bps is not None else None,
        "spread_source": spread_source,
        "dollar_adv": round(dollar_adv, 2) if dollar_adv is not None else None,
        "adv_source": adv_source,
        "short_interest_timestamp": short_interest_timestamp,
        "feature_timestamps": feature_timestamps,
        "feature_age_minutes": feature_age_minutes,
        "available": available,
        "missing_fields": [name for name, present in available.items() if not present],
    }


def _feature_contract(
    *,
    df_15m: pd.DataFrame,
    df_1h: pd.DataFrame,
    df_4h: pd.DataFrame,
    df_1d: pd.DataFrame,
    signal_timestamp: str,
) -> dict[str, Any]:
    frames = {"15m": df_15m, "1h": df_1h, "4h": df_4h, "1d": df_1d}
    feature_timestamps: dict[str, str | None] = {}
    feature_age_minutes: dict[str, float | None] = {}
    signal_ts = pd.Timestamp(signal_timestamp)
    if signal_ts.tzinfo is not None:
        signal_ts = signal_ts.tz_localize(None)
    for name, frame in frames.items():
        if frame.empty:
            feature_timestamps[name] = None
            feature_age_minutes[name] = None
            continue
        latest = pd.Timestamp(frame.index[-1])
        if latest.tzinfo is not None:
            latest = latest.tz_localize(None)
        feature_timestamps[name] = latest.isoformat()
        feature_age_minutes[name] = round(max(0.0, (signal_ts - latest).total_seconds() / 60.0), 2)

    spread_bps = None
    spread_source = "missing"
    for column in ("spread_bps", "spread_pct"):
        if column in df_15m.columns and pd.notna(df_15m[column].iloc[-1]):
            value = float(df_15m[column].iloc[-1])
            spread_bps = value if column == "spread_bps" else value * 100.0
            spread_source = column
            break
    if spread_bps is None and all(column in df_15m.columns for column in ("bid", "ask")):
        bid = float(df_15m["bid"].iloc[-1])
        ask = float(df_15m["ask"].iloc[-1])
        mid = (bid + ask) / 2.0
        if bid > 0 and ask >= bid and mid > 0:
            spread_bps = (ask - bid) / mid * 10_000.0
            spread_source = "bid_ask"

    dollar_adv = None
    adv_source = "missing"
    if all(column in df_1d.columns for column in ("Close", "Volume")):
        dollar_volume = pd.to_numeric(df_1d["Close"], errors="coerce") * pd.to_numeric(
            df_1d["Volume"], errors="coerce"
        )
        dollar_volume = dollar_volume.dropna().tail(20)
        if len(dollar_volume) >= 5:
            dollar_adv = float(dollar_volume.mean())
            adv_source = "close_volume_20d"

    short_interest_timestamp = df_1d.attrs.get("short_interest_timestamp")
    if short_interest_timestamp is not None and hasattr(short_interest_timestamp, "isoformat"):
        short_interest_timestamp = short_interest_timestamp.isoformat()
    available = {
        "spread_bps": spread_bps is not None,
        "dollar_adv": dollar_adv is not None,
        "short_interest_timestamp": short_interest_timestamp is not None,
    }
    return {
        "spread_bps": round(spread_bps, 4) if spread_bps is not None else None,
        "spread_source": spread_source,
        "dollar_adv": round(dollar_adv, 2) if dollar_adv is not None else None,
        "adv_source": adv_source,
        "short_interest_timestamp": short_interest_timestamp,
        "feature_timestamps": feature_timestamps,
        "feature_age_minutes": feature_age_minutes,
        "available": available,
        "missing_fields": [name for name, present in available.items() if not present],
    }


def evaluate_symbol(
    symbol: str,
    kelly_fraction: float = 0.5,
    prefetched_data: dict[str, pd.DataFrame] | None = None,
) -> dict[str, Any] | None:
    """Comprehensive single-symbol evaluation with multi-timeframe analysis."""
    # Daily portfolio drawdown gate (task 25): refuse to emit new signals once
    # today's realised loss exceeds the configured threshold (default 3%).
    if daily_dd_breached(threshold=0.03):
        return None
    try:
        if prefetched_data is not None:
            df_15m = prefetched_data.get("15m", pd.DataFrame())
            df_1h = prefetched_data.get("1h", pd.DataFrame())
            df_4h = prefetched_data.get("4h", pd.DataFrame())
            df_1d = prefetched_data.get("1d", pd.DataFrame())
        else:
            data = fetch_multi_timeframe(symbol, with_indicators=True, max_workers=4)
            df_15m = data.get("15m", pd.DataFrame())
            df_1h = data.get("1h", pd.DataFrame())
            df_4h = data.get("4h", pd.DataFrame())
            df_1d = data.get("1d", pd.DataFrame())

        # Hard minimum: need at least some data to evaluate
        if len(df_15m) < 15 or len(df_1h) < 10 or len(df_4h) < 15 or len(df_1d) < 50:
            return _unavailable_result(symbol, "insufficient_history")

        # Track whether we have enough history for high-quality signals
        _has_full_history = len(df_1d) >= 200

        # Stage 1: TREND FILTER (Daily)
        try:
            c_daily = safe_float(df_1d["Close"].iloc[-1])
            # Use ema200 only when 200 bars available, else fall back to ema50
            if _has_full_history and "ema200" in df_1d.columns:
                e200_daily = safe_float(df_1d["ema200"].iloc[-1])
            else:
                e200_daily = (
                    safe_float(df_1d["ema50"].iloc[-1]) if "ema50" in df_1d.columns else c_daily
                )
            e50_daily = safe_float(df_1d["ema50"].iloc[-1]) if "ema50" in df_1d.columns else c_daily
            regime = c_daily > e200_daily
            direction = c_daily > e50_daily
        except Exception:
            regime = False
            direction = False

        # Stage 2: MOMENTUM & VOLUME SCORE
        score = 0
        try:
            if len(df_1d) >= 2:
                row = df_1d.iloc[-1]
                prev = df_1d.iloc[-2]
                if 30 <= safe_float(row["rsi"]) <= 70:
                    score += 1
                if safe_float(row["Volume"]) > safe_float(row["vol_med20"]) * 1.2:
                    score += 1
                if safe_float(row["macd_hist"]) > 0 and safe_float(row["macd_hist"]) > safe_float(
                    prev["macd_hist"]
                ):
                    score += 1
        except Exception:
            score = 0

        last_price = df_15m["Close"].iloc[-1]
        atr_val = df_15m["atr"].iloc[-1]
        momentum_analysis = analyze_price_momentum(df_1d)

        volume_spike = bool(check_volume_spike(df_1d))
        price_momentum = bool(momentum_analysis.get("positive", False))
        trend_strength = bool(check_trend_strength(df_1d))
        filter_score = int(volume_spike) + int(price_momentum) + int(trend_strength)

        try:
            current_vol = safe_float(df_1d["Volume"].iloc[-1])
            avg_vol = safe_float(df_1d["vol_avg10"].iloc[-1])
            volume_multiple = (current_vol / avg_vol) if avg_vol > 0 else 0.0
        except Exception:
            volume_multiple = 0.0

        metrics = momentum_analysis.get("metrics", [])
        momentum_3d_pct = next(
            (float(m["return_pct"]) for m in metrics if m.get("horizon") == 3), 0.0
        )
        dominant_zscore = float(momentum_analysis.get("dominant_zscore", 0.0))
        dominant_return_pct = float(momentum_analysis.get("dominant_return_pct", 0.0))
        dominant_horizon = (
            int(momentum_analysis.get("best", {}).get("horizon", 0))
            if momentum_analysis.get("best")
            else 0
        )
        z_threshold_effective = float(
            momentum_analysis.get("z_threshold_effective", get_setting("momentum_z_threshold", 1.5))
        )
        z_threshold_base = float(
            momentum_analysis.get("z_threshold_base", get_setting("momentum_z_threshold", 1.5))
        )
        z_segment_raw = momentum_analysis.get("z_threshold_segment")
        z_dynamic_raw = momentum_analysis.get("z_threshold_dynamic")
        z_threshold_segment = float(z_segment_raw) if z_segment_raw is not None else None
        z_threshold_dynamic = float(z_dynamic_raw) if z_dynamic_raw is not None else None
        baseline_window_used = int(
            momentum_analysis.get("baseline_window", get_setting("momentum_baseline_window", 20))
        )
        liquidity_segment = momentum_analysis.get("liquidity_segment")
        dynamic_sample_count = int(momentum_analysis.get("dynamic_threshold_samples", 0))
        momentum_bias = {1: "bullish", -1: "bearish"}.get(
            int(momentum_analysis.get("dominant_direction", 0)), "neutral"
        )

        try:
            ema50 = safe_float(df_1d["ema50"].iloc[-1])
            ema200 = safe_float(df_1d["ema200"].iloc[-1])
            ema_gap_pct = (((ema50 - ema200) / ema200) * 100) if ema200 else 0.0
        except Exception:
            ema_gap_pct = 0.0

        timeframe_aligned, alignment_ratio, _ = check_timeframe_alignment(df_1h, df_4h, df_1d)
        timeframe_aligned = bool(timeframe_aligned)
        alignment_ratio = float(alignment_ratio or 0.0)
        momentum_confluence, momentum_ratio = check_momentum_confluence(df_15m, df_4h)
        momentum_confluence = bool(momentum_confluence)
        momentum_ratio = float(momentum_ratio or 0.0)

        min_score_threshold = 3
        reject_reasons: list[str] = []
        if not regime:
            reject_reasons.append("regime_gate")
        if not direction:
            reject_reasons.append("direction_gate")
        if score < min_score_threshold:
            reject_reasons.append("momentum_score_gate")
        core_signal = bool(regime and direction and (score >= min_score_threshold))
        entry_ok = bool(score == 3) if core_signal else False

        # Faz 5: is_premium_symbol removed — subjective hardcoded list had no
        # measurable lift in scoring (score_engine never read the key; it was
        # a no-op in the composite calculation). high_quality_signal retained
        # as a reporting flag for UI display only.
        is_premium_symbol = False
        # Downgrade to non-high-quality if we didn't have 200 days of history
        high_quality_signal = entry_ok and _has_full_history

        try:
            price_ok = safe_float(df_1d["Close"].iloc[-1]) >= get_setting("min_price", 2.0)
        except Exception:
            price_ok = True
        try:
            avg_vol_ok = safe_float(df_1d["vol_avg10"].iloc[-1]) >= get_setting(
                "min_avg_vol", 300_000
            )
        except Exception:
            avg_vol_ok = True
        liquidity_ok = bool(price_ok and avg_vol_ok)
        if not liquidity_ok:
            reject_reasons.append("liquidity_gate")
        entry_ok = bool(entry_ok and liquidity_ok)

        try:
            rsi_val = safe_float(df_1d["rsi"].iloc[-1])
            macd_val = safe_float(df_1d["macd_hist"].iloc[-1])
            rsi_score = max(0, min(100, (rsi_val - 30) / 70 * 100))
            macd_score = 100 if macd_val > 0 else 0
            trend_score = 100 if direction else 0
            momentum_score = (rsi_score * 0.4) + (macd_score * 0.3) + (trend_score * 0.3)
        except Exception:
            momentum_score = 50

        # Use Yang-Zhang vol when ≥21 daily bars available; fall back to ATR otherwise
        if len(df_1d) >= 21 and all(c in df_1d.columns for c in ("Open", "High", "Low", "Close")):
            risk_data = calculate_risk_management_yz(
                price=safe_float(last_price),
                df=df_1d,
                momentum_score=int(momentum_score),
            )
        else:
            risk_data = calculate_risk_management(
                price=safe_float(last_price),
                atr_val=safe_float(atr_val) if pd.notna(atr_val) else 0.01,
                momentum_score=int(momentum_score),
            )

        # EODHD news-sentiment factor (env-gated, cache-only — see
        # scanner/sentiment.py). Honest-neutral: the old `regime_detection` /
        # `altdata` imports this replaced lived only in archive/scripts_legacy
        # and were silently failing on every scan (ModuleNotFoundError caught
        # by a bare except) while the code pretended to use them. This reads a
        # scheduler-populated cache only — no per-symbol network call, and
        # `sentiment_score` stays None when the feature is off so scoring is
        # byte-for-byte unchanged.
        sentiment = 0.0
        onchain_metric = 0.0
        sentiment_score: float | None = None
        try:
            from scanner.sentiment import compute_sentiment_factor, sentiment_enabled

            if sentiment_enabled():
                sentiment_score = compute_sentiment_factor(symbol)
                sentiment = sentiment_score
        except Exception:
            logger.debug("Sentiment factor unavailable", exc_info=True)

        if entry_ok and not CURRENT_MARKET_STATUS["safe"]:
            entry_ok = False
            reject_reasons.append("market_safety_gate")

        # Sprint 15: Earnings blackout filter
        earnings_blackout = False
        earnings_prox = 0.0
        try:
            from scanner.earnings_blackout import (  # noqa: PLC0415
                earnings_proximity,
                is_earnings_blackout,
            )

            earnings_blackout = is_earnings_blackout(symbol, days_before=2, days_after=1)
            earnings_prox = earnings_proximity(symbol)
            if earnings_blackout and entry_ok:
                entry_ok = False
                reject_reasons.append("earnings_blackout")
                logger.info("[%s] earnings blackout — signal suppressed", symbol)
        except Exception:
            pass

        # Sprint 15: Sector RS + vol regime alpha features
        sector_rs = 0.0
        vol_regime_val = 1
        squeeze_factor = 0.0
        try:
            from scanner.features import get_alpha_features  # noqa: PLC0415

            alpha = get_alpha_features(symbol, df_1d=df_1d)
            sector_rs = alpha.get("sector_rs", 0.0)
            vol_regime_val = alpha.get("vol_regime", 1)
            squeeze_factor = alpha.get("squeeze_factor", 0.0)
        except Exception:
            pass

        try:
            from scanner.features import (
                compute_extension_factor,
                compute_gap_factor,
                compute_rvol_factor,
            )

            alpha_gap = compute_gap_factor(df_1d)
            alpha_rvol = compute_rvol_factor(df_1d)
            alpha_ext = compute_extension_factor(df_1d)
        except Exception:
            alpha_gap = alpha_rvol = alpha_ext = 0.0

        # SEC EDGAR catalyst factor (env-gated, reads from cache — hot-path safe)
        catalyst_factor = 0.0
        try:
            from scanner.catalyst import compute_catalyst_factor  # noqa: PLC0415

            catalyst_factor = compute_catalyst_factor(symbol)
        except Exception:
            pass

        # Faz 1: Lottery/MAX fade factor (pure pandas, no network call)
        lottery_factor = 0.0
        try:
            from scanner.features import compute_lottery_factor  # noqa: PLC0415

            lottery_factor = compute_lottery_factor(df_1d)
        except Exception:
            pass

        # Faz 4: Overnight gap reversal factor (pure pandas, no network call)
        overnight_gap_factor = 0.0
        try:
            from scanner.features import compute_overnight_gap_factor  # noqa: PLC0415

            overnight_gap_factor = compute_overnight_gap_factor(df_1d)
        except Exception:
            pass

        # Regime × score-band gate (2026-06-12 barrier audit findings)
        _score_input = {
            "regime": regime,
            "direction": bool(direction),
            "score": int(score),
            "filter_score": int(filter_score),
            "alignment_ratio": float(alignment_ratio),
            "momentum_ratio": float(momentum_ratio),
            "volume_spike": bool(volume_spike),
            "price_momentum": bool(price_momentum),
            "trend_strength": bool(trend_strength),
            "is_premium_symbol": bool(is_premium_symbol),
            # Faz 3: vol_regime drives momentum weight in score_engine
            "vol_regime": int(vol_regime_val),
            "squeeze_factor": float(squeeze_factor),
            "gap_factor": float(alpha_gap),
            "rvol_factor": float(alpha_rvol),
            "extension_factor": float(alpha_ext),
            "catalyst_factor": float(catalyst_factor),
            # Faz 1/2: lottery penalty (gated by FINPILOT_ENABLE_LOTTERY_FADE)
            "lottery_factor": float(lottery_factor),
            # Faz 4: overnight gap reversal (gated by FINPILOT_ENABLE_OVERNIGHT_GAP)
            "overnight_gap_factor": float(overnight_gap_factor),
            # Faz 5: is_premium_symbol removed (was dead code — score_engine
            # never read it). Kept as False in return dict for UI compat.
        }
        _score_raw = compute_recommendation_score(_score_input, sentiment_score=sentiment_score)
        _score_components = score_component_breakdown(_score_input, sentiment_score=sentiment_score)
        _composite_score = compute_recommendation_strength(
            _score_input, sentiment_score=sentiment_score
        )
        _gate_mult = regime_gate_mult(bool(regime), _composite_score)

        # ── Task 2: Risk-adjusted metrics from daily OHLC ─────────────────
        _risk_metrics = calculate_risk_adjusted_metrics(df_1d) if len(df_1d) >= 10 else {}
        _ann_vol_pct = float(_risk_metrics.get("ann_vol_pct", 20.0) or 20.0)

        # ── Task 3: Dynamic position sizing ──────────────────────────────
        _dyn_pos = calculate_dynamic_position(
            price=safe_float(last_price),
            stop_loss=risk_data["stop_loss"],
            composite_score=int(_composite_score),
            is_bull_regime=bool(regime),
            risk_reward=float(risk_data["risk_reward_ratio"]),
            ann_vol_pct=_ann_vol_pct,
            kelly_fraction=kelly_fraction,
        )
        _atr_pct_daily = 0.0
        try:
            from scanner.features import compute_atr_pct, compute_conviction

            _atr_pct_daily = compute_atr_pct(df_1d)
            _conv_tier, _conv_prob = (
                compute_conviction(
                    float(squeeze_factor), float(alpha_gap), float(alpha_rvol), _atr_pct_daily
                )
                if entry_ok
                else ("", 0.0)
            )
        except Exception:
            _conv_tier, _conv_prob = "", 0.0
        _signal_timestamp = df_15m.index[-1].strftime("%Y-%m-%d %H:%M")
        _data_quality = _feature_contract(
            df_15m=df_15m,
            df_1h=df_1h,
            df_4h=df_4h,
            df_1d=df_1d,
            signal_timestamp=_signal_timestamp,
        )
        _execution_contract_data = execution_contract(_data_quality)
        _reject_reasons = list(_execution_contract_data.get("execution_reject_reason", []))
        if not entry_ok:
            _reject_reasons.append("signal_not_eligible")
        _execution_contract_data["reject_reason"] = list(dict.fromkeys(_reject_reasons))
        _execution_contract_data["selection_eligible"] = bool(
            entry_ok and _execution_contract_data["execution_feasible"]
        )
        _legacy_quality_score = compute_legacy_quality_score(
            regime=regime,
            direction=bool(direction),
            raw_score=float(score),
            atr_pct=_atr_pct_daily,
            rvol=(1.0 + float(alpha_rvol) * 2.0 if alpha_rvol else None),
            squeeze_factor=float(squeeze_factor),
            lottery_factor=float(lottery_factor),
            overnight_gap_factor=float(overnight_gap_factor),
        )
        _ranking_score = (
            _composite_score if legacy_composite_ranking_enabled() else _legacy_quality_score
        )
        _v2_score = compute_v2_score(
            gap_factor=float(alpha_gap),
            rvol_factor=float(alpha_rvol),
            atr_pct=float(_atr_pct_daily),
            squeeze_factor=float(squeeze_factor),
        )
        _position_cap = position_cap(
            _data_quality["dollar_adv"],
            float(risk_data["position_size"]) * safe_float(last_price),
        )
        _position_cap["position_size"] = (
            round(_position_cap["position_notional"] / safe_float(last_price), 4)
            if safe_float(last_price) > 0
            else 0
        )
        return {
            "symbol": symbol,
            "price": round(safe_float(last_price), 4),
            "score": int(score),
            "regime": regime,
            "direction": bool(direction),
            "atr": round(safe_float(atr_val), 6) if pd.notna(atr_val) else None,
            "entry_ok": bool(entry_ok),
            "market_status": CURRENT_MARKET_STATUS["reason"],
            "timestamp": _signal_timestamp,
            "spread_bps": _data_quality["spread_bps"],
            "spread_source": _data_quality["spread_source"],
            "dollar_adv": _data_quality["dollar_adv"],
            "adv_source": _data_quality["adv_source"],
            "short_interest_timestamp": _data_quality["short_interest_timestamp"],
            "feature_timestamps": _data_quality["feature_timestamps"],
            "feature_age_minutes": _data_quality["feature_age_minutes"],
            "data_quality": _data_quality,
            "entry_drift_pct": None,
            **_execution_contract_data,
            "liquidity_ok": bool(liquidity_ok),
            "volume_spike": bool(volume_spike),
            "price_momentum": bool(price_momentum),
            "trend_strength": bool(trend_strength),
            "filter_score": int(filter_score),
            "volume_multiple": round(volume_multiple, 2),
            "momentum_3d_pct": round(momentum_3d_pct, 2),
            "momentum_best_horizon": int(dominant_horizon),
            "momentum_best_zscore": round(dominant_zscore, 2),
            "momentum_best_return_pct": round(dominant_return_pct, 2),
            "momentum_bias": momentum_bias,
            "momentum_z_effective": round(z_threshold_effective, 2),
            "momentum_z_base": round(z_threshold_base, 2),
            "momentum_z_segment": (round(z_threshold_segment, 2) if z_threshold_segment else None),
            "momentum_z_dynamic": (round(z_threshold_dynamic, 2) if z_threshold_dynamic else None),
            "momentum_liquidity_segment": liquidity_segment,
            "momentum_dynamic_samples": dynamic_sample_count,
            "momentum_baseline_window": baseline_window_used,
            "ema_gap_pct": round(ema_gap_pct, 2),
            "timeframe_aligned": bool(timeframe_aligned),
            "alignment_ratio": round(alignment_ratio, 2),
            "momentum_confluence": bool(momentum_confluence),
            "momentum_ratio": round(momentum_ratio, 2),
            "is_premium_symbol": bool(is_premium_symbol),
            "high_quality_signal": bool(high_quality_signal),
            "stop_loss": risk_data["stop_loss"],
            "take_profit": risk_data["take_profit"],
            "position_size": risk_data["position_size"],
            "risk_reward": risk_data["risk_reward_ratio"],
            "stop_loss_percent": risk_data["stop_loss_percent"],
            "kelly_fraction": kelly_fraction,
            "sentiment": sentiment,
            # Edge Report bucketing key (build_edge_report(group_by="sentiment_band")):
            # None when the sentiment feature is off/uncomputed, so shadow-mode
            # reports can distinguish "no data" from "measured neutral".
            "sentiment_band": (
                None
                if sentiment_score is None
                else (
                    "positive"
                    if sentiment_score > 0.6
                    else "negative"
                    if sentiment_score < 0.4
                    else "neutral"
                )
            ),
            "onchain_metric": onchain_metric,
            "earnings_blackout": bool(earnings_blackout),
            "earnings_proximity": round(earnings_prox, 4),
            "sector_rs": round(sector_rs, 4),
            "vol_regime": vol_regime_val,
            "lottery_factor": round(lottery_factor, 4),
            "overnight_gap_factor": round(overnight_gap_factor, 4),
            "composite_score": _composite_score,
            "conviction_tier": _conv_tier,
            "conviction_prob": round(float(_conv_prob), 3),
            "legacy_quality_score": _legacy_quality_score,
            "ranking_score": _ranking_score,
            "ranking_method": "legacy_quality",
            "v2_score": _v2_score,
            "strategy_scores": {"legacy_quality": _legacy_quality_score, "v2": _v2_score},
            **_position_cap,
            **decision_telemetry(
                reject_reasons=reject_reasons,
                score=_score_raw,
                components=_score_components,
                data_quality=_data_quality,
            ),
            "regime_gate_mult": _gate_mult,
            "position_size_gated": int(risk_data["position_size"] * _gate_mult),
            # ── Task 2: Risk-adjusted performance metrics ─────────────────
            "sharpe_ratio": _risk_metrics.get("sharpe_ratio", 0.0),
            "sortino_ratio": _risk_metrics.get("sortino_ratio", 0.0),
            "calmar_ratio": _risk_metrics.get("calmar_ratio", 0.0),
            "max_drawdown_pct": _risk_metrics.get("max_drawdown_pct", 0.0),
            "ann_vol_pct": _risk_metrics.get("ann_vol_pct", 0.0),
            "ann_return_pct": _risk_metrics.get("ann_return_pct", 0.0),
            "ev_per_trade": _risk_metrics.get("ev_per_trade", 0.0),
            "risk_data_quality": _risk_metrics.get("data_quality", "low"),
            # ── Task 3: Dynamic position sizing ──────────────────────────
            "dyn_shares": _dyn_pos.get("shares", 0),
            "dyn_notional": _dyn_pos.get("notional", 0.0),
            "dyn_risk_pct": _dyn_pos.get("risk_pct", 0.0),
            "dyn_position_pct": _dyn_pos.get("position_pct", 0.0),
            "dyn_kelly_pct": _dyn_pos.get("kelly_pct", 0.0),
            "dyn_regime_scale": _dyn_pos.get("regime_scale", 1.0),
            "dyn_portfolio_ok": _dyn_pos.get("portfolio_ok", True),
            "dyn_sizing_method": _dyn_pos.get("sizing_method", "fixed-fractional"),
            # ── Faz 6: Cost-adjusted expected return + edge decay label ────
            # net_expected_return: ev_per_trade minus estimated round-trip cost
            # (slippage + commission). Uses core.slippage_tracker when available;
            # falls back to 0.20% flat assumption (typical retail, low-cap).
            # Edge decay labels warn when edge may be thin or regime-dependent:
            #   "ok"         — net EV > 0.3% and vol is normal/low
            #   "thin_edge"  — net EV between 0% and 0.3% (barely profitable)
            #   "edge_decay" — high-vol regime (vol_regime==2) AND net EV < 0.5%
            #   "negative"   — net EV ≤ 0 (expected loss after costs)
            **_compute_cost_labels(
                ev_per_trade=float(_risk_metrics.get("ev_per_trade") or 0.0),
                ann_vol_pct=_ann_vol_pct,
                vol_regime=int(vol_regime_val),
                price=safe_float(last_price),
            ),
        }
    except Exception as e:
        logger.error("[%s] evaluation error: %s", symbol, e)
        return _unavailable_result(symbol, "evaluation_error", detail=str(e))


def _unavailable_result(symbol: str, reason: str, detail: str | None = None) -> dict[str, Any]:
    """Keep unavailable symbols in the scan contract without grading them."""
    result: dict[str, Any] = {
        "symbol": symbol,
        "scan_status": "unavailable",
        "data_quality_tier": "Tier 3",
        "data_quality_status": "missing",
        "reject_reason": [reason],
        "selection_eligible": False,
        "entry_ok": False,
        "execution_feasible": False,
        "selected_by_legacy_quality": False,
        "selected_by_v2": False,
        "selected_by_both": False,
        "legacy_only": False,
        "v2_only": False,
        "ranking_method": "legacy_quality",
        "score": 0,
        "composite_score": 0,
    }
    if detail:
        result["error_detail"] = detail[:200]
    return result


def evaluate_symbols_parallel(
    symbols: list[str],
    kelly_fraction: float = 0.5,
    progress_callback: Callable[[int, int], None] | None = None,
    use_prefetch: bool = True,
) -> list[dict[str, Any]]:
    """Evaluate multiple symbols in parallel with optimized data fetching."""
    # Filter known-delisted / acquired symbols to eliminate yfinance "No data" noise
    before = len(symbols)
    symbols = [s for s in symbols if s.upper() not in DELISTED_SYMBOLS_SET]
    removed = before - len(symbols)
    if removed:
        logger.info("Delisted filter: skipped %d symbol(s) from scan", removed)

    results: list[dict[str, Any]] = []
    total = len(symbols)

    if use_prefetch and total > 1:
        logger.info("Prefetching data for %d symbols...", total)

        def prefetch_progress(current: int, subtotal: int) -> None:
            if progress_callback:
                pct = int((current / subtotal) * 50)
                progress_callback(pct, 100)

        try:
            all_data = prefetch_symbols_multi_timeframe(
                symbols,
                with_indicators=True,
                max_workers=10,
                progress_callback=prefetch_progress,
            )
        except TimeoutError:
            logger.warning("Prefetch phase timed out — continuing with partial data")
            all_data = {}

        total_done = 0

        # Parallel evaluation: evaluate_symbol is CPU-light after prefetch (pure pandas),
        # so ThreadPoolExecutor gives ~4-8× speedup for 50+ symbol batches.
        _eval_workers = min(32, max(4, total))

        def _eval_one(symbol: str) -> dict[str, Any] | None:
            symbol_data = all_data.get(symbol, {})
            return evaluate_symbol(symbol, kelly_fraction, prefetched_data=symbol_data)

        with ThreadPoolExecutor(max_workers=_eval_workers) as pool:
            future_map = {pool.submit(_eval_one, sym): sym for sym in symbols}
            for fut in as_completed(future_map):
                sym = future_map[fut]
                try:
                    result = fut.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.warning("Evaluate error for %s: %s", sym, e)
                    results.append(_unavailable_result(sym, "evaluation_error", detail=str(e)))
                total_done += 1
                if progress_callback:
                    try:
                        pct = 50 + int((total_done / total) * 50)
                        progress_callback(pct, 100)
                    except Exception:
                        logger.debug("Progress callback error — ignored")

    else:
        # Single symbol or prefetch disabled — evaluate directly without batch prefetch
        for symbol in symbols:
            try:
                result = evaluate_symbol(symbol, kelly_fraction)
                if result:
                    results.append(result)
            except Exception as e:
                logger.warning("Evaluate error for %s: %s", symbol, e)
                results.append(_unavailable_result(symbol, "evaluation_error", detail=str(e)))

    logger.info("evaluate_symbols_parallel complete: %d/%d results", len(results), total)
    return results
