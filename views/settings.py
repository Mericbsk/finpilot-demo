import json
import os

import streamlit as st

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


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_SETTINGS
    return DEFAULT_SETTINGS


def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4, ensure_ascii=False)


def render_settings_page():
    st.markdown("## ⚙️ Kişiselleştirme & Ayarlar")
    st.markdown("FinPilot deneyiminizi buradan özelleştirin.")

    settings = load_settings()

    with st.form("settings_form"):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 👤 Profil ve Risk")
            risk_score = st.slider(
                "Risk İştahı (1: Çok Muhafazakar - 10: Çok Agresif)",
                min_value=1,
                max_value=10,
                value=settings.get("risk_score", 5),
            )
            portfolio_size = st.number_input(
                "Portföy Büyüklüğü ($)", min_value=100, value=settings.get("portfolio_size", 10000)
            )
            max_loss_pct = st.number_input(
                "Maksimum Kayıp Limiti (%)",
                min_value=1,
                max_value=50,
                value=settings.get("max_loss_pct", 10),
            )

        with col2:
            st.markdown("### 📊 Strateji ve Piyasa")
            strategy = st.selectbox(
                "Tarama Stratejisi",
                ["Normal", "Agresif", "Defansif", "Momentum"],
                index=["Normal", "Agresif", "Defansif", "Momentum"].index(
                    settings.get("strategy", "Normal")
                ),
            )
            market = st.selectbox(
                "Çalışma Piyasası",
                ["BIST", "Kripto", "NASDAQ", "Forex"],
                index=["BIST", "Kripto", "NASDAQ", "Forex"].index(settings.get("market", "BIST")),
            )
            timeframe = st.selectbox(
                "Varsayılan Zaman Dilimi",
                ["Günlük", "Haftalık", "Aylık", "4 Saatlik"],
                index=["Günlük", "Haftalık", "Aylık", "4 Saatlik"].index(
                    settings.get("timeframe", "Günlük")
                ),
            )

        st.markdown("---")
        st.markdown("### 🔔 Bildirimler (Telegram)")

        telegram_active = st.checkbox(
            "Telegram Bildirimlerini Aç", value=settings.get("telegram_active", False)
        )
        telegram_id = st.text_input(
            "Telegram Chat ID", value=settings.get("telegram_id", ""), disabled=not telegram_active
        )

        st.markdown("---")
        st.markdown("### 📈 Teknik Göstergeler")

        ind_cols = st.columns(3)
        indicators = settings.get("indicators", DEFAULT_SETTINGS["indicators"])

        with ind_cols[0]:
            ema = st.checkbox("EMA (Üstel Hareketli Ort.)", value=indicators.get("ema", True))
        with ind_cols[1]:
            rsi = st.checkbox("RSI (Göreceli Güç)", value=indicators.get("rsi", False))
        with ind_cols[2]:
            atr = st.checkbox("ATR (Volatilite)", value=indicators.get("atr", True))

        submitted = st.form_submit_button("💾 Ayarları Kaydet", type="primary")

        if submitted:
            new_settings = {
                "risk_score": risk_score,
                "portfolio_size": portfolio_size,
                "max_loss_pct": max_loss_pct,
                "strategy": strategy,
                "market": market,
                "telegram_active": telegram_active,
                "telegram_id": telegram_id,
                "timeframe": timeframe,
                "indicators": {"ema": ema, "rsi": rsi, "atr": atr},
            }
            save_settings(new_settings)
            st.success(
                "Ayarlar başarıyla kaydedildi! Değişikliklerin etkili olması için sayfayı yenileyebilirsiniz."
            )
            st.session_state["user_settings"] = new_settings
