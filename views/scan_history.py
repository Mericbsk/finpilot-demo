"""
Scanner History — Tüm tarama sonuçlarını birleştirip takip eden modül.

77+ ayrı shortlist CSV dosyasını tek bir konsolide görünümde sunar.
Tarih/saat, hisse bazlı filtreleme, entry sinyal geçmişi ve trend takibi sağlar.
"""

import glob
import logging
import os
from datetime import datetime

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

SHORTLIST_DIR = os.path.join("data", "shortlists")
SUGGESTIONS_DIR = os.path.join("data", "suggestions")


# ─── DATA LOADING ──────────────────────────────────────────


def _parse_scan_datetime(filename: str):
    """Extract datetime from filename like shortlist_20251201_2111.csv"""
    try:
        base = os.path.basename(filename).replace(".csv", "")
        # Standard format: shortlist_YYYYMMDD_HHMM
        parts = base.split("_")
        for i, p in enumerate(parts):
            if len(p) == 8 and p.isdigit() and p.startswith("20"):
                date_str = p
                time_str = parts[i + 1] if i + 1 < len(parts) and len(parts[i + 1]) == 4 and parts[i + 1].isdigit() else "0000"
                return datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M")
    except Exception:
        pass
    return None


def load_all_scans() -> pd.DataFrame:
    """Load all shortlist CSVs into a single DataFrame with scan metadata."""
    all_files = sorted(glob.glob(os.path.join(SHORTLIST_DIR, "shortlist_*.csv")))

    if not all_files:
        return pd.DataFrame()

    frames = []
    for fpath in all_files:
        try:
            df = pd.read_csv(fpath)
            if df.empty:
                continue

            scan_dt = _parse_scan_datetime(fpath)
            if scan_dt is None:
                continue

            df["scan_date"] = scan_dt.strftime("%Y-%m-%d")
            df["scan_time"] = scan_dt.strftime("%H:%M")
            df["scan_datetime"] = scan_dt
            df["scan_file"] = os.path.basename(fpath)
            frames.append(df)
        except Exception as e:
            logger.warning(f"Dosya okunamadı: {fpath}: {e}")
            continue

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values("scan_datetime", ascending=False)
    return combined


