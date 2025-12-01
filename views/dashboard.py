import os
import glob
import pandas as pd
import streamlit as st
from html import escape
from textwrap import dedent
import datetime
import csv
import yfinance as yf
import altair as alt

import scanner
from scanner import load_symbols, build_explanation, build_reason, compute_recommendation_score
from .utils import (
    render_progress_tracker, render_summary_panel, render_buyable_table, 
    render_buyable_cards, render_symbol_snapshot, render_mobile_symbol_cards,
    render_mobile_recommendation_cards, render_settings_card,
    get_demo_scan_results, detect_symbol_column, extract_symbols_from_df,
    trigger_rerun, DEMO_MODE_ENABLED, normalize_narrative, is_advanced_view,
    render_signal_history_overview, get_gemini_research
)
from .finsense import render_finsense_page

def latest_csv(prefix: str):
    if prefix == "shortlist":
        search_dir = os.path.join(os.getcwd(), "data", "shortlists")
    elif prefix == "suggestions":
        search_dir = os.path.join(os.getcwd(), "data", "suggestions")
    else:
        search_dir = os.getcwd()
        
    files = sorted(glob.glob(os.path.join(search_dir, f"{prefix}_*.csv")), key=os.path.getmtime, reverse=True)
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
        aggressive_mode = st.toggle("Agresif Mod", value=False, help="Daha fazla fırsat yakalamak için filtreleri gevşetir.")
        
        # 2. Portföy Yönetimi (Expander)
        with st.expander("💰 Portföy & Risk Yönetimi", expanded=True):
            portfolio_value = st.number_input("Portföy Büyüklüğü ($)", value=10000, step=1000, min_value=1000)
            
            c1, c2 = st.columns(2)
            with c1:
                risk_percent = st.number_input("Risk %", min_value=0.5, max_value=5.0, value=2.0, step=0.5)
            with c2:
                kelly_fraction = st.number_input("Kelly", min_value=0.1, max_value=1.0, value=0.25, step=0.05, help="Kelly Kriteri çarpanı (Önerilen: 0.25)")

        # 3. Gelişmiş Algoritma Ayarları (Gizli)
        with st.expander("🛠️ Gelişmiş Algoritma Ayarları", expanded=False):
            st.caption("Z-Skoru ve İstatistiksel Eşikler")
            
            baseline_window_ui = st.select_slider(
                "Lookback (Gün)", options=[20, 40, 60, 90, 120], value=60,
                help="Geçmiş veri penceresi uzunluğu."
            )
            
            dynamic_enabled_ui = st.toggle("Dinamik Eşik (Adaptive)", value=True)
            
            if dynamic_enabled_ui:
                dynamic_window_ui = st.slider("Adaptasyon Penceresi", 20, 160, 60)
                dynamic_quantile_ui = st.slider("Hassasiyet (Quantile)", 0.90, 0.995, 0.975, 0.005)
            else:
                dynamic_window_ui = 60
                dynamic_quantile_ui = 0.975
                
            segment_enabled_ui = st.toggle("Likidite Bazlı Ayar", value=True, help="Hacme göre otomatik optimizasyon.")

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
            scanner.DEFAULT_SETTINGS["momentum_segment_thresholds"].copy() if segment_enabled_ui else {}
        )
        scanner.SETTINGS = settings
        
        st.markdown("---")
        st.caption(f"v2.1.0 | {datetime.date.today().strftime('%d %b %Y')}")

    # --- Market Pulse (Piyasa Nabzı) ---
    df = st.session_state.get('scan_df', pd.DataFrame())
    
    # Metrikleri hesapla
    bull_ratio = 0
    avg_score = 0
    signal_count = 0
    last_update = "-"
    
    if not df.empty:
        if 'regime' in df.columns:
            bull_ratio = len(df[df['regime'].astype(str).str.contains('bull|trend', case=False, na=False)]) / len(df) * 100
        if 'recommendation_score' in df.columns:
            avg_score = df['recommendation_score'].mean()
        if 'entry_ok' in df.columns:
            signal_count = len(df[df['entry_ok']])
        if 'timestamp' in df.columns:
            last_update = df['timestamp'].iloc[0]

    # Pulse Bar
    st.markdown("""
    <style>
    .pulse-container {
        background-color: #1e293b;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #334155;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown("<div class='pulse-container'>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Piyasa Rejimi", "Boğa" if bull_ratio > 50 else "Ayı", f"%{bull_ratio:.1f} Bullish")
        c2.metric("Ortalama Skor", f"{avg_score:.1f}", delta_color="normal")
        c3.metric("Aktif Sinyal", f"{signal_count}", f"+{signal_count} yeni")
        c4.metric("Son Güncelleme", last_update)
        st.markdown("</div>", unsafe_allow_html=True)

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

    c1, c2, c3 = st.columns([2, 1, 1], gap="small")
    with c1:
        run_btn = st.button(primary_label, key="run_btn", disabled=status_for_label == "loading", use_container_width=True, type=primary_type)
    with c2:
        refresh_btn = st.button("🔄 Önbelleği Temizle", key="refresh_btn", disabled=status_for_label == "loading", use_container_width=True, help="Verileri ve önbelleği temizleyip sayfayı yeniler.")
    with c3:
        load_btn = st.button("📂 Yükle", key="load_btn", disabled=status_for_label == "loading", use_container_width=True, help="Kaydedilmiş bir shortlist CSV dosyasını yükle.")

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
        csv_scan_btn = st.button("▶️ CSV Listesini Tara", key="csv_scan_btn", disabled=(uploaded_csv is None or status_for_label == "loading"), type="primary")

    # --- Tarama Mantığı ---
    if run_btn:
        st.session_state["scan_status"] = "loading"
        st.session_state["scan_message"] = "Tarama başlatıldı."
        with st.spinner("Semboller analiz ediliyor..."):
            symbols = load_symbols()
            backtest_kelly = kelly_fraction if kelly_fraction else 0.5
            results = scanner.evaluate_symbols_parallel(symbols, kelly_fraction=backtest_kelly)
            df = pd.DataFrame(results)
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            if not df.empty:
                df['timestamp'] = now
            st.session_state['scan_df'] = df
            st.session_state['scan_src'] = 'live'
            st.session_state['scan_time'] = now
        st.session_state["scan_status"] = "completed" if not df.empty else "idle"
        st.session_state["scan_message"] = f"{len(df)} sembol analiz edildi."
        st.rerun()
    elif refresh_btn:
        st.cache_data.clear()
        st.session_state["scan_status"] = "loading"
        st.session_state["scan_message"] = "Tarama yenileniyor."
        with st.spinner("Yeniden analiz ediliyor..."):
            symbols = load_symbols()
            results = scanner.evaluate_symbols_parallel(symbols)
            df = pd.DataFrame(results)
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            if not df.empty:
                df['timestamp'] = now
            st.session_state['scan_df'] = df
            st.session_state['scan_src'] = 'live'
            st.session_state['scan_time'] = now
        st.session_state["scan_status"] = "completed" if not df.empty else "idle"
        st.session_state["scan_message"] = "Tarama yenilendi."
        st.rerun()
    elif load_btn:
        st.session_state["scan_status"] = "loading"
        path = latest_csv('shortlist')
        if path:
            df = load_csv(path)
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            if not df.empty:
                df['timestamp'] = now
            st.session_state['scan_df'] = df
            st.session_state['scan_src'] = os.path.basename(path)
            st.success(f"Son CSV yüklendi: {os.path.basename(path)}")
            st.session_state['scan_time'] = now
            st.session_state["scan_status"] = "completed" if not df.empty else "idle"
            st.session_state["scan_message"] = f"CSV'den {len(df)} satır yüklendi."
            st.rerun()
        else:
            st.warning("Yüklenecek shortlist CSV bulunamadı.")
            df = st.session_state.get('scan_df', pd.DataFrame())
            st.session_state["scan_status"] = "error"
    elif csv_scan_btn and uploaded_csv is not None:
        try:
            st.session_state["scan_status"] = "loading"
            uploaded_csv.seek(0)
            df_in = pd.read_csv(uploaded_csv)
            symbols = extract_symbols_from_df(df_in)
            if not symbols:
                st.error("❌ CSV içinde 'Symbol' veya 'Ticker' sütunu bulunamadı.")
                st.session_state["scan_status"] = "error"
                df = st.session_state.get('scan_df', pd.DataFrame())
            else:
                with st.spinner(f"CSV'den {len(symbols)} sembol analiz ediliyor..."):
                    results = scanner.evaluate_symbols_parallel(symbols)
                    df = pd.DataFrame(results)
                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    if not df.empty:
                        df['timestamp'] = now
                    st.session_state['scan_df'] = df
                    st.session_state['scan_src'] = f"csv:{getattr(uploaded_csv, 'name', 'uploaded.csv')}"
                    st.session_state['scan_time'] = now
                    st.session_state['scan_status'] = "completed" if not df.empty else "idle"
                    st.session_state['scan_message'] = f"CSV'den {len(df)} sembol analiz edildi."
                st.rerun()
        except Exception as e:
            st.error(f"CSV okunamadı: {e}")
            df = st.session_state.get('scan_df', pd.DataFrame())
            st.session_state["scan_status"] = "error"

    # --- Ana İçerik Sekmeleri ---
    st.markdown("---")
    tab_signals, tab_market, tab_ai, tab_perf, tab_edu = st.tabs([
        "🎯 Sinyaller (Action Zone)", 
        "📊 Piyasa Tarayıcı", 
        "🧠 AI Laboratuvarı", 
        "📈 Performans & Geçmiş",
        "🎓 FinSense Eğitim"
    ])

    # --- TAB 1: Sinyaller ---
    with tab_signals:
        if df is None or df.empty:
            st.info("Veri yok. Lütfen taramayı çalıştırın.")
        else:
            buyable = df[df["entry_ok"]].copy()
            
            if not buyable.empty:
                buyable["recommendation_score"] = buyable.apply(compute_recommendation_score, axis=1)
                # Sort by score
                buyable = buyable.sort_values("recommendation_score", ascending=False)
                
                # --- Top Fırsatlar (Cards) ---
                st.markdown("### 🔥 En Güçlü Fırsatlar (Top 4)")
                
                top_n = buyable.head(4)
                cols = st.columns(4)
                
                for i, (idx, row) in enumerate(top_n.iterrows()):
                    score = row['recommendation_score']
                    score_color = "#22c55e" if score >= 80 else "#eab308"
                    
                    with cols[i]:
                        st.markdown(f"""
<div style="background: linear-gradient(145deg, #1e293b, #0f172a); border-radius: 12px; padding: 1.5rem; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); position: relative; overflow: hidden; transition: transform 0.2s;">
<div style="position: absolute; top: 0; left: 0; width: 100%; height: 4px; background: {score_color};"></div>
<div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
<div>
<h2 style="margin: 0; font-size: 1.8rem; font-weight: 800; color: #f8fafc;">{row['symbol']}</h2>
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
""", unsafe_allow_html=True)
                        
                        if st.button("🧠 AI Analizi", key=f"btn_card_{row['symbol']}", use_container_width=True):
                            st.session_state['selected_ai_symbol'] = row['symbol']
                            st.toast(f"{row['symbol']} AI Laboratuvarına aktarıldı.", icon="🤖")

                # --- Detaylı Liste (Hibrit Yapı - İnteraktif) ---
                st.markdown("### 📋 Tüm Alım Sinyalleri")
                st.caption("Listeden bir hisse seçerek detaylı analiz kartını görüntüleyebilirsiniz.")

                # 1. Özet Tablo (İnteraktif)
                summary_df = buyable[["symbol", "price", "recommendation_score", "risk_reward", "regime"]].copy()
                summary_df["risk_reward"] = summary_df["risk_reward"].round(2)
                summary_df["recommendation_score"] = summary_df["recommendation_score"].round(1)
                
                # Piyasa Ortalaması (Kıyaslama için)
                if 'recommendation_score' not in df.columns:
                    df["recommendation_score"] = df.apply(compute_recommendation_score, axis=1)
                market_avg_score = df['recommendation_score'].mean()

                # İnteraktif Tablo
                selection = st.dataframe(
                    summary_df,
                    column_config={
                        "symbol": "Sembol",
                        "price": st.column_config.NumberColumn("Fiyat", format="$%.2f"),
                        "recommendation_score": st.column_config.ProgressColumn("Sinyal Gücü", min_value=0, max_value=100, format="%.1f"),
                        "risk_reward": st.column_config.NumberColumn("Risk/Ödül", format="%.2f"),
                        "regime": "Piyasa Rejimi"
                    },
                    use_container_width=True,
                    hide_index=True,
                    height=250,
                    on_select="rerun",
                    selection_mode="single-row",
                    key="signal_list_table"
                )

                # 2. Seçim Mantığı
                selected_symbol_detail = None
                if selection.selection.rows:
                    selected_index = selection.selection.rows[0]
                    selected_symbol_detail = summary_df.iloc[selected_index]['symbol']
                elif not summary_df.empty:
                    # Varsayılan olarak en üsttekini seç
                    selected_symbol_detail = summary_df.iloc[0]['symbol']

                if selected_symbol_detail:
                    row = buyable[buyable['symbol'] == selected_symbol_detail].iloc[0]
                    
                    # FinPilot Edge Hesabı
                    edge_score = row['recommendation_score'] - market_avg_score
                    edge_color = "#22c55e" if edge_score > 0 else "#ef4444"
                    edge_text = f"+{edge_score:.1f}" if edge_score > 0 else f"{edge_score:.1f}"
                    
                    # Detay Kartı Tasarımı
                    strategy_tag = row.get('strategy_tag', row.get('regime', 'N/A'))
                    
                    st.markdown(f"""
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
                    """, unsafe_allow_html=True)

                    c1, c2, c3 = st.columns([2, 1, 1])
                    
                    with c1:
                        st.markdown("#### 💡 Yapay Zeka Görüşü")
                        # Dinamik açıklama
                        reason = "Güçlü momentum ve pozitif trend."
                        if row['recommendation_score'] > 80:
                            reason = "Çok güçlü yükseliş trendi, hacim destekli ve risk düşük."
                        elif row['recommendation_score'] > 60:
                            reason = "Yükseliş potansiyeli var, ancak volatiliteye dikkat edilmeli."
                        
                        st.info(f"{reason}\n\n**Risk/Ödül Oranı:** {row['risk_reward']:.2f}")
                        
                        # FinPilot Edge Göstergesi (Farklılaştırıcı Özellik)
                        st.markdown(f"""
                        <div style="background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px; margin-top: 10px; border-left: 4px solid {edge_color};">
                            <strong style="color: #f8fafc;">🚀 FinPilot Edge:</strong> 
                            <span style="color: #94a3b8;">Piyasa ortalamasından</span> 
                            <strong style="color: {edge_color};">{edge_text} puan</strong> 
                            <span style="color: #94a3b8;">ayrışıyor.</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with c2:
                        st.markdown("#### 🎯 Ticaret Planı")
                        
                        # Kademeli Hedefler (Varsa)
                        tp1 = row.get('tp1')
                        tp2 = row.get('tp2')
                        tp3 = row.get('tp3')
                        
                        if pd.notna(tp1) and pd.notna(tp2):
                            st.markdown(f"""
                            <div style="display: flex; justify-content: space-between; font-size: 0.9rem; margin-bottom: 5px;">
                                <span>TP1 (%50):</span> <strong style="color: #4ade80;">${tp1:.2f}</strong>
                            </div>
                            <div style="display: flex; justify-content: space-between; font-size: 0.9rem; margin-bottom: 5px;">
                                <span>TP2 (%30):</span> <strong style="color: #22c55e;">${tp2:.2f}</strong>
                            </div>
                            """, unsafe_allow_html=True)
                            if pd.notna(tp3) and tp3 > 0:
                                st.markdown(f"""
                                <div style="display: flex; justify-content: space-between; font-size: 0.9rem; margin-bottom: 10px;">
                                    <span>TP3 (%20):</span> <strong style="color: #15803d;">🚀 Trailing Stop</strong>
                                </div>
                                <div style="font-size: 0.75rem; color: #94a3b8; text-align: right;">(Ref: ${tp3:.2f})</div>
                                """, unsafe_allow_html=True)
                        else:
                            st.metric("Hedef (TP)", f"${row['take_profit']:.2f}", delta=f"%{((row['take_profit']-row['price'])/row['price']*100):.1f}")

                        st.metric("Stop (SL)", f"${row['stop_loss']:.2f}", delta=f"-%{((row['price']-row['stop_loss'])/row['price']*100):.1f}", delta_color="inverse")
                        
                        st.markdown("#### 📊 Teknik Göstergeler")
                        st.markdown(f"""
                        - **Rejim:** `{row.get('regime', '-')}`
                        - **Volatilite:** `{row.get('atr', 0):.2f}`
                        """)
                        
                    with c3:
                        st.markdown("#### ⚡ Aksiyon")
                        st.write("Bu hisse için daha derin bir araştırma yapmak ister misiniz?")
                        if st.button("🧠 AI Laboratuvarına Git", key=f"list_btn_{row['symbol']}", type="primary", use_container_width=True):
                            st.session_state['selected_ai_symbol'] = row['symbol']
                            st.toast(f"{row['symbol']} seçildi, AI sekmesine yönlendiriliyorsunuz...", icon="🚀")

            else:
                st.warning("Şu an kriterlere uyan aktif alım sinyali bulunmuyor. Ayarları gevşetmeyi (Agresif Mod) deneyebilirsiniz.")

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
                market_df = market_df[market_df['symbol'].str.contains(search_term.upper())]
            
            if 'recommendation_score' not in market_df.columns:
                market_df["recommendation_score"] = market_df.apply(compute_recommendation_score, axis=1)

            st.dataframe(
                market_df[["symbol", "price", "recommendation_score", "entry_ok", "regime", "sentiment"]],
                column_config={
                    "symbol": "Sembol",
                    "price": st.column_config.NumberColumn("Fiyat", format="$%.2f"),
                    "recommendation_score": st.column_config.ProgressColumn("Skor", min_value=0, max_value=100),
                    "entry_ok": st.column_config.CheckboxColumn("Al Sinyali?"),
                    "regime": "Rejim",
                    "sentiment": st.column_config.NumberColumn("Sentiment", help="-1 (Negatif) ile +1 (Pozitif)")
                },
                use_container_width=True,
                hide_index=True
            )

    # --- TAB 3: AI Laboratuvarı ---
    with tab_ai:
        st.markdown("### 🧠 Yapay Zeka Araştırma Merkezi")
        st.caption("Google Gemini ve DuckDuckGo destekli derinlemesine analiz.")
        
        if df is not None and not df.empty:
            symbol_list = df['symbol'].tolist()
            default_idx = 0
            if 'selected_ai_symbol' in st.session_state and st.session_state['selected_ai_symbol'] in symbol_list:
                default_idx = symbol_list.index(st.session_state['selected_ai_symbol'])
                
            col_sym, col_lang = st.columns([3, 1])
            with col_sym:
                selected_ai_sym = st.selectbox("Analiz edilecek hisseyi seçin:", symbol_list, index=default_idx)
            with col_lang:
                selected_lang = st.selectbox("Rapor Dili:", ["Türkçe", "English", "Deutsch"], index=0)
            
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
        st.markdown("### 📈 Sistem Performansı ve Geçmiş")
        
        # Geçmiş Sinyaller
        signal_log_path = os.path.join(os.getcwd(), "data", "logs", "signal_log.csv")
        if os.path.exists(signal_log_path):
            try:
                log_df = pd.read_csv(signal_log_path, header=None)
                log_df.columns = [
                    "Tarih", "Sembol", "Fiyat", "Stop-Loss", "Take-Profit", "Skor", "Güç", "Rejim", "Sentiment", "Onchain", "Alım?", "Özet", "Neden"
                ]
                st.dataframe(log_df.head(50), use_container_width=True)
            except Exception:
                st.error("Log dosyası okunamadı.")
        else:
            st.info("Henüz geçmiş sinyal kaydı yok.")
            
        # Optimizasyon Sonuçları
        wfo_path = os.path.join(os.getcwd(), "wfo_grid_search_results.csv")
        if os.path.exists(wfo_path):
            st.markdown("#### WFO Backtest Sonuçları")
            wfo_df = pd.read_csv(wfo_path)
            st.dataframe(wfo_df, use_container_width=True)

    # --- TAB 5: FinSense Eğitim ---
    with tab_edu:
        render_finsense_page()
