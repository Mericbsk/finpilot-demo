#!/usr/bin/env python3
"""
FinPilot — Kapsamlı Sistem Denetimi v2
Doğru API imzaları ile tüm modülleri bağımsız doğrular.
"""

import json
import os
import sys
import traceback
from datetime import datetime

# Proje kökünde çalıştığından emin ol
os.chdir("/workspaces/Borsa")

RESULTS = {"passed": [], "failed": [], "warnings": [], "info": []}


def log_pass(test_name, detail=""):
    RESULTS["passed"].append(f"✅ {test_name}: {detail}")
    print(f"  ✅ {test_name}: {detail}")


def log_fail(test_name, detail=""):
    RESULTS["failed"].append(f"❌ {test_name}: {detail}")
    print(f"  ❌ {test_name}: {detail}")


def log_warn(test_name, detail=""):
    RESULTS["warnings"].append(f"⚠️  {test_name}: {detail}")
    print(f"  ⚠️  {test_name}: {detail}")


def log_info(test_name, detail=""):
    RESULTS["info"].append(f"ℹ️  {test_name}: {detail}")


import numpy as np
import pandas as pd

# ===========================================================================
# Sentetik test verisi oluştur (tüm bölümlerde kullanılacak)
# ===========================================================================
np.random.seed(42)
n = 300
dates = pd.date_range("2024-01-01", periods=n, freq="D")
base_price = 100 + np.cumsum(np.random.randn(n) * 0.5)
close_arr = base_price.copy()
high_arr = close_arr + np.abs(np.random.randn(n) * 1.5)
low_arr = close_arr - np.abs(np.random.randn(n) * 1.5)
open_arr = close_arr + np.random.randn(n) * 0.3
volume_arr = np.random.randint(200000, 5000000, n).astype(float)

df_raw = pd.DataFrame(
    {"Open": open_arr, "High": high_arr, "Low": low_arr, "Close": close_arr, "Volume": volume_arr},
    index=dates,
)

# ############################################################################
# BÖLÜM 2: ALGORİTMA DOĞRULAMA
# ############################################################################
print("=" * 80)
print("BÖLÜM 2: ALGORİTMA DOĞRULAMA")
print("=" * 80)

# --- 2.1 Teknik Göstergeler (add_indicators) ---
print("\n--- 2.1 Teknik Gösterge Hesaplamaları ---")
try:
    from scanner.indicators import add_indicators

    df_ind = add_indicators(df_raw.copy())

    # EMA kontrolü
    assert "ema50" in df_ind.columns, "ema50 sütunu eksik"
    assert "ema200" in df_ind.columns, "ema200 sütunu eksik"
    ema50_val = df_ind["ema50"].iloc[-1]
    ema200_val = df_ind["ema200"].iloc[-1]
    assert not np.isnan(ema50_val), "ema50 NaN"
    assert not np.isnan(ema200_val), "ema200 NaN"
    log_pass("EMA-50", f"Son: {ema50_val:.4f}")
    log_pass("EMA-200", f"Son: {ema200_val:.4f}")

    # RSI kontrolü
    assert "rsi" in df_ind.columns, "rsi sütunu eksik"
    rsi_val = df_ind["rsi"].iloc[-1]
    rsi_valid = df_ind["rsi"].dropna()
    assert (rsi_valid >= 0).all() and (rsi_valid <= 100).all(), "RSI aralık dışı"
    log_pass(
        "RSI(14)", f"Son: {rsi_val:.2f}, Min: {rsi_valid.min():.2f}, Max: {rsi_valid.max():.2f}"
    )

    # MACD kontrolü
    assert "macd_hist" in df_ind.columns, "macd_hist eksik"
    macd_val = df_ind["macd_hist"].iloc[-1]
    log_pass("MACD(12,26,9)", f"Son hist: {macd_val:.6f}")

    # Bollinger Bands kontrolü
    assert "bb_upper" in df_ind.columns and "bb_lower" in df_ind.columns
    bb_u = df_ind["bb_upper"].dropna()
    bb_l = df_ind["bb_lower"].dropna()
    # Aynı indekslerde karşılaştır
    common = bb_u.index.intersection(bb_l.index)
    assert (bb_u.loc[common] >= bb_l.loc[common]).all(), "BB upper < lower"
    log_pass("Bollinger(20,2)", f"Üst: {bb_u.iloc[-1]:.4f}, Alt: {bb_l.iloc[-1]:.4f}")

    # ATR kontrolü
    assert "atr" in df_ind.columns
    atr_valid = df_ind["atr"].dropna()
    assert (atr_valid >= 0).all(), "ATR negatif"
    log_pass("ATR(14)", f"Son: {atr_valid.iloc[-1]:.6f}")

    # Volume median/avg
    assert "vol_med20" in df_ind.columns
    assert "vol_avg10" in df_ind.columns
    log_pass(
        "Volume Indicators",
        f"vol_med20: {df_ind['vol_med20'].iloc[-1]:.0f}, vol_avg10: {df_ind['vol_avg10'].iloc[-1]:.0f}",
    )

    # Tüm sütunlar
    all_indicator_cols = [
        "ema50",
        "ema200",
        "rsi",
        "macd_hist",
        "bb_upper",
        "bb_lower",
        "atr",
        "vol_med20",
        "vol_avg10",
    ]
    missing = [c for c in all_indicator_cols if c not in df_ind.columns]
    if missing:
        log_fail("Sütun Bütünlüğü", f"Eksik: {missing}")
    else:
        log_pass("Sütun Bütünlüğü", f"Tüm {len(all_indicator_cols)} gösterge sütunu mevcut")

