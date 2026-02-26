import datetime
import glob
import json
import logging
import os

import pandas as pd
import scanner
import streamlit as st
from scanner import (
    compute_recommendation_score,
    evaluate_symbols_parallel,
    load_symbols,
)

from .components.ai_signals import (
    get_drl_predictions,
    refresh_inference_json,
    render_ai_insights_panel,
    render_drl_signals_panel,
)
from .components.export import render_export_panel
from .components.helpers import validate_csv_upload
from .components.hybrid_panel import render_hybrid_panel
from .components.research import get_ai_research
from .components.signal_tracker import log_signals_to_csv, render_signal_performance_tab
from .components.stock_presets import (
    STOCK_PRESETS,
)
from .components.watchlist import (
    get_watchlist_scan_symbols,
    is_watchlist_scan_triggered,
    render_watchlist_sidebar,
)
from .finsense import render_finsense_page
from .scan_history import render_scan_history_page

# DRL Integration
try:
    from drl.inference import DRLInference, has_trained_model  # noqa: F401

    DRL_AVAILABLE = True
except ImportError:
    DRL_AVAILABLE = False

logger = logging.getLogger(__name__)


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


def _render_drl_model_status():
    """DRL Model Registry durumunu gosteren panel (flat-dict format, 3 rejim ajani)."""
    st.markdown("### \U0001f916 DRL Model Durumu \u2014 3 Rejim Ajani")

    registry_path = os.path.join(os.getcwd(), "models", "registry.json")
    if not os.path.exists(registry_path):
        st.info("Henuz egitilmis model bulunamadi. Sprint 14 model egitimini calistirin.")
        return

    try:
        with open(registry_path) as f:
            registry = json.load(f)
    except Exception as e:
        st.error(f"Registry okunamadi: {e}")
        return

    if not isinstance(registry, dict) or not registry:
        st.info("Registry'de kayitli model yok.")
        return

    # Collect active models by regime tag
    active_models = {k: v for k, v in registry.items() if v.get("is_active")}
    tag_icons = {"trend": "\U0001f4c8", "volatile": "\U0001f30a", "range": "\U0001f4d0"}

    st.success(f"**Aktif Model Sayisi:** {len(active_models)} / {len(registry)}")

    cols = st.columns(min(len(active_models), 3)) if active_models else []
    for idx, (model_id, meta) in enumerate(active_models.items()):
        tags = meta.get("tags", [])
        tag = tags[0] if tags else "unknown"
        icon = tag_icons.get(tag, "\U0001f916")
        metrics = meta.get("metrics", {})
        sharpe = metrics.get("test_sharpe", 0)
        ret = metrics.get("test_return") or metrics.get("total_return", 0)
        trades = metrics.get("total_trades", "N/A")

        with cols[idx % len(cols)]:
            st.markdown(f"#### {icon} {tag.upper()} Agent")
            st.caption(f"`{model_id}`")
            m1, m2 = st.columns(2)
            m1.metric("Sharpe", f"{sharpe:.4f}" if isinstance(sharpe, (int, float)) else "N/A")
            m2.metric("Return", f"{ret:+.1%}" if isinstance(ret, (int, float)) else "N/A")
            st.metric("Islem Sayisi", trades)

    # All models table
    with st.expander(f"\U0001f4cb Tum Modeller ({len(registry)})", expanded=False):
        rows = []
        for mid, meta in registry.items():
            met = meta.get("metrics", {})
            tags = meta.get("tags", [])
            s = met.get("test_sharpe") or met.get("sharpe_ratio")
            r = met.get("test_return") or met.get("total_return")
            rows.append(
                {
                    "Model ID": mid,
                    "Tag": tags[0] if tags else "-",
                    "Sharpe": round(s, 4) if isinstance(s, (int, float)) else None,
                    "Return": f"{r:+.1%}" if isinstance(r, (int, float)) else None,
                    "Islem": met.get("total_trades", None),
                    "Aktif": "\u2705" if meta.get("is_active") else "",
                }
            )
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # DRL availability check
    if DRL_AVAILABLE:
        st.caption("\u2705 DRL modulu aktif \u2014 canli tahminler kullanilabilir.")
    else:
        st.caption(
            "\u26a0\ufe0f DRL modulu yuklenemedi \u2014 `pip install stable-baselines3` gerekebilir."
        )


