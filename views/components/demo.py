# -*- coding: utf-8 -*-
"""
FinPilot Demo Data
==================
Demo verileri ve örnek scan sonuçları.
"""

import datetime

import pandas as pd
import streamlit as st

# Standart TTL: 300 saniye (tüm modüllerle uyumlu)
DEMO_CACHE_TTL = 300


@st.cache_data(ttl=DEMO_CACHE_TTL, show_spinner=False)
def get_demo_scan_results() -> pd.DataFrame:
    """Return a lightweight demo dataframe to showcase the experience when no data exists."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    demo_rows = [
        {
            "symbol": "AAPL",
            "price": 186.40,
            "stop_loss": 180.80,
            "take_profit": 198.20,
            "position_size": 12,
            "risk_reward": 2.65,
            "entry_ok": True,
            "filter_score": 3,
            "score": 88,
            "recommendation_score": 95,
            "strength": 90,
            "regime": "Trend",
            "sentiment": 0.74,
            "onchain_metric": 68,
            "why": "Trend ve hacim onaylı.",
            "reason": "ML skoru 0.87, momentum taze.",
        },
        {
            "symbol": "NVDA",
            "price": 469.10,
            "stop_loss": 452.00,
            "take_profit": 505.00,
            "position_size": 6,
            "risk_reward": 2.94,
            "entry_ok": True,
            "filter_score": 3,
            "score": 91,
            "recommendation_score": 97,
            "strength": 92,
            "regime": "Trend",
            "sentiment": 0.81,
            "onchain_metric": 72,
            "why": "AI ivmesi güçlü.",
            "reason": "DRL stratejisi %84 uyum, volatilite kontrollü.",
        },
        {
            "symbol": "MSFT",
            "price": 335.60,
            "stop_loss": 324.00,
            "take_profit": 352.40,
            "position_size": 8,
            "risk_reward": 2.37,
            "entry_ok": True,
            "filter_score": 2,
            "score": 86,
            "recommendation_score": 92,
            "strength": 88,
            "regime": "Trend",
            "sentiment": 0.69,
            "onchain_metric": 63,
            "why": "Kurumsal talep artıyor.",
            "reason": "Kelly %4 öneriyor, earnings momentum pozitif.",
        },
        {
            "symbol": "TSLA",
            "price": 244.30,
            "stop_loss": 232.00,
            "take_profit": 262.50,
            "position_size": 0,
            "risk_reward": 1.95,
            "entry_ok": False,
            "filter_score": 2,
            "score": 78,
            "recommendation_score": 81,
            "strength": 75,
            "regime": "Yan",
            "sentiment": 0.41,
            "onchain_metric": 45,
            "why": "Volatilite yüksek.",
            "reason": "Trend teyidi bekleniyor, risk/ödül sınırlı.",
        },
        {
            "symbol": "AMD",
            "price": 112.80,
            "stop_loss": 106.50,
            "take_profit": 124.00,
            "position_size": 9,
            "risk_reward": 2.20,
            "entry_ok": True,
            "filter_score": 3,
            "score": 84,
            "recommendation_score": 90,
            "strength": 84,
            "regime": "Trend",
            "sentiment": 0.62,
            "onchain_metric": 59,
            "why": "Yarı iletken talebi güçlü.",
            "reason": "Momentum stabil, hacim 30 günlük ortalamanın 1.6x'i.",
        },
        {
            "symbol": "COIN",
            "price": 88.40,
            "stop_loss": 82.20,
            "take_profit": 102.50,
            "position_size": 0,
            "risk_reward": 2.41,
            "entry_ok": False,
            "filter_score": 1,
            "score": 72,
            "recommendation_score": 78,
            "strength": 70,
            "regime": "Yan",
            "sentiment": 0.35,
            "onchain_metric": 52,
            "why": "Regülasyon belirsiz.",
            "reason": "Risk seviyesi yüksek, on-chain hafif zayıf.",
        },
    ]

    df_demo = pd.DataFrame(demo_rows)
    df_demo["timestamp"] = now
    return df_demo