def get_scan_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Her tarama oturumu için özet istatistikler."""
    if df.empty:
        return pd.DataFrame()

    summary = df.groupby(["scan_date", "scan_time"]).agg(
        total_stocks=("symbol", "count"),
        entry_signals=("entry_ok", lambda x: x.sum() if x.dtype == bool else (x == True).sum()),
        avg_score=("score", "mean"),
        top_symbol=("symbol", "first"),
        scan_file=("scan_file", "first"),
    ).reset_index()

    summary = summary.sort_values(["scan_date", "scan_time"], ascending=[False, False])
    summary.columns = ["📅 Tarih", "🕐 Saat", "📊 Hisse", "🟢 Sinyal", "⭐ Ort. Skor", "🏆 Top", "Dosya"]
    return summary


def get_entry_signals_history(df: pd.DataFrame) -> pd.DataFrame:
    """Sadece entry_ok=True olan sinyalleri tarihsel olarak listele."""
    if df.empty:
        return pd.DataFrame()

    entry_df = df[df["entry_ok"] == True].copy()
    if entry_df.empty:
        return pd.DataFrame()

    cols = ["scan_date", "scan_time", "symbol", "price", "score"]
    optional_cols = ["stop_loss", "take_profit", "risk_reward", "filter_score",
                     "momentum_3d_pct", "volume_multiple", "ema_gap_pct"]
    for c in optional_cols:
        if c in entry_df.columns:
            cols.append(c)

    entry_df = entry_df[cols].sort_values(["scan_date", "scan_time"], ascending=[False, False])
    return entry_df


def get_symbol_history(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """Bir hissenin tüm tarama geçmişi."""
    if df.empty:
        return pd.DataFrame()

    sym_df = df[df["symbol"] == symbol].copy()
    if sym_df.empty:
        return pd.DataFrame()

    cols = ["scan_date", "scan_time", "price", "score", "entry_ok"]
    optional_cols = ["direction", "filter_score", "volume_multiple",
                     "momentum_3d_pct", "ema_gap_pct", "stop_loss", "take_profit"]
    for c in optional_cols:
        if c in sym_df.columns:
            cols.append(c)

    return sym_df[cols].sort_values(["scan_date", "scan_time"], ascending=[False, False])


def get_most_signaled_stocks(df: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    """En çok entry sinyali veren hisseler."""
    if df.empty:
        return pd.DataFrame()

    entry_df = df[df["entry_ok"] == True]
    if entry_df.empty:
        return pd.DataFrame()

    counts = entry_df.groupby("symbol").agg(
        signal_count=("entry_ok", "count"),
        avg_price=("price", "mean"),
        avg_score=("score", "mean"),
        last_signal=("scan_date", "max"),
        first_signal=("scan_date", "min"),
    ).reset_index()

    counts = counts.sort_values("signal_count", ascending=False).head(top_n)
    counts.columns = ["Hisse", "Sinyal Sayısı", "Ort. Fiyat", "Ort. Skor", "Son Sinyal", "İlk Sinyal"]
    return counts


# ─── UI RENDERING ──────────────────────────────────────────


def render_scan_history_page():
    """Ana scanner geçmişi sayfası."""

    st.markdown("""
    <div style='background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
         padding: 24px; border-radius: 16px; margin-bottom: 24px;
         border: 1px solid #334155;'>
        <h2 style='color: #f8fafc; margin: 0;'>📋 Scanner Geçmişi</h2>
        <p style='color: #94a3b8; margin: 4px 0 0;'>
            Tüm tarama sonuçları • Tarihsel sinyal takibi • Hisse bazlı analiz
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Load all data
    with st.spinner("Tarama geçmişi yükleniyor..."):
        all_data = load_all_scans()

    if all_data.empty:
        st.warning("Henüz tarama verisi bulunamadı. `data/shortlists/` klasörünü kontrol edin.")
        return

    # ─── KPI CARDS ─────────────────────────────────────────
    unique_dates = all_data["scan_date"].nunique()
    total_scans = all_data.groupby(["scan_date", "scan_time"]).ngroups
    total_entries = (all_data["entry_ok"] == True).sum()
    unique_symbols = all_data["symbol"].nunique()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📅 Taranan Gün", unique_dates)
    c2.metric("🔄 Toplam Tarama", total_scans)
    c3.metric("🟢 Entry Sinyali", int(total_entries))
    c4.metric("📊 Farklı Hisse", unique_symbols)

    st.markdown("---")

    # ─── TABS ──────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Tarama Özeti",
        "🟢 Entry Sinyalleri",
        "🔍 Hisse Takibi",
        "🏆 En Çok Sinyal Verenler"
    ])

    # ── TAB 1: Tarama Özeti ──
    with tab1:
        st.subheader("Tüm Tarama Oturumları")

        summary = get_scan_summary(all_data)
        if not summary.empty:
            # Date filter
            all_dates = sorted(all_data["scan_date"].unique(), reverse=True)
            date_options = ["Tümü"] + all_dates
            selected_date = st.selectbox("📅 Tarih Filtresi", date_options, key="hist_date_filter")

            if selected_date != "Tümü":
                summary = summary[summary["📅 Tarih"] == selected_date]

            st.dataframe(
                summary.drop(columns=["Dosya"]),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "📊 Hisse": st.column_config.NumberColumn(format="%d"),
                    "🟢 Sinyal": st.column_config.NumberColumn(format="%d"),
                    "⭐ Ort. Skor": st.column_config.NumberColumn(format="%.1f"),
                },
            )

            st.caption(f"Toplam {len(summary)} tarama oturumu gösteriliyor")

            # Expandable: show a specific scan's detail
            st.markdown("#### 📄 Tarama Detayı")
            scan_options = summary.apply(
                lambda r: f"{r['📅 Tarih']} {r['🕐 Saat']} ({r['📊 Hisse']} hisse, {r['🟢 Sinyal']} sinyal)",
                axis=1
            ).tolist()

            if scan_options:
                selected_scan = st.selectbox("Tarama seçin:", scan_options, key="scan_detail_select")
                idx = scan_options.index(selected_scan)
                selected_row = summary.iloc[idx]
                scan_date = selected_row["📅 Tarih"]
                scan_time = selected_row["🕐 Saat"]

                detail = all_data[
                    (all_data["scan_date"] == scan_date) &
                    (all_data["scan_time"] == scan_time)
                ]

                display_cols = ["symbol", "price", "score", "entry_ok", "direction"]
                optional_display = ["filter_score", "volume_multiple", "momentum_3d_pct",
                                    "ema_gap_pct", "stop_loss", "take_profit", "risk_reward"]
                for c in optional_display:
                    if c in detail.columns:
                        display_cols.append(c)

                detail_show = detail[display_cols].copy()
                detail_show = detail_show.sort_values(["entry_ok", "score"], ascending=[False, False])

                # Color entry_ok
                st.dataframe(
                    detail_show,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "entry_ok": st.column_config.CheckboxColumn("Entry", default=False),
                        "price": st.column_config.NumberColumn("Fiyat", format="$%.2f"),
                        "score": st.column_config.NumberColumn("Skor", format="%d"),
                        "stop_loss": st.column_config.NumberColumn("Stop", format="$%.2f"),
                        "take_profit": st.column_config.NumberColumn("Hedef", format="$%.2f"),
                        "risk_reward": st.column_config.NumberColumn("R/R", format="%.1f"),
                    },
                )

    # ── TAB 2: Entry Sinyalleri ──
    with tab2:
        st.subheader("🟢 Tüm Entry Sinyalleri (Alım Fırsatları)")
        st.caption("entry_ok = True olan tüm sinyaller, tarih sırasıyla")

        entries = get_entry_signals_history(all_data)
        if entries.empty:
            st.info("Henüz entry sinyali kaydedilmemiş.")
        else:
            # Date range filter
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                min_date = entries["scan_date"].min()
                max_date = entries["scan_date"].max()
                start_date = st.date_input("Başlangıç", value=pd.to_datetime(min_date), key="entry_start")
            with col_f2:
                end_date = st.date_input("Bitiş", value=pd.to_datetime(max_date), key="entry_end")

            filtered = entries[
                (entries["scan_date"] >= str(start_date)) &
                (entries["scan_date"] <= str(end_date))
            ]

            rename_map = {
                "scan_date": "📅 Tarih", "scan_time": "🕐 Saat",
                "symbol": "Hisse", "price": "Fiyat",
                "score": "Skor", "stop_loss": "Stop Loss",
                "take_profit": "Hedef", "risk_reward": "R/R",
                "filter_score": "Filtre", "momentum_3d_pct": "3g Mom%",
                "volume_multiple": "Hacim x", "ema_gap_pct": "EMA%",
            }
            display = filtered.rename(columns={k: v for k, v in rename_map.items() if k in filtered.columns})

            st.dataframe(
                display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Fiyat": st.column_config.NumberColumn(format="$%.2f"),
                    "Stop Loss": st.column_config.NumberColumn(format="$%.2f"),
                    "Hedef": st.column_config.NumberColumn(format="$%.2f"),
                    "R/R": st.column_config.NumberColumn(format="%.1f"),
                },
            )

            st.success(f"Toplam {len(filtered)} entry sinyali ({start_date} → {end_date})")

    # ── TAB 3: Hisse Takibi ──
    with tab3:
        st.subheader("🔍 Hisse Bazlı Geçmiş")

        all_symbols = sorted(all_data["symbol"].unique())
        selected_symbol = st.selectbox(
            "Hisse seçin:", all_symbols, key="symbol_tracker"
        )

        if selected_symbol:
            sym_history = get_symbol_history(all_data, selected_symbol)
            if sym_history.empty:
                st.info(f"{selected_symbol} için veri bulunamadı.")
            else:
                # Summary metrics
                total_appearances = len(sym_history)
                entry_count = (sym_history["entry_ok"] == True).sum()
                price_range = f"${sym_history['price'].min():.2f} — ${sym_history['price'].max():.2f}"
                last_price = sym_history.iloc[0]["price"]

                mc1, mc2, mc3, mc4 = st.columns(4)
                mc1.metric(f"{selected_symbol}", f"${last_price:.2f}")
                mc2.metric("Taramada Görünme", total_appearances)
                mc3.metric("Entry Sinyali", int(entry_count))
                mc4.metric("Fiyat Aralığı", price_range)

                # Price chart over scans
                if "price" in sym_history.columns and len(sym_history) > 1:
                    chart_data = sym_history[["scan_date", "price"]].copy()
                    chart_data = chart_data.sort_values("scan_date")
                    chart_data = chart_data.set_index("scan_date")
                    st.line_chart(chart_data["price"], use_container_width=True)

                # History table
                rename_map = {
                    "scan_date": "📅 Tarih", "scan_time": "🕐 Saat",
                    "price": "Fiyat", "score": "Skor", "entry_ok": "Entry",
                    "direction": "Yön", "filter_score": "Filtre",
                    "volume_multiple": "Hacim x", "momentum_3d_pct": "3g Mom%",
                    "ema_gap_pct": "EMA%", "stop_loss": "Stop", "take_profit": "Hedef",
                }
                display = sym_history.rename(columns={k: v for k, v in rename_map.items() if k in sym_history.columns})

                st.dataframe(
                    display,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Entry": st.column_config.CheckboxColumn(default=False),
                        "Fiyat": st.column_config.NumberColumn(format="$%.2f"),
                        "Stop": st.column_config.NumberColumn(format="$%.2f"),
                        "Hedef": st.column_config.NumberColumn(format="$%.2f"),
                    },
                )

    # ── TAB 4: En Çok Sinyal Verenler ──
    with tab4:
        st.subheader("🏆 En Çok Entry Sinyali Veren Hisseler")
        st.caption("Tekrarlayan alım fırsatları — güçlü trendlerin göstergesi")

        top_n = st.slider("Kaç hisse gösterilsin?", 5, 30, 15, key="top_n_slider")
        top_stocks = get_most_signaled_stocks(all_data, top_n=top_n)

        if top_stocks.empty:
            st.info("Henüz yeterli entry sinyali yok.")
        else:
            # Bar chart
            chart_df = top_stocks.set_index("Hisse")["Sinyal Sayısı"]
            st.bar_chart(chart_df, use_container_width=True)

            # Table
            st.dataframe(
                top_stocks,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Ort. Fiyat": st.column_config.NumberColumn(format="$%.2f"),
                    "Ort. Skor": st.column_config.NumberColumn(format="%.1f"),
                },
            )

    # ─── EXPORT ────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📥 Dışa Aktar")

    col_ex1, col_ex2 = st.columns(2)
    with col_ex1:
        # Export all entries
        entries = get_entry_signals_history(all_data)
        if not entries.empty:
            csv_data = entries.to_csv(index=False)
            st.download_button(
                "📥 Tüm Entry Sinyallerini İndir (CSV)",
                csv_data,
                file_name=f"finpilot_entry_signals_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )
    with col_ex2:
        # Export full history
        if not all_data.empty:
            export_cols = ["scan_date", "scan_time", "symbol", "price", "score",
                           "entry_ok", "direction"]
            optional = ["filter_score", "stop_loss", "take_profit", "risk_reward"]
            for c in optional:
                if c in all_data.columns:
                    export_cols.append(c)
            csv_full = all_data[export_cols].to_csv(index=False)
            st.download_button(
                "📥 Tüm Tarama Geçmişini İndir (CSV)",
                csv_full,
                file_name=f"finpilot_scan_history_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )
