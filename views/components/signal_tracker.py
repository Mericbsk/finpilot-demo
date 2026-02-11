"""
Signal Performance Tracker for FinPilot.

Reads historical signals from signal_log.csv and shortlist CSVs,
fetches subsequent price data, and calculates outcome metrics:
- Did the signal hit Take Profit (TP)?
- Did it hit Stop Loss (SL)?
- What was the return after 1 day, 1 week, 1 month?

Provides KPI calculations and Streamlit rendering functions.
"""

from __future__ import annotations

import csv
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SIGNAL_LOG_PATH = os.path.join(os.getcwd(), "data", "logs", "signal_log.csv")
SHORTLISTS_DIR = os.path.join(os.getcwd(), "data", "shortlists")

SIGNAL_LOG_COLUMNS = [
    "timestamp",
    "symbol",
    "price",
    "stop_loss",
    "take_profit",
    "score",
    "strength",
    "regime",
    "sentiment",
    "onchain",
    "entry_ok",
    "summary",
    "reason",
]


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------
@dataclass
class SignalOutcome:
    """Result of tracking a single signal forward in time."""

    symbol: str
    signal_date: str
    entry_price: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    score: float
    entry_ok: bool

    # Outcome fields (filled after price lookup)
    current_price: Optional[float] = None
    price_1d: Optional[float] = None
    price_1w: Optional[float] = None
    price_1m: Optional[float] = None
    change_pct: Optional[float] = None
    change_1d_pct: Optional[float] = None
    change_1w_pct: Optional[float] = None
    change_1m_pct: Optional[float] = None
    status: str = "⏳ Açık"  # ✅ TP Ulaştı | ❌ SL Tetiklendi | ⏳ Açık
    hit_date: Optional[str] = None
    days_to_result: Optional[int] = None


