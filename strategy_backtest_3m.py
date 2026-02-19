#!/usr/bin/env python3
"""
FinPilot — 3 Aylık Strateji Backtest Raporu
============================================
Tüm hisseleri son 3 aylık veriyle tarıyor, sinyal üretiyor,
simüle edilmiş alım-satım işlemleri yapıyor ve detaylı rapor çıkarıyor.
"""

import json
import os
import warnings
from datetime import datetime, timedelta
from typing import Any

warnings.filterwarnings("ignore")
os.chdir("/workspaces/Borsa")

# calculate_risk_management scanner.py (dosya) içinde, scanner/ (paket) içinde değil
import importlib.util

import numpy as np
import pandas as pd
import yfinance as yf
from scanner.indicators import add_indicators
from scanner.signals import (
    analyze_price_momentum,
    check_price_momentum,
    check_trend_strength,
    check_volume_spike,
    compute_recommendation_score,
    compute_recommendation_strength,
    signal_score_row,
)

_spec = importlib.util.spec_from_file_location("scanner_module", "/workspaces/Borsa/scanner.py")
_scanner_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_scanner_mod)
calculate_risk_management = _scanner_mod.calculate_risk_management

# ───────────────────────────────────────────────────────────────────────
# KONFİGÜRASYON
# ───────────────────────────────────────────────────────────────────────
INITIAL_CAPITAL = 100_000  # $100K başlangıç
RISK_PER_TRADE = 0.02  # İşlem başına %2 risk
MAX_CONCURRENT = 5  # Aynı anda max 5 pozisyon
COMMISSION_BPS = 5  # 5 bps komisyon (alım + satım)
LOOKBACK_DAYS = 400  # EMA200 için yeterli veri
TEST_PERIOD_DAYS = 90  # Son 3 ay test dönemi

# 200 hisselik genişletilmiş liste
SYMBOLS = [
    # ── Mega-Cap Tech ──
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "META",
    "NVDA",
    "TSLA",
    "AVGO",
    "ORCL",
    "ADBE",
    "CRM",
    "AMD",
    "INTC",
    "QCOM",
    "TXN",
    "NFLX",
    "SHOP",
    "SNOW",
    "PANW",
    "PLTR",
    "NOW",
    "UBER",
    "SQ",
    "PYPL",
    "MU",
    "ANET",
    "SNPS",
    "CDNS",
    "MRVL",
    "KLAC",
    "LRCX",
    "CRWD",
    "DDOG",
    "ZS",
    "FTNT",
    "NET",
    "WDAY",
    "TEAM",
    "HUBS",
    "BILL",
    # ── Finans ──
    "JPM",
    "GS",
    "MS",
    "BAC",
    "WFC",
    "C",
    "BLK",
    "SCHW",
    "AXP",
    "V",
    "MA",
    "COF",
    "USB",
    "PNC",
    "TFC",
    "BK",
    "CME",
    "ICE",
    "MCO",
    "SPGI",
    # ── Sağlık ──
    "UNH",
    "JNJ",
    "LLY",
    "PFE",
    "ABBV",
    "MRK",
    "TMO",
    "ABT",
    "DHR",
    "BMY",
    "AMGN",
    "GILD",
    "VRTX",
    "REGN",
    "ISRG",
    "MDT",
    "SYK",
    "BSX",
    "EW",
    "ZTS",
    # ── Tüketici ──
    "WMT",
    "COST",
    "HD",
    "LOW",
    "TGT",
    "SBUX",
    "MCD",
    "NKE",
    "LULU",
    "TJX",
    "PEP",
    "KO",
    "PG",
    "CL",
    "EL",
    "MNST",
    "KHC",
    "GIS",
    "HSY",
    "KDP",
    # ── Enerji ──
    "XOM",
    "CVX",
    "COP",
    "SLB",
    "EOG",
    "PXD",
    "MPC",
    "VLO",
    "PSX",
    "OXY",
    # ── Sanayi / Savunma ──
    "BA",
    "LMT",
    "RTX",
    "GE",
    "HON",
    "CAT",
    "DE",
    "UNP",
    "UPS",
    "FDX",
    "MMM",
    "EMR",
    "ETN",
    "ITW",
    "PH",
    "GD",
    "NOC",
    "LHX",
    "TDG",
    "WM",
    # ── Telekom / Medya ──
    "DIS",
    "CMCSA",
    "T",
    "VZ",
    "TMUS",
    "CHTR",
    # ── Gayrimenkul ──
    "AMT",
    "PLD",
    "CCI",
    "EQIX",
    "SPG",
    "O",
    # ── Malzeme ──
    "LIN",
    "APD",
    "SHW",
    "ECL",
    "DD",
    "NEM",
    # ── ETF'ler ──
    "SPY",
    "QQQ",
    "XLK",
    "XLI",
    "SMH",
    "XLE",
    "XLF",
    "XLV",
    "XLP",
    "ARKK",
    "IWM",
    "DIA",
    "SOXX",
    "XBI",
    # ── Mevcut sinyallerden ──
    "CVS",
    "ATAI",
    "BETR",
    "TNGX",
    "WINA",
    # ── Ek büyüme / değer hisseleri ──
    "ABNB",
    "DASH",
    "RIVN",
    "LCID",
    "COIN",
    "MELI",
    "SE",
    "BABA",
    "JD",
    "PDD",
    "ARM",
    "SMCI",
    "DELL",
    "HPE",
    "IBM",
    "CSCO",
    "INTU",
    "FISV",
    "FIS",
    "ADP",
    "SPOT",
    "ZM",
    "OKTA",
    "TWLO",
    "MDB",
    "VEEV",
    "PAYC",
    "PCTY",
    "TTD",
    "RBLX",
    "ENPH",
    "FSLR",
    "ON",
]

