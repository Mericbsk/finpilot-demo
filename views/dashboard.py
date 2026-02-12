import csv
import datetime
import glob
import json
import logging
import os
from html import escape
from textwrap import dedent

import altair as alt
import pandas as pd
import streamlit as st
import yfinance as yf

import scanner
from scanner import (
    build_explanation,
    build_reason,
    compute_recommendation_score,
    evaluate_symbols_parallel,
    load_symbols,
)

from .components.export import render_export_button_row, render_export_panel
from .components.helpers import CSVValidationResult, validate_csv_upload
from .components.signal_tracker import log_signals_to_csv, render_signal_performance_tab
from .scan_history import render_scan_history_page
from .components.stock_presets import (
    STOCK_PRESETS,
    get_preset_symbols,
    render_preset_cards,
    render_quick_preset_buttons,
)
from .components.watchlist import (
    get_watchlist_scan_symbols,
    initialize_watchlist,
    is_watchlist_scan_triggered,
    render_watchlist_sidebar,
)
from .finsense import render_finsense_page
from .utils import (
    DEMO_MODE_ENABLED,
    detect_symbol_column,
    extract_symbols_from_df,
    get_demo_scan_results,
    get_gemini_research,
    is_advanced_view,
    normalize_narrative,
    render_buyable_cards,
    render_buyable_table,
    render_mobile_recommendation_cards,
    render_mobile_symbol_cards,
    render_progress_tracker,
    render_settings_card,
    render_signal_history_overview,
    render_summary_panel,
    render_symbol_snapshot,
    trigger_rerun,
)

# DRL Integration
try:
    from drl.inference import ActionType, DRLInference, has_trained_model

    DRL_AVAILABLE = True
except ImportError:
    DRL_AVAILABLE = False

logger = logging.getLogger(__name__)


def load_ai_signals():
    """AI Sinyal dosyasını yükler."""
    try:
        path = os.path.join(os.getcwd(), "data", "inference.json")
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def get_drl_predictions(symbols: list, max_symbols: int = 10) -> dict:
    """
    DRL modeli ile tahminler üretir.

    Args:
        symbols: Sembol listesi
        max_symbols: Maksimum sembol sayısı

    Returns:
        {symbol: {"action": "BUY", "confidence": 0.78, ...}} dict
    """
    if not DRL_AVAILABLE:
        return {}

    try:
        if not has_trained_model():
            logger.info("No trained DRL model found")
            return {}

        inference = DRLInference()
        if not inference.load_model():
            return {}

        results = {}
        predictions = inference.batch_predict(symbols[:max_symbols])

        for pred in predictions:
            results[pred.symbol] = {
                "action": pred.action.name,
                "confidence": pred.confidence,
                "suggested_position": pred.suggested_position,
                "regime": pred.regime,
                "is_actionable": pred.is_actionable,
                "raw_action": pred.raw_action,
            }

        return results

    except Exception as e:
        logger.error(f"DRL prediction error: {e}")
        return {}


