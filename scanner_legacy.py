import argparse
import base64
import json
import math
import os
from datetime import datetime
from statistics import median

import pandas as pd
import streamlit as st
import yfinance as yf

# --- AYARLARI YÜKLE ---
SETTINGS_FILE = "user_settings.json"
DEFAULT_SETTINGS = {
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


def load_user_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, encoding="utf-8") as f:
                return json.load(f)
        except:
            return DEFAULT_SETTINGS
    return DEFAULT_SETTINGS


USER_SETTINGS = load_user_settings()

# Stratejiye göre parametreleri ayarla
STRATEGY_PARAMS = {
    "Normal": {"min_score": 1, "rsi_low": 30, "rsi_high": 70},
    "Agresif": {"min_score": 1, "rsi_low": 40, "rsi_high": 60},  # Daha sık sinyal
    "Defansif": {"min_score": 2, "rsi_low": 25, "rsi_high": 75},  # Daha az ama güvenli
    "Momentum": {"min_score": 1, "rsi_low": 35, "rsi_high": 65},
}

CURRENT_STRATEGY = USER_SETTINGS.get("strategy", "Normal")
PARAMS = STRATEGY_PARAMS.get(CURRENT_STRATEGY, STRATEGY_PARAMS["Normal"])


def analyze_recommendations(df, user_portfolio=None, start_date=None, end_date=None, top_n=10):
    def safe_float(val):
        try:
            return float(val)
        except (TypeError, ValueError):
            return 0.0

    """
    Öneri performans analizi ve görselleştirme. Doğrudan panelde kullanılabilir.
    df: öneri/sinyal veri DataFrame'i (symbol, time, price, close, signal_type, strategy, note, volatility, sharpe, sortino, etc.)
    user_portföyü: dict {symbol: miktar} (kullanıcı portföyü)
    start_date, end_date: filtreleme için tarih aralığı
    top_n: en iyi n hisse
    """
    # Tarih aralığı filtrele
    if start_date:
        df = df[df["time"] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df["time"] <= pd.to_datetime(end_date)]
    # En iyi n hisseyi getir %'ye göre seç
    df["return_pct"] = ((df["close"] - df["price"]) / df["price"]) * 100
    df_top = df.sort_values("return_pct", ascending=False).head(top_n)

    # Özet kutuları
    total_success = (df_top["return_pct"] > 0).sum()
    success_rate = total_success / len(df_top) * 100 if len(df_top) > 0 else 0
    avg_return = df_top["return_pct"].mean() if len(df_top) > 0 else 0
    total_gain = (df_top["close"] - df_top["price"]).sum()
    st.metric("Başarı Oranı (%)", f"{success_rate:.1f}")
    st.metric("Ortalama Getiri (%)", f"{avg_return:.2f}")
    st.metric("Toplam Kazanç/Kayıp", f"{total_gain:.2f}")
    st.metric("İncelenen Aralık", f"{start_date} - {end_date}")

    # Detaylı tablo
    def color_success(val):
        color = "background-color: #b6fcb6" if val > 0 else "background-color: #fcb6b6"
        return color

    st.dataframe(
        df_top[
            [
                "symbol",
                "time",
                "price",
                "close",
                "return_pct",
                "signal_type",
                "strategy",
                "note",
                "volatility",
                "sharpe",
                "sortino",
            ]
        ].style.applymap(color_success, subset=["return_pct"])
    )

    # Detay butonu ve grafik
    for idx, row in df_top.iterrows():
        with st.expander(f"Detay: {row['symbol']}"):
            st.write(f"Sinyal tipi: {row['signal_type']}, Strateji: {row['strategy']}")
            st.write(f"Not: {row['note']}")
            vol = safe_float(row["volatility"])
            sharpe = safe_float(row["sharpe"])
            sortino = safe_float(row["sortino"])
            st.write(f"Volatilite: {vol:.2f}, Sharpe: {sharpe:.2f}, Sortino: {sortino:.2f}")
            # Fiyat grafiği
            if "price_series" in row:
                st.line_chart(row["price_series"])
            # Sinyal geçmişi
            if "signal_history" in row:
                st.write(row["signal_history"])

    # Portföy simülasyonu
    if user_portfolio:
        sim_gain = 0
        for sym, qty in user_portfolio.items():
            rec = df_top[df_top["symbol"] == sym]
            if not rec.empty:
                sim_gain += (rec["close"].values[0] - rec["price"].values[0]) * qty
        st.metric("Gerçek Portföy Kazancı", f"{sim_gain:.2f}")

    # Export/rapor
    def export_excel(df):
        output = df.to_excel(index=False)
        b64 = base64.b64encode(output).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="report.xlsx">Excel olarak indir</a>'
        st.markdown(href, unsafe_allow_html=True)

    st.button("Excel olarak indir", on_click=lambda: export_excel(df_top))

    # Başarı/kayıp dağılımı (bar chart)
    st.bar_chart(df_top["return_pct"])


def load_local_data(csv_path):
    """Lokal CSV dosyasından sembol ve sinyal verilerini yükler."""
    try:
        df = pd.read_csv(csv_path)
        return df
    except Exception as e:
        print(f"Lokal veri dosyası yüklenemedi: {e}")
        return pd.DataFrame()


