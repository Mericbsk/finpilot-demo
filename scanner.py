"""
Stock Scanner - Refactored Modular Version

A simplified stock scanning system using modular components.
All technical indicators, signals, and data fetching are handled
by the scanner package modules.

Usage:
    python scanner.py [--aggressive]
"""

import argparse
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import pandas as pd

# Configure module logger
logger = logging.getLogger(__name__)

# Import from modular scanner package
from scanner import (  # Parallel fetching (Faz 2 Performance)
    AGGRESSIVE_OVERRIDES,
    DEFAULT_SETTINGS,
    SETTINGS,
    add_indicators,
    analyze_price_momentum,
    atr,
    build_explanation,
    build_reason,
    check_momentum_confluence,
    check_price_momentum,
    check_timeframe_alignment,
    check_trend_strength,
    check_volume_spike,
    compute_recommendation_score,
    compute_recommendation_strength,
    fetch,
    fetch_multi_timeframe,
    get_market_regime_status,
    load_symbols,
    prefetch_symbols_multi_timeframe,
)
from scanner.config import apply_aggressive_mode, get_setting, reset_to_default
from scanner.signals import safe_float

# --- USER SETTINGS ---
SETTINGS_FILE = "user_settings.json"
USER_DEFAULT_SETTINGS = {
    "risk_score": 5,
    "portfolio_size": 10000,
    "max_loss_pct": 10,
    "strategy": "Normal",
    "market": "BIST",
    "telegram_active": False,
    "telegram_id": "",
    "timeframe": "Günlük",
    "indicators": {"ema": True, "rsi": False, "atr": True},
}

STRATEGY_PARAMS = {
    "Normal": {"min_score": 1, "rsi_low": 30, "rsi_high": 70},
    "Agresif": {"min_score": 1, "rsi_low": 40, "rsi_high": 60},
    "Defansif": {"min_score": 2, "rsi_low": 25, "rsi_high": 75},
    "Momentum": {"min_score": 1, "rsi_low": 35, "rsi_high": 65},
}

# Global market status
CURRENT_MARKET_STATUS = {"safe": True, "reason": "Varsayılan"}