def render_drl_signals_panel(symbols: list):
    """
    Dashboard'da DRL model sinyallerini gösterir.

    Args:
        symbols: Taramadan gelen sembol listesi
    """
    if not DRL_AVAILABLE:
        return

    if not has_trained_model():
        with st.expander("🤖 DRL Pilot Sinyalleri (Eğitim Gerekiyor)", expanded=False):
            st.info(
                "Henüz eğitilmiş bir DRL modeli bulunamadı. "
                "Model eğitildikten sonra AI destekli sinyaller burada görünecek."
            )
            st.caption("Eğitim için: `python -m drl.training --train`")
        return

    predictions = get_drl_predictions(symbols)

    if not predictions:
        return

    st.markdown("### 🤖 DRL Pilot Sinyalleri")
    st.caption("Yapay zeka modeli tarafından üretilen alım/satım önerileri")

    # Actionable predictions only
    actionable = {k: v for k, v in predictions.items() if v.get("is_actionable", False)}

    if not actionable:
        st.info("Şu an aksiyon alınabilir sinyal yok. Model HOLD konumunda.")
        return

    # Signal cards
    buy_signals = {k: v for k, v in actionable.items() if v["action"] == "BUY"}
    sell_signals = {k: v for k, v in actionable.items() if v["action"] == "SELL"}

    col1, col2 = st.columns(2)

    with col1:
        if buy_signals:
            st.markdown("#### 🟢 ALIŞ Sinyalleri")
            for symbol, data in sorted(buy_signals.items(), key=lambda x: -x[1]["confidence"]):
                conf = data["confidence"]
                conf_pct = int(conf * 100)
                pos_pct = int(data.get("suggested_position", 0) * 100)

                st.markdown(
                    f"""
                <div style="background: linear-gradient(145deg, #064e3b, #065f46);
                            border-radius: 8px; padding: 12px; margin-bottom: 8px;
                            border-left: 4px solid #10b981;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: bold; font-size: 1.1em;">{symbol}</span>
                        <span style="background: #10b981; padding: 2px 8px; border-radius: 4px; font-size: 0.8em;">
                            AI BUY
                        </span>
                    </div>
                    <div style="margin-top: 8px; font-size: 0.9em; color: #d1fae5;">
                        Güven: %{conf_pct} | Pozisyon: %{pos_pct}
                    </div>
                    <div style="margin-top: 4px;">
                        <div style="background: rgba(255,255,255,0.2); border-radius: 3px; height: 4px;">
                            <div style="background: #10b981; width: {conf_pct}%; height: 100%; border-radius: 3px;"></div>
                        </div>
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
        else:
            st.caption("Aktif alış sinyali yok")

    with col2:
        if sell_signals:
            st.markdown("#### 🔴 SATIŞ Sinyalleri")
            for symbol, data in sorted(sell_signals.items(), key=lambda x: -x[1]["confidence"]):
                conf = data["confidence"]
                conf_pct = int(conf * 100)

                st.markdown(
                    f"""
                <div style="background: linear-gradient(145deg, #7f1d1d, #991b1b);
                            border-radius: 8px; padding: 12px; margin-bottom: 8px;
                            border-left: 4px solid #ef4444;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: bold; font-size: 1.1em;">{symbol}</span>
                        <span style="background: #ef4444; padding: 2px 8px; border-radius: 4px; font-size: 0.8em;">
                            AI SELL
                        </span>
                    </div>
                    <div style="margin-top: 8px; font-size: 0.9em; color: #fecaca;">
                        Güven: %{conf_pct}
                    </div>
                    <div style="margin-top: 4px;">
                        <div style="background: rgba(255,255,255,0.2); border-radius: 3px; height: 4px;">
                            <div style="background: #ef4444; width: {conf_pct}%; height: 100%; border-radius: 3px;"></div>
                        </div>
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
        else:
            st.caption("Aktif satış sinyali yok")

    st.markdown("---")


def render_ai_insights_panel():
    """Ana dashboard'a AI Pilot sinyallerini ekler."""
    data = load_ai_signals()
    if not data:
        return

    st.markdown("### 🧠 FinPilot AI Gözlemleri (Canlı)")

    cols = st.columns(len(data)) if len(data) <= 5 else st.columns(4)

    for idx, (symbol, info) in enumerate(data.items()):
        col = cols[idx % len(cols)]

        score = info.get("ai_score", 50)
        signal = info.get("signal", "HOLD")
        confidence = info.get("confidence", 0.0)
        regime = info.get("regime", "UNKNOWN")

        # Color & Icon logic
        if signal == "BUY":
            color = "green"
            icon = "🟢"
        elif signal == "SELL":
            color = "red"
            icon = "🔴"
        else:
            color = "gray"
            icon = "⚪"

        with col:
            st.markdown(
                f"""
            <div style="border: 1px solid #444; border-radius: 8px; padding: 10px; background-color: #1a1a1a;">
                <div style="font-weight: bold; font-size: 1.1em;">{symbol} {icon}</div>
                <div style="font-size: 0.9em; color: #888;">Fiyat: ${info.get('price', 0)}</div>
                <hr style="margin: 5px 0; border-color: #333;">
                <div style="display: flex; justify-content: space-between;">
                    <span>Sinyal:</span>
                    <span style="color: {color}; font-weight: bold;">{signal}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span>Güven:</span>
                    <span>%{confidence*100:.0f}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span>Skor:</span>
                    <span>{score}/100</span>
                </div>
                 <div style="font-size: 0.8em; color: #666; margin-top: 5px;">Rejim: {regime}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    st.caption(f"Son Yapay Zeka Analizi: {list(data.values())[0].get('timestamp', '')[:16]}")
    st.markdown("---")


def latest_csv(prefix: str):
    if prefix == "shortlist":
        search_dir = os.path.join(os.getcwd(), "data", "shortlists")
    elif prefix == "suggestions":
        search_dir = os.path.join(os.getcwd(), "data", "suggestions")
    else:
        search_dir = os.getcwd()

    files = sorted(
        glob.glob(os.path.join(search_dir, f"{prefix}_*.csv")), key=os.path.getmtime, reverse=True
    )
    return files[0] if files else None


def load_csv(path: str):
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def render_scanner_page():
    if "scan_status" not in st.session_state:
        st.session_state["scan_status"] = "idle"
    if "scan_message" not in st.session_state:
        st.session_state["scan_message"] = None
    if "scan_df" not in st.session_state:
        st.session_state["scan_df"] = pd.DataFrame()
    if "scan_src" not in st.session_state:
        st.session_state["scan_src"] = None
    if "scan_time" not in st.session_state:
        st.session_state["scan_time"] = None
    if "guide_tooltip_shown" not in st.session_state:
        st.session_state["guide_tooltip_shown"] = False

    # --- Sidebar - Portföy Ayarları ---
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/bullish.png", width=64)
        st.title("FinPilot Kontrol")

        # 1. Temel Ayarlar (Her zaman görünür)
        st.markdown("### 🚀 Hızlı Ayarlar")
        aggressive_mode = st.toggle(
            "Agresif Mod", value=False, help="Daha fazla fırsat yakalamak için filtreleri gevşetir."
        )

        # 2. Portföy Yönetimi (Expander)
        with st.expander("💰 Portföy & Risk Yönetimi", expanded=True):
            portfolio_value = st.number_input(
                "Portföy Büyüklüğü ($)", value=10000, step=1000, min_value=1000
            )

            c1, c2 = st.columns(2)
            with c1:
                risk_percent = st.number_input(
                    "Risk %", min_value=0.5, max_value=5.0, value=2.0, step=0.5
                )
            with c2:
                kelly_fraction = st.number_input(
                    "Kelly",
                    min_value=0.1,
                    max_value=1.0,
                    value=0.25,
                    step=0.05,
                    help="Kelly Kriteri çarpanı (Önerilen: 0.25)",
                )

        # 3. Gelişmiş Algoritma Ayarları (Gizli)
        with st.expander("🛠️ Gelişmiş Algoritma Ayarları", expanded=False):
            st.caption("Z-Skoru ve İstatistiksel Eşikler")

            baseline_window_ui = st.select_slider(
                "Lookback (Gün)",
                options=[20, 40, 60, 90, 120],
                value=60,
                help="Geçmiş veri penceresi uzunluğu.",
            )

            dynamic_enabled_ui = st.toggle("Dinamik Eşik (Adaptive)", value=True)

            if dynamic_enabled_ui:
                dynamic_window_ui = st.slider("Adaptasyon Penceresi", 20, 160, 60)
                dynamic_quantile_ui = st.slider("Hassasiyet (Quantile)", 0.90, 0.995, 0.975, 0.005)
            else:
                dynamic_window_ui = 60
                dynamic_quantile_ui = 0.975

            segment_enabled_ui = st.toggle(
                "Likidite Bazlı Ayar", value=True, help="Hacme göre otomatik optimizasyon."
            )

        # 4. Veri ve Bildirimler
        with st.expander("📡 Veri & Bildirimler", expanded=False):
            use_adjusted = st.checkbox("Temettü Ayarlı Fiyat", value=True)
            include_prepost = st.checkbox("Pre/After Market", value=False)

            st.divider()

            # Telegram
            try:
                from telegram_config import BOT_TOKEN, CHAT_ID

                if BOT_TOKEN != "YOUR_BOT_TOKEN_HERE":
                    st.success("✅ Telegram Bağlı")
                    send_panel_telegram = st.toggle("Sinyalleri Gönder", value=True)
                else:
                    st.warning("⚠️ Telegram Ayarlanmadı")
                    send_panel_telegram = False
            except ImportError:
                send_panel_telegram = False

        # 5. Watchlist (İzleme Listesi)
        render_watchlist_sidebar()

        # Ayarları Kaydet
        settings = scanner.DEFAULT_SETTINGS.copy()
        if aggressive_mode:
            settings.update(scanner.AGGRESSIVE_OVERRIDES.copy())

        settings["auto_adjust"] = bool(use_adjusted)
        settings["prepost"] = bool(include_prepost)
        settings["momentum_baseline_window"] = int(baseline_window_ui)
        settings["momentum_dynamic_enabled"] = bool(dynamic_enabled_ui)
        settings["momentum_dynamic_window"] = int(dynamic_window_ui)
        settings["momentum_dynamic_quantile"] = float(dynamic_quantile_ui)
        settings["momentum_segment_thresholds"] = (
            scanner.DEFAULT_SETTINGS["momentum_segment_thresholds"].copy()
            if segment_enabled_ui
            else {}
        )
        scanner.SETTINGS = settings

        st.markdown("---")
        st.caption(f"v2.1.0 | {datetime.date.today().strftime('%d %b %Y')}")

    # --- Market Pulse (Piyasa Nabzı) ---
    df = st.session_state.get("scan_df", pd.DataFrame())

    # Metrikleri hesapla
    bull_ratio = 0
    avg_score = 0
    signal_count = 0
    last_update = "-"

    if not df.empty:
        if "regime" in df.columns:
            bull_ratio = (
                len(df[df["regime"].astype(str).str.contains("bull|trend", case=False, na=False)])
                / len(df)
                * 100
            )
        if "recommendation_score" in df.columns:
            avg_score = df["recommendation_score"].mean()
        if "entry_ok" in df.columns:
            signal_count = len(df[df["entry_ok"]])
        if "timestamp" in df.columns:
            last_update = df["timestamp"].iloc[0]

    # Pulse Bar
    st.markdown(
        """
    <style>
    .pulse-container {
        background-color: #1e293b;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #334155;
        margin-bottom: 20px;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    with st.container():
        st.markdown("<div class='pulse-container'>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(
            "Piyasa Rejimi", "Boğa" if bull_ratio > 50 else "Ayı", f"%{bull_ratio:.1f} Bullish"
        )
        c2.metric("Ortalama Skor", f"{avg_score:.1f}", delta_color="normal")
        c3.metric("Aktif Sinyal", f"{signal_count}", f"+{signal_count} yeni")
        c4.metric("Son Güncelleme", last_update)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- AI Pilot Insights Section (NEW) ---
    render_ai_insights_panel()

    # --- DRL Pilot Sinyalleri ---
    if not df.empty and "symbol" in df.columns:
        render_drl_signals_panel(df["symbol"].tolist())

    # --- Hazır Tarama Setleri (NEW) ---
    st.markdown("### 📊 Hazır Tarama Setleri")
    st.caption("Tek tıkla popüler kategorileri tarayın")

    # Initialize preset symbols in session state
    if "preset_symbols" not in st.session_state:
        st.session_state["preset_symbols"] = None

    preset_tabs = st.tabs(
        ["🔥 Popüler", "💼 Sektörler", "🎯 Tematik", "📈 Strateji", "🌐 Bölgesel"]
    )

    def _render_preset_row(keys, prefix):
        """Render a row of preset buttons (4 per row)."""
        for row_start in range(0, len(keys), 4):
            row_keys = keys[row_start : row_start + 4]
            cols = st.columns(4)
            for idx, key in enumerate(row_keys):
                preset = STOCK_PRESETS[key]
                with cols[idx]:
                    if st.button(
                        f"{preset.icon} {preset.name}",
                        key=f"{prefix}_{key}",
                        use_container_width=True,
                        help=f"{preset.description} ({len(preset.symbols)} hisse)",
                    ):
                        st.session_state["preset_symbols"] = preset.symbols
                        st.session_state["preset_name"] = preset.name

    with preset_tabs[0]:  # Popüler
        _render_preset_row(
            ["tech_giants", "ai_leaders", "semiconductors", "growth_momentum", "trending_momentum"],
            "pop",
        )

    with preset_tabs[1]:  # Sektörler
        _render_preset_row(
            [
                "biotech_large",
                "finance_banks",
                "energy_oil",
                "industrials",
                "pharma_pipeline",
                "medical_devices",
                "enterprise_software",
                "finance_diversified",
            ],
            "sec",
        )

    with preset_tabs[2]:  # Tematik
        _render_preset_row(
            ["ev_mobility", "space_defense", "crypto_blockchain", "cloud_saas"],
            "theme",
        )

    with preset_tabs[3]:  # Strateji
        _render_preset_row(
            [
                "high_dividend",
                "value_picks",
                "small_cap_growth",
                "biotech_emerging",
                "trending_momentum",
            ],
            "strat",
        )

    with preset_tabs[4]:  # Bölgesel
        _render_preset_row(
            ["international_mix"],
            "region",
        )

    # Show selected preset info
    if st.session_state.get("preset_symbols"):
        preset_name = st.session_state.get("preset_name", "Seçilen Set")
        symbols = st.session_state["preset_symbols"]
        st.info(
            f"✅ **{preset_name}** seçildi ({len(symbols)} hisse). Aşağıdaki 'Seçili Seti Tara' butonuna tıklayın."
        )

        with st.expander("📋 Seçili Semboller", expanded=False):
            st.write(", ".join(symbols))

    st.markdown("---")

    # --- Kontrol Paneli (CTA) ---
    st.markdown("### 🎮 İşlemler")
    status_for_label = st.session_state.get("scan_status", "idle")

    if status_for_label == "loading":
        primary_label = "⏳ Tarama yapılıyor…"
        primary_type = "secondary"
    elif status_for_label == "completed":
        primary_label = "🔁 Yeniden Başlat"
        primary_type = "primary"
    else:
        primary_label = "▶️ Taramayı Başlat"
        primary_type = "primary"

    # Add preset scan button if preset is selected
    has_preset = st.session_state.get("preset_symbols") is not None

    if has_preset:
        c1, c2, c3, c4 = st.columns([2, 2, 1, 1], gap="small")
        with c1:
            run_btn = st.button(
                primary_label,
                key="run_btn",
                disabled=status_for_label == "loading",
                use_container_width=True,
                type="secondary",
            )
        with c2:
            preset_btn = st.button(
                f"🎯 Seçili Seti Tara ({len(st.session_state['preset_symbols'])})",
                key="preset_scan_btn",
                disabled=status_for_label == "loading",
                use_container_width=True,
                type="primary",
            )
        with c3:
            refresh_btn = st.button(
                "🔄 Temizle",
                key="refresh_btn",
                disabled=status_for_label == "loading",
                use_container_width=True,
            )
        with c4:
            load_btn = st.button(
                "📂 Yükle",
                key="load_btn",
                disabled=status_for_label == "loading",
                use_container_width=True,
            )
    else:
        preset_btn = False
        c1, c2, c3 = st.columns([2, 1, 1], gap="small")
        with c1:
            run_btn = st.button(
                primary_label,
                key="run_btn",
                disabled=status_for_label == "loading",
                use_container_width=True,
                type=primary_type,
            )
        with c2:
            refresh_btn = st.button(
                "🔄 Önbelleği Temizle",
                key="refresh_btn",
                disabled=status_for_label == "loading",
                use_container_width=True,
                help="Verileri ve önbelleği temizleyip sayfayı yeniler.",
            )
        with c3:
            load_btn = st.button(
                "📂 Yükle",
                key="load_btn",
                disabled=status_for_label == "loading",
                use_container_width=True,
                help="Kaydedilmiş bir shortlist CSV dosyasını yükle.",
            )

    # Durum Mesajı
    if "scan_message" in st.session_state and st.session_state["scan_message"]:
        if status_for_label == "completed":
            st.success(st.session_state["scan_message"], icon="✅")
        elif status_for_label == "loading":
            st.info(st.session_state["scan_message"], icon="⏳")
        else:
            st.info(st.session_state["scan_message"], icon="ℹ️")

    # --- CSV Yükleme Alanı ---
    with st.expander("📂 Harici CSV Dosyası ile Tara", expanded=False):
        st.info("Kendi sembol listenizi yükleyerek tarama yapabilirsiniz.")
        uploaded_csv = st.file_uploader("CSV Dosyası Seçin", type=["csv"], key="csv_uploader_new")
        if uploaded_csv:
            st.caption("Dosya yüklendi. 'Symbol' sütunu aranacak.")
        csv_scan_btn = st.button(
            "▶️ CSV Listesini Tara",
            key="csv_scan_btn",
            disabled=(uploaded_csv is None or status_for_label == "loading"),
            type="primary",
        )

    # --- Tarama Mantığı ---
    if run_btn:
        st.session_state["scan_status"] = "loading"
        st.session_state["scan_message"] = "Tarama başlatıldı."
        symbols = load_symbols()
        backtest_kelly = kelly_fraction if kelly_fraction else 0.5

        # Progress bar ile tarama
        progress_bar = st.progress(0, text="Semboller analiz ediliyor...")
        progress_text = st.empty()

        def update_progress(current, total):
            pct = current / total if total > 0 else 0
            progress_bar.progress(pct, text=f"Analiz ediliyor: {current}/{total} sembol")

        results = evaluate_symbols_parallel(
            symbols, kelly_fraction=backtest_kelly, progress_callback=update_progress
        )
        progress_bar.progress(1.0, text="✅ Tarama tamamlandı!")

        df = pd.DataFrame(results)
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        if not df.empty:
            df["timestamp"] = now
        st.session_state["scan_df"] = df
        st.session_state["scan_src"] = "live"
        st.session_state["scan_time"] = now
        st.session_state["scan_status"] = "completed" if not df.empty else "idle"
        st.session_state["scan_message"] = f"{len(df)} sembol analiz edildi."
        # Log signals for performance tracking
        if not df.empty:
            logged = log_signals_to_csv(df)
            logger.info(f"Logged {logged} signals from live scan")
        st.rerun()
    elif preset_btn and st.session_state.get("preset_symbols"):
        # Preset scan with selected symbols
        st.session_state["scan_status"] = "loading"
        preset_name = st.session_state.get("preset_name", "Hazır Set")
        st.session_state["scan_message"] = f"'{preset_name}' taranıyor..."
        symbols = st.session_state["preset_symbols"]
        backtest_kelly = kelly_fraction if kelly_fraction else 0.5

        # Progress bar ile tarama
        progress_bar = st.progress(0, text=f"'{preset_name}' analiz ediliyor...")
        progress_text = st.empty()

        def update_progress(current, total):
            pct = current / total if total > 0 else 0
            progress_bar.progress(
                pct, text=f"Analiz ediliyor: {current}/{total} sembol ({preset_name})"
            )

        results = evaluate_symbols_parallel(
            symbols, kelly_fraction=backtest_kelly, progress_callback=update_progress
        )
        progress_bar.progress(1.0, text=f"✅ '{preset_name}' taraması tamamlandı!")

        df = pd.DataFrame(results)
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        if not df.empty:
            df["timestamp"] = now
            df["preset_source"] = preset_name  # Add source info
        st.session_state["scan_df"] = df
        st.session_state["scan_src"] = f"preset:{preset_name}"
        st.session_state["scan_time"] = now
        st.session_state["scan_status"] = "completed" if not df.empty else "idle"
        st.session_state["scan_message"] = f"'{preset_name}': {len(df)} hisse analiz edildi."
        # Log signals for performance tracking
        if not df.empty:
            logged = log_signals_to_csv(df)
            logger.info(f"Logged {logged} signals from preset scan")
        st.rerun()
    elif refresh_btn:
        st.cache_data.clear()
        st.session_state["scan_status"] = "loading"
        st.session_state["scan_message"] = "Tarama yenileniyor."
        # Clear preset selection on refresh
        st.session_state["preset_symbols"] = None
        st.session_state.pop("preset_name", None)
        symbols = load_symbols()

        # Progress bar ile yenileme
        progress_bar = st.progress(0, text="Yeniden analiz ediliyor...")

        def update_progress(current, total):
            pct = current / total if total > 0 else 0
            progress_bar.progress(pct, text=f"Yenileniyor: {current}/{total} sembol")

        results = evaluate_symbols_parallel(symbols, progress_callback=update_progress)
        progress_bar.progress(1.0, text="✅ Yenileme tamamlandı!")

        df = pd.DataFrame(results)
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        if not df.empty:
            df["timestamp"] = now
        st.session_state["scan_df"] = df
        st.session_state["scan_src"] = "live"
        st.session_state["scan_time"] = now
        st.session_state["scan_status"] = "completed" if not df.empty else "idle"
        st.session_state["scan_message"] = "Tarama yenilendi."
        st.rerun()
    elif load_btn:
        st.session_state["scan_status"] = "loading"
        path = latest_csv("shortlist")
        if path:
            df = load_csv(path)
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            if not df.empty:
                df["timestamp"] = now
            st.session_state["scan_df"] = df
            st.session_state["scan_src"] = os.path.basename(path)
            st.success(f"Son CSV yüklendi: {os.path.basename(path)}")
            st.session_state["scan_time"] = now
            st.session_state["scan_status"] = "completed" if not df.empty else "idle"
            st.session_state["scan_message"] = f"CSV'den {len(df)} satır yüklendi."
            st.rerun()
        else:
            st.warning("Yüklenecek shortlist CSV bulunamadı.")
            df = st.session_state.get("scan_df", pd.DataFrame())
            st.session_state["scan_status"] = "error"
    elif csv_scan_btn and uploaded_csv is not None:
        try:
            st.session_state["scan_status"] = "loading"
            uploaded_csv.seek(0)
            df_in = pd.read_csv(uploaded_csv)

            # CSV Validation
            validation_result = validate_csv_upload(df_in)

            if not validation_result.is_valid:
                for error in validation_result.errors:
                    st.error(f"❌ {error}")
                st.session_state["scan_status"] = "error"
                df = st.session_state.get("scan_df", pd.DataFrame())
            else:
                # Show warnings if any
                for warning in validation_result.warnings:
                    st.warning(f"⚠️ {warning}")

                symbols = validation_result.df["symbol"].tolist()

                # Progress bar ile CSV tarama
                progress_bar = st.progress(
                    0, text=f"CSV'den {len(symbols)} sembol analiz ediliyor..."
                )

                def update_progress(current, total):
                    pct = current / total if total > 0 else 0
                    progress_bar.progress(pct, text=f"CSV Analiz: {current}/{total} sembol")

                results = evaluate_symbols_parallel(symbols, progress_callback=update_progress)
                progress_bar.progress(1.0, text="✅ CSV taraması tamamlandı!")

                df = pd.DataFrame(results)
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                if not df.empty:
                    df["timestamp"] = now
                st.session_state["scan_df"] = df
                st.session_state["scan_src"] = (
                    f"csv:{getattr(uploaded_csv, 'name', 'uploaded.csv')}"
                )
                st.session_state["scan_time"] = now
                st.session_state["scan_status"] = "completed" if not df.empty else "idle"
                st.session_state["scan_message"] = f"CSV'den {len(df)} sembol analiz edildi."
                # Log signals for performance tracking
                if not df.empty:
                    logged = log_signals_to_csv(df)
                    logger.info(f"Logged {logged} signals from CSV scan")
                st.rerun()
        except Exception as e:
            st.error(f"CSV okunamadı: {e}")
            df = st.session_state.get("scan_df", pd.DataFrame())
            st.session_state["scan_status"] = "error"

    # --- Watchlist Scan ---
    if is_watchlist_scan_triggered():
        watchlist_symbols = get_watchlist_scan_symbols()
        if watchlist_symbols:
            st.session_state["scan_status"] = "loading"
            st.session_state["scan_message"] = (
                f"İzleme listesi taranıyor ({len(watchlist_symbols)} sembol)..."
            )

            progress_bar = st.progress(
                0, text=f"Watchlist'ten {len(watchlist_symbols)} sembol analiz ediliyor..."
            )

            def update_progress(current, total):
                pct = current / total if total > 0 else 0
                progress_bar.progress(pct, text=f"Watchlist Analiz: {current}/{total} sembol")

            backtest_kelly = kelly_fraction if kelly_fraction else 0.5
            results = evaluate_symbols_parallel(
                watchlist_symbols, kelly_fraction=backtest_kelly, progress_callback=update_progress
            )
            progress_bar.progress(1.0, text="✅ Watchlist taraması tamamlandı!")

            df = pd.DataFrame(results)
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            if not df.empty:
                df["timestamp"] = now
            st.session_state["scan_df"] = df
            st.session_state["scan_src"] = "watchlist"
            st.session_state["scan_time"] = now
            st.session_state["scan_status"] = "completed" if not df.empty else "idle"
            st.session_state["scan_message"] = f"İzleme listesinden {len(df)} sembol analiz edildi."
            st.rerun()

    # --- Ana İçerik Sekmeleri ---
    st.markdown("---")
    tab_signals, tab_market, tab_ai, tab_perf, tab_history, tab_edu = st.tabs(
        [
            "🎯 Sinyaller (Action Zone)",
            "📊 Piyasa Tarayıcı",
            "🧠 AI Laboratuvarı",
            "📈 Performans & Geçmiş",
            "📋 Scanner Geçmişi",
            "🎓 FinSense Eğitim",
        ]
    )

    # --- TAB 1: Sinyaller ---
    with tab_signals:
        if df is None or df.empty:
            st.info("Veri yok. Lütfen taramayı çalıştırın.")
        else:
            buyable = df[df["entry_ok"]].copy()

            if not buyable.empty:
                buyable["recommendation_score"] = buyable.apply(
                    compute_recommendation_score, axis=1
                )
                # Sort by score
                buyable = buyable.sort_values("recommendation_score", ascending=False)

                # Get DRL predictions for badge display
                drl_preds = get_drl_predictions(buyable["symbol"].tolist(), max_symbols=20)

                # --- Top Fırsatlar (Cards) ---
                st.markdown("### 🔥 En Güçlü Fırsatlar (Top 4)")

                top_n = buyable.head(4)
                cols = st.columns(4)

                for i, (idx, row) in enumerate(top_n.iterrows()):
                    score = row["recommendation_score"]
                    score_color = "#22c55e" if score >= 80 else "#eab308"
                    symbol = row["symbol"]

                    # Check if DRL also recommends this symbol
                    drl_info = drl_preds.get(symbol, {})
                    drl_action = drl_info.get("action", "")
                    drl_conf = drl_info.get("confidence", 0)
                    has_ai_buy = drl_action == "BUY" and drl_conf > 0.5
                    ai_badge = (
                        '<span style="background: #8b5cf6; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; margin-left: 5px;">🤖 AI</span>'
                        if has_ai_buy
                        else ""
                    )

                    with cols[i]:
                        st.markdown(
                            f"""
<div style="background: linear-gradient(145deg, #1e293b, #0f172a); border-radius: 12px; padding: 1.5rem; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); position: relative; overflow: hidden; transition: transform 0.2s;">
<div style="position: absolute; top: 0; left: 0; width: 100%; height: 4px; background: {score_color};"></div>
<div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
<div>
<h2 style="margin: 0; font-size: 1.8rem; font-weight: 800; color: #f8fafc;">{symbol}{ai_badge}</h2>
<span style="font-size: 0.9rem; color: #94a3b8;">{row.get('regime', 'N/A')}</span>
</div>
<div style="text-align: right;">
<div style="font-size: 1.5rem; font-weight: 700; color: #f8fafc;">${row['price']:.2f}</div>
</div>
</div>
<div style="margin-bottom: 1rem;">
<div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
<span style="font-size: 0.8rem; color: #94a3b8;">Sinyal Gücü</span>
<span style="font-size: 0.8rem; font-weight: 600; color: {score_color};">{score:.1f}/100</span>
</div>
<div style="width: 100%; height: 6px; background: #334155; border-radius: 3px; overflow: hidden;">
<div style="width: {score}%; height: 100%; background: {score_color}; border-radius: 3px;"></div>
</div>
</div>
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; font-size: 0.85rem;">
<div style="background: rgba(255,255,255,0.05); padding: 0.5rem; border-radius: 6px; text-align: center;">
<div style="color: #94a3b8; font-size: 0.7rem;">HEDEF</div>
<div style="color: #22c55e; font-weight: 600;">${row['take_profit']:.2f}</div>
</div>
<div style="background: rgba(255,255,255,0.05); padding: 0.5rem; border-radius: 6px; text-align: center;">
<div style="color: #94a3b8; font-size: 0.7rem;">STOP</div>
<div style="color: #ef4444; font-weight: 600;">${row['stop_loss']:.2f}</div>
</div>
</div>
</div>
""",
                            unsafe_allow_html=True,
                        )

                        if st.button(
                            "🧠 AI Analizi",
                            key=f"btn_card_{row['symbol']}",
                            use_container_width=True,
                        ):
                            st.session_state["selected_ai_symbol"] = row["symbol"]
                            st.toast(f"{row['symbol']} AI Laboratuvarına aktarıldı.", icon="🤖")

                # --- Detaylı Liste (Hibrit Yapı - İnteraktif) ---
                st.markdown("### 📋 Tüm Alım Sinyalleri")
                st.caption(
                    "Listeden bir hisse seçerek detaylı analiz kartını görüntüleyebilirsiniz."
                )

                # 1. Özet Tablo (İnteraktif)
                summary_df = buyable[
                    ["symbol", "price", "recommendation_score", "risk_reward", "regime"]
                ].copy()
                summary_df["risk_reward"] = summary_df["risk_reward"].round(2)
                summary_df["recommendation_score"] = summary_df["recommendation_score"].round(1)

                # Piyasa Ortalaması (Kıyaslama için)
                if "recommendation_score" not in df.columns:
                    df["recommendation_score"] = df.apply(compute_recommendation_score, axis=1)
                market_avg_score = df["recommendation_score"].mean()

                # İnteraktif Tablo
                selection = st.dataframe(
                    summary_df,
                    column_config={
                        "symbol": "Sembol",
                        "price": st.column_config.NumberColumn("Fiyat", format="$%.2f"),
                        "recommendation_score": st.column_config.ProgressColumn(
                            "Sinyal Gücü", min_value=0, max_value=100, format="%.1f"
                        ),
                        "risk_reward": st.column_config.NumberColumn("Risk/Ödül", format="%.2f"),
                        "regime": "Piyasa Rejimi",
                    },
                    use_container_width=True,
                    hide_index=True,
                    height=250,
                    on_select="rerun",
                    selection_mode="single-row",
                    key="signal_list_table",
                )

                # 2. Seçim Mantığı
                selected_symbol_detail = None
                if selection.selection.rows:
                    selected_index = selection.selection.rows[0]
                    selected_symbol_detail = summary_df.iloc[selected_index]["symbol"]
                elif not summary_df.empty:
                    # Varsayılan olarak en üsttekini seç
                    selected_symbol_detail = summary_df.iloc[0]["symbol"]

                if selected_symbol_detail:
                    row = buyable[buyable["symbol"] == selected_symbol_detail].iloc[0]

                    # FinPilot Edge Hesabı
                    edge_score = row["recommendation_score"] - market_avg_score
                    edge_color = "#22c55e" if edge_score > 0 else "#ef4444"
                    edge_text = f"+{edge_score:.1f}" if edge_score > 0 else f"{edge_score:.1f}"

                    # Detay Kartı Tasarımı
                    strategy_tag = row.get("strategy_tag", row.get("regime", "N/A"))

                    st.markdown(
                        f"""
                    <div style="background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 1.5rem; margin-top: 1rem;">
                        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem;">
                            <div style="background: #3b82f6; color: white; width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1.2rem;">
                                {row['symbol'][0]}
                            </div>
                            <div>
                                <h3 style="margin: 0; color: #f8fafc;">{row['symbol']} Analiz Raporu</h3>
                                <span style="color: #94a3b8; font-size: 0.9rem;">Strateji: <strong style="color: #facc15;">{strategy_tag}</strong> | Zaman: {st.session_state.get('scan_time', 'Yeni')}</span>
                            </div>
                            <div style="margin-left: auto; text-align: right;">
                                <div style="font-size: 1.5rem; font-weight: 700; color: #22c55e;">${row['price']:.2f}</div>
                                <div style="color: #94a3b8; font-size: 0.8rem;">Anlık Fiyat</div>
                            </div>
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    c1, c2, c3 = st.columns([2, 1, 1])

                    with c1:
                        st.markdown("#### 💡 Yapay Zeka Görüşü")
                        # Dinamik açıklama
                        reason = "Güçlü momentum ve pozitif trend."
                        if row["recommendation_score"] > 80:
                            reason = "Çok güçlü yükseliş trendi, hacim destekli ve risk düşük."
                        elif row["recommendation_score"] > 60:
                            reason = "Yükseliş potansiyeli var, ancak volatiliteye dikkat edilmeli."

                        st.info(f"{reason}\n\n**Risk/Ödül Oranı:** {row['risk_reward']:.2f}")

                        # FinPilot Edge Göstergesi (Farklılaştırıcı Özellik)
                        st.markdown(
                            f"""
                        <div style="background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px; margin-top: 10px; border-left: 4px solid {edge_color};">
                            <strong style="color: #f8fafc;">🚀 FinPilot Edge:</strong>
                            <span style="color: #94a3b8;">Piyasa ortalamasından</span>
                            <strong style="color: {edge_color};">{edge_text} puan</strong>
                            <span style="color: #94a3b8;">ayrışıyor.</span>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                    with c2:
                        st.markdown("#### 🎯 Ticaret Planı")

                        # Kademeli Hedefler (Varsa)
                        tp1 = row.get("tp1")
                        tp2 = row.get("tp2")
                        tp3 = row.get("tp3")

                        if pd.notna(tp1) and pd.notna(tp2):
                            st.markdown(
                                f"""
                            <div style="display: flex; justify-content: space-between; font-size: 0.9rem; margin-bottom: 5px;">
                                <span>TP1 (%50):</span> <strong style="color: #4ade80;">${tp1:.2f}</strong>
                            </div>
                            <div style="display: flex; justify-content: space-between; font-size: 0.9rem; margin-bottom: 5px;">
                                <span>TP2 (%30):</span> <strong style="color: #22c55e;">${tp2:.2f}</strong>
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )
                            if pd.notna(tp3) and tp3 > 0:
                                st.markdown(
                                    f"""
                                <div style="display: flex; justify-content: space-between; font-size: 0.9rem; margin-bottom: 10px;">
                                    <span>TP3 (%20):</span> <strong style="color: #15803d;">🚀 Trailing Stop</strong>
                                </div>
                                <div style="font-size: 0.75rem; color: #94a3b8; text-align: right;">(Ref: ${tp3:.2f})</div>
                                """,
                                    unsafe_allow_html=True,
                                )
                        else:
                            st.metric(
                                "Hedef (TP)",
                                f"${row['take_profit']:.2f}",
                                delta=f"%{((row['take_profit']-row['price'])/row['price']*100):.1f}",
                                help="Take Profit: Kar alma hedef fiyatı. Bu fiyata ulaşıldığında pozisyon kapatılmalı.",
                            )

                        st.metric(
                            "Stop (SL)",
                            f"${row['stop_loss']:.2f}",
                            delta=f"-%{((row['price']-row['stop_loss'])/row['price']*100):.1f}",
                            delta_color="inverse",
                            help="Stop Loss: Zarar durdurma seviyesi. Fiyat bu seviyeye düşerse pozisyon kapatılmalı.",
                        )

                        st.markdown("#### 📊 Teknik Göstergeler")
                        st.markdown(
                            f"""
                        - **Rejim:** `{row.get('regime', '-')}`
                        - **Volatilite:** `{row.get('atr', 0):.2f}`
                        """
                        )

                    with c3:
                        st.markdown("#### ⚡ Aksiyon")
                        st.write("Bu hisse için daha derin bir araştırma yapmak ister misiniz?")
                        if st.button(
                            "🧠 AI Laboratuvarına Git",
                            key=f"list_btn_{row['symbol']}",
                            type="primary",
                            use_container_width=True,
                        ):
                            st.session_state["selected_ai_symbol"] = row["symbol"]
                            st.toast(
                                f"{row['symbol']} seçildi, AI sekmesine yönlendiriliyorsunuz...",
                                icon="🚀",
                            )

                # --- Export Panel ---
                st.markdown("---")
                render_export_panel(buyable)

            else:
                st.warning(
                    "Şu an kriterlere uyan aktif alım sinyali bulunmuyor. Ayarları gevşetmeyi (Agresif Mod) deneyebilirsiniz."
                )

    # --- TAB 2: Piyasa Tarayıcı ---
    with tab_market:
        if df is None or df.empty:
            st.info("Veri yok.")
        else:
            st.markdown("### 🔎 Tüm Piyasa Görünümü")

            # Filtreleme
            search_term = st.text_input("Sembol Ara", placeholder="AAPL, TSLA...")

            market_df = df.copy()
            if search_term:
                market_df = market_df[market_df["symbol"].str.contains(search_term.upper())]

            if "recommendation_score" not in market_df.columns:
                market_df["recommendation_score"] = market_df.apply(
                    compute_recommendation_score, axis=1
                )

            st.dataframe(
                market_df[
                    ["symbol", "price", "recommendation_score", "entry_ok", "regime", "sentiment"]
                ],
                column_config={
                    "symbol": "Sembol",
                    "price": st.column_config.NumberColumn("Fiyat", format="$%.2f"),
                    "recommendation_score": st.column_config.ProgressColumn(
                        "Skor", min_value=0, max_value=100
                    ),
                    "entry_ok": st.column_config.CheckboxColumn("Al Sinyali?"),
                    "regime": "Rejim",
                    "sentiment": st.column_config.NumberColumn(
                        "Sentiment", help="-1 (Negatif) ile +1 (Pozitif)"
                    ),
                },
                use_container_width=True,
                hide_index=True,
            )

    # --- TAB 3: AI Laboratuvarı ---
    # (Groq Entegrasyonu Aktif)
    with tab_ai:
        st.markdown("### 🧠 Yapay Zeka Araştırma Merkezi")
        st.caption("Google Gemini ve DuckDuckGo destekli derinlemesine analiz.")

        if df is not None and not df.empty:
            symbol_list = df["symbol"].tolist()
            default_idx = 0
            if (
                "selected_ai_symbol" in st.session_state
                and st.session_state["selected_ai_symbol"] in symbol_list
            ):
                default_idx = symbol_list.index(st.session_state["selected_ai_symbol"])

            col_sym, col_lang = st.columns([3, 1])
            with col_sym:
                selected_ai_sym = st.selectbox(
                    "Analiz edilecek hisseyi seçin:", symbol_list, index=default_idx
                )
            with col_lang:
                selected_lang = st.selectbox(
                    "Rapor Dili:", ["Türkçe", "English", "Deutsch"], index=0
                )

            lang_map = {"Türkçe": "tr", "English": "en", "Deutsch": "de"}

            if st.button(f"🚀 {selected_ai_sym} İçin Araştırmayı Başlat", type="primary"):
                with st.spinner("Yapay zeka interneti tarıyor ve raporu hazırlıyor..."):
                    report = get_gemini_research(selected_ai_sym, language=lang_map[selected_lang])
                    st.markdown("---")
                    st.markdown(report)
                    st.success("Analiz tamamlandı.")
        else:
            st.warning("Analiz için önce tarama yapmalısınız.")

    # --- TAB 4: Performans ---
    with tab_perf:
        render_signal_performance_tab()

        # Optimizasyon Sonuçları (ek bilgi)
        with st.expander("📊 WFO Grid Search Sonuçları", expanded=False):
            wfo_path = os.path.join(os.getcwd(), "wfo_grid_search_results.csv")
            if os.path.exists(wfo_path):
                wfo_df = pd.read_csv(wfo_path)
                st.dataframe(wfo_df, use_container_width=True)
            else:
                st.info("WFO backtest sonuçları bulunamadı.")

    # --- TAB 5: Scanner Geçmişi ---
    with tab_history:
        render_scan_history_page()

    # --- TAB 6: FinSense Eğitim ---
    with tab_edu:
        render_finsense_page()
