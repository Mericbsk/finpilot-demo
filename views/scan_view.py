"""
Scan View — Sidebar Settings, Scan Execution & Market Pulse
============================================================

Extracted from dashboard.py (Sprint P7).
Contains sidebar configuration, scan button logic, and the market pulse bar.
"""

from __future__ import annotations

import datetime
import glob
import logging
import os

import pandas as pd
import scanner
import streamlit as st
from scanner import evaluate_symbols_parallel, load_symbols

from .components.helpers import validate_csv_upload
from .components.signal_tracker import log_signals_to_csv
from .components.stock_presets import STOCK_PRESETS
from .components.watchlist import (
    get_watchlist_scan_symbols,
    is_watchlist_scan_triggered,
    render_watchlist_sidebar,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# CSV Helpers
# ---------------------------------------------------------------------------


def latest_csv(prefix: str) -> str | None:
    """Return the path for the most recent CSV matching *prefix*."""
    if prefix == "shortlist":
        search_dir = os.path.join(os.getcwd(), "data", "shortlists")
    elif prefix == "suggestions":
        search_dir = os.path.join(os.getcwd(), "data", "suggestions")
    else:
        search_dir = os.getcwd()

    files = sorted(
        glob.glob(os.path.join(search_dir, f"{prefix}_*.csv")),
        key=os.path.getmtime,
        reverse=True,
    )
    return files[0] if files else None


def load_csv(path: str) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------


def _init_session_state() -> None:
    """Ensure all required session state keys exist."""
    defaults = {
        "scan_status": "idle",
        "scan_message": None,
        "scan_df": pd.DataFrame(),
        "scan_src": None,
        "scan_time": None,
        "guide_tooltip_shown": False,
        "preset_symbols": None,
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------


def render_sidebar() -> dict:
    """Render all sidebar controls and return the aggregated settings dict."""
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/bullish.png", width=64)
        st.title("FinPilot Kontrol")

        # 1. Quick settings
        st.markdown("### 🚀 Hızlı Ayarlar")
        aggressive_mode = st.toggle(
            "Agresif Mod",
            value=False,
            help="Daha fazla fırsat yakalamak için filtreleri gevşetir.",
        )

        # 2. Portfolio management
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

        # 3. Advanced algorithm settings
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
                dynamic_quantile_ui = st.slider(
                    "Hassasiyet (Quantile)", 0.90, 0.995, 0.975, 0.005
                )
            else:
                dynamic_window_ui = 60
                dynamic_quantile_ui = 0.975

            segment_enabled_ui = st.toggle(
                "Likidite Bazlı Ayar",
                value=True,
                help="Hacme göre otomatik optimizasyon.",
            )

        # 4. Data & notifications
        send_panel_telegram = False
        with st.expander("📡 Veri & Bildirimler", expanded=False):
            use_adjusted = st.checkbox("Temettü Ayarlı Fiyat", value=True)
            include_prepost = st.checkbox("Pre/After Market", value=False)

            st.divider()

            try:
                from telegram_config import BOT_TOKEN

                if BOT_TOKEN != "YOUR_BOT_TOKEN_HERE":
                    st.success("✅ Telegram Bağlı")
                    send_panel_telegram = st.toggle("Sinyalleri Gönder", value=True)
                else:
                    st.warning("⚠️ Telegram Ayarlanmadı")
            except ImportError:
                pass

        # 5. Watchlist
        render_watchlist_sidebar()

        # Build settings dict
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

    return {
        "kelly_fraction": kelly_fraction,
        "send_telegram": send_panel_telegram,
    }


# ---------------------------------------------------------------------------
# Market Pulse Bar
# ---------------------------------------------------------------------------


def render_market_pulse(df: pd.DataFrame) -> None:
    """Render the top-of-page market metrics bar."""
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
            "Piyasa Rejimi",
            "Boğa" if bull_ratio > 50 else "Ayı",
            f"%{bull_ratio:.1f} Bullish",
        )
        c2.metric("Ortalama Skor", f"{avg_score:.1f}", delta_color="normal")
        c3.metric("Aktif Sinyal", f"{signal_count}", f"+{signal_count} yeni")
        c4.metric("Son Güncelleme", last_update)
        st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Preset Scanner
# ---------------------------------------------------------------------------


def render_preset_selector() -> None:
    """Render the preset stock set selector."""
    st.markdown("### 📊 Hazır Tarama Setleri")
    st.caption("Tek tıkla popüler kategorileri tarayın")

    if "preset_symbols" not in st.session_state:
        st.session_state["preset_symbols"] = None

    preset_tabs = st.tabs(
        ["🔥 Popüler", "💼 Sektörler", "🎯 Tematik", "📈 Strateji", "🌐 Bölgesel"]
    )

    def _render_preset_row(keys, prefix):
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

    with preset_tabs[0]:
        _render_preset_row(
            ["tech_giants", "ai_leaders", "semiconductors", "growth_momentum", "trending_momentum"],
            "pop",
        )
    with preset_tabs[1]:
        _render_preset_row(
            [
                "biotech_large", "finance_banks", "energy_oil", "industrials",
                "pharma_pipeline", "medical_devices", "enterprise_software", "finance_diversified",
            ],
            "sec",
        )
    with preset_tabs[2]:
        _render_preset_row(
            ["ev_mobility", "space_defense", "crypto_blockchain", "cloud_saas"],
            "theme",
        )
    with preset_tabs[3]:
        _render_preset_row(
            ["high_dividend", "value_picks", "small_cap_growth", "biotech_emerging", "trending_momentum"],
            "strat",
        )
    with preset_tabs[4]:
        _render_preset_row(["international_mix"], "region")

    # Show selected preset info
    if st.session_state.get("preset_symbols"):
        preset_name = st.session_state.get("preset_name", "Seçilen Set")
        symbols = st.session_state["preset_symbols"]
        st.info(
            f"✅ **{preset_name}** seçildi ({len(symbols)} hisse). "
            "Aşağıdaki 'Seçili Seti Tara' butonuna tıklayın."
        )
        with st.expander("📋 Seçili Semboller", expanded=False):
            st.write(", ".join(symbols))

    st.markdown("---")


# ---------------------------------------------------------------------------
# Scan Execution
# ---------------------------------------------------------------------------


def _run_scan(symbols: list[str], kelly_fraction: float, label: str, source: str) -> None:
    """Execute a scan with progress bar and update session state."""
    st.session_state["scan_status"] = "loading"
    st.session_state["scan_message"] = f"'{label}' taranıyor..."

    progress_bar = st.progress(0, text=f"'{label}' analiz ediliyor...")

    def update_progress(current, total):
        pct = current / total if total > 0 else 0
        progress_bar.progress(pct, text=f"Analiz ediliyor: {current}/{total} sembol")

    results = evaluate_symbols_parallel(
        symbols, kelly_fraction=kelly_fraction, progress_callback=update_progress
    )
    progress_bar.progress(1.0, text=f"✅ '{label}' taraması tamamlandı!")

    df = pd.DataFrame(results)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    if not df.empty:
        df["timestamp"] = now
        if source.startswith("preset:"):
            df["preset_source"] = source.split(":", 1)[1]

    st.session_state["scan_df"] = df
    st.session_state["scan_src"] = source
    st.session_state["scan_time"] = now
    st.session_state["scan_status"] = "completed" if not df.empty else "idle"
    st.session_state["scan_message"] = f"'{label}': {len(df)} sembol analiz edildi."

    if not df.empty:
        logged = log_signals_to_csv(df)
        logger.info(f"Logged {logged} signals from {source}")

    st.rerun()


def render_scan_controls(kelly_fraction: float) -> None:
    """Render the scan control buttons and execute scan logic."""
    st.markdown("### 🎮 İşlemler")
    status = st.session_state.get("scan_status", "idle")

    if status == "loading":
        primary_label = "⏳ Tarama yapılıyor…"
    elif status == "completed":
        primary_label = "🔁 Yeniden Başlat"
    else:
        primary_label = "▶️ Taramayı Başlat"

    has_preset = st.session_state.get("preset_symbols") is not None

    if has_preset:
        c1, c2, c3, c4 = st.columns([2, 2, 1, 1], gap="small")
        with c1:
            run_btn = st.button(
                primary_label, key="run_btn",
                disabled=status == "loading", use_container_width=True, type="secondary",
            )
        with c2:
            preset_btn = st.button(
                f"🎯 Seçili Seti Tara ({len(st.session_state['preset_symbols'])})",
                key="preset_scan_btn",
                disabled=status == "loading", use_container_width=True, type="primary",
            )
        with c3:
            refresh_btn = st.button(
                "🔄 Temizle", key="refresh_btn",
                disabled=status == "loading", use_container_width=True,
            )
        with c4:
            load_btn = st.button(
                "📂 Yükle", key="load_btn",
                disabled=status == "loading", use_container_width=True,
            )
    else:
        preset_btn = False
        c1, c2, c3 = st.columns([2, 1, 1], gap="small")
        with c1:
            run_btn = st.button(
                primary_label, key="run_btn",
                disabled=status == "loading", use_container_width=True,
                type="primary" if status != "loading" else "secondary",
            )
        with c2:
            refresh_btn = st.button(
                "🔄 Önbelleği Temizle", key="refresh_btn",
                disabled=status == "loading", use_container_width=True,
                help="Verileri ve önbelleği temizleyip sayfayı yeniler.",
            )
        with c3:
            load_btn = st.button(
                "📂 Yükle", key="load_btn",
                disabled=status == "loading", use_container_width=True,
                help="Kaydedilmiş bir shortlist CSV dosyasını yükle.",
            )

    # Status message
    if st.session_state.get("scan_message"):
        if status == "completed":
            st.success(st.session_state["scan_message"], icon="✅")
        elif status == "loading":
            st.info(st.session_state["scan_message"], icon="⏳")
        else:
            st.info(st.session_state["scan_message"], icon="ℹ️")

    # CSV upload area
    with st.expander("📂 Harici CSV Dosyası ile Tara", expanded=False):
        st.info("Kendi sembol listenizi yükleyerek tarama yapabilirsiniz.")
        uploaded_csv = st.file_uploader("CSV Dosyası Seçin", type=["csv"], key="csv_uploader_new")
        if uploaded_csv:
            st.caption("Dosya yüklendi. 'Symbol' sütunu aranacak.")
        csv_scan_btn = st.button(
            "▶️ CSV Listesini Tara", key="csv_scan_btn",
            disabled=(uploaded_csv is None or status == "loading"), type="primary",
        )

    # Execution logic
    kf = kelly_fraction or 0.5
    if run_btn:
        _run_scan(load_symbols(), kf, "Tam Tarama", "live")
    elif preset_btn and st.session_state.get("preset_symbols"):
        name = st.session_state.get("preset_name", "Hazır Set")
        _run_scan(st.session_state["preset_symbols"], kf, name, f"preset:{name}")
    elif refresh_btn:
        st.cache_data.clear()
        st.session_state["preset_symbols"] = None
        st.session_state.pop("preset_name", None)
        _run_scan(load_symbols(), kf, "Yenileme", "live")
    elif load_btn:
        _handle_load()
    elif csv_scan_btn and uploaded_csv is not None:
        _handle_csv_scan(uploaded_csv, kf)

    # Watchlist scan
    if is_watchlist_scan_triggered():
        watchlist_symbols = get_watchlist_scan_symbols()
        if watchlist_symbols:
            _run_scan(watchlist_symbols, kf, "İzleme Listesi", "watchlist")


def _handle_load() -> None:
    """Handle loading the most recent shortlist CSV."""
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
        st.session_state["scan_status"] = "error"


def _handle_csv_scan(uploaded_csv, kelly_fraction: float) -> None:
    """Handle scanning from an uploaded CSV file."""
    try:
        st.session_state["scan_status"] = "loading"
        uploaded_csv.seek(0)
        df_in = pd.read_csv(uploaded_csv)

        validation_result = validate_csv_upload(df_in)

        if not validation_result.is_valid:
            for error in validation_result.errors:
                st.error(f"❌ {error}")
            st.session_state["scan_status"] = "error"
            return

        for warning in validation_result.warnings:
            st.warning(f"⚠️ {warning}")

        symbols = validation_result.df["symbol"].tolist()
        label = getattr(uploaded_csv, "name", "uploaded.csv")
        _run_scan(symbols, kelly_fraction, f"CSV: {label}", f"csv:{label}")

    except Exception as e:
        st.error(f"CSV okunamadı: {e}")
        st.session_state["scan_status"] = "error"