def load_user_settings() -> Dict[str, Any]:
    """Load user settings from JSON file."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return USER_DEFAULT_SETTINGS
    return USER_DEFAULT_SETTINGS


# 🔔 Telegram module availability check
try:
    import importlib.util as _ils

    TELEGRAM_ENABLED = (
        _ils.find_spec("telegram_alerts") is not None
        and _ils.find_spec("telegram_config") is not None
    )
    if not TELEGRAM_ENABLED:
        print("⚠️ Telegram modülü bulunamadı. Uyarılar devre dışı.")
except Exception:
    TELEGRAM_ENABLED = False
    print("⚠️ Telegram kontrolü sırasında hata. Uyarılar devre dışı.")


def calculate_risk_management(price: float, atr_val: float, momentum_score: int) -> Dict[str, Any]:
    """
    Calculate dynamic stop-loss and take-profit levels.

    Uses ATR-based positioning with momentum-adjusted multipliers.

    Args:
        price: Current price
        atr_val: Average True Range value
        momentum_score: Momentum score (0-100)

    Returns:
        Dictionary with risk management parameters
    """
    if momentum_score >= 70:
        # Sniper Mode (Strong Market)
        stop_mult = 1.5
        tp1_mult = 3.0
        tp2_mult = 5.0
        tp3_mult = 8.0
        strategy_tag = "Sniper 🎯"
    elif momentum_score < 50:
        # Defensive Mode (Weak Market)
        stop_mult = 2.5
        tp1_mult = 4.5
        tp2_mult = 6.5
        tp3_mult = 0  # No TP3
        strategy_tag = "Defansif 🛡️"
    else:
        # Normal Mode
        stop_mult = 2.0
        tp1_mult = 3.5
        tp2_mult = 5.5
        tp3_mult = 7.5
        strategy_tag = "Normal 📈"

    stop_loss = price - (atr_val * stop_mult)
    tp1 = price + (atr_val * tp1_mult)
    tp2 = price + (atr_val * tp2_mult)
    tp3 = price + (atr_val * tp3_mult) if tp3_mult > 0 else 0

    take_profit = tp2  # Main target
    position_size = 1000  # Fixed

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
    prefetched_data: Optional[Dict[str, pd.DataFrame]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Comprehensive symbol evaluation with multi-timeframe analysis.

    Fetches data across multiple timeframes and applies technical
    analysis, trend detection, and signal generation.

    Args:
        symbol: Stock ticker symbol
        kelly_fraction: Kelly criterion fraction for position sizing
        prefetched_data: Optional pre-fetched data dict {interval: DataFrame}
                        If provided, skips data fetching for better performance.

    Returns:
        Dictionary with evaluation results, or None on failure
    """
    try:
        # Use prefetched data if available (parallel mode), otherwise fetch
        if prefetched_data is not None:
            df_15m = prefetched_data.get("15m", pd.DataFrame())
            df_1h = prefetched_data.get("1h", pd.DataFrame())
            df_4h = prefetched_data.get("4h", pd.DataFrame())
            df_1d = prefetched_data.get("1d", pd.DataFrame())
        else:
            # Parallel fetch all timeframes at once (Faz 2 Performance)
            data = fetch_multi_timeframe(symbol, with_indicators=True, max_workers=4)
            df_15m = data.get("15m", pd.DataFrame())
            df_1h = data.get("1h", pd.DataFrame())
            df_4h = data.get("4h", pd.DataFrame())
            df_1d = data.get("1d", pd.DataFrame())

        # Validate data sufficiency
        if len(df_15m) < 30 or len(df_1h) < 20 or len(df_4h) < 30 or len(df_1d) < 200:
            return None

        # Stage 1: TREND FILTER (Daily)
        try:
            c_daily = safe_float(df_1d["Close"].iloc[-1])
            e200_daily = safe_float(df_1d["ema200"].iloc[-1])
            e50_daily = safe_float(df_1d["ema50"].iloc[-1])

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

                # RSI Signal (30-70 range)
                if 30 <= safe_float(row["rsi"]) <= 70:
                    score += 1

                # Volume Signal (+20% above average)
                if safe_float(row["Volume"]) > safe_float(row["vol_med20"]) * 1.2:
                    score += 1

                # MACD Signal (positive and rising)
                if safe_float(row["macd_hist"]) > 0 and safe_float(row["macd_hist"]) > safe_float(
                    prev["macd_hist"]
                ):
                    score += 1
        except Exception:
            score = 0

        last_price = df_15m["Close"].iloc[-1]
        atr_val = df_15m["atr"].iloc[-1]

        # Momentum analysis
        momentum_analysis = analyze_price_momentum(df_1d)

        # 3 Powerful Filters
        volume_spike = bool(check_volume_spike(df_1d))
        price_momentum = bool(momentum_analysis.get("positive", False))
        trend_strength = bool(check_trend_strength(df_1d))
        filter_score = int(volume_spike) + int(price_momentum) + int(trend_strength)

        # Proximity metrics
        try:
            current_vol = safe_float(df_1d["Volume"].iloc[-1])
            avg_vol = safe_float(df_1d["vol_avg10"].iloc[-1])
            volume_multiple = (current_vol / avg_vol) if avg_vol > 0 else 0.0
        except Exception:
            volume_multiple = 0.0

        # Momentum metrics
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

        # Dynamic thresholds
        z_segment_raw = momentum_analysis.get("z_threshold_segment")
        z_dynamic_raw = momentum_analysis.get("z_threshold_dynamic")
        z_threshold_segment = float(z_segment_raw) if z_segment_raw is not None else None
        z_threshold_dynamic = float(z_dynamic_raw) if z_dynamic_raw is not None else None

        baseline_window_used = int(
            momentum_analysis.get("baseline_window", get_setting("momentum_baseline_window", 20))
        )
        liquidity_segment = momentum_analysis.get("liquidity_segment")
        dynamic_sample_count = int(momentum_analysis.get("dynamic_threshold_samples", 0))

        momentum_bias = {
            1: "bullish",
            -1: "bearish",
        }.get(int(momentum_analysis.get("dominant_direction", 0)), "neutral")

        # EMA gap
        try:
            ema50 = safe_float(df_1d["ema50"].iloc[-1])
            ema200 = safe_float(df_1d["ema200"].iloc[-1])
            ema_gap_pct = (((ema50 - ema200) / ema200) * 100) if ema200 else 0.0
        except Exception:
            ema_gap_pct = 0.0

        # Timeframe alignment
        timeframe_aligned, alignment_ratio, _ = check_timeframe_alignment(df_1h, df_4h, df_1d)
        timeframe_aligned = bool(timeframe_aligned)
        alignment_ratio = float(alignment_ratio or 0.0)

        # Momentum confluence
        momentum_confluence, momentum_ratio = check_momentum_confluence(df_15m, df_4h)
        momentum_confluence = bool(momentum_confluence)
        momentum_ratio = float(momentum_ratio or 0.0)

        # 4-Stage Filter (Backtest-approved system)
        min_score_threshold = 2
        core_signal = bool(regime and direction and (score >= min_score_threshold))
        mtf_ok = alignment_ratio >= 0.66

        if core_signal:
            if score == 3:
                entry_ok = True
            elif score == 2 and mtf_ok:
                entry_ok = True
            else:
                entry_ok = False
        else:
            entry_ok = False

        # Premium symbols
        is_premium_symbol = symbol in ["SPY", "QQQ", "GOOGL", "NVDA", "AAPL", "MSFT"]
        high_quality_signal = entry_ok

        # Liquidity filter
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

        # Momentum Score (RSI + MACD + Trend)
        try:
            rsi_val = safe_float(df_1d["rsi"].iloc[-1])
            macd_val = safe_float(df_1d["macd_hist"].iloc[-1])

            rsi_score = max(0, min(100, (rsi_val - 30) / 70 * 100))
            macd_score = 100 if macd_val > 0 else 0
            trend_score = 100 if direction else 0

            momentum_score = (rsi_score * 0.4) + (macd_score * 0.3) + (trend_score * 0.3)
        except Exception:
            momentum_score = 50

        # Risk management
        risk_data = calculate_risk_management(
            price=safe_float(last_price),
            atr_val=safe_float(atr_val) if pd.notna(atr_val) else 0.01,
            momentum_score=int(momentum_score),
        )

        # Alternative data integration
        sentiment = 0.0
        onchain_metric = 0.0
        try:
            from regime_detection import detect_market_regime

            prices_for_regime = df_1d["Close"] if "Close" in df_1d else None
            regime = (
                detect_market_regime(prices_for_regime) if prices_for_regime is not None else regime
            )
        except Exception:
            pass
        try:
            from altdata import get_onchain_metric, get_sentiment_score

            sentiment = get_sentiment_score(symbol)
            onchain_metric = get_onchain_metric(symbol)
        except Exception:
            pass

        # Adaptive filter with alternative data
        if regime == 1 and sentiment < 0:
            entry_ok = False

        # Global Market Filter
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
            "momentum_z_segment": round(z_threshold_segment, 2) if z_threshold_segment else None,
            "momentum_z_dynamic": round(z_threshold_dynamic, 2) if z_threshold_dynamic else None,
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
        print(f"[ERROR] {symbol}: {e}")
        return None