print("=" * 90)
print("  FinPilot — 3 Aylık Strateji Backtest ve Sinyal Analizi")
print(f"  Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print(f"  Sermaye: ${INITIAL_CAPITAL:,.0f} | Risk/trade: {RISK_PER_TRADE * 100}%")
print(f"  Hisse sayısı: {len(SYMBOLS)} | Test dönemi: Son {TEST_PERIOD_DAYS} gün")
print("=" * 90)

# ───────────────────────────────────────────────────────────────────────
# ADIM 1: VERİ ÇEKİMİ
# ───────────────────────────────────────────────────────────────────────
print("\n📥 Adım 1: Veri çekiliyor...")

data_cache: dict[str, pd.DataFrame] = {}
failed_symbols = []
end_date = datetime.now()
start_date = end_date - timedelta(days=LOOKBACK_DAYS)

# Toplu çekim (yfinance batch)
try:
    tickers_str = " ".join(SYMBOLS)
    print(f"   {len(SYMBOLS)} hisse için {LOOKBACK_DAYS} günlük veri indiriliyor...")
    raw_data = yf.download(
        tickers_str,
        start=start_date.strftime("%Y-%m-%d"),
        end=end_date.strftime("%Y-%m-%d"),
        interval="1d",
        group_by="ticker",
        progress=False,
        threads=True,
    )
    print(f"   Ham veri boyutu: {raw_data.shape}")

    for symbol in SYMBOLS:
        try:
            if len(SYMBOLS) == 1:
                df_sym = raw_data.copy()
            else:
                df_sym = raw_data[symbol].copy()

            df_sym = df_sym.dropna(subset=["Close"])
            if len(df_sym) >= 200:
                data_cache[symbol] = df_sym
            else:
                failed_symbols.append((symbol, f"Yetersiz veri: {len(df_sym)} gün"))
        except Exception as e:
            failed_symbols.append((symbol, str(e)[:50]))

except Exception as e:
    print(f"   ❌ Toplu çekim başarısız: {e}")
    # Tek tek dene
    for symbol in SYMBOLS:
        try:
            df_sym = yf.download(
                symbol, start=start_date, end=end_date, interval="1d", progress=False
            )
            df_sym = df_sym.dropna(subset=["Close"])
            if len(df_sym) >= 200:
                data_cache[symbol] = df_sym
            else:
                failed_symbols.append((symbol, f"Yetersiz: {len(df_sym)}"))
        except Exception as e2:
            failed_symbols.append((symbol, str(e2)[:50]))

print(f"   ✅ Başarılı: {len(data_cache)} hisse | ❌ Başarısız: {len(failed_symbols)}")
if failed_symbols:
    for sym, reason in failed_symbols[:5]:
        print(f"      ⚠️  {sym}: {reason}")
    if len(failed_symbols) > 5:
        print(f"      ... ve {len(failed_symbols) - 5} hisse daha")

# ───────────────────────────────────────────────────────────────────────
# ADIM 2: GÖSTERGELERİ HESAPLA VE GÜN GÜN TARA
# ───────────────────────────────────────────────────────────────────────
print("\n📊 Adım 2: Göstergeler hesaplanıyor ve her gün taranıyor...")

# Her hisse için göstergeleri hesapla
indicator_cache: dict[str, pd.DataFrame] = {}
for symbol, df in data_cache.items():
    try:
        df_ind = add_indicators(df)
        if len(df_ind) > 0 and "rsi" in df_ind.columns:
            indicator_cache[symbol] = df_ind
    except Exception as e:
        print(f"   ⚠️  {symbol} gösterge hatası: {e}")

print(f"   ✅ {len(indicator_cache)} hisse için göstergeler hesaplandı")

# Test dönemi başlangıcını belirle
test_start = end_date - timedelta(days=TEST_PERIOD_DAYS)

# Her gün, her hisse için sinyal tara
all_signals: list[dict[str, Any]] = []
daily_scans: dict[str, dict] = {}

for symbol, df_ind in indicator_cache.items():
    # Son 3 aydaki günleri filtrele
    test_dates = df_ind.index[df_ind.index >= pd.Timestamp(test_start)]

    for i, date in enumerate(test_dates):
        # O güne kadar olan veriyi al (look-ahead bias yok)
        idx = df_ind.index.get_loc(date)
        if idx < 200:  # EMA200 için yeterli veri gerekli
            continue

        df_slice = df_ind.iloc[: idx + 1]

        try:
            # Fiyat ve göstergeler
            row = df_slice.iloc[-1]
            close = float(row["Close"])
            rsi_val = float(row["rsi"]) if pd.notna(row["rsi"]) else 50
            macd_val = float(row["macd_hist"]) if pd.notna(row["macd_hist"]) else 0
            atr_val = float(row["atr"]) if pd.notna(row["atr"]) else close * 0.02
            ema50_val = float(row["ema50"]) if pd.notna(row["ema50"]) else close
            ema200_val = float(row["ema200"]) if pd.notna(row["ema200"]) else close

            # Stage 1: Trend Filter
            regime = close > ema200_val
            direction = close > ema50_val

            # Stage 2: Sinyal Skoru (signal_score_row kullanarak)
            score = signal_score_row(df_slice)

            # Stage 3: Güç Filtreleri
            volume_spike = check_volume_spike(df_slice)
            price_momentum_ok = check_price_momentum(df_slice)
            trend_strength = check_trend_strength(df_slice)
            filter_score = int(volume_spike) + int(price_momentum_ok) + int(trend_strength)

            # Stage 4: Momentum Analizi
            momentum_analysis = analyze_price_momentum(df_slice)
            momentum_positive = momentum_analysis.get("positive", False)

            # Momentum Score (0-100)
            rsi_score = max(0, min(100, (rsi_val - 30) / 70 * 100))
            macd_score_val = 100 if macd_val > 0 else 0
            trend_score_val = 100 if direction else 0
            momentum_score = int(
                (rsi_score * 0.4) + (macd_score_val * 0.3) + (trend_score_val * 0.3)
            )

            # Entry kararı (evaluate_symbol mantığı)
            core_signal = regime and direction and (score >= 2)
            mtf_ok = True  # Tek timeframe test, alignment varsay

            if core_signal:
                if score == 3 or score == 4 or score == 2 and mtf_ok:
                    entry_ok = True
                else:
                    entry_ok = False
            else:
                entry_ok = False

            # Likidite filtresi
            min_price = 5.0
            min_avg_vol = 300_000
            avg_vol = float(row["vol_avg10"]) if pd.notna(row.get("vol_avg10")) else 0
            price_ok = close >= min_price
            vol_ok = avg_vol >= min_avg_vol
            entry_ok = entry_ok and price_ok and vol_ok

            # Risk yönetimi
            risk_data = calculate_risk_management(
                price=close, atr_val=atr_val, momentum_score=momentum_score
            )

            # Öneri skoru
            reco_data = {
                "regime": regime,
                "direction": direction,
                "score": score,
                "filter_score": filter_score,
                "momentum_confluence": momentum_positive,
                "momentum_ratio": momentum_analysis.get("dominant_return_pct", 0) / 100,
                "volume_spike": volume_spike,
                "price_momentum": price_momentum_ok,
                "trend_strength": trend_strength,
                "is_premium_symbol": symbol in ["SPY", "QQQ", "GOOGL", "NVDA", "AAPL", "MSFT"],
            }
            reco_score = compute_recommendation_score(reco_data)
            reco_strength = compute_recommendation_strength(reco_score)

            signal = {
                "date": date.strftime("%Y-%m-%d"),
                "symbol": symbol,
                "close": close,
                "rsi": round(rsi_val, 2),
                "macd_hist": round(macd_val, 4),
                "atr": round(atr_val, 4),
                "ema50": round(ema50_val, 2),
                "ema200": round(ema200_val, 2),
                "regime": regime,
                "direction": direction,
                "score": score,
                "filter_score": filter_score,
                "volume_spike": volume_spike,
                "price_momentum": price_momentum_ok,
                "trend_strength": trend_strength,
                "momentum_score": momentum_score,
                "entry_ok": entry_ok,
                "strategy_tag": risk_data["strategy_tag"],
                "stop_loss": risk_data["stop_loss"],
                "take_profit": risk_data["take_profit"],
                "tp1": risk_data["tp1"],
                "tp2": risk_data["tp2"],
                "tp3": risk_data["tp3"],
                "risk_reward": risk_data["risk_reward_ratio"],
                "stop_loss_pct": risk_data["stop_loss_percent"],
                "reco_score": reco_score,
                "reco_strength": reco_strength,
            }
            all_signals.append(signal)

        except Exception:
            continue

print(f"   ✅ {len(all_signals)} toplam sinyal üretildi (tüm günler × tüm hisseler)")

# ───────────────────────────────────────────────────────────────────────
# ADIM 3: SİNYAL ANALİZİ
# ───────────────────────────────────────────────────────────────────────
print("\n🔍 Adım 3: Sinyal analizi...")

df_signals = pd.DataFrame(all_signals)

# Temel istatistikler
total_scans = len(df_signals)
entry_signals = df_signals[df_signals["entry_ok"] == True]
no_entry = df_signals[df_signals["entry_ok"] == False]

# Regime ve Direction dağılımı
regime_true = (df_signals["regime"] == True).sum()
direction_true = (df_signals["direction"] == True).sum()
score_ge2 = (df_signals["score"] >= 2).sum()
score_ge3 = (df_signals["score"] >= 3).sum()

print(f"""
   ┌─────────────────────────────────────────────────────────┐
   │              SİNYAL İSTATİSTİKLERİ                      │
   ├─────────────────────────────────────────────────────────┤
   │  Toplam tarama          : {total_scans:>8,}                       │
   │  Rejim (Close > EMA200) : {regime_true:>8,} ({regime_true / total_scans * 100:5.1f}%)          │
   │  Yön   (Close > EMA50)  : {direction_true:>8,} ({direction_true / total_scans * 100:5.1f}%)          │
   │  Sinyal Skoru ≥ 2       : {score_ge2:>8,} ({score_ge2 / total_scans * 100:5.1f}%)          │
   │  Sinyal Skoru ≥ 3       : {score_ge3:>8,} ({score_ge3 / total_scans * 100:5.1f}%)          │
   │  ─────────────────────────────────────────────────      │
   │  ✅ Entry Sinyali        : {len(entry_signals):>8,} ({len(entry_signals) / total_scans * 100:5.1f}%)          │
   │  ❌ Giriş Yok            : {len(no_entry):>8,} ({len(no_entry) / total_scans * 100:5.1f}%)          │
   └─────────────────────────────────────────────────────────┘
""")

# Strateji dağılımı
if len(entry_signals) > 0:
    strat_dist = entry_signals["strategy_tag"].value_counts()
    print("   Strateji Dağılımı (Entry sinyalleri):")
    for tag, cnt in strat_dist.items():
        print(f"     {tag}: {cnt} sinyal ({cnt / len(entry_signals) * 100:.1f}%)")

    # Hisse bazlı entry dağılımı
    sym_entries = entry_signals["symbol"].value_counts()
    print("\n   Hisse Bazlı Entry Sinyalleri (top 15):")
    for sym, cnt in sym_entries.head(15).items():
        print(f"     {sym:8s}: {'█' * min(cnt, 50)} {cnt}")

    # Günlük dağılım
    daily_entries = entry_signals.groupby("date").size()
    print("\n   Günlük Entry Dağılımı:")
    print(f"     Toplam gün: {len(daily_entries)}")
    print(f"     Ort. sinyal/gün: {daily_entries.mean():.1f}")
    print(f"     Max sinyal/gün: {daily_entries.max()} ({daily_entries.idxmax()})")
    print(f"     Min sinyal/gün: {daily_entries.min()}")
else:
    print("   ⚠️  Hiç entry sinyali bulunamadı!")

# ───────────────────────────────────────────────────────────────────────
# ADIM 4: TRADE SİMÜLASYONU (Paper Trading)
# ───────────────────────────────────────────────────────────────────────
print("\n💰 Adım 4: Trade simülasyonu çalıştırılıyor...")


class TradeSimulator:
    """ATR tabanlı alım-satım simülasyonu."""

    def __init__(
        self,
        initial_capital: float,
        risk_per_trade: float,
        max_concurrent: int,
        commission_bps: float,
    ):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.max_concurrent = max_concurrent
        self.commission_rate = commission_bps / 10000
        self.open_positions: dict[str, dict] = {}
        self.closed_trades: list[dict] = []
        self.equity_curve: list[dict] = []
        self.peak_capital = initial_capital
        self.max_drawdown = 0.0

    def calculate_position_size(self, price: float, stop_loss: float) -> int:
        """Risk bazlı pozisyon büyüklüğü hesapla."""
        risk_amount = self.capital * self.risk_per_trade
        risk_per_share = abs(price - stop_loss)
        if risk_per_share <= 0:
            return 0
        shares = int(risk_amount / risk_per_share)
        # Sermayenin %20'sinden fazlasını tek pozisyona koyma
        max_by_capital = int((self.capital * 0.20) / price)
        return min(shares, max_by_capital, 500)  # Max 500 hisse

    def open_trade(self, signal: dict, date: str):
        """Pozisyon aç."""
        symbol = signal["symbol"]

        if symbol in self.open_positions:
            return None
        if len(self.open_positions) >= self.max_concurrent:
            return None

        price = signal["close"]
        stop_loss = signal["stop_loss"]
        take_profit = signal["take_profit"]
        tp1 = signal["tp1"]
        tp2 = signal["tp2"]
        tp3 = signal["tp3"]

        shares = self.calculate_position_size(price, stop_loss)
        if shares <= 0:
            return None

        cost = price * shares
        commission = cost * self.commission_rate
        total_cost = cost + commission

        if total_cost > self.capital:
            shares = int((self.capital * 0.95) / (price * (1 + self.commission_rate)))
            if shares <= 0:
                return None
            cost = price * shares
            commission = cost * self.commission_rate
            total_cost = cost + commission

        self.capital -= total_cost

        trade = {
            "symbol": symbol,
            "entry_date": date,
            "entry_price": price,
            "shares": shares,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "tp1": tp1,
            "tp2": tp2,
            "tp3": tp3,
            "strategy": signal["strategy_tag"],
            "entry_commission": commission,
            "entry_rsi": signal["rsi"],
            "entry_score": signal["score"],
            "entry_reco_strength": signal["reco_strength"],
            "tp1_hit": False,
            "tp2_hit": False,
        }
        self.open_positions[symbol] = trade
        return trade

    def check_exits(self, symbol: str, high: float, low: float, close: float, date: str):
        """Stop-loss ve take-profit kontrolü."""
        if symbol not in self.open_positions:
            return None

        trade = self.open_positions[symbol]
        exit_price = None
        exit_reason = None

        # Stop-loss check (gün içi low ile)
        if low <= trade["stop_loss"]:
            exit_price = trade["stop_loss"]
            exit_reason = "Stop-Loss 🛑"
        # TP1 check
        elif high >= trade["tp1"] and not trade["tp1_hit"]:
            trade["tp1_hit"] = True
            # TP1'de pozisyonun %30'unu kapat
            partial_shares = max(1, int(trade["shares"] * 0.30))
            partial_revenue = partial_shares * trade["tp1"]
            partial_commission = partial_revenue * self.commission_rate
            self.capital += partial_revenue - partial_commission

            partial_pnl = (
                (trade["tp1"] - trade["entry_price"]) * partial_shares
                - partial_commission
                - (trade["entry_commission"] * partial_shares / trade["shares"])
            )
            self.closed_trades.append(
                {
                    "symbol": symbol,
                    "entry_date": trade["entry_date"],
                    "exit_date": date,
                    "entry_price": trade["entry_price"],
                    "exit_price": trade["tp1"],
                    "shares": partial_shares,
                    "pnl": round(partial_pnl, 2),
                    "exit_reason": "TP1 Partial (30%) 🎯",
                    "strategy": trade["strategy"],
                    "pnl_pct": round((trade["tp1"] / trade["entry_price"] - 1) * 100, 2),
                    "holding_days": (pd.Timestamp(date) - pd.Timestamp(trade["entry_date"])).days,
                }
            )
            trade["shares"] -= partial_shares

        # TP2 check
        elif high >= trade["tp2"] and trade["tp1_hit"] and not trade["tp2_hit"]:
            trade["tp2_hit"] = True
            # TP2'de kalan pozisyonun %50'sini kapat
            partial_shares = max(1, int(trade["shares"] * 0.50))
            partial_revenue = partial_shares * trade["tp2"]
            partial_commission = partial_revenue * self.commission_rate
            self.capital += partial_revenue - partial_commission

            partial_pnl = (
                trade["tp2"] - trade["entry_price"]
            ) * partial_shares - partial_commission
            self.closed_trades.append(
                {
                    "symbol": symbol,
                    "entry_date": trade["entry_date"],
                    "exit_date": date,
                    "entry_price": trade["entry_price"],
                    "exit_price": trade["tp2"],
                    "shares": partial_shares,
                    "pnl": round(partial_pnl, 2),
                    "exit_reason": "TP2 Partial (50%) 🎯🎯",
                    "strategy": trade["strategy"],
                    "pnl_pct": round((trade["tp2"] / trade["entry_price"] - 1) * 100, 2),
                    "holding_days": (pd.Timestamp(date) - pd.Timestamp(trade["entry_date"])).days,
                }
            )
            trade["shares"] -= partial_shares

        # TP3 check (kalan pozisyon)
        elif trade.get("tp3") and high >= trade["tp3"] and trade["tp2_hit"]:
            exit_price = trade["tp3"]
            exit_reason = "TP3 Full Exit 🎯🎯🎯"

        # Tam çıkış
        if exit_price and exit_reason:
            remaining_shares = trade["shares"]
            revenue = remaining_shares * exit_price
            commission = revenue * self.commission_rate
            self.capital += revenue - commission

            entry_comm_remaining = (
                trade["entry_commission"] * remaining_shares / max(1, trade["shares"])
            )
            pnl = (
                (exit_price - trade["entry_price"]) * remaining_shares
                - commission
                - entry_comm_remaining
            )
            self.closed_trades.append(
                {
                    "symbol": symbol,
                    "entry_date": trade["entry_date"],
                    "exit_date": date,
                    "entry_price": trade["entry_price"],
                    "exit_price": exit_price,
                    "shares": remaining_shares,
                    "pnl": round(pnl, 2),
                    "exit_reason": exit_reason,
                    "strategy": trade["strategy"],
                    "pnl_pct": round((exit_price / trade["entry_price"] - 1) * 100, 2),
                    "holding_days": (pd.Timestamp(date) - pd.Timestamp(trade["entry_date"])).days,
                }
            )
            del self.open_positions[symbol]
            return exit_reason

        return None

    def update_equity(self, date: str, prices: dict[str, float]):
        """Günlük equity hesapla."""
        unrealized = sum(
            (prices.get(sym, t["entry_price"]) - t["entry_price"]) * t["shares"]
            for sym, t in self.open_positions.items()
        )
        equity = (
            self.capital
            + unrealized
            + sum(t["entry_price"] * t["shares"] for t in self.open_positions.values())
        )
        self.equity_curve.append(
            {"date": date, "equity": equity, "open_positions": len(self.open_positions)}
        )

        if equity > self.peak_capital:
            self.peak_capital = equity
        dd = (self.peak_capital - equity) / self.peak_capital * 100
        if dd > self.max_drawdown:
            self.max_drawdown = dd


# Simülasyon çalıştır
sim = TradeSimulator(INITIAL_CAPITAL, RISK_PER_TRADE, MAX_CONCURRENT, COMMISSION_BPS)

# Tüm günleri sırala
if len(entry_signals) > 0:
    all_dates = sorted(df_signals["date"].unique())
    test_dates = [d for d in all_dates if d >= test_start.strftime("%Y-%m-%d")]

    trades_opened = 0
    trades_skipped_capital = 0
    trades_skipped_max_pos = 0

    for date in test_dates:
        # 1. Mevcut pozisyonları kontrol et (stop/TP)
        for symbol in list(sim.open_positions.keys()):
            if symbol in indicator_cache:
                df_sym = indicator_cache[symbol]
                date_ts = pd.Timestamp(date)
                if date_ts in df_sym.index:
                    row = df_sym.loc[date_ts]
                    h = float(row["High"]) if pd.notna(row["High"]) else float(row["Close"])
                    l = float(row["Low"]) if pd.notna(row["Low"]) else float(row["Close"])
                    c = float(row["Close"])
                    sim.check_exits(symbol, h, l, c, date)

        # 2. Yeni entry sinyallerini işle
        day_entries = entry_signals[entry_signals["date"] == date].sort_values(
            "reco_strength", ascending=False
        )

        for _, signal in day_entries.iterrows():
            result = sim.open_trade(signal.to_dict(), date)
            if result:
                trades_opened += 1
            elif signal["symbol"] in sim.open_positions:
                pass  # Zaten pozisyon var
            elif len(sim.open_positions) >= MAX_CONCURRENT:
                trades_skipped_max_pos += 1
            else:
                trades_skipped_capital += 1

        # 3. Equity güncelle
        day_prices = {}
        for symbol in sim.open_positions:
            if symbol in indicator_cache:
                df_sym = indicator_cache[symbol]
                date_ts = pd.Timestamp(date)
                if date_ts in df_sym.index:
                    day_prices[symbol] = float(df_sym.loc[date_ts, "Close"])
        sim.update_equity(date, day_prices)

    # Son gün açık pozisyonları market fiyatından kapat
    for symbol in list(sim.open_positions.keys()):
        if symbol in indicator_cache:
            df_sym = indicator_cache[symbol]
            last_close = float(df_sym["Close"].iloc[-1])
            last_date = df_sym.index[-1].strftime("%Y-%m-%d")
            trade = sim.open_positions[symbol]
            remaining = trade["shares"]
            revenue = remaining * last_close
            commission = revenue * sim.commission_rate
            sim.capital += revenue - commission
            pnl = (last_close - trade["entry_price"]) * remaining - commission
            sim.closed_trades.append(
                {
                    "symbol": symbol,
                    "entry_date": trade["entry_date"],
                    "exit_date": last_date,
                    "entry_price": trade["entry_price"],
                    "exit_price": last_close,
                    "shares": remaining,
                    "pnl": round(pnl, 2),
                    "exit_reason": "Dönem Sonu Kapatma 📅",
                    "strategy": trade["strategy"],
                    "pnl_pct": round((last_close / trade["entry_price"] - 1) * 100, 2),
                    "holding_days": (
                        pd.Timestamp(last_date) - pd.Timestamp(trade["entry_date"])
                    ).days,
                }
            )
        del sim.open_positions[symbol]

# ───────────────────────────────────────────────────────────────────────
# ADIM 5: SONUÇ RAPORU
# ───────────────────────────────────────────────────────────────────────
print("\n📋 Adım 5: Sonuç raporu oluşturuluyor...\n")

df_trades = pd.DataFrame(sim.closed_trades) if sim.closed_trades else pd.DataFrame()
df_equity = pd.DataFrame(sim.equity_curve) if sim.equity_curve else pd.DataFrame()

total_trades = len(df_trades)
winning_trades = len(df_trades[df_trades["pnl"] > 0]) if total_trades > 0 else 0
losing_trades = len(df_trades[df_trades["pnl"] < 0]) if total_trades > 0 else 0
breakeven_trades = len(df_trades[df_trades["pnl"] == 0]) if total_trades > 0 else 0

total_pnl = df_trades["pnl"].sum() if total_trades > 0 else 0
avg_pnl = df_trades["pnl"].mean() if total_trades > 0 else 0
total_return_pct = (total_pnl / INITIAL_CAPITAL * 100) if total_trades > 0 else 0

win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
avg_win = df_trades[df_trades["pnl"] > 0]["pnl"].mean() if winning_trades > 0 else 0
avg_loss = df_trades[df_trades["pnl"] < 0]["pnl"].mean() if losing_trades > 0 else 0
profit_factor = (
    abs(df_trades[df_trades["pnl"] > 0]["pnl"].sum() / df_trades[df_trades["pnl"] < 0]["pnl"].sum())
    if losing_trades > 0 and df_trades[df_trades["pnl"] < 0]["pnl"].sum() != 0
    else float("inf")
    if winning_trades > 0
    else 0
)

avg_holding = df_trades["holding_days"].mean() if total_trades > 0 else 0
max_holding = df_trades["holding_days"].max() if total_trades > 0 else 0
min_holding = df_trades["holding_days"].min() if total_trades > 0 else 0

final_capital = sim.capital
max_dd = sim.max_drawdown

# Sharpe (günlük equity getirilerinden)
if len(df_equity) > 1:
    eq = pd.Series([e["equity"] for e in sim.equity_curve])
    daily_returns = eq.pct_change().dropna()
    sharpe = (
        (daily_returns.mean() / daily_returns.std() * np.sqrt(252))
        if daily_returns.std() > 0
        else 0
    )
else:
    sharpe = 0

print("═" * 90)
print("  FinPilot — 3 AYLIK STRATEJİ BACKTEST SONUÇ RAPORU")
print(f"  Rapor tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print("═" * 90)

print(f"""
  ┌──────────────────────────── PORTFÖY PERFORMANSI ─────────────────────────────┐
  │                                                                              │
  │  Başlangıç Sermayesi : ${INITIAL_CAPITAL:>12,.2f}                                     │
  │  Bitiş Sermayesi     : ${final_capital:>12,.2f}                                     │
  │  Toplam Kâr/Zarar    : ${total_pnl:>+12,.2f} ({total_return_pct:+.2f}%)                      │
  │  Max Drawdown        : {max_dd:>11.2f}%                                           │
  │  Sharpe Ratio (yıl.) : {sharpe:>11.2f}                                            │
  │                                                                              │
  ├──────────────────────────── İŞLEM İSTATİSTİKLERİ ────────────────────────────┤
  │                                                                              │
  │  Açılan pozisyon     : {trades_opened:>8}                                            │
  │  Toplam trade (çıkış): {total_trades:>8}                                            │
  │  Kazanan trade       : {winning_trades:>8} ({win_rate:.1f}%)                               │
  │  Kaybeden trade      : {losing_trades:>8}                                            │
  │  Başa-baş            : {breakeven_trades:>8}                                            │
  │  Profit Factor       : {profit_factor:>8.2f}                                            │
  │                                                                              │
  │  Ort. Kâr/trade      : ${avg_pnl:>+10,.2f}                                         │
  │  Ort. kazanç         : ${avg_win:>+10,.2f}                                         │
  │  Ort. kayıp          : ${avg_loss:>+10,.2f}                                         │
  │                                                                              │
  │  Ort. pozisyon süresi: {avg_holding:>7.1f} gün                                        │
  │  Max pozisyon süresi : {max_holding:>7.0f} gün                                        │
  │  Min pozisyon süresi : {min_holding:>7.0f} gün                                        │
  │                                                                              │
  │  Skip (max pozisyon) : {trades_skipped_max_pos:>8}                                            │
  │  Skip (sermaye)      : {trades_skipped_capital:>8}                                            │
  │                                                                              │
  └──────────────────────────────────────────────────────────────────────────────┘
""")

# Strateji bazlı performans
if total_trades > 0:
    print("  ┌────────────────────── STRATEJİ BAZLI PERFORMANS ───────────────────────┐")
    for strat in df_trades["strategy"].unique():
        st = df_trades[df_trades["strategy"] == strat]
        st_pnl = st["pnl"].sum()
        st_wr = (len(st[st["pnl"] > 0]) / len(st) * 100) if len(st) > 0 else 0
        st_avg = st["pnl"].mean()
        print(
            f"  │  {strat:20s} │ {len(st):3} trade │ PnL: ${st_pnl:>+9,.2f} │ WR: {st_wr:5.1f}% │ Ort: ${st_avg:>+8,.2f} │"
        )
    print("  └───────────────────────────────────────────────────────────────────────┘")

# Hisse bazlı performans
if total_trades > 0:
    print("\n  ┌──────────────────────── HİSSE BAZLI PERFORMANS ────────────────────────┐")
    sym_perf = (
        df_trades.groupby("symbol")
        .agg(
            trades=("pnl", "count"),
            total_pnl=("pnl", "sum"),
            avg_pnl=("pnl", "mean"),
            win_rate=("pnl", lambda x: (x > 0).sum() / len(x) * 100),
            avg_hold=("holding_days", "mean"),
        )
        .sort_values("total_pnl", ascending=False)
    )

    print(
        f"  │  {'Hisse':8s} │ {'Trade':>5s} │ {'Toplam PnL':>12s} │ {'Ort. PnL':>10s} │ {'WR%':>6s} │ {'Süre':>6s} │"
    )
    print(f"  │  {'─' * 8} │ {'─' * 5} │ {'─' * 12} │ {'─' * 10} │ {'─' * 6} │ {'─' * 6} │")
    for sym, row in sym_perf.iterrows():
        bar = "🟢" if row["total_pnl"] > 0 else "🔴"
        print(
            f"  │  {bar}{sym:7s} │ {int(row['trades']):>5} │ ${row['total_pnl']:>+10,.2f} │ ${row['avg_pnl']:>+8,.2f} │ {row['win_rate']:>5.1f}% │ {row['avg_hold']:>5.1f}d │"
        )
    print("  └───────────────────────────────────────────────────────────────────────┘")

# Trade detayları (tüm işlemler)
if total_trades > 0:
    print(
        f"\n  ┌──────────────────────── TÜM İŞLEM DETAYLARI ({total_trades}) ─────────────────────┐"
    )
    for _, t in df_trades.iterrows():
        pnl_icon = "🟢" if t["pnl"] > 0 else "🔴" if t["pnl"] < 0 else "⚪"
        print(
            f"  │ {pnl_icon} {t['symbol']:6s} │ {t['entry_date']} → {t['exit_date']} │ ${t['entry_price']:>8.2f} → ${t['exit_price']:>8.2f} │ {t['shares']:>4} lot │ ${t['pnl']:>+9.2f} ({t['pnl_pct']:>+6.2f}%) │ {t['exit_reason']} │"
        )
    print("  └───────────────────────────────────────────────────────────────────────┘")

# Çıkış nedeni dağılımı
if total_trades > 0:
    print("\n  Çıkış Nedeni Dağılımı:")
    for reason, cnt in df_trades["exit_reason"].value_counts().items():
        pnl_by_reason = df_trades[df_trades["exit_reason"] == reason]["pnl"].sum()
        print(f"    {reason}: {cnt} trade, PnL: ${pnl_by_reason:+,.2f}")

# ───────────────────────────────────────────────────────────────────────
# ADIM 6: RAPORU DOSYAYA KAYDET
# ───────────────────────────────────────────────────────────────────────
print("\n💾 Adım 6: Raporlar kaydediliyor...")

report_dir = "reports/backtest_3month"
os.makedirs(report_dir, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M")

# 1. Sinyal CSV
signals_file = f"{report_dir}/signals_{timestamp}.csv"
df_signals.to_csv(signals_file, index=False)
print(f"   ✅ Sinyaller: {signals_file} ({len(df_signals)} satır)")

# 2. Trade CSV
if total_trades > 0:
    trades_file = f"{report_dir}/trades_{timestamp}.csv"
    df_trades.to_csv(trades_file, index=False)
    print(f"   ✅ Trade'ler: {trades_file} ({total_trades} satır)")

# 3. Equity Curve CSV
if len(df_equity) > 0:
    equity_file = f"{report_dir}/equity_curve_{timestamp}.csv"
    df_equity.to_csv(equity_file, index=False)
    print(f"   ✅ Equity curve: {equity_file} ({len(df_equity)} satır)")

# 4. Entry sinyali veren hisseler CSV
if len(entry_signals) > 0:
    entry_file = f"{report_dir}/entry_signals_{timestamp}.csv"
    entry_signals.to_csv(entry_file, index=False)
    print(f"   ✅ Entry sinyalleri: {entry_file} ({len(entry_signals)} satır)")

# 5. Özet JSON
summary = {
    "report_date": datetime.now().isoformat(),
    "test_period_days": TEST_PERIOD_DAYS,
    "symbols_tested": len(indicator_cache),
    "symbols_failed": len(failed_symbols),
    "initial_capital": INITIAL_CAPITAL,
    "final_capital": round(final_capital, 2),
    "total_pnl": round(total_pnl, 2),
    "total_return_pct": round(total_return_pct, 2),
    "max_drawdown_pct": round(max_dd, 2),
    "sharpe_ratio": round(sharpe, 2),
    "total_scans": total_scans,
    "entry_signals": len(entry_signals),
    "entry_rate_pct": round(len(entry_signals) / total_scans * 100, 2) if total_scans > 0 else 0,
    "total_trades": total_trades,
    "winning_trades": winning_trades,
    "losing_trades": losing_trades,
    "win_rate": round(win_rate, 2),
    "profit_factor": round(profit_factor, 2) if profit_factor != float("inf") else "inf",
    "avg_pnl": round(avg_pnl, 2),
    "avg_win": round(avg_win, 2),
    "avg_loss": round(avg_loss, 2),
    "avg_holding_days": round(avg_holding, 1),
    "symbol_performance": sym_perf.to_dict("index") if total_trades > 0 else {},
}

summary_file = f"{report_dir}/summary_{timestamp}.json"
with open(summary_file, "w") as f:
    json.dump(summary, f, indent=2, default=str)
print(f"   ✅ Özet JSON: {summary_file}")

print(f"\n{'═' * 90}")
print(f"  Rapor tamamlandı! Tüm dosyalar: {report_dir}/")
print(f"{'═' * 90}")