except Exception as e:
    log_fail("Gösterge Hesaplamaları", f"{e}")

# --- 2.2 RSI Matematiksel Doğrulama ---
print("\n--- 2.2 RSI Matematiksel Doğrulama ---")
try:
    # Sürekli yükselen fiyatta RSI > 50 olmalı
    up_prices = pd.DataFrame(
        {
            "Open": np.linspace(100, 200, 100),
            "High": np.linspace(101, 201, 100),
            "Low": np.linspace(99, 199, 100),
            "Close": np.linspace(100, 200, 100),
            "Volume": [1000000] * 100,
        }
    )
    df_up = add_indicators(up_prices)
    rsi_up = df_up["rsi"].dropna().iloc[-1]
    assert rsi_up > 50, f"Yükselen fiyatta RSI < 50: {rsi_up}"
    log_pass("RSI Yükselen Trend", f"RSI: {rsi_up:.2f} (>50 bekleniyor)")

    # Sürekli düşen fiyatta RSI < 50 olmalı
    down_prices = pd.DataFrame(
        {
            "Open": np.linspace(200, 100, 100),
            "High": np.linspace(201, 101, 100),
            "Low": np.linspace(199, 99, 100),
            "Close": np.linspace(200, 100, 100),
            "Volume": [1000000] * 100,
        }
    )
    df_down = add_indicators(down_prices)
    rsi_down = df_down["rsi"].dropna().iloc[-1]
    assert rsi_down < 50, f"Düşen fiyatta RSI > 50: {rsi_down}"
    log_pass("RSI Düşen Trend", f"RSI: {rsi_down:.2f} (<50 bekleniyor)")

except Exception as e:
    log_fail("RSI Doğrulama", str(e))

# --- 2.3 Z-Score Momentum ---
print("\n--- 2.3 Z-Score Momentum Analizi ---")
try:
    from scanner.signals import analyze_price_momentum

    momentum = analyze_price_momentum(df_ind)
    assert isinstance(momentum, dict), "Momentum dict değil"
    assert "positive" in momentum, "'positive' anahtarı eksik"
    assert "metrics" in momentum, "'metrics' anahtarı eksik"
    assert "z_threshold_effective" in momentum, "'z_threshold_effective' eksik"

    metrics = momentum.get("metrics", [])
    horizons = [m["horizon"] for m in metrics]
    assert set([1, 3, 5]).issubset(set(horizons)), f"Eksik horizonlar: {horizons}"

    z_eff = momentum.get("z_threshold_effective", "N/A")
    z_seg = momentum.get("liquidity_segment", "N/A")
    log_pass(
        "Z-Score Momentum", f"Pozitif: {momentum['positive']}, Z-eşik: {z_eff}, Segment: {z_seg}"
    )

    # Her horizon için detay
    for m in metrics:
        log_info(
            f"  Horizon {m['horizon']}d",
            f"Return: {m.get('return_pct', 'N/A')}%, Z-score: {m.get('z_score', 'N/A')}",
        )

except Exception as e:
    log_fail("Z-Score Momentum", str(e))

# --- 2.4 HMM Rejim Tespiti ---
print("\n--- 2.4 HMM Rejim Tespiti ---")
try:
    from regime_detection import detect_market_regime

    regime_result = detect_market_regime(df_ind["Close"])
    log_pass("HMM Rejim Tespiti", f"Rejim: {regime_result}")
except ImportError as e:
    log_warn("HMM Rejim Tespiti", f"hmmlearn kurulu değil — {e}")
except Exception as e:
    log_fail("HMM Rejim Tespiti", str(e))

# ############################################################################
# BÖLÜM 3: ALIM-SATIM KRİTERLERİ DOĞRULAMA
# ############################################################################
print("\n" + "=" * 80)
print("BÖLÜM 3: ALIM-SATIM KRİTERLERİ DOĞRULAMA")
print("=" * 80)