def evaluate_symbols_parallel(
    symbols: List[str],
    kelly_fraction: float = 0.5,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    use_prefetch: bool = True,
) -> List[Dict[str, Any]]:
    """
    Evaluate multiple symbols in parallel with optimized data fetching.

    Uses a two-phase approach for maximum performance:
    1. Prefetch all data for all symbols in parallel
    2. Evaluate each symbol using prefetched data

    Args:
        symbols: List of stock ticker symbols
        kelly_fraction: Kelly criterion fraction
        progress_callback: Optional callback function(current, total) for progress updates
        use_prefetch: Use prefetch mode for better performance (default: True)

    Returns:
        List of evaluation results (non-None only)
    """
    results = []
    total = len(symbols)

    if use_prefetch and total > 1:
        # Phase 1: Prefetch all data in parallel (Faz 2 Performance)
        logger.info("Prefetching data for %d symbols...", total)

        # Progress callback for prefetch phase (0-50%)
        def prefetch_progress(current: int, subtotal: int) -> None:
            if progress_callback:
                # Map to 0-50% range
                pct = int((current / subtotal) * 50)
                progress_callback(pct, 100)

        all_data = prefetch_symbols_multi_timeframe(
            symbols, with_indicators=True, max_workers=10, progress_callback=prefetch_progress
        )

        # Phase 2: Evaluate with prefetched data
        completed = 0
        for symbol in symbols:
            symbol_data = all_data.get(symbol, {})
            result = evaluate_symbol(symbol, kelly_fraction, prefetched_data=symbol_data)
            if result:
                results.append(result)

            completed += 1
            if progress_callback:
                try:
                    # Map to 50-100% range
                    pct = 50 + int((completed / total) * 50)
                    progress_callback(pct, 100)
                except Exception:
                    pass
    else:
        # Fallback: Traditional parallel evaluation (for single symbol or disabled prefetch)
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
                        pass

    return results