# ---------------------------------------------------------------------------
# Signal Logging (Write)
# ---------------------------------------------------------------------------
def log_signals_to_csv(df: pd.DataFrame) -> int:
    """
    Append scan results to signal_log.csv.

    Args:
        df: DataFrame from scanner results with columns like
            symbol, price, stop_loss, take_profit, etc.

    Returns:
        Number of signals logged.
    """
    if df is None or df.empty:
        return 0

    os.makedirs(os.path.dirname(SIGNAL_LOG_PATH), exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    count = 0

    try:
        with open(SIGNAL_LOG_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for _, row in df.iterrows():
                writer.writerow(
                    [
                        now,
                        row.get("symbol", ""),
                        row.get("price", ""),
                        row.get("stop_loss", ""),
                        row.get("take_profit", ""),
                        row.get("recommendation_score", row.get("score", "")),
                        row.get("strength", row.get("filter_score", "")),
                        row.get("regime", ""),
                        row.get("sentiment", ""),
                        row.get("onchain_metric", row.get("onchain", "")),
                        row.get("entry_ok", ""),
                        row.get("why", row.get("summary", "")),
                        row.get("reason", ""),
                    ]
                )
                count += 1
        logger.info(f"Logged {count} signals to {SIGNAL_LOG_PATH}")
    except Exception as e:
        logger.error(f"Failed to log signals: {e}")

    return count


# ---------------------------------------------------------------------------
# Signal Reading
# ---------------------------------------------------------------------------
def load_signal_log() -> pd.DataFrame:
    """Load signal_log.csv into a DataFrame with proper columns."""
    if not os.path.exists(SIGNAL_LOG_PATH):
        return pd.DataFrame(columns=SIGNAL_LOG_COLUMNS)

    try:
        df = pd.read_csv(SIGNAL_LOG_PATH, header=None, names=SIGNAL_LOG_COLUMNS)
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        df["stop_loss"] = pd.to_numeric(df["stop_loss"], errors="coerce")
        df["take_profit"] = pd.to_numeric(df["take_profit"], errors="coerce")
        df["score"] = pd.to_numeric(df["score"], errors="coerce")
        df["strength"] = pd.to_numeric(df["strength"], errors="coerce")
        df["entry_ok"] = (
            df["entry_ok"].astype(str).str.lower().isin({"1", "true", "evet", "al", "yes"})
        )
        df = df.dropna(subset=["timestamp", "symbol", "price"])
        df = df.sort_values("timestamp", ascending=False)
        return df
    except Exception as e:
        logger.error(f"Failed to load signal log: {e}")
        return pd.DataFrame(columns=SIGNAL_LOG_COLUMNS)


def load_all_shortlists() -> pd.DataFrame:
    """Load and combine all shortlist CSVs from data/shortlists/."""
    if not os.path.exists(SHORTLISTS_DIR):
        return pd.DataFrame()

    frames = []
    for fname in sorted(os.listdir(SHORTLISTS_DIR)):
        if not fname.startswith("shortlist_") or not fname.endswith(".csv"):
            continue
        fpath = os.path.join(SHORTLISTS_DIR, fname)
        try:
            sdf = pd.read_csv(fpath)
            if "symbol" in sdf.columns and "price" in sdf.columns:
                # Extract date from filename: shortlist_YYYYMMDD_HHMM.csv
                date_str = fname.replace("shortlist_", "").replace(".csv", "")
                parts = date_str.split("_")
                if len(parts) >= 2:
                    try:
                        parsed = datetime.strptime(f"{parts[0]}_{parts[1]}", "%Y%m%d_%H%M")
                        sdf["scan_date"] = parsed
                    except ValueError:
                        sdf["scan_date"] = pd.NaT
                frames.append(sdf)
        except Exception as e:
            logger.debug(f"Skipping {fname}: {e}")

    if not frames:
        return pd.DataFrame()

    # Filter out empty frames to avoid FutureWarning
    frames = [f for f in frames if not f.empty and not f.isna().all().all()]
    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    combined["price"] = pd.to_numeric(combined["price"], errors="coerce")
    combined["stop_loss"] = pd.to_numeric(
        combined.get("stop_loss", pd.Series(dtype=float)), errors="coerce"
    )
    combined["take_profit"] = pd.to_numeric(
        combined.get("take_profit", pd.Series(dtype=float)), errors="coerce"
    )
    return combined


# ---------------------------------------------------------------------------
# Price Fetching & Outcome Calculation
# ---------------------------------------------------------------------------
@st.cache_data(ttl=900, show_spinner=False)
def _fetch_price_history(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch daily price history for a symbol between two dates."""
    try:
        import yfinance as yf

        df = yf.download(
            symbol,
            start=start_date,
            end=end_date,
            interval="1d",
            progress=False,
            auto_adjust=True,
        )
        if df is not None and not df.empty:
            # Handle MultiIndex columns from yfinance
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df.reset_index()
            return df
    except Exception as e:
        logger.debug(f"Price fetch failed for {symbol}: {e}")
    return pd.DataFrame()


def calculate_signal_outcomes(
    signals_df: pd.DataFrame,
    max_signals: int = 100,
) -> pd.DataFrame:
    """
    For each signal, fetch subsequent prices and determine outcome.

    Returns a DataFrame with outcome columns added.
    """
    if signals_df.empty:
        return pd.DataFrame()

    # Deduplicate: keep latest signal per symbol per day
    if "timestamp" in signals_df.columns:
        signals_df = signals_df.copy()
        signals_df["date_only"] = pd.to_datetime(signals_df["timestamp"], errors="coerce").dt.date
        signals_df = signals_df.drop_duplicates(subset=["symbol", "date_only"], keep="first")
    elif "scan_date" in signals_df.columns:
        signals_df = signals_df.copy()
        signals_df["date_only"] = pd.to_datetime(signals_df["scan_date"], errors="coerce").dt.date
        signals_df = signals_df.drop_duplicates(subset=["symbol", "date_only"], keep="first")

    # Limit for performance
    signals_df = signals_df.head(max_signals)

    results = []
    today = datetime.now()

    for _, row in signals_df.iterrows():
        symbol = str(row.get("symbol", ""))
        entry_price = float(row.get("price", 0))

        if not symbol or entry_price <= 0:
            continue

        # Parse signal date
        sig_date = row.get("timestamp", row.get("scan_date", None))
        if pd.isna(sig_date):
            continue
        sig_dt = pd.to_datetime(sig_date)

        sl = row.get("stop_loss", None)
        tp = row.get("take_profit", None)
        if pd.notna(sl):
            sl = float(sl)
        else:
            sl = None
        if pd.notna(tp):
            tp = float(tp)
        else:
            tp = None

        score = float(row.get("score", row.get("recommendation_score", 0)))
        entry_ok = bool(row.get("entry_ok", False))

        outcome = SignalOutcome(
            symbol=symbol,
            signal_date=sig_dt.strftime("%Y-%m-%d"),
            entry_price=round(entry_price, 2),
            stop_loss=round(sl, 2) if sl else None,
            take_profit=round(tp, 2) if tp else None,
            score=round(score, 1),
            entry_ok=entry_ok,
        )

        # Fetch prices from signal date to today
        start_str = sig_dt.strftime("%Y-%m-%d")
        end_str = (today + timedelta(days=1)).strftime("%Y-%m-%d")
        hist = _fetch_price_history(symbol, start_str, end_str)

        if hist.empty or "Close" not in hist.columns:
            results.append(outcome)
            continue

        close_series = hist["Close"].values
        date_series = pd.to_datetime(hist["Date"]) if "Date" in hist.columns else hist.index

        # Current price (latest)
        outcome.current_price = round(float(close_series[-1]), 2)
        outcome.change_pct = round((outcome.current_price - entry_price) / entry_price * 100, 2)

        # 1-day return
        if len(close_series) >= 2:
            outcome.price_1d = round(float(close_series[1]), 2)
            outcome.change_1d_pct = round((outcome.price_1d - entry_price) / entry_price * 100, 2)

        # 1-week return (~5 trading days)
        if len(close_series) >= 6:
            outcome.price_1w = round(float(close_series[5]), 2)
            outcome.change_1w_pct = round((outcome.price_1w - entry_price) / entry_price * 100, 2)

        # 1-month return (~21 trading days)
        if len(close_series) >= 22:
            outcome.price_1m = round(float(close_series[21]), 2)
            outcome.change_1m_pct = round((outcome.price_1m - entry_price) / entry_price * 100, 2)

        # Check SL/TP hit
        if sl and tp:
            high_series = hist["High"].values if "High" in hist.columns else close_series
            low_series = hist["Low"].values if "Low" in hist.columns else close_series

            for i in range(1, len(close_series)):
                low_val = float(low_series[i])
                high_val = float(high_series[i])

                if low_val <= sl:
                    outcome.status = "❌ SL"
                    if hasattr(date_series, "iloc"):
                        outcome.hit_date = date_series.iloc[i].strftime("%Y-%m-%d")
                    outcome.days_to_result = i
                    break
                elif high_val >= tp:
                    outcome.status = "✅ TP"
                    if hasattr(date_series, "iloc"):
                        outcome.hit_date = date_series.iloc[i].strftime("%Y-%m-%d")
                    outcome.days_to_result = i
                    break
        elif outcome.change_pct is not None:
            # No SL/TP defined, just use % change for status
            if outcome.change_pct >= 3.0:
                outcome.status = "✅ Kâr"
            elif outcome.change_pct <= -3.0:
                outcome.status = "❌ Zarar"

        results.append(outcome)

    # Convert to DataFrame
    if not results:
        return pd.DataFrame()

    records = []
    for o in results:
        records.append(
            {
                "Sembol": o.symbol,
                "Sinyal Tarihi": o.signal_date,
                "Giriş $": o.entry_price,
                "SL $": o.stop_loss if o.stop_loss else "-",
                "TP $": o.take_profit if o.take_profit else "-",
                "Skor": o.score,
                "Şu An $": o.current_price if o.current_price else "-",
                "Değişim %": o.change_pct if o.change_pct is not None else "-",
                "1G %": o.change_1d_pct if o.change_1d_pct is not None else "-",
                "1H %": o.change_1w_pct if o.change_1w_pct is not None else "-",
                "1A %": o.change_1m_pct if o.change_1m_pct is not None else "-",
                "Durum": o.status,
                "Sonuç Gün": o.days_to_result if o.days_to_result else "-",
                "Giriş?": "✅" if o.entry_ok else "—",
            }
        )

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# KPI Calculations
# ---------------------------------------------------------------------------
def calculate_kpis(outcomes_df: pd.DataFrame) -> Dict:
    """Calculate performance KPIs from outcomes DataFrame."""
    if outcomes_df.empty:
        return {
            "total": 0,
            "tp_count": 0,
            "sl_count": 0,
            "open_count": 0,
            "win_rate": 0.0,
            "avg_return": 0.0,
            "best_signal": None,
            "worst_signal": None,
            "avg_days_to_result": 0,
        }

    total = len(outcomes_df)
    tp_count = len(outcomes_df[outcomes_df["Durum"].str.contains("TP|Kâr", na=False)])
    sl_count = len(outcomes_df[outcomes_df["Durum"].str.contains("SL|Zarar", na=False)])
    open_count = len(outcomes_df[outcomes_df["Durum"].str.contains("Açık", na=False)])

    closed = tp_count + sl_count
    win_rate = (tp_count / closed * 100) if closed > 0 else 0.0

    # Average return
    change_col = outcomes_df["Değişim %"]
    numeric_changes = pd.to_numeric(change_col, errors="coerce").dropna()
    avg_return = float(numeric_changes.mean()) if not numeric_changes.empty else 0.0

    # Best / worst
    best_signal = None
    worst_signal = None
    if not numeric_changes.empty:
        best_idx = numeric_changes.idxmax()
        worst_idx = numeric_changes.idxmin()
        best_row = outcomes_df.loc[best_idx]
        worst_row = outcomes_df.loc[worst_idx]
        best_signal = f"{best_row['Sembol']} (+{numeric_changes[best_idx]:.1f}%)"
        worst_signal = f"{worst_row['Sembol']} ({numeric_changes[worst_idx]:.1f}%)"

    # Avg days to result
    days_col = outcomes_df["Sonuç Gün"]
    numeric_days = pd.to_numeric(days_col, errors="coerce").dropna()
    avg_days = float(numeric_days.mean()) if not numeric_days.empty else 0

    return {
        "total": total,
        "tp_count": tp_count,
        "sl_count": sl_count,
        "open_count": open_count,
        "win_rate": round(win_rate, 1),
        "avg_return": round(avg_return, 2),
        "best_signal": best_signal,
        "worst_signal": worst_signal,
        "avg_days_to_result": round(avg_days, 1),
    }


# ---------------------------------------------------------------------------
# Streamlit Rendering
# ---------------------------------------------------------------------------
def render_signal_performance_tab():
    """Render the full Signal Performance tab in the dashboard."""
    st.markdown("### 📈 Sinyal Performans Takibi")
    st.caption(
        "Geçmiş sinyallerin gerçek piyasa performansı. "
        "Her sinyal için giriş fiyatı, hedef, stop-loss ve sonuç."
    )

    # --- Data Source Selection ---
    source = st.radio(
        "Veri Kaynağı",
        ["📋 Sinyal Logu", "📁 Shortlist Arşivi"],
        horizontal=True,
        key="perf_data_source",
    )

    # --- Period Filter ---
    col_period, col_limit = st.columns([3, 1])
    with col_period:
        period = st.radio(
            "Dönem",
            ["Tümü", "Son 90 Gün", "Son 30 Gün", "Son 7 Gün"],
            horizontal=True,
            key="perf_period",
        )
    with col_limit:
        max_signals = st.selectbox(
            "Maks Sinyal",
            [25, 50, 100],
            index=0,
            key="perf_max_signals",
        )

    # --- Load Data ---
    if source == "📋 Sinyal Logu":
        raw_df = load_signal_log()
        date_col = "timestamp"
    else:
        raw_df = load_all_shortlists()
        date_col = "scan_date"

    if raw_df.empty:
        st.info(
            "Henüz kayıtlı sinyal bulunmuyor. "
            "Tarama yaptığınızda sinyaller otomatik olarak kaydedilecektir."
        )
        return

    # Show total count before filtering
    total_before_filter = len(raw_df)

    # Apply period filter
    if date_col in raw_df.columns:
        raw_df[date_col] = pd.to_datetime(raw_df[date_col], errors="coerce")
        now = pd.Timestamp.now()
        if period == "Son 7 Gün":
            raw_df = raw_df[raw_df[date_col] >= now - pd.Timedelta(days=7)]
        elif period == "Son 30 Gün":
            raw_df = raw_df[raw_df[date_col] >= now - pd.Timedelta(days=30)]
        elif period == "Son 90 Gün":
            raw_df = raw_df[raw_df[date_col] >= now - pd.Timedelta(days=90)]

    if raw_df.empty:
        # Determine the date range of available data
        reload_df = load_signal_log() if source == "📋 Sinyal Logu" else load_all_shortlists()
        d_col = "timestamp" if source == "📋 Sinyal Logu" else "scan_date"
        if d_col in reload_df.columns and not reload_df.empty:
            reload_df[d_col] = pd.to_datetime(reload_df[d_col], errors="coerce")
            min_d = reload_df[d_col].min()
            max_d = reload_df[d_col].max()
            st.warning(
                f"Seçilen dönemde sinyal bulunamadı. "
                f"Mevcut veriler **{min_d:%d.%m.%Y}** – **{max_d:%d.%m.%Y}** arasında "
                f"({total_before_filter} sinyal). **'Tümü'** filtresini deneyin."
            )
        else:
            st.warning("Seçilen dönemde sinyal bulunamadı.")
        return

    st.markdown(f"*{len(raw_df)} sinyal bulundu, sonuçlar hesaplanıyor...*")

    # --- Calculate Outcomes ---
    with st.spinner("Fiyat verileri çekiliyor ve sonuçlar hesaplanıyor..."):
        outcomes_df = calculate_signal_outcomes(raw_df, max_signals=max_signals)

    if outcomes_df.empty:
        st.warning("Sonuç hesaplanamadı. Veri yetersiz olabilir.")
        return

    # --- KPI Dashboard ---
    kpis = calculate_kpis(outcomes_df)

    st.markdown("#### 📊 Performans Özeti")
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Toplam Sinyal", kpis["total"])
    k2.metric(
        "Başarı Oranı",
        f"%{kpis['win_rate']}",
        delta=f"{kpis['tp_count']} TP / {kpis['sl_count']} SL",
    )
    k3.metric(
        "Ort. Getiri",
        f"%{kpis['avg_return']}",
        delta="pozitif" if kpis["avg_return"] > 0 else "negatif",
        delta_color="normal" if kpis["avg_return"] > 0 else "inverse",
    )
    k4.metric("Açık Pozisyon", kpis["open_count"])
    k5.metric("Ort. Sonuç Süresi", f"{kpis['avg_days_to_result']} gün")

    # Best / Worst
    if kpis["best_signal"] or kpis["worst_signal"]:
        b1, b2 = st.columns(2)
        if kpis["best_signal"]:
            b1.success(f"🏆 En İyi: {kpis['best_signal']}")
        if kpis["worst_signal"]:
            b2.error(f"📉 En Kötü: {kpis['worst_signal']}")

    st.markdown("---")

    # --- Results Table ---
    st.markdown("#### 📋 Sinyal Sonuç Tablosu")

    # Color-coded status filter
    status_filter = st.multiselect(
        "Durum Filtresi",
        ["✅ TP", "✅ Kâr", "❌ SL", "❌ Zarar", "⏳ Açık"],
        default=["✅ TP", "✅ Kâr", "❌ SL", "❌ Zarar", "⏳ Açık"],
        key="perf_status_filter",
    )

    display_df = outcomes_df[
        outcomes_df["Durum"].apply(lambda s: any(f in s for f in status_filter))
    ].copy()

    if display_df.empty:
        st.info("Seçili filtreye uygun sinyal yok.")
    else:
        # Style the dataframe
        st.dataframe(
            display_df,
            column_config={
                "Sembol": st.column_config.TextColumn("Sembol", width="small"),
                "Sinyal Tarihi": st.column_config.TextColumn("Tarih", width="small"),
                "Giriş $": st.column_config.NumberColumn("Giriş $", format="%.2f"),
                "Şu An $": st.column_config.TextColumn("Şu An $"),
                "Değişim %": st.column_config.TextColumn("Değişim %"),
                "1G %": st.column_config.TextColumn("1 Gün %"),
                "1H %": st.column_config.TextColumn("1 Hafta %"),
                "1A %": st.column_config.TextColumn("1 Ay %"),
                "Skor": st.column_config.NumberColumn("Skor", format="%.0f"),
                "Durum": st.column_config.TextColumn("Durum", width="small"),
                "Sonuç Gün": st.column_config.TextColumn("Gün", width="small"),
                "Giriş?": st.column_config.TextColumn("Giriş?", width="small"),
            },
            use_container_width=True,
            hide_index=True,
            height=min(len(display_df) * 38 + 40, 600),
        )

    st.markdown("---")

    # --- Equity Curve ---
    st.markdown("#### 📈 Kümülatif Getiri")
    _render_equity_curve(outcomes_df)

    # --- Top Signals Cards ---
    st.markdown("#### 🏆 En Başarılı 5 Sinyal")
    _render_top_signals(outcomes_df, n=5)


def _render_equity_curve(outcomes_df: pd.DataFrame):
    """Render a cumulative return chart from outcomes."""
    try:
        import altair as alt
    except ImportError:
        st.info("Grafik için altair gerekli.")
        return

    change_col = pd.to_numeric(outcomes_df["Değişim %"], errors="coerce")
    valid_mask = change_col.notna()

    if valid_mask.sum() < 2:
        st.info("Grafik için yeterli veri yok (en az 2 sonuçlanmış sinyal gerekli).")
        return

    chart_df = outcomes_df[valid_mask].copy()
    chart_df["return_pct"] = change_col[valid_mask].values
    chart_df = chart_df.sort_values("Sinyal Tarihi")
    chart_df["cumulative_return"] = chart_df["return_pct"].cumsum()
    chart_df["index"] = range(len(chart_df))

    # Build chart
    base = alt.Chart(chart_df).encode(
        x=alt.X("Sinyal Tarihi:N", title="Sinyal Tarihi", sort=None),
    )

    line = base.mark_line(color="#00e6e6", strokeWidth=2.5).encode(
        y=alt.Y("cumulative_return:Q", title="Kümülatif Getiri (%)"),
        tooltip=[
            alt.Tooltip("Sembol:N"),
            alt.Tooltip("Sinyal Tarihi:N"),
            alt.Tooltip("return_pct:Q", title="Getiri %", format=".2f"),
            alt.Tooltip("cumulative_return:Q", title="Kümülatif %", format=".2f"),
        ],
    )

    zero_line = (
        alt.Chart(pd.DataFrame({"y": [0]}))
        .mark_rule(color="rgba(255,255,255,0.3)", strokeDash=[4, 4])
        .encode(y="y:Q")
    )

    points = base.mark_circle(size=50).encode(
        y=alt.Y("cumulative_return:Q"),
        color=alt.condition(
            alt.datum.return_pct > 0,
            alt.value("#22c55e"),
            alt.value("#ef4444"),
        ),
        tooltip=[
            alt.Tooltip("Sembol:N"),
            alt.Tooltip("return_pct:Q", title="Getiri %", format=".2f"),
        ],
    )

    chart = (
        (zero_line + line + points)
        .properties(height=300)
        .configure_view(strokeWidth=0)
        .configure_axis(
            labelColor="#94a3b8",
            titleColor="#cbd5e1",
            gridColor="rgba(148,163,184,0.15)",
        )
    )

    st.altair_chart(chart, use_container_width=True)


def _render_top_signals(outcomes_df: pd.DataFrame, n: int = 5):
    """Render top N performing signal cards."""
    change_col = pd.to_numeric(outcomes_df["Değişim %"], errors="coerce")
    valid = outcomes_df[change_col.notna()].copy()
    valid["_change"] = change_col[change_col.notna()].values

    if valid.empty:
        st.info("Sonuçlanmış sinyal bulunamadı.")
        return

    top = valid.nlargest(n, "_change")

    cols = st.columns(min(n, len(top)))
    for i, (_, row) in enumerate(top.iterrows()):
        change = row["_change"]
        color = "#22c55e" if change > 0 else "#ef4444"
        arrow = "↑" if change > 0 else "↓"
        with cols[i]:
            st.markdown(
                f"""
                <div style="
                    background: rgba(15,23,42,0.8);
                    border: 1px solid {color}33;
                    border-radius: 12px;
                    padding: 16px;
                    text-align: center;
                ">
                    <div style="font-size:1.1rem; font-weight:700; color:#f8fafc;">
                        {row['Sembol']}
                    </div>
                    <div style="font-size:1.4rem; font-weight:800; color:{color}; margin:8px 0;">
                        {arrow} {change:+.1f}%
                    </div>
                    <div style="font-size:0.75rem; color:#94a3b8;">
                        {row['Sinyal Tarihi']} · ${row['Giriş $']}
                    </div>
                    <div style="font-size:0.75rem; color:#94a3b8;">
                        {row['Durum']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