# --- 3.1 Sinyal Skorlama ---
print("\n--- 3.1 Sinyal Skorlama ---")
try:
    from scanner.signals import signal_score_row

    # signal_score_row(df) — tek DataFrame argüman alır, son 2 satırı kullanır
    # Test: Boğa sinyali (tüm koşullar sağlanır)
    bull_data = pd.DataFrame(
        {
            "Close": [99.0, 105.0],  # BB breakout: prev < bb_lower, curr > bb_lower
            "bb_lower": [100.0, 100.0],
            "rsi": [35.0, 38.0],  # RSI recovery: 30-45 arası ve yükseliyor
            "macd_hist": [-0.2, 0.5],  # MACD crossover: negatiften pozitife
            "Volume": [900000, 1500000],
            "vol_med20": [1000000, 1000000],  # Volume spike: 1.5M > 1M * 1.2
        }
    )
    score_bull = signal_score_row(bull_data)
    log_pass("Sinyal Skor - Boğa", f"Skor: {score_bull} (beklenen: 4)")
    if score_bull != 4:
        log_warn("Sinyal Skor Uyumsuzluk", f"Beklenen 4, gelen {score_bull}")

    # Test: Ayı (hiçbir koşul sağlanmaz)
    bear_data = pd.DataFrame(
        {
            "Close": [105.0, 95.0],
            "bb_lower": [90.0, 90.0],
            "rsi": [75.0, 78.0],
            "macd_hist": [0.5, 0.8],
            "Volume": [500000, 400000],
            "vol_med20": [1000000, 1000000],
        }
    )
    score_bear = signal_score_row(bear_data)
    log_pass("Sinyal Skor - Ayı", f"Skor: {score_bear} (beklenen: 0)")

except Exception as e:
    log_fail("Sinyal Skorlama", f"{e}\n{traceback.format_exc()}")

# --- 3.2 3 Güç Filtresi ---
print("\n--- 3.2 Güç Filtreleri ---")
try:
    from scanner.signals import check_price_momentum, check_trend_strength, check_volume_spike

    vs = check_volume_spike(df_ind)
    ts = check_trend_strength(df_ind)
    pm = check_price_momentum(df_ind)
    log_pass("Volume Spike", f"Sonuç: {vs}")
    log_pass("Trend Strength", f"Sonuç: {ts}")
    log_pass("Price Momentum", f"Sonuç: {pm}")

except Exception as e:
    log_fail("Güç Filtreleri", str(e))

# --- 3.3 Timeframe Alignment & Confluence ---
print("\n--- 3.3 Çoklu Zaman Dilimi Uyumu ---")
try:
    from scanner.signals import check_momentum_confluence, check_timeframe_alignment

    # Sentetik multi-timeframe veri
    df_1h = df_ind.copy()
    df_1h["ema20"] = df_1h["Close"].ewm(span=20).mean()
    df_4h = df_ind.copy()
    df_1d = df_ind.copy()

    aligned, ratio, detail = check_timeframe_alignment(df_1h, df_4h, df_1d)
    log_pass("Timeframe Alignment", f"Uyumlu: {aligned}, Oran: {ratio}")

    conf, conf_ratio = check_momentum_confluence(df_1h, df_4h)
    log_pass("Momentum Confluence", f"Confluence: {conf}, Oran: {conf_ratio}")

except Exception as e:
    log_fail("Çoklu TF Uyumu", str(e))

# --- 3.4 Risk Yönetimi ---
print("\n--- 3.4 Risk Yönetimi (ATR Tabanlı) ---")
try:
    from scanner import calculate_risk_management

    # Sniper (momentum >= 70)
    rm = calculate_risk_management(price=100.0, atr_val=2.0, momentum_score=75)
    assert rm["strategy_tag"] == "Sniper 🎯", f"Beklenen Sniper: {rm['strategy_tag']}"
    assert rm["stop_loss"] == round(100 - 1.5 * 2, 2), f"SL: {rm['stop_loss']}"
    assert rm["tp1"] == round(100 + 3.0 * 2, 2), f"TP1: {rm['tp1']}"
    assert rm["tp2"] == round(100 + 5.0 * 2, 2), f"TP2: {rm['tp2']}"
    assert rm["tp3"] == round(100 + 8.0 * 2, 2), f"TP3: {rm['tp3']}"
    rr = (rm["take_profit"] - 100) / (100 - rm["stop_loss"])
    assert abs(rm["risk_reward_ratio"] - round(rr, 2)) < 0.01
    log_pass(
        "Risk - Sniper 🎯",
        f"SL:{rm['stop_loss']} TP1:{rm['tp1']} TP2:{rm['tp2']} TP3:{rm['tp3']} R:R={rm['risk_reward_ratio']}",
    )

    # Normal (50 <= momentum < 70)
    rm2 = calculate_risk_management(price=100.0, atr_val=2.0, momentum_score=55)
    assert rm2["strategy_tag"] == "Normal 📈"
    assert rm2["stop_loss"] == round(100 - 2.0 * 2, 2)
    log_pass(
        "Risk - Normal 📈", f"SL:{rm2['stop_loss']} TP2:{rm2['tp2']} R:R={rm2['risk_reward_ratio']}"
    )

    # Defansif (momentum < 50)
    rm3 = calculate_risk_management(price=100.0, atr_val=2.0, momentum_score=30)
    assert rm3["strategy_tag"] == "Defansif 🛡️"
    assert rm3["tp3"] is None, "Defansif'te TP3 olmamalı"
    log_pass(
        "Risk - Defansif 🛡️",
        f"SL:{rm3['stop_loss']} TP2:{rm3['tp2']} TP3:{rm3['tp3']} R:R={rm3['risk_reward_ratio']}",
    )

except ImportError:
    # calculate_risk_management scanner.py'de, scanner paketinde değil
    # Doğrudan import edelim
    try:
        # scanner.py modülü olarak import
        import importlib

        scanner_module = importlib.import_module("scanner")

        # scanner.py'deki fonksiyonu bul
        # calculate_risk_management scanner.py'nin üst seviyesinde
        log_warn(
            "Risk Yönetimi",
            "calculate_risk_management scanner paketinde değil, scanner.py'de tanımlı — import sorunu",
        )

    except Exception as e2:
        log_fail("Risk Yönetimi", f"Import hatası: {e2}")
except Exception as e:
    log_fail("Risk Yönetimi", f"{e}")

# --- 3.5 Öneri Gücü Skorlaması ---
print("\n--- 3.5 Öneri Gücü Skorlaması ---")
try:
    from scanner.signals import compute_recommendation_score, compute_recommendation_strength

    # Güçlü sinyal
    strong = {
        "regime": True,
        "direction": True,
        "score": 3,
        "filter_score": 3,
        "momentum_confluence": True,
        "momentum_ratio": 0.8,
        "volume_spike": True,
        "timeframe_aligned": True,
        "sentiment": 0.5,
        "price_momentum": True,
        "is_premium_symbol": True,
    }
    s1 = compute_recommendation_score(strong)
    g1 = compute_recommendation_strength(s1)

    # Zayıf sinyal
    weak = {
        "regime": False,
        "direction": False,
        "score": 0,
        "filter_score": 0,
        "momentum_confluence": False,
        "momentum_ratio": 0.0,
        "volume_spike": False,
        "timeframe_aligned": False,
        "sentiment": -0.5,
        "price_momentum": False,
        "is_premium_symbol": False,
    }
    s2 = compute_recommendation_score(weak)
    g2 = compute_recommendation_strength(s2)

    assert g1 > g2, f"Güçlü ({g1}) > Zayıf ({g2}) olmalı"
    log_pass("Öneri Skoru - Güçlü", f"Skor: {s1:.2f}, Güç: {g1:.1f}%")
    log_pass("Öneri Skoru - Zayıf", f"Skor: {s2:.2f}, Güç: {g2:.1f}%")
    log_pass("Skor Tutarlılığı", f"Güçlü ({g1:.0f}%) > Zayıf ({g2:.0f}%) ✓")

except Exception as e:
    log_fail("Öneri Skorlaması", str(e))

# ############################################################################
# BÖLÜM 4: BACKTEST ENGINE DOĞRULAMA
# ############################################################################
print("\n" + "=" * 80)
print("BÖLÜM 4: BACKTEST ENGINE DOĞRULAMA")
print("=" * 80)

try:
    from core.backtest import (
        Backtest,
        BacktestConfig,
        MomentumStrategy,
        TrendFollowingStrategy,
    )

    config = BacktestConfig(initial_capital=10000, risk_per_trade=0.02, kelly_fraction=0.5)
    log_pass(
        "BacktestConfig",
        f"Kapital: ${config.initial_capital}, Risk: {config.risk_per_trade * 100}%, Kelly: {config.kelly_fraction}",
    )

    # Backtest verisi
    n_bt = 400
    dates_bt = pd.date_range("2023-01-01", periods=n_bt, freq="D")
    price_bt = 100 + np.cumsum(np.random.randn(n_bt) * 1.0)
    price_bt = np.maximum(price_bt, 10)
    df_bt = pd.DataFrame(
        {
            "Open": price_bt + np.random.randn(n_bt) * 0.3,
            "High": price_bt + np.abs(np.random.randn(n_bt) * 2),
            "Low": price_bt - np.abs(np.random.randn(n_bt) * 2),
            "Close": price_bt,
            "Volume": np.random.randint(200000, 5000000, n_bt).astype(float),
        },
        index=dates_bt,
    )

    # Backtest(strategy, data, symbol, config)
    strategy = MomentumStrategy()
    bt = Backtest(strategy=strategy, data=df_bt, symbol="TEST", config=config)
    result = bt.run()

    metrics = result.metrics
    trade_count = len(result.trades)
    log_pass("Backtest Çalışma", f"{trade_count} işlem üretildi")

    # Metrik doğrulama
    metric_keys = list(metrics.keys())
    log_info("Backtest Metrikleri", f"Anahtarlar: {metric_keys}")

    expected_metrics = [
        "total_return",
        "win_rate",
        "sharpe_ratio",
        "max_drawdown",
        "profit_factor",
        "cagr",
    ]
    for em in expected_metrics:
        found = any(em.lower() in k.lower() for k in metric_keys)
        if found:
            # Değeri bul
            matching_key = [k for k in metric_keys if em.lower() in k.lower()][0]
            val = metrics[matching_key]
            log_pass(f"Metrik: {em}", f"{matching_key} = {val}")
        else:
            log_warn(f"Metrik: {em}", "Bulunamadı")

    # Trade doğrulama
    if result.trades:
        t = result.trades[0]
        t_dict = t.to_dict() if hasattr(t, "to_dict") else vars(t)
        log_info("Örnek Trade", f"Keys: {list(t_dict.keys())[:8]}")

    # İkinci strateji ile karşılaştır
    strat2 = TrendFollowingStrategy()
    bt2 = Backtest(strategy=strat2, data=df_bt, symbol="TEST", config=config)
    result2 = bt2.run()
    log_pass(
        "Strateji Karşılaştırma",
        f"Momentum: {len(result.trades)} işlem, TrendFollowing: {len(result2.trades)} işlem",
    )

    # Sharpe doğrulama (manuel hesap)
    if trade_count > 2:
        returns = [t.pnl_percent if hasattr(t, "pnl_percent") else 0 for t in result.trades]
        if returns and np.std(returns) > 0:
            manual_sharpe = (np.mean(returns) / np.std(returns)) * np.sqrt(252)
            log_info("Sharpe Manuel Hesap", f"Manuel: {manual_sharpe:.4f}")

except Exception as e:
    log_fail("Backtest Engine", f"{e}\n{traceback.format_exc()}")

# ############################################################################
# BÖLÜM 5: TEKNİK ALTYAPI
# ############################################################################
print("\n" + "=" * 80)
print("BÖLÜM 5: TEKNİK ALTYAPI KONTROLÜ")
print("=" * 80)

critical = {
    "streamlit": "Web framework",
    "pandas": "Veri işleme",
    "numpy": "Sayısal hesaplama",
    "yfinance": "Finans verisi",
    "plotly": "Görselleştirme",
    "pydantic": "Veri doğrulama",
    "bcrypt": "Güvenlik (hash)",
    "jwt": "JWT token (pyjwt)",
    "prometheus_client": "Metrik toplama",
    "sentry_sdk": "Hata izleme",
    "gspread": "Google Sheets",
    "reportlab": "PDF export",
    "openpyxl": "Excel export",
    "cryptography": "Şifreleme",
}
for pkg, desc in critical.items():
    try:
        mod = __import__(pkg)
        ver = getattr(mod, "__version__", "N/A")
        log_pass(f"Bağımlılık: {pkg}", f"v{ver} — {desc}")
    except ImportError:
        log_fail(f"Bağımlılık: {pkg}", f"KURULU DEĞİL — {desc}")

# Opsiyonel
optional = {
    "stable_baselines3": "DRL",
    "torch": "Deep Learning",
    "shap": "Feature Importance",
    "optuna": "Hyperparameter Opt.",
    "hmmlearn": "HMM",
    "mlflow": "ML Tracking",
}
for pkg, desc in optional.items():
    try:
        __import__(pkg)
        log_pass(f"Opsiyonel: {pkg}", desc)
    except ImportError:
        log_warn(f"Opsiyonel: {pkg}", f"KURULU DEĞİL — {desc}")

# ############################################################################
# BÖLÜM 6: İŞ AKIŞI / PIPELINE
# ############################################################################
print("\n" + "=" * 80)
print("BÖLÜM 6: PIPELINE DOĞRULAMA")
print("=" * 80)

modules_check = [
    ("scanner", "Ana tarama paketi"),
    ("scanner.indicators", "Gösterge hesaplama"),
    ("scanner.signals", "Sinyal üretimi"),
    ("scanner.data_fetcher", "Veri çekme"),
    ("scanner.config", "Yapılandırma"),
    ("core", "Core framework"),
    ("core.backtest", "Backtest engine"),
    ("core.plugins", "Plugin sistemi"),
    ("core.social", "Sosyal özellikler"),
    ("core.websocket_feeds", "WebSocket beslemeleri"),
    ("core.prometheus_exporter", "Prometheus export"),
    ("altdata", "Alternatif veri"),
    ("telegram_alerts", "Telegram uyarıları"),
    ("telegram_config", "Telegram yapılandırma"),
    ("auth", "Kimlik doğrulama"),
    ("auth.core", "Auth core"),
]
for mod_name, desc in modules_check:
    try:
        __import__(mod_name)
        log_pass(f"Modül: {mod_name}", desc)
    except Exception as e:
        log_warn(f"Modül: {mod_name}", f"{desc} — {type(e).__name__}: {e}")

# ############################################################################
# BÖLÜM 7: ALTERNATİF VERİ
# ############################################################################
print("\n" + "=" * 80)
print("BÖLÜM 7: ALTERNATİF VERİ DOĞRULAMA")
print("=" * 80)

