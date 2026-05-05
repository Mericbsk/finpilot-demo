"""Scanner Evaluation Module — Sprint 2 B3 Refactoring

evaluate_symbol() ve evaluate_symbols_parallel() fonksiyonları
artık scanner package'ı içinde yaşıyor.  Eski scanner.py dosyası
geriye dönük uyumluluk için bu modülü import eder.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pandas as pd

from .config import DELISTED_SYMBOLS_SET, get_setting
from .data_fetcher import (
    fetch_multi_timeframe,
    prefetch_symbols_multi_timeframe,
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


def calculate_risk_management(price: float, atr_val: float, momentum_score: int) -> dict[str, Any]:
    """ATR-based dynamic stop-loss & take-profit."""
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


def evaluate_symbol(
    symbol: str,
    kelly_fraction: float = 0.5,
    prefetched_data: dict[str, pd.DataFrame] | None = None,
) -> dict[str, Any] | None:
    """Comprehensive single-symbol evaluation with multi-timeframe analysis."""
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
            return None

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

        min_score_threshold = 2
        core_signal = bool(regime and direction and (score >= min_score_threshold))
        mtf_ok = alignment_ratio >= 0.66
        entry_ok = bool(score == 3 or score == 2 and mtf_ok) if core_signal else False

        is_premium_symbol = symbol in ["SPY", "QQQ", "GOOGL", "NVDA", "AAPL", "MSFT"]
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

        risk_data = calculate_risk_management(
            price=safe_float(last_price),
            atr_val=safe_float(atr_val) if pd.notna(atr_val) else 0.01,
            momentum_score=int(momentum_score),
        )

        sentiment = 0.0
        onchain_metric = 0.0
        try:
            from regime_detection import detect_market_regime

            prices_for_regime = df_1d.get("Close", None)
            regime = (
                detect_market_regime(prices_for_regime) if prices_for_regime is not None else regime
            )
        except Exception:
            logger.debug("Regime detection unavailable", exc_info=True)
        try:
            from altdata import get_onchain_metric, get_sentiment_score

            sentiment = get_sentiment_score(symbol)
            onchain_metric = get_onchain_metric(symbol)
        except Exception:
            logger.debug("Alt data unavailable", exc_info=True)

        if regime == 1 and sentiment < 0:
            entry_ok = False
        if entry_ok and not CURRENT_MARKET_STATUS["safe"]:
            entry_ok = False

        return {
            "symbol": symbol,
            "price": round(safe_float(last_price), 4),
            "score": int(score),
            "regime": regime,
            "direction": bool(direction),
            "atr": round(safe_float(atr_val), 6) if pd.notna(atr_val) else None,
            "entry_ok": bool(entry_ok),
            "market_status": CURRENT_MARKET_STATUS["reason"],
            "timestamp": df_15m.index[-1].strftime("%Y-%m-%d %H:%M"),
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
            "onchain_metric": onchain_metric,
        }
    except Exception as e:
        logger.error("[%s] evaluation error: %s", symbol, e)
        return None


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

        completed = 0
        for symbol in symbols:
            symbol_data = all_data.get(symbol, {})
            try:
                result = evaluate_symbol(symbol, kelly_fraction, prefetched_data=symbol_data)
                if result:
                    results.append(result)
            except Exception as e:
                logger.warning("Evaluate error for %s: %s", symbol, e)
            completed += 1
            if progress_callback:
                try:
                    pct = 50 + int((completed / total) * 50)
                    progress_callback(pct, 100)
                except Exception:
                    logger.debug("Progress callback failed", exc_info=True)
    else:
        completed = 0
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [
                executor.submit(evaluate_symbol, symbol, kelly_fraction, None) for symbol in symbols
            ]
            for future in futures:
                result = future.result()
                if result:
                    results.append(result)
                completed += 1
                if progress_callback:
                    try:
                        progress_callback(completed, total)
                    except Exception:
                        logger.debug("Progress callback failed", exc_info=True)

    return results