def _render_ensemble_status(df):
    """Ensemble Router durumu ve canli tahminler paneli."""
    st.markdown("### \U0001f3af Ensemble Router \u2014 3 Ajan Oylama")

    try:
        from drl.ensemble_router import ENSEMBLE_AVAILABLE as ENS_OK
        from drl.ensemble_router import get_ensemble_router
    except ImportError:
        ENS_OK = False

    if not ENS_OK:
        st.warning("Ensemble Router modulu yuklenemedi.")
        return

    router = get_ensemble_router()
    status = router.get_status()

    # Status cards
    c1, c2, c3 = st.columns(3)
    c1.metric("Router Durumu", "\u2705 Aktif" if status.get("loaded") else "\u274c Pasif")
    c2.metric("Yuklu Ajan", f"{status.get('n_agents', 0)} / 3")
    c3.metric("Mevcut Rejim", status.get("current_regime", "N/A"))

    # Agent detail
    agents_info = status.get("agents", {})
    if agents_info:
        st.markdown("#### Ajan Detaylari")
        tag_icons = {"trend": "\U0001f4c8", "volatile": "\U0001f30a", "range": "\U0001f4d0"}
        agent_cols = st.columns(len(agents_info))
        for idx, (tag, info) in enumerate(agents_info.items()):
            with agent_cols[idx]:
                icon = tag_icons.get(tag, "\U0001f916")
                loaded = "\u2705" if info.get("loaded") else "\u274c"
                st.markdown(f"**{icon} {tag.upper()}** {loaded}")
                st.caption(f"Model: `{info.get('model_id', 'N/A')}`")

    st.divider()

    # Live predictions
    st.markdown("#### \U0001f52e Canli Ensemble Tahminleri")
    if df is not None and not df.empty and status.get("loaded"):
        symbols = df["symbol"].tolist()[:15]
        try:
            results = router.batch_predict(symbols)
            pred_rows = []
            action_map = {0: "\U0001f534 SAT", 1: "\u26aa TUT", 2: "\U0001f7e2 AL"}
            for res in results:
                pred_rows.append(
                    {
                        "Sembol": res.symbol,
                        "Karar": action_map.get(res.final_action, "?"),
                        "Guven": f"{res.final_confidence:.1%}",
                        "Rejim": res.dominant_regime,
                        "Uzlasi": f"{res.agreement_score:.1%}",
                        "Pozisyon": f"{res.suggested_position:+.2f}",
                    }
                )
            st.dataframe(pd.DataFrame(pred_rows), use_container_width=True, hide_index=True)

            # Vote breakdown
            with st.expander("\U0001f5f3\ufe0f Ajan Oy Detaylari", expanded=False):
                for res in results:
                    st.markdown(f"**{res.symbol}**")
                    vote_data = []
                    for v in res.votes:
                        vote_data.append(
                            {
                                "Ajan": v.agent_tag,
                                "Aksiyon": action_map.get(v.action, "?"),
                                "Guven": f"{v.confidence:.1%}",
                                "Agirlik": f"{v.weight:.2f}",
                            }
                        )
                    st.dataframe(pd.DataFrame(vote_data), use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Ensemble tahmin hatasi: {e}")
    elif df is None or df.empty:
        st.info("Tahmin icin once tarama yapin.")
    else:
        st.warning("Ensemble Router yuklenemedi \u2014 modeller eksik olabilir.")


def _render_optuna_results():
    """Optuna HP optimizasyon sonuclarini gosterir."""
    st.markdown("### \U0001f52c Optuna Hiperparametre Optimizasyonu")

    results_path = os.path.join(os.getcwd(), "data", "optuna_range_results.json")
    if not os.path.exists(results_path):
        st.info("Henuz Optuna sonucu bulunamadi. `scripts/optuna_range.py` calistirin.")
        return

    try:
        with open(results_path) as f:
            data = json.load(f)
    except Exception as e:
        st.error(f"Optuna sonuclari okunamadi: {e}")
        return

    best = data.get("best_params", {})
    best_attrs = data.get("best_attrs", {})
    best_value = data.get("best_value", 0)
    best_trial = data.get("best_trial", "?")
    trials = data.get("all_trials", [])

    # Summary cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("En Iyi Trial", f"#{best_trial}")
    c2.metric("Objektif Skor", f"{best_value:.4f}")
    c3.metric("Sharpe", f"{best_attrs.get('sharpe', 0):.4f}")
    c4.metric("Return", f"{best_attrs.get('total_return', 0):+.1%}")

    # Best params
    with st.expander("\U0001f3c6 En Iyi Hiperparametreler", expanded=True):
        param_cols = st.columns(3)
        param_items = list(best.items())
        for i, (k, v) in enumerate(param_items):
            with param_cols[i % 3]:
                if isinstance(v, float):
                    st.metric(k, f"{v:.6f}")
                else:
                    st.metric(k, str(v))

    # Trial chart
    if trials:
        st.markdown("#### \U0001f4ca Trial Performanslari")
        trial_df = pd.DataFrame(trials)
        if "value" in trial_df.columns and "number" in trial_df.columns:
            chart_df = trial_df[["number", "value"]].dropna()
            chart_df = chart_df.rename(columns={"number": "Trial", "value": "Objektif"})
            st.line_chart(chart_df.set_index("Trial"))

        # Top 5 table
        st.markdown("#### \U0001f3c5 En Iyi 5 Trial")
        top5 = trial_df.nlargest(5, "value") if "value" in trial_df.columns else trial_df.head(5)
        display_cols = ["number", "value"]
        if "params" in top5.columns:
            params_expanded = pd.json_normalize(top5["params"])
            top5_display = pd.concat(
                [
                    top5[["number", "value"]].reset_index(drop=True),
                    params_expanded.reset_index(drop=True),
                ],
                axis=1,
            )
        else:
            top5_display = (
                top5[display_cols] if all(c in top5.columns for c in display_cols) else top5
            )
        st.dataframe(top5_display, use_container_width=True, hide_index=True)

    st.caption(f"Toplam {len(trials)} trial tamamlandi.")


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
            _portfolio_value = st.number_input(
                "Portföy Büyüklüğü ($)", value=10000, step=1000, min_value=1000
            )

            c1, c2 = st.columns(2)
            with c1:
                _risk_percent = st.number_input(
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
                from telegram_config import BOT_TOKEN

                if BOT_TOKEN != "YOUR_BOT_TOKEN_HERE":  # noqa: S105
                    st.success("✅ Telegram Bağlı")
                    send_panel_telegram = st.toggle("Sinyalleri Gönder", value=True)
                else:
                    st.warning("⚠️ Telegram Ayarlanmadı")
                    send_panel_telegram = False  # noqa: F841
            except ImportError:
                send_panel_telegram = False  # noqa: F841

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
        _progress_text = st.empty()

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
        _progress_text = st.empty()

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

    # --- Refresh DRL inference cache after any scan completion ---
    if st.session_state.get("scan_status") == "completed" and df is not None and not df.empty:
        try:
            refresh_inference_json(df)
        except Exception as e:
            logger.warning("refresh_inference_json failed: %s", e)

    # --- Ana İçerik Sekmeleri ---
    st.markdown("---")
    tab_signals, tab_market, tab_ai, tab_perf, tab_edu = st.tabs(
        [
            "🎯 Sinyaller (Action Zone)",
            "📊 Piyasa Tarayıcı",
            "🧠 AI Laboratuvarı",
            "📈 Performans & Geçmiş",
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

                for i, (_idx, row) in enumerate(top_n.iterrows()):
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
<span style="font-size: 0.9rem; color: #94a3b8;">{row.get("regime", "N/A")}</span>
</div>
<div style="text-align: right;">
<div style="font-size: 1.5rem; font-weight: 700; color: #f8fafc;">${row["price"]:.2f}</div>
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
<div style="color: #22c55e; font-weight: 600;">${row["take_profit"]:.2f}</div>
</div>
<div style="background: rgba(255,255,255,0.05); padding: 0.5rem; border-radius: 6px; text-align: center;">
<div style="color: #94a3b8; font-size: 0.7rem;">STOP</div>
<div style="color: #ef4444; font-weight: 600;">${row["stop_loss"]:.2f}</div>
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
                _summary_want = ["symbol", "price", "recommendation_score", "risk_reward", "regime"]
                _summary_have = [c for c in _summary_want if c in buyable.columns]
                summary_df = buyable[_summary_have].copy()
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
                                {row["symbol"][0]}
                            </div>
                            <div>
                                <h3 style="margin: 0; color: #f8fafc;">{row["symbol"]} Analiz Raporu</h3>
                                <span style="color: #94a3b8; font-size: 0.9rem;">Strateji: <strong style="color: #facc15;">{strategy_tag}</strong> | Zaman: {st.session_state.get("scan_time", "Yeni")}</span>
                            </div>
                            <div style="margin-left: auto; text-align: right;">
                                <div style="font-size: 1.5rem; font-weight: 700; color: #22c55e;">${row["price"]:.2f}</div>
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
                                delta=f"%{((row['take_profit'] - row['price']) / row['price'] * 100):.1f}",
                                help="Take Profit: Kar alma hedef fiyatı. Bu fiyata ulaşıldığında pozisyon kapatılmalı.",
                            )

                        st.metric(
                            "Stop (SL)",
                            f"${row['stop_loss']:.2f}",
                            delta=f"-%{((row['price'] - row['stop_loss']) / row['price'] * 100):.1f}",
                            delta_color="inverse",
                            help="Stop Loss: Zarar durdurma seviyesi. Fiyat bu seviyeye düşerse pozisyon kapatılmalı.",
                        )

                        st.markdown("#### 📊 Teknik Göstergeler")
                        st.markdown(
                            f"""
                        - **Rejim:** `{row.get("regime", "-")}`
                        - **Volatilite:** `{row.get("atr", 0):.2f}`
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

            desired_cols = [
                "symbol",
                "price",
                "recommendation_score",
                "entry_ok",
                "regime",
                "sentiment",
            ]
            display_cols = [c for c in desired_cols if c in market_df.columns]

            col_cfg = {}
            if "symbol" in display_cols:
                col_cfg["symbol"] = "Sembol"
            if "price" in display_cols:
                col_cfg["price"] = st.column_config.NumberColumn("Fiyat", format="$%.2f")
            if "recommendation_score" in display_cols:
                col_cfg["recommendation_score"] = st.column_config.ProgressColumn(
                    "Skor", min_value=0, max_value=100
                )
            if "entry_ok" in display_cols:
                col_cfg["entry_ok"] = st.column_config.CheckboxColumn("Al Sinyali?")
            if "regime" in display_cols:
                col_cfg["regime"] = "Rejim"
            if "sentiment" in display_cols:
                col_cfg["sentiment"] = st.column_config.NumberColumn(
                    "Sentiment", help="-1 (Negatif) ile +1 (Pozitif)"
                )

            st.dataframe(
                market_df[display_cols],
                column_config=col_cfg,
                use_container_width=True,
                hide_index=True,
            )

    # --- TAB 3: AI Laboratuvarı ---
    with tab_ai:
        ai_sub_tab1, ai_sub_tab2, ai_sub_tab3, ai_sub_tab4, ai_sub_tab5 = st.tabs(
            [
                "🧠 AI Araştırma",
                "⚡ Hybrid Engine",
                "🤖 Model Durumu",
                "🎯 Ensemble Router",
                "🔬 Optuna HP",
            ]
        )

        # --- AI Research Sub-tab ---
        with ai_sub_tab1:
            st.markdown("### 🧠 Yapay Zeka Araştırma Merkezi")
            st.caption("Groq LLM ve DuckDuckGo destekli derinlemesine analiz.")

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
                        report = get_ai_research(selected_ai_sym, language=lang_map[selected_lang])
                        st.markdown("---")
                        st.markdown(report)
                        st.success("Analiz tamamlandı.")
            else:
                st.warning("Analiz için önce tarama yapmalısınız.")

        # --- Hybrid Engine Sub-tab (Sprint 13) ---
        with ai_sub_tab2:
            render_hybrid_panel(df)

        # --- DRL Model Status Sub-tab (Sprint 17 updated) ---
        with ai_sub_tab3:
            _render_drl_model_status()

        # --- Ensemble Router Sub-tab (Sprint 17 new) ---
        with ai_sub_tab4:
            _render_ensemble_status(df)

        # --- Optuna HP Sub-tab (Sprint 17 new) ---
        with ai_sub_tab5:
            _render_optuna_results()

    # --- TAB 4: Performans ---
    with tab_perf:
        perf_sub1, perf_sub2, perf_sub3, perf_sub4 = st.tabs(
            [
                "\U0001f4c8 Sinyal Performans",
                "\U0001f4cb Scanner Gecmisi",
                "\U0001f916 DRL Model Karsilastirma",
                "\U0001f4ca WFO & Backtest",
            ]
        )

        with perf_sub1:
            render_signal_performance_tab()

        with perf_sub2:
            render_scan_history_page()

        with perf_sub3:
            _render_drl_model_status()

        with perf_sub4:
            st.markdown("### \U0001f4ca WFO & Backtest Sonuclari")
            # WFO Grid Search
            wfo_path = os.path.join(os.getcwd(), "wfo_grid_search_results.csv")
            if os.path.exists(wfo_path):
                wfo_df = pd.read_csv(wfo_path)
                st.dataframe(wfo_df, use_container_width=True, hide_index=True)
            else:
                st.info("WFO backtest sonuclari bulunamadi.")

            # Walk-Forward Validation Report
            wf_report = os.path.join(os.getcwd(), "reports", "wf_validation_report.txt")
            if os.path.exists(wf_report):
                with st.expander("\U0001f4dd Walk-Forward Validation Raporu", expanded=False):
                    report_text = open(wf_report).read()  # noqa: SIM115
                    st.code(report_text, language="text")

    # --- TAB 5: FinSense Egitim ---
    with tab_edu:
        render_finsense_page()