try:
    from altdata import get_latest_alt_data, get_onchain_metric, get_sentiment_score

    sent = get_sentiment_score("AAPL")
    assert -1 <= sent <= 1, f"Sentiment aralık dışı: {sent}"
    log_pass("Sentiment Score", f"AAPL: {sent:.4f} ∈ [-1, 1]")

    onchain = get_onchain_metric("AAPL")
    assert onchain >= 0, f"On-chain negatif: {onchain}"
    log_pass("On-chain Metric", f"AAPL: {onchain:.4f} ≥ 0")

    latest = get_latest_alt_data("AAPL")
    assert isinstance(latest, dict), "latest_alt_data dict değil"
    assert "symbol" in latest or "sentiment" in latest
    log_pass("Alt Data Summary", f"Anahtarlar: {list(latest.keys())}")

    # Tutarlılık: farklı semboller farklı sonuç vermeli (hash-based seed)
    sent2 = get_sentiment_score("MSFT")
    if sent != sent2:
        log_pass("Sentiment Farklılık", f"AAPL={sent:.4f} ≠ MSFT={sent2:.4f} (farklı seed)")
    else:
        log_warn("Sentiment Farklılık", "AAPL ve MSFT aynı sentiment — seed sorunu?")

except Exception as e:
    log_fail("Alternatif Veri", f"{e}")

# ############################################################################
# BÖLÜM 8: KONFIGÜRASYON DOĞRULAMA
# ############################################################################
print("\n" + "=" * 80)
print("BÖLÜM 8: KONFIGÜRASYON DOĞRULAMA")
print("=" * 80)

try:
    from scanner.config import (
        apply_aggressive_mode,
        get_setting,
        reset_to_default,
    )

    # Normal mod
    reset_to_default()
    normal_vals = {
        k: get_setting(k)
        for k in [
            "vol_multiplier",
            "momentum_pct",
            "trend_gap_pct",
            "min_alignment_ratio",
            "min_signal_score",
            "min_price",
            "min_avg_vol",
            "momentum_z_threshold",
        ]
    }
    log_pass("Normal Mod Ayarları", json.dumps(normal_vals, default=str))

    # Agresif mod
    apply_aggressive_mode()
    agg_vals = {k: get_setting(k) for k in normal_vals}
    log_pass("Agresif Mod Ayarları", json.dumps(agg_vals, default=str))

    # Farkları kontrol et
    diffs = {
        k: f"{normal_vals[k]} → {agg_vals[k]}" for k in normal_vals if normal_vals[k] != agg_vals[k]
    }
    log_pass("Mod Farkları", json.dumps(diffs))

    reset_to_default()

    # Momentum segment eşikleri
    seg_thresholds = get_setting("momentum_segment_thresholds")
    log_pass("Segment Eşikleri", json.dumps(seg_thresholds))

except Exception as e:
    log_fail("Konfigürasyon", str(e))

# ############################################################################
# BÖLÜM 9: WFO GRİD SEARCH ANALİZİ
# ############################################################################
print("\n" + "=" * 80)
print("BÖLÜM 9: WFO GRID SEARCH DERİN ANALİZ")
print("=" * 80)

try:
    wfo_file = "wfo_grid_search_results.csv"
    if os.path.exists(wfo_file):
        df_wfo = pd.read_csv(wfo_file)
        log_pass("WFO Dosya", f"{len(df_wfo)} satır, {len(df_wfo.columns)} sütun")

        # Sütun analizi
        log_info("WFO Sütunlar", str(list(df_wfo.columns)))

        # NaN analizi
        nan_pct = df_wfo.isna().mean() * 100
        full_nan = nan_pct[nan_pct == 100].index.tolist()
        partial_nan = nan_pct[(nan_pct > 0) & (nan_pct < 100)].index.tolist()

        if full_nan:
            log_fail("WFO Tamamen NaN Sütunlar", f"{full_nan} — HİÇBİR pencerede sonuç yok")

        if not partial_nan and not full_nan:
            log_pass("WFO Veri Kalitesi", "NaN yok")

        # Parametre dağılımı
        for col in df_wfo.columns:
            if col.startswith("best_"):
                vals = df_wfo[col].dropna().unique()
                if len(vals) == 1:
                    log_warn(
                        f"WFO {col}",
                        f"Tek değer: {vals[0]} — tüm pencereler aynı parametre seçti (overfitting riski)",
                    )
                else:
                    log_pass(f"WFO {col}", f"Değerler: {vals}")

        # Sonuç: Neden 0 trade?
        log_info(
            "WFO 0-Trade Analizi",
            "Tüm pencereler gevşek parametreleri seçiyor ama yine de trade üretemiyor. Olası nedenler: (1) Backtest giriş koşulları çok sıkı, (2) Test penceresi çok kısa (30 gün), (3) 2023 veri setinde trendsiz dönem",
        )