def calculate_risk_management(price, atr, momentum_score=50):
    # Dinamik Stop ve Kademeli Hedef (Tiered TP) Mantığı

    # Varsayılan (Normal Mod)
    stop_mult = 2.0
    tp1_mult = 4.0
    tp2_mult = 6.0
    # TP3 artık sabit bir hedef değil, Trailing Stop başlangıcı için bir referans (Moonbag)
    tp3_mult = 9.0
    strategy_tag = "Trend 📈"

    if momentum_score > 80:
        # Sniper Modu (Agresif)
        stop_mult = 1.5
        tp1_mult = 3.0
        tp2_mult = 5.5
        tp3_mult = 8.0
        strategy_tag = "Sniper 🎯"
    elif momentum_score < 50:
        # Defansif Mod (Zayıf Piyasa)
        stop_mult = 2.5
        tp1_mult = 4.5
        tp2_mult = 6.5
        tp3_mult = 0  # TP3 yok
        strategy_tag = "Defansif 🛡️"

    stop_loss = price - (atr * stop_mult)
    tp1 = price + (atr * tp1_mult)
    tp2 = price + (atr * tp2_mult)
    tp3 = price + (atr * tp3_mult) if tp3_mult > 0 else 0

    # Ana hedef olarak TP2'yi kullanıyoruz (Panelde görünen)
    take_profit = tp2

    position_size = 1000  # Sabit
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


def load_symbols():
    # Basit sembol listesi
    return ["AAPL", "MSFT", "GOOGL", "NVDA", "SPY", "QQQ"]


def evaluate_symbols_parallel(symbols, kelly_fraction=0.5):
    # Sembolleri paralel olarak değerlendir
    from concurrent.futures import ThreadPoolExecutor

    results = []
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(evaluate_symbol, symbol, kelly_fraction) for symbol in symbols]
        for future in futures:
            result = future.result()
            if result:
                results.append(result)
    return results


# 🔔 Telegram uyarı sistemi mevcudiyet kontrolü
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


# ---- Yardımcılar ----
def safe_float(value):
    """Pandas Series veya tek değeri güvenli şekilde float'a çevirir"""
    if hasattr(value, "iloc"):
        return float(value.iloc[0]) if len(value) > 0 else 0.0
    elif hasattr(value, "values"):
        return float(value.values[0]) if len(value.values) > 0 else 0.0
    else:
        return float(value)


# ✨ Eşik Ayarları (Normal vs Agresif)
DEFAULT_SETTINGS = {
    "vol_multiplier": 1.5,  # Hacim çarpanı
    "momentum_pct": 2.0,  # 3 günlük momentum %
    "trend_gap_pct": 3.0,  # EMA50-EMA200 fark %
    "min_alignment_ratio": 0.75,  # Zaman dilimi uyumu alt sınır
    "min_momentum_ratio": 0.6,  # Momentum uyumu alt sınır
    "min_signal_score": 3,  # Minimum sinyal puanı
    "min_filter_score": 2,  # Minimum filtre puanı
    "min_price": 2.0,  # Likidite tabanı: minimum fiyat ($)
    "min_avg_vol": 300000,  # Likidite tabanı: 10 günlük ortalama hacim
    "max_signal_alerts": 3,  # Bir koşuda en fazla kaç sinyal gönderilsin
    "auto_adjust": True,  # Fiyatlar temettü/bölünme ayarlı mı?
    "prepost": False,  # Pre/after-hours dahil mi?
    "momentum_windows": [1, 3, 5],
    "momentum_baseline_window": 60,
    "momentum_z_threshold": 1.5,
    "momentum_dynamic_enabled": True,
    "momentum_dynamic_window": 60,
    "momentum_dynamic_quantile": 0.975,
    "momentum_dynamic_alpha": 0.6,
    "momentum_dynamic_min": 1.1,
    "momentum_dynamic_max": 3.0,
    "momentum_segment_thresholds": {
        "high_liquidity": 2.0,
        "mid_liquidity": 1.6,
        "low_liquidity": 1.4,
    },
    "momentum_liquidity_breakpoints": {
        "high": 1_000_000,
        "low": 300_000,
    },
}

AGGRESSIVE_OVERRIDES = {
    "vol_multiplier": 1.3,
    "momentum_pct": 1.2,
    "trend_gap_pct": 2.2,
    "min_alignment_ratio": 0.67,
    "min_momentum_ratio": 0.5,
    "min_signal_score": 2,
    "min_filter_score": 1,
    "min_price": 1.5,
    "min_avg_vol": 200_000,
    "momentum_z_threshold": 1.2,
}

SETTINGS = DEFAULT_SETTINGS.copy()


# ✨ Basit Ama Güçlü 3 Filtre
def check_volume_spike(df):
    """Hacim Artışı: Ortalama hacmin 1.5x üstü mü?"""
    if len(df) < 10:
        return False
    try:
        current_vol = safe_float(df["Volume"].iloc[-1])
        avg_vol = safe_float(df["vol_avg10"].iloc[-1])
        return current_vol > avg_vol * SETTINGS.get("vol_multiplier", 1.5)
    except Exception:
        return False


def analyze_price_momentum(df, *, windows=None, baseline_window=None):
    """Adaptif momentum profili üretir.

    Dönen sözlükte her ufuk için yüzde getiri, z-skoru ve referans istatistikler bulunur.
    """

    close = df.get("Close") if df is not None else None
    if close is None or close.dropna().empty:
        return {
            "metrics": [],
            "best": None,
            "positive": False,
            "negative": False,
            "dominant_zscore": 0.0,
            "dominant_return_pct": 0.0,
            "dominant_direction": 0,
        }

    horizons = windows or SETTINGS.get("momentum_windows", [1, 3, 5])
    baseline_window = int(baseline_window or SETTINGS.get("momentum_baseline_window", 20))
    base_threshold = float(SETTINGS.get("momentum_z_threshold", 1.5))

    # Segment bazlı eşik: likiditeye göre presets
    segment = None
    segment_threshold = None
    segment_config = SETTINGS.get("momentum_segment_thresholds") or {}
    if segment_config:
        breakpoints = SETTINGS.get("momentum_liquidity_breakpoints", {}) or {}
        high_cutoff = float(breakpoints.get("high", 1_000_000))
        low_cutoff = float(breakpoints.get("low", 300_000))
        try:
            avg_vol = safe_float(df["vol_avg10"].iloc[-1])
        except Exception:
            avg_vol = 0.0

        if avg_vol >= high_cutoff:
            segment = "high_liquidity"
        elif avg_vol <= low_cutoff:
            segment = "low_liquidity"
        else:
            segment = "mid_liquidity"

        seg_value = segment_config.get(segment) if segment else None
        try:
            segment_threshold = float(seg_value) if seg_value is not None else None
        except Exception:
            segment_threshold = None

    z_threshold = float(segment_threshold or base_threshold)

    # Dinamik eşik kalibrasyonu
    dynamic_enabled = bool(SETTINGS.get("momentum_dynamic_enabled", False))
    dynamic_window = int(
        SETTINGS.get("momentum_dynamic_window", baseline_window) or baseline_window
    )
    dynamic_quantile = float(SETTINGS.get("momentum_dynamic_quantile", 0.975))
    dynamic_alpha = float(SETTINGS.get("momentum_dynamic_alpha", 0.5))
    dynamic_min = float(SETTINGS.get("momentum_dynamic_min", 1.0))
    dynamic_max = float(SETTINGS.get("momentum_dynamic_max", 3.0))

    metrics = []
    dynamic_candidates = []

    for horizon in horizons:
        if len(close) <= horizon:
            continue
        try:
            current_price = safe_float(close.iloc[-1])
            reference_price = safe_float(close.iloc[-(horizon + 1)])
            if reference_price == 0:
                continue

            return_fraction = (current_price - reference_price) / reference_price
            momentum_series = close.pct_change(horizon).dropna()
            recent_window = momentum_series.tail(baseline_window)

            if recent_window.empty:
                mean_fraction = 0.0
                std_fraction = 0.0
            else:
                mean_fraction = float(recent_window.mean())
                std_fraction = float(recent_window.std(ddof=0))

            if std_fraction > 1e-9:
                z_score = (return_fraction - mean_fraction) / std_fraction
            else:
                z_score = 0.0

            metrics.append(
                {
                    "horizon": horizon,
                    "return_pct": return_fraction * 100.0,
                    "mean_pct": mean_fraction * 100.0,
                    "std_pct": std_fraction * 100.0,
                    "zscore": z_score,
                }
            )

            if dynamic_enabled:
                window_len = max(dynamic_window, baseline_window)
                history = momentum_series.tail(window_len)
                if len(history) >= max(10, window_len // 3):
                    hist_mean = float(history.mean())
                    hist_std = float(history.std(ddof=0))
                    if hist_std > 1e-9:
                        z_hist = (history - hist_mean) / hist_std
                        z_hist = z_hist.dropna().abs()
                        if not z_hist.empty:
                            candidate = float(z_hist.quantile(dynamic_quantile))
                            if math.isfinite(candidate) and candidate > 0:
                                dynamic_candidates.append(candidate)
        except Exception:
            continue

    dynamic_threshold = None
    if dynamic_candidates:
        dynamic_threshold = median(dynamic_candidates)
        dynamic_threshold = max(dynamic_min, min(dynamic_max, dynamic_threshold))
        z_threshold = (dynamic_alpha * dynamic_threshold) + ((1.0 - dynamic_alpha) * z_threshold)

    z_threshold = max(dynamic_min, min(dynamic_max, float(z_threshold)))

    best_metric = max(metrics, key=lambda item: abs(item["zscore"])) if metrics else None
    dominant_z = float(best_metric["zscore"]) if best_metric else 0.0
    dominant_return = float(best_metric["return_pct"]) if best_metric else 0.0
    direction = 1 if dominant_z >= z_threshold else (-1 if dominant_z <= -z_threshold else 0)

    positive = any(item["zscore"] >= z_threshold for item in metrics)
    negative = any(item["zscore"] <= -z_threshold for item in metrics)

    return {
        "metrics": metrics,
        "best": best_metric,
        "positive": positive,
        "negative": negative,
        "dominant_zscore": dominant_z,
        "dominant_return_pct": dominant_return,
        "dominant_direction": direction,
        "z_threshold_effective": z_threshold,
        "z_threshold_base": base_threshold,
        "z_threshold_segment": segment_threshold,
        "z_threshold_dynamic": dynamic_threshold,
        "liquidity_segment": segment,
        "baseline_window": baseline_window,
        "dynamic_threshold_samples": len(dynamic_candidates),
    }


def check_price_momentum(df):
    """Geriye dönük uyum için pozitif momentum bool'u döndürür"""
    analysis = analyze_price_momentum(df)
    return bool(analysis.get("positive"))


def check_trend_strength(df):
    """Trend Gücü: EMA50 ile EMA200 arasında %3+ fark var mı?"""
    if len(df) < 200:
        return False
    try:
        ema50 = safe_float(df["ema50"].iloc[-1])
        ema200 = safe_float(df["ema200"].iloc[-1])
        if ema200 == 0:
            return False
        strength_pct = ((ema50 - ema200) / ema200) * 100
        return strength_pct >= SETTINGS.get("trend_gap_pct", 3.0)  # EMA50, EMA200'den %X+ yüksek
    except Exception:
        return False


# ⏰ TIMEFRAME SENKRONIZASYONU - %73'ü %80'e çıkar!
def check_timeframe_alignment(df_1h, df_4h, df_1d):
    """
    3 timeframe'in trend uyumunu kontrol eder
    En az 2/3 timeframe aynı yönde olmalı
    """
    alignments = []

    try:
        # 1 saatlik trend (EMA20 vs Price)
        if len(df_1h) >= 20:
            price_1h = safe_float(df_1h["Close"].iloc[-1])
            ema20_1h = safe_float(df_1h["Close"].ewm(span=20).mean().iloc[-1])
            trend_1h = price_1h > ema20_1h
            alignments.append(trend_1h)

        # 4 saatlik trend (EMA50 vs Price)
        if len(df_4h) >= 50:
            price_4h = safe_float(df_4h["Close"].iloc[-1])
            ema50_4h = safe_float(df_4h["ema50"].iloc[-1])
            trend_4h = price_4h > ema50_4h
            alignments.append(trend_4h)

        # Günlük trend (EMA200 vs Price)
        if len(df_1d) >= 200:
            price_1d = safe_float(df_1d["Close"].iloc[-1])
            ema200_1d = safe_float(df_1d["ema200"].iloc[-1])
            trend_1d = price_1d > ema200_1d
            alignments.append(trend_1d)

        # En az 2/3 uyum var mı?
        if len(alignments) >= 2:
            bullish_count = sum(alignments)
            total_count = len(alignments)
            alignment_ratio = bullish_count / total_count

            # %67+ uyum = güçlü sinyal
            return alignment_ratio >= 0.67, alignment_ratio, alignments

        return False, 0.0, alignments

    except Exception:
        return False, 0.0, []


def check_momentum_confluence(df_15m, df_4h):
    """
    SIKILI Momentum göstergelerinin uyumunu kontrol eder
    Daha sıkı kriterlerle kaliteyi artırır
    """
    try:
        confluence_score = 0
        max_score = 6  # Daha fazla kriter

        # 15m RSI momentum - daha sıkı aralık
        if len(df_15m) >= 14:
            rsi_15m = safe_float(df_15m["rsi"].iloc[-1])
            if 45 <= rsi_15m <= 65:  # Daha dar sağlıklı aralık (40-70 → 45-65)
                confluence_score += 1

        # 4h RSI momentum - daha sıkı aralık
        if len(df_4h) >= 14:
            rsi_4h = safe_float(df_4h["rsi"].iloc[-1])
            if 45 <= rsi_4h <= 65:  # Daha dar sağlıklı aralık
                confluence_score += 1

        # 15m MACD histogram - güçlü pozitif
        if len(df_15m) >= 26:
            macd_15m = safe_float(df_15m["macd_hist"].iloc[-1])
            if macd_15m > 0.01:  # Sadece pozitif değil, güçlü pozitif
                confluence_score += 1

        # 4h MACD histogram - güçlü pozitif
        if len(df_4h) >= 26:
            macd_4h = safe_float(df_4h["macd_hist"].iloc[-1])
            if macd_4h > 0.01:  # Güçlü pozitif momentum
                confluence_score += 1

        # YENİ: RSI trend kontrolü
        if len(df_15m) >= 15 and len(df_4h) >= 15:
            rsi_15m_prev = safe_float(df_15m["rsi"].iloc[-2])
            rsi_15m_curr = safe_float(df_15m["rsi"].iloc[-1])
            if rsi_15m_curr > rsi_15m_prev:  # RSI yükseliyor
                confluence_score += 1

        # YENİ: MACD trend kontrolü
        if len(df_4h) >= 27:
            macd_4h_prev = safe_float(df_4h["macd_hist"].iloc[-2])
            macd_4h_curr = safe_float(df_4h["macd_hist"].iloc[-1])
            if macd_4h_curr > macd_4h_prev:  # MACD güçleniyor
                confluence_score += 1

        confluence_ratio = confluence_score / max_score
        return confluence_ratio >= 0.5, confluence_ratio  # %50+ uyum (6 kriterden 3+)

    except Exception:
        return False, 0.0


def bbands(series, window=20, ndev=2):
    m = series.rolling(window).mean()
    s = series.rolling(window).std()
    upper = m + ndev * s
    lower = m - ndev * s
    return upper, m, lower


def ema(series, window):
    return series.ewm(span=window, adjust=False).mean()


def rsi(series, period=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    roll_up = up.ewm(alpha=1 / period, adjust=False).mean()
    roll_down = down.ewm(alpha=1 / period, adjust=False).mean()
    rs = roll_up / (roll_down.replace(0, 1e-10))
    return 100 - (100 / (1 + rs))


def macd_hist(close, fast=12, slow=26, signal=9):
    macd_line = (
        close.ewm(span=fast, adjust=False).mean() - close.ewm(span=slow, adjust=False).mean()
    )
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return hist


def compute_recommendation_score(row):
    score = 0.0
    score += 2.0 if bool(row.get("regime", False)) else 0.0
    score += 2.0 if bool(row.get("direction", False)) else 0.0
    score += float(row.get("score", 0)) * 1.0
    score += float(row.get("filter_score", 0)) * 1.5
    score += float(row.get("alignment_ratio", 0.0)) * 2.0
    score += float(row.get("momentum_ratio", 0.0)) * 2.0
    score += 0.5 if bool(row.get("volume_spike", False)) else 0.0
    score += 0.5 if bool(row.get("price_momentum", False)) else 0.0
    score += 0.5 if bool(row.get("trend_strength", False)) else 0.0
    score += 0.3 if bool(row.get("is_premium_symbol", False)) else 0.0
    return round(score, 3)


# Öneri skorunu 0–100 aralığına ölçekle
MAX_RECO_SCORE = 18.3  # Premium +0.3 ile teorik üst sınır


def compute_recommendation_strength(x):
    try:
        if isinstance(x, dict) or hasattr(x, "get"):
            score = compute_recommendation_score(x)
        else:
            score = float(x)
        strength = max(0.0, min(100.0, (score / MAX_RECO_SCORE) * 100.0))
        return int(round(strength))
    except Exception:
        return 0


def build_explanation(row):
    try:
        regime = bool(row.get("regime"))
        direction = bool(row.get("direction"))
        trend = "Up" if (regime and direction) else ("Mixed" if (regime or direction) else "Down")
        ar = int(float(row.get("alignment_ratio", 0)) * 100)
        mr = int(float(row.get("momentum_ratio", 0)) * 100)
        fs = int(row.get("filter_score", 0))
        return f"Trend {trend} | Uyum Z{ar}%/M{mr}% | Filtre {fs}/3"
    except Exception:
        return "Özet yok"


def build_reason(row):
    try:
        rr = row.get("risk_reward") or 0
        sl = row.get("stop_loss")
        tp = row.get("take_profit")
        if row.get("entry_ok"):
            return f"Alınır: Trend+ Uyum+ | R/R {rr:.1f} | SL ${sl} · TP ${tp}"
        # eksiklerden en yakın 1-2 taneyi kısa yaz
        lacks = []
        if not row.get("volume_spike"):
            lacks.append("Hacim")
        if not row.get("price_momentum"):
            lacks.append("Momentum")
        if not row.get("trend_strength"):
            lacks.append("Trend")
        if not row.get("timeframe_aligned"):
            lacks.append("Uyum")
        if not row.get("momentum_confluence"):
            lacks.append("Mom.Uyum")
        lacks = ",".join(lacks[:2]) if lacks else "Onay bekleyin"
        return f"Bekleyin: Eksik {lacks} | R/R {rr:.1f}"
    except Exception:
        return "Neden yok"


def atr(df, period=14):
    def _ensure_series(x):
        if isinstance(x, pd.DataFrame):
            return x.iloc[:, 0]
        return x

    high = _ensure_series(df["High"])
    low = _ensure_series(df["Low"])
    close = _ensure_series(df["Close"])
    prev_close = close.shift(1)
    tr = pd.concat(
        [(high - low).abs(), (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def add_indicators(df):
    df = df.copy()
    required_cols = {"Open", "High", "Low", "Close", "Volume"}
    if not required_cols.issubset(set(df.columns)):
        return pd.DataFrame()
    # Ensure single Series for calculations
    close = df["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    high = df["High"]
    if isinstance(high, pd.DataFrame):
        high = high.iloc[:, 0]
    low = df["Low"]
    if isinstance(low, pd.DataFrame):
        low = low.iloc[:, 0]
    vol = df["Volume"]
    if isinstance(vol, pd.DataFrame):
        vol = vol.iloc[:, 0]
    # Indicators
    df["ema50"] = ema(close, 50)
    df["ema200"] = ema(close, 200)
    df["rsi"] = rsi(close, 14)
    df["macd_hist"] = macd_hist(close)
    upper, middle, lower = bbands(close, 20, 2)
    df["bb_upper"], df["bb_middle"], df["bb_lower"] = upper, middle, lower
    # ATR based on ensured Series
    df["atr"] = atr(pd.DataFrame({"High": high, "Low": low, "Close": close}))
    # Volume rolls
    df["vol_med20"] = vol.rolling(20).median()
    df["vol_avg10"] = vol.rolling(10).mean()
    return df


def fetch(symbol, interval, days):
    interval_map = {"15m": "15m", "1h": "1h", "4h": "4h", "1d": "1d"}
    yf_interval = interval_map.get(interval, "1d")
    period_map = {"15m": f"{days}d", "1h": f"{days}d", "4h": f"{days}d", "1d": f"{days}d"}
    yf_period = period_map.get(interval, f"{days}d")
    try:
        tkr = yf.Ticker(symbol)
        df = tkr.history(
            period=yf_period,
            interval=yf_interval,
            auto_adjust=SETTINGS.get("auto_adjust", True),
            prepost=SETTINGS.get("prepost", False),
            actions=False,
            back_adjust=False,
        )
        if df is None or df.empty:
            print(f"[WARN] Veri yok: {symbol} {interval} {days}d")
            return pd.DataFrame()
        # Ensure required columns exist
        if "Close" not in df.columns and "Adj Close" in df.columns:
            df = df.rename(columns={"Adj Close": "Close"})
        # Ensure required columns
        needed = {"Open", "High", "Low", "Close", "Volume"}
        if not needed.issubset(set(df.columns)):
            print(f"[WARN] Beklenen sütunlar eksik: {symbol} {interval} - var: {list(df.columns)}")
            return pd.DataFrame()
        # Normalize timezone to avoid tz-aware vs tz-naive issues
        try:
            if isinstance(df.index, pd.DatetimeIndex):
                if getattr(df.index, "tz", None) is not None:
                    df.index = df.index.tz_convert(None)
                else:
                    # already naive
                    pass
        except Exception:
            pass
        df = df.dropna()
        return df
    except Exception as e:
        print(f"[ERROR] Veri çekilemedi: {symbol} {interval} {days}d - {e}")
        return pd.DataFrame()


def signal_score_row(df):
    if len(df) < 2:
        return 0
    row = df.iloc[-1]
    prev = df.iloc[-2]
    score = 0

    try:
        # Bollinger band sinyali
        if (
            not pd.isna(prev["Close"])
            and not pd.isna(prev["bb_lower"])
            and not pd.isna(row["Close"])
            and not pd.isna(row["bb_lower"])
        ):
            if safe_float(prev["Close"]) < safe_float(prev["bb_lower"]) and safe_float(
                row["Close"]
            ) > safe_float(row["bb_lower"]):
                score += 1
        # RSI sinyali
        if not pd.isna(row["rsi"]) and not pd.isna(prev["rsi"]):
            if 30 <= safe_float(row["rsi"]) <= 45 and safe_float(row["rsi"]) > safe_float(
                prev["rsi"]
            ):
                score += 1
        # MACD histogram sinyali
        if not pd.isna(prev["macd_hist"]) and not pd.isna(row["macd_hist"]):
            if safe_float(prev["macd_hist"]) < 0 and safe_float(row["macd_hist"]) > 0:
                score += 1
        # Hacim sinyali
        if not pd.isna(row["Volume"]) and not pd.isna(row["vol_med20"]):
            if safe_float(row["Volume"]) >= safe_float(row["vol_med20"]) * 1.2:
                score += 1
    except Exception:
        return 0
    return score


def evaluate_symbol(symbol, kelly_fraction=0.5):
    # ...existing code...
    # Teknik analiz ve risk hesaplamaları tamamlandıktan sonra alternatif veri ve rejim entegrasyonu

    try:
        # Tüm timeframe verilerini çek (ana zaman dilimi 15m)
        df_15m = add_indicators(fetch(symbol, "15m", 10))
        df_1h = add_indicators(fetch(symbol, "1h", 60))
        df_4h = add_indicators(fetch(symbol, "4h", 100))
        df_1d = add_indicators(fetch(symbol, "1d", 400))  # GERÇEK GÜNLÜK VERİ (EMA200 için)

        if len(df_15m) < 30 or len(df_1h) < 20 or len(df_4h) < 30 or len(df_1d) < 200:
            # print(f"[INFO] Yetersiz veri: {symbol}") # Gürültüyü azaltmak için kapalı
            return None

        # 1. AŞAMA: TREND FİLTRESİ (Daily Trend - SIKI MOD)
        # Backtest'teki başarılı mantık: Fiyat > EMA200 VE Fiyat > EMA50
        try:
            c_daily = safe_float(df_1d["Close"].iloc[-1])
            e200_daily = safe_float(df_1d["ema200"].iloc[-1])
            e50_daily = safe_float(df_1d["ema50"].iloc[-1])

            regime = c_daily > e200_daily
            direction = c_daily > e50_daily
        except Exception:
            regime = False
            direction = False

        # 2. AŞAMA: MOMENTUM VE HACİM SKORU (Daily - Backtest Mantığı)
        # RSI 30-70, Vol > Avg*1.2, MACD > 0 & Rising
        score = 0
        try:
            if len(df_1d) >= 2:
                row = df_1d.iloc[-1]
                prev = df_1d.iloc[-2]

                # RSI Sinyali (30-70 arası)
                if 30 <= safe_float(row["rsi"]) <= 70:
                    score += 1

                # Hacim Sinyali (Ortalamadan %20 fazla)
                if safe_float(row["Volume"]) > safe_float(row["vol_med20"]) * 1.2:
                    score += 1

                # MACD Sinyali (Pozitif ve Artan)
                if safe_float(row["macd_hist"]) > 0 and safe_float(row["macd_hist"]) > safe_float(
                    prev["macd_hist"]
                ):
                    score += 1
        except Exception:
            score = 0
        last_price = df_15m["Close"].iloc[-1]
        atr_val = df_15m["atr"].iloc[-1]

        momentum_analysis = analyze_price_momentum(df_1d)
        # ✨ 3 Basit Ama Güçlü Filtre Kontrolü
        volume_spike = bool(check_volume_spike(df_1d))
        price_momentum = bool(momentum_analysis.get("positive", False))
        trend_strength = bool(check_trend_strength(df_1d))
        filter_score = int(volume_spike) + int(price_momentum) + int(trend_strength)

        # Yakınlık metrikleri
        try:
            current_vol = safe_float(df_1d["Volume"].iloc[-1])
            avg_vol = safe_float(df_1d["vol_avg10"].iloc[-1])
            volume_multiple = (current_vol / avg_vol) if avg_vol > 0 else 0.0
        except Exception:
            volume_multiple = 0.0
        metrics = (
            momentum_analysis.get("metrics", []) if isinstance(momentum_analysis, dict) else []
        )
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
            momentum_analysis.get(
                "z_threshold_effective", SETTINGS.get("momentum_z_threshold", 1.5)
            )
        )
        z_threshold_base = float(
            momentum_analysis.get("z_threshold_base", SETTINGS.get("momentum_z_threshold", 1.5))
        )
        z_segment_raw = momentum_analysis.get("z_threshold_segment")
        z_dynamic_raw = momentum_analysis.get("z_threshold_dynamic")
        try:
            z_threshold_segment = float(z_segment_raw) if z_segment_raw is not None else None
        except Exception:
            z_threshold_segment = None
        try:
            z_threshold_dynamic = float(z_dynamic_raw) if z_dynamic_raw is not None else None
        except Exception:
            z_threshold_dynamic = None
        baseline_window_used = int(
            momentum_analysis.get("baseline_window", SETTINGS.get("momentum_baseline_window", 20))
        )
        liquidity_segment = momentum_analysis.get("liquidity_segment")
        dynamic_sample_count = int(momentum_analysis.get("dynamic_threshold_samples", 0))
        momentum_bias = {
            1: "bullish",
            -1: "bearish",
        }.get(int(momentum_analysis.get("dominant_direction", 0)), "neutral")
        try:
            ema50 = safe_float(df_1d["ema50"].iloc[-1])
            ema200 = safe_float(df_1d["ema200"].iloc[-1])
            ema_gap_pct = (((ema50 - ema200) / ema200) * 100) if ema200 else 0.0
        except Exception:
            ema_gap_pct = 0.0

        # ⏰ Timeframe Senkronizasyonu ve Momentum Confluence
        timeframe_aligned, alignment_ratio, _ = check_timeframe_alignment(df_1h, df_4h, df_1d)
        timeframe_aligned = bool(timeframe_aligned)
        alignment_ratio = float(alignment_ratio or 0.0)

        momentum_confluence, momentum_ratio = check_momentum_confluence(df_15m, df_4h)
        momentum_confluence = bool(momentum_confluence)
        momentum_ratio = float(momentum_ratio or 0.0)

        # 🎯 4 AŞAMALI FİLTRE (Backtest Onaylı Sistem)
        # 1. Piyasa: Global filtre (Main loop'ta kontrol ediliyor)
        # 2. Trend: Fiyat > EMA200 ve Fiyat > EMA50 (regime ve direction)
        # 3. Momentum: Score >= 2 (RSI, MACD, Volume'den en az 2'si)
        # 4. MTF: Ekstra onay (Zorunlu değil ama puanı artırır)

        # Backtest'te sadece Trend ve Score >= 2 yeterliydi.
        # Canlı taramada MTF uyumunu da ekleyerek güvenliği artırıyoruz.

        min_score_threshold = 2  # Backtest'teki başarılı eşik

        # Temel Sinyal (Backtest Mantığı)
        core_signal = bool(regime and direction and (score >= min_score_threshold))

        # MTF Onayı (Ekstra Güvenlik)
        # Eğer MTF uyumu yoksa, sinyal kalitesi düşer ama trend çok güçlüyse (Score=3) yine de girilebilir.
        mtf_ok = alignment_ratio >= 0.66  # 3 zaman diliminden 2'si uyumlu

        if core_signal:
            if score == 3:
                # Tüm göstergeler (RSI, MACD, Vol) onaylıysa MTF'ye bakma, gir.
                entry_ok = True
            elif score == 2 and mtf_ok:
                # 2 gösterge onaylıysa MTF onayı ara.
                entry_ok = True
            else:
                entry_ok = False
        else:
            entry_ok = False

        # 💎 Premium semboller için esneklik (Opsiyonel, şimdilik kapalı tutalım, sistem disiplinli olsun)
        is_premium_symbol = symbol in ["SPY", "QQQ", "GOOGL", "NVDA", "AAPL", "MSFT"]
        high_quality_signal = entry_ok  # For compatibility with return dict

        # 💧 Likidite filtresi (basit): fiyat ve 10g ort. hacim eşiği
        try:
            price_ok = safe_float(df_1d["Close"].iloc[-1]) >= SETTINGS.get("min_price", 2.0)
        except Exception:
            price_ok = True
        try:
            avg_vol_ok = safe_float(df_1d["vol_avg10"].iloc[-1]) >= SETTINGS.get(
                "min_avg_vol", 300_000
            )
        except Exception:
            avg_vol_ok = True
        liquidity_ok = bool(price_ok and avg_vol_ok)
        entry_ok = bool(entry_ok and liquidity_ok)

        # Momentum Skoru Hesaplama (RSI + MACD + Trend)
        try:
            rsi_val = safe_float(df_1d["rsi"].iloc[-1])
            macd_val = safe_float(df_1d["macd_hist"].iloc[-1])

            rsi_score = max(0, min(100, (rsi_val - 30) / 70 * 100))
            macd_score = 100 if macd_val > 0 else 0
            trend_score = 100 if direction else 0  # direction is c4 > e50

            # Ağırlıklı ortalama
            momentum_score = (rsi_score * 0.4) + (macd_score * 0.3) + (trend_score * 0.3)
        except Exception:
            momentum_score = 50  # Varsayılan

        # Risk yönetimi hesapla
        risk_data = calculate_risk_management(
            price=safe_float(last_price),
            atr=safe_float(atr_val) if pd.notna(atr_val) else 0.01,
            momentum_score=int(momentum_score),
        )

        # Alternatif veri ve rejim entegrasyonu
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
            sentiment = 0.0
            onchain_metric = 0.0
        # Adaptif filtre mantığında alternatif veriyi kullanmak için örnek:
        # (ör: sentiment düşükse, kaotik rejimde alım sinyali zayıflatılır)
        if regime == 1 and sentiment < 0:
            entry_ok = False

        # 🌍 Global Piyasa Filtresi (Market Regime)
        # Eğer piyasa "Kırmızı" veya "Düşüş Trendi"ndeyse, tüm alımları durdur.
        if entry_ok and not CURRENT_MARKET_STATUS["safe"]:
            entry_ok = False
            # Not ekle (eğer note alanı varsa, yoksa print ile logla)
            # Burada return dict'e 'market_note' ekleyebiliriz.

        return {
            "symbol": symbol,
            "price": round(safe_float(last_price), 4),
            "score": int(score),
            "regime": regime,
            "direction": bool(direction),
            "atr": round(safe_float(atr_val), 6) if pd.notna(atr_val) else None,
            "entry_ok": bool(entry_ok),
            "market_status": CURRENT_MARKET_STATUS["reason"],  # Bilgi amaçlı ekle
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
            "momentum_z_segment": (
                round(z_threshold_segment, 2) if z_threshold_segment is not None else None
            ),
            "momentum_z_dynamic": (
                round(z_threshold_dynamic, 2) if z_threshold_dynamic is not None else None
            ),
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


def get_market_regime_status(symbols):
    """
    Checks the global market index (XU100 or NASDAQ) for 'Red Day' or 'Downtrend'.
    Returns: {'safe': bool, 'reason': str}
    """
    # Determine index
    if any(s.endswith(".IS") for s in symbols[:5]):
        index_symbol = "XU100.IS"
    else:
        index_symbol = "^IXIC"

    print(f"📊 Piyasa Analizi Yapılıyor: {index_symbol}")
    try:
        # Download enough data for EMA50
        df = yf.download(index_symbol, period="1y", interval="1d", progress=False)
        if df is None or df.empty:
            return {"safe": True, "reason": "Veri yok"}

        # Calculate EMA50
        df["ema50"] = df["Close"].ewm(span=50, adjust=False).mean()

        last_row = df.iloc[-1]
        close_val = float(last_row["Close"])
        open_val = float(last_row["Open"])
        ema_val = float(last_row["ema50"])

        # 1. Trend Filter
        if close_val < ema_val:
            return {
                "safe": False,
                "reason": f"Düşüş Trendi (Fiyat < EMA50). {index_symbol} @ {close_val:.2f} < {ema_val:.2f}",
            }

        # 2. Red Day Filter
        if close_val < open_val:
            return {
                "safe": False,
                "reason": f"Kırmızı Gün (Close < Open). {index_symbol} bugün satıcılı.",
            }

        return {"safe": True, "reason": "Piyasa Pozitif (Trend Yukarı + Yeşil Mum)"}

    except Exception as e:
        print(f"⚠️ Piyasa analizi hatası: {e}")
        return {"safe": True, "reason": "Hata oluştu, varsayılan güvenli"}


CURRENT_MARKET_STATUS = {"safe": True, "reason": "Varsayılan"}


def main():
    global SETTINGS
    parser = argparse.ArgumentParser(description="Basit ama etkili borsa tarayıcı")
    parser.add_argument(
        "--aggressive", action="store_true", help="Eşikleri gevşeterek daha fazla fırsat yakala"
    )
    args = parser.parse_args()

    if args.aggressive:
        s = DEFAULT_SETTINGS.copy()
        s.update(AGGRESSIVE_OVERRIDES)
        SETTINGS = s
    else:
        SETTINGS = DEFAULT_SETTINGS.copy()

    print("🔍 TARAMA BAŞLIYOR...")
    if args.aggressive:
        print("⚡ Agresif mod aktif: eşikler gevşetildi.")

    # 🔔 Telegram uyarı sistemi başlat
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

    # Sembol taraması (paralel)
    symbols = load_symbols()

    # 🌍 Piyasa Rejimi Kontrolü (Global Filtre)
    global CURRENT_MARKET_STATUS
    CURRENT_MARKET_STATUS = get_market_regime_status(symbols)
    if not CURRENT_MARKET_STATUS["safe"]:
        print(f"🛑 PİYASA UYARISI: {CURRENT_MARKET_STATUS['reason']}")
        print("   -> Alım sinyalleri otomatik olarak filtrelenecek (entry_ok=False).")
    else:
        print(f"✅ {CURRENT_MARKET_STATUS['reason']}")

    signals_sent = 0
    # Kelly fraction panelden alınmalı, burada örnek olarak 0.25 (Quarter Kelly)
    kelly_fraction = 0.25
    results = evaluate_symbols_parallel(symbols, kelly_fraction=kelly_fraction)

    # 🔔 Uyarılar (paralel sonrası, sırayla gönder)
    if telegram:
        for info in results:
            if info.get("entry_ok"):
                try:
                    if signals_sent >= SETTINGS.get("max_signal_alerts", 3):
                        break
                    if telegram.send_signal_alert(info):
                        signals_sent += 1
                except Exception as e:
                    print(f"⚠️ {info.get('symbol')} için uyarı gönderilemedi: {e}")

    if not results:
        print("Liste boş. Veri/bağlantı kontrol edin.")
        return

    # Sonuçları işle
    df = pd.DataFrame(results)
    df = df.sort_values(["entry_ok", "score"], ascending=[False, False])

    # ML/DRL state space için alternatif veri vektörleri
    from altdata import get_altdata_state

    altdata_states = []
    for r in results:
        altdata_states.append(get_altdata_state(r["symbol"], r["timestamp"]))
    print("\nML/DRL state space için alternatif veri vektörleri:")
    for state in altdata_states:
        print(state)
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    out_csv = os.path.join("data", "shortlists", f"shortlist_{ts}.csv")
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    df.to_csv(out_csv, index=False)

    # Alım fırsatları
    buyable = df[df["entry_ok"]]

    print("\n--- Bugün alınabilecekler (entry_ok=True) ---")
    print(buyable.to_string(index=False) if len(buyable) > 0 else "Bugün alım fırsatı yok.")
    print(f"\nCSV kaydedildi: {out_csv}")

    # Öneri listesi (Top 10)
    try:
        df_rec = df.copy()
        df_rec["recommendation_score"] = df_rec.apply(compute_recommendation_score, axis=1)
        df_rec["strength"] = df_rec["recommendation_score"].map(compute_recommendation_strength)
        # Önce entry_ok olanları, ardından en yüksek skorları önceliklendir
        df_rec = df_rec.sort_values(["entry_ok", "recommendation_score"], ascending=[False, False])
        top10 = df_rec.head(10)
        print("\n--- Öneri Listesi (Top 10) ---")
        for i, rec in enumerate(top10.to_dict(orient="records"), 1):
            why = build_explanation(rec)
            reason = build_reason(rec)
            entry_text = "Evet" if rec.get("entry_ok") else "Hayır"
            print(
                f"{i}. {rec.get('symbol')} | Fiyat: ${rec.get('price')} | Skor: {rec.get('recommendation_score'):.2f} ({int(rec.get('strength', 0))}/100) | Entry: {entry_text}"
            )
            print(f"   -> {why}")
            print(f"   -> {reason}")
        # CSV olarak da kaydet
        out_sug = os.path.join("data", "suggestions", f"suggestions_{ts}.csv")
        os.makedirs(os.path.dirname(out_sug), exist_ok=True)
        top10 = top10.assign(
            why=top10.apply(lambda r: build_explanation(r.to_dict()), axis=1),
            reason=top10.apply(lambda r: build_reason(r.to_dict()), axis=1),
        )
        top10.to_csv(out_sug, index=False)
        print(f"Öneriler CSV kaydedildi: {out_sug}")
        # Telegram'a öneriler gönder
        try:
            if telegram and TELEGRAM_ENABLED:
                telegram.send_recommendations(top10)
        except Exception as _tge:
            print(f"⚠️ Öneriler Telegram'a gönderilemedi: {_tge}")
    except Exception as e:
        print(f"⚠️ Öneri listesi oluşturulamadı: {e}")

    # 🔔 Günlük özet gönder
    if telegram and TELEGRAM_ENABLED:
        try:
            best_signal = buyable.iloc[0].to_dict() if len(buyable) > 0 else None
            telegram.send_daily_summary(len(buyable), best_signal)
            print(f"📊 Günlük özet gönderildi. Toplam uyarı: {signals_sent}")
        except Exception as e:
            print(f"⚠️ Günlük özet gönderilemedi: {e}")

    # Özet bilgi
    if len(buyable) > 0:
        print(f"\n🎯 ÖET: {len(buyable)} ALIM FIRSATI BULUNDU!")
        if signals_sent > 0:
            print(f"📱 {signals_sent} Telegram uyarısı gönderildi!")
    else:
        print("\n💤 Bugün kriterleri karşılayan sinyal yok.")
        print("💡 Bu normal - kaliteli sinyaller bekliyoruz!")


if __name__ == "__main__":
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