def main():
    """Main entry point for the scanner."""
    global CURRENT_MARKET_STATUS

    parser = argparse.ArgumentParser(description="Modular Stock Scanner")
    parser.add_argument(
        "--aggressive", action="store_true", help="Use relaxed thresholds for more signals"
    )
    args = parser.parse_args()

    # Apply mode
    if args.aggressive:
        apply_aggressive_mode()
        print("⚡ Agresif mod aktif: eşikler gevşetildi.")
    else:
        reset_to_default()

    print("🔍 TARAMA BAŞLIYOR...")

    # Telegram setup
    telegram = None
    if TELEGRAM_ENABLED:
        try:
            from telegram_alerts import TelegramNotifier as _TelegramNotifier
            from telegram_config import BOT_TOKEN as _BOT_TOKEN
            from telegram_config import CHAT_ID as _CHAT_ID

            telegram = _TelegramNotifier(_BOT_TOKEN, _CHAT_ID)
            if telegram.is_configured():
                print("✅ Telegram uyarı sistemi aktif!")
            else:
                print("⚠️ Telegram yapılandırılmamış. telegram_config.py kontrol edin.")
                telegram = None
        except Exception as e:
            print(f"⚠️ Telegram hatası: {e}")
            telegram = None

    # Load symbols
    symbols = load_symbols()

    # Market regime check
    CURRENT_MARKET_STATUS = get_market_regime_status(symbols)
    if not CURRENT_MARKET_STATUS["safe"]:
        print(f"🛑 PİYASA UYARISI: {CURRENT_MARKET_STATUS['reason']}")
        print("   -> Alım sinyalleri otomatik olarak filtrelenecek.")
    else:
        print(f"✅ {CURRENT_MARKET_STATUS['reason']}")

    # Evaluate symbols
    signals_sent = 0
    kelly_fraction = 0.25
    results = evaluate_symbols_parallel(symbols, kelly_fraction=kelly_fraction)

    # Send alerts
    if telegram:
        for info in results:
            if info.get("entry_ok"):
                try:
                    if signals_sent >= get_setting("max_signal_alerts", 3):
                        break
                    if telegram.send_signal_alert(info):
                        signals_sent += 1
                except Exception as e:
                    print(f"⚠️ {info.get('symbol')} için uyarı gönderilemedi: {e}")

    if not results:
        print("Liste boş. Veri/bağlantı kontrol edin.")
        return

    # Process results
    df = pd.DataFrame(results)
    df = df.sort_values(["entry_ok", "score"], ascending=[False, False])

    # Save results
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    out_csv = os.path.join("data", "shortlists", f"shortlist_{ts}.csv")
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    df.to_csv(out_csv, index=False)

    # Show buyable signals
    buyable = df[df["entry_ok"]]
    print("\n--- Bugün alınabilecekler (entry_ok=True) ---")
    print(buyable.to_string(index=False) if len(buyable) > 0 else "Bugün alım fırsatı yok.")
    print(f"\nCSV kaydedildi: {out_csv}")

    # Recommendation list (Top 10)
    try:
        df_rec = df.copy()
        df_rec["recommendation_score"] = df_rec.apply(
            lambda r: compute_recommendation_score(r.to_dict()), axis=1
        )
        df_rec["strength"] = df_rec["recommendation_score"].map(compute_recommendation_strength)
        df_rec = df_rec.sort_values(["entry_ok", "recommendation_score"], ascending=[False, False])
        top10 = df_rec.head(10)

        print("\n--- Öneri Listesi (Top 10) ---")
        for i, rec in enumerate(top10.to_dict(orient="records"), 1):
            rec_typed = {str(k): v for k, v in rec.items()}  # ensure str keys
            why = build_explanation(rec_typed)
            reason = build_reason(rec_typed)
            entry_text = "Evet" if rec_typed.get("entry_ok") else "Hayır"
            print(
                f"{i}. {rec_typed.get('symbol')} | Fiyat: ${rec_typed.get('price')} | "
                f"Skor: {rec_typed.get('recommendation_score'):.2f} ({int(rec_typed.get('strength',0))}/100) | "
                f"Entry: {entry_text}"
            )
            print(f"   -> {why}")
            print(f"   -> {reason}")

        # Save suggestions
        out_sug = os.path.join("data", "suggestions", f"suggestions_{ts}.csv")
        os.makedirs(os.path.dirname(out_sug), exist_ok=True)
        top10 = top10.assign(
            why=top10.apply(lambda r: build_explanation(r.to_dict()), axis=1),
            reason=top10.apply(lambda r: build_reason(r.to_dict()), axis=1),
        )
        top10.to_csv(out_sug, index=False)
        print(f"Öneriler CSV kaydedildi: {out_sug}")

        # Send to Telegram
        if telegram and TELEGRAM_ENABLED:
            try:
                telegram.send_recommendations(top10)
            except Exception as _tge:
                print(f"⚠️ Öneriler Telegram'a gönderilemedi: {_tge}")

    except Exception as e:
        print(f"⚠️ Öneri listesi oluşturulamadı: {e}")

    # Daily summary
    if telegram and TELEGRAM_ENABLED:
        try:
            best_signal = buyable.iloc[0].to_dict() if len(buyable) > 0 else None
            telegram.send_daily_summary(len(buyable), best_signal)
            print(f"📊 Günlük özet gönderildi. Toplam uyarı: {signals_sent}")
        except Exception as e:
            print(f"⚠️ Günlük özet gönderilemedi: {e}")

    # Summary
    if len(buyable) > 0:
        print(f"\n🎯 ÖZET: {len(buyable)} ALIM FIRSATI BULUNDU!")
        if signals_sent > 0:
            print(f"📱 {signals_sent} Telegram uyarısı gönderildi!")
    else:
        print("\n💤 Bugün kriterleri karşılayan sinyal yok.")
        print("💡 Bu normal - kaliteli sinyaller bekliyoruz!")


if __name__ == "__main__":
    # Windows encoding fix
    try:
        import sys

        if os.name == "nt":
            try:
                _reconf_out = getattr(sys.stdout, "reconfigure", None)
                if callable(_reconf_out):
                    _reconf_out(encoding="utf-8", errors="replace")
                _reconf_err = getattr(sys.stderr, "reconfigure", None)
                if callable(_reconf_err):
                    _reconf_err(encoding="utf-8", errors="replace")
            except Exception:
                pass
    except Exception:
        pass

    main()