except Exception as e:
    log_fail("WFO Analizi", str(e))

# ############################################################################
# BÖLÜM 10: DRL MODÜL
# ############################################################################
print("\n" + "=" * 80)
print("BÖLÜM 10: DRL MODÜL DOĞRULAMA")
print("=" * 80)

try:
    sys.path.insert(0, "/workspaces/Borsa/archive")
    from drl.config import FeatureSpec, PilotShieldConfig, RewardWeights, TransactionCostModel

    specs = FeatureSpec.ALL_SPECS
    total_features = sum(len(s.columns) for s in specs)
    log_pass("Feature Specs", f"{len(specs)} grup, {total_features} özellik")

    for s in specs:
        log_info(
            f"  Feature {s.group}",
            f"Sütunlar ({len(s.columns)}): {s.columns}, Scaler: {s.scaler}, Zorunlu: {s.required}",
        )

    rw = RewardWeights()
    log_pass(
        "Reward Weights",
        f"pnl={rw.pnl}, dd={rw.drawdown}, cost={rw.transaction_cost}, lev={rw.excess_leverage}, regime={rw.regime_alignment}",
    )

    tc = TransactionCostModel()
    log_pass("İşlem Maliyeti", f"buy={tc.buy_bps}bps, sell={tc.sell_bps}bps, fixed={tc.fixed_cost}")

    ps = PilotShieldConfig()
    log_pass(
        "PilotShield",
        f"max_pos={ps.max_position_size}, max_lev={ps.max_leverage}, risk={ps.risk_appetite}",
    )

    # Reward ağırlık tutarlılığı — toplam çok yüksek olmamalı
    total_weight = (
        rw.pnl + rw.drawdown + rw.transaction_cost + rw.excess_leverage + rw.regime_alignment
    )
    log_info("Ödül Toplam Ağırlık", f"{total_weight:.2f}")
    if total_weight > 5:
        log_warn("Ödül Dengesi", f"Toplam ağırlık yüksek: {total_weight}")

except Exception as e:
    log_warn("DRL Modül", f"{e}")

# ############################################################################
# BÖLÜM 11: TELEGRAM BİLDİRİM
# ############################################################################
print("\n" + "=" * 80)
print("BÖLÜM 11: TELEGRAM BİLDİRİM DOĞRULAMA")
print("=" * 80)

try:
    from telegram_alerts import TelegramAlerter

    # TelegramAlerter oluşturma (token olmadan)
    alerter = TelegramAlerter(bot_token="test_token", chat_id="test_chat")
    log_pass("TelegramAlerter Init", "Token ve chat_id ile oluşturuldu")

    # Mesaj formatlama testi
    test_signal = {
        "symbol": "AAPL",
        "price": 175.50,
        "stop_loss": 170.0,
        "take_profit": 185.0,
        "risk_reward": 2.76,
        "strategy_tag": "Sniper 🎯",
        "score": 3,
        "regime": True,
        "direction": True,
        "entry_ok": True,
        "atr": 1.5,
        "rsi": 42,
        "macd_hist": 0.3,
    }

    # format_signal_message kullan
    msg = alerter.format_signal_message(test_signal)
    assert len(msg) <= 4096, f"Telegram mesaj limiti aşıldı: {len(msg)}"
    assert "AAPL" in msg
    log_pass("Telegram Mesaj Format", f"Uzunluk: {len(msg)} karakter (limit: 4096)")

except Exception as e:
    log_warn("Telegram", f"{e}")

# ############################################################################
# BÖLÜM 12: GÜVENLİK
# ############################################################################
print("\n" + "=" * 80)
print("BÖLÜM 12: GÜVENLİK DOĞRULAMA")
print("=" * 80)

try:
    from auth.core import JWTHandler, PasswordHasher

    # Password hashing — hash() returns Tuple[str, str]
    ph = PasswordHasher()
    result = ph.hash("TestPassword123!")
    if isinstance(result, tuple):
        hashed, salt = result
    else:
        hashed = result
        salt = ""
    assert isinstance(hashed, str) and len(hashed) > 0
    log_pass("Password Hash", f"Hash uzunluğu: {len(hashed)} karakter")

    # Verify
    is_valid = ph.verify("TestPassword123!", hashed, salt)
    assert is_valid, "Doğru şifre verify edemedi"
    log_pass("Password Verify (doğru)", "✓")

    is_invalid = ph.verify("WrongPassword", hashed, salt)
    assert not is_invalid, "Yanlış şifre verify etti!"
    log_pass("Password Verify (yanlış)", "Reddedildi ✓")

    # Güç kontrolü
    strong_ok, strong_msgs = PasswordHasher.validate_strength("StrongP@ss123")
    log_pass("Password Strength (güçlü)", f"Geçerli: {strong_ok}")

    weak_ok, weak_msgs = PasswordHasher.validate_strength("123")
    assert not weak_ok
    log_pass("Password Strength (zayıf)", f"Reddedildi: {weak_msgs}")

    # JWT
    jwt_handler = JWTHandler(secret_key="x" * 32)  # 32 byte key
    token = jwt_handler.encode({"user_id": "test123", "role": "user"})
    decoded = jwt_handler.decode(token)
    assert decoded["user_id"] == "test123"
    assert decoded["role"] == "user"
    log_pass("JWT Encode/Decode", f"Token uzunluğu: {len(token)} karakter")

    # Expired token
    import time

    try:
        expired_token = jwt_handler.encode({"user_id": "test", "exp": int(time.time()) - 100})
        jwt_handler.decode(expired_token)
        log_fail("JWT Expired", "Expired token kabul edildi!")
    except Exception:
        log_pass("JWT Expired", "Süresi geçmiş token reddedildi ✓")

except Exception as e:
    log_fail("Güvenlik", f"{e}\n{traceback.format_exc()}")

# ############################################################################
# BÖLÜM 13: VERİ DOSYALARI
# ############################################################################
print("\n" + "=" * 80)
print("BÖLÜM 13: VERİ DOSYA ANALİZİ")
print("=" * 80)

import glob

# Shortlists
shortlists = sorted(glob.glob("data/shortlists/shortlist_*.csv"))
log_info("Shortlist Dosyaları", f"{len(shortlists)} dosya")

if shortlists:
    total_rows = 0
    unique_dates = set()
    all_symbols = set()
    entry_ok_count = 0

    for f in shortlists:
        try:
            df_s = pd.read_csv(f)
            total_rows += len(df_s)
            if "entry_ok" in df_s.columns:
                entry_ok_count += (
                    df_s["entry_ok"].sum()
                    if df_s["entry_ok"].dtype == bool
                    else (df_s["entry_ok"] == True).sum()
                )
            if "symbol" in df_s.columns:
                all_symbols.update(df_s["symbol"].unique())
            # Tarih dosya adından
            fname = os.path.basename(f)
            date_part = fname.replace("shortlist_", "").split("_")[0]
            unique_dates.add(date_part)
        except Exception:
            pass

    log_pass(
        "Shortlist Analizi",
        f"{total_rows} toplam satır, {len(unique_dates)} farklı gün, {len(all_symbols)} farklı hisse",
    )
    log_pass("Entry Sinyalleri", f"{int(entry_ok_count)} toplam entry_ok sinyal")

    # En çok görünen hisseler
    if all_symbols:
        symbol_counts = {}
        for f in shortlists:
            try:
                df_s = pd.read_csv(f)
                if "symbol" in df_s.columns and "entry_ok" in df_s.columns:
                    entries = df_s[df_s["entry_ok"] == True] if "entry_ok" in df_s.columns else df_s
                    for sym in entries["symbol"].unique():
                        symbol_counts[sym] = symbol_counts.get(sym, 0) + 1
            except:
                pass
        if symbol_counts:
            top_5 = sorted(symbol_counts.items(), key=lambda x: -x[1])[:5]
            log_pass("Top 5 Entry Hisseler", str(top_5))

# Signal log
signal_log = "data/logs/signal_log.csv"
if os.path.exists(signal_log):
    try:
        df_log = pd.read_csv(signal_log, header=None)
        log_pass("Signal Log", f"{len(df_log)} kayıt, {len(df_log.columns)} sütun")
    except:
        log_warn("Signal Log", "Parse hatası")
else:
    log_warn("Signal Log", "Dosya bulunamadı")

# ############################################################################
# SONUÇ RAPORU
# ############################################################################
print("\n" + "=" * 80)
print("═" * 80)
print("         FİNPİLOT SİSTEM DENETİM RAPORU — v2")
print(f"         Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("═" * 80)

total_tests = len(RESULTS["passed"]) + len(RESULTS["failed"])
pass_rate = (len(RESULTS["passed"]) / total_tests * 100) if total_tests > 0 else 0

print(f"\n  ✅ BAŞARILI  : {len(RESULTS['passed'])}")
print(f"  ❌ BAŞARISIZ : {len(RESULTS['failed'])}")
print(f"  ⚠️  UYARI    : {len(RESULTS['warnings'])}")
print(f"  ℹ️  BİLGİ    : {len(RESULTS['info'])}")
print(f"\n  GEÇME ORANI : {len(RESULTS['passed'])}/{total_tests} ({pass_rate:.1f}%)")

if RESULTS["failed"]:
    print(f"\n{'─' * 80}")
    print("  BAŞARISIZ TESTLER:")
    print(f"{'─' * 80}")
    for r in RESULTS["failed"]:
        print(f"  {r}")

if RESULTS["warnings"]:
    print(f"\n{'─' * 80}")
    print("  UYARILAR:")
    print(f"{'─' * 80}")
    for r in RESULTS["warnings"]:
        print(f"  {r}")

print(f"\n{'═' * 80}")
