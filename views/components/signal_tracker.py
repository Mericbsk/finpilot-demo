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
    stop_loss: float | None
    take_profit: float | None
    score: float
    entry_ok: bool

    # Outcome fields (filled after price lookup)
    current_price: float | None = None
    price_1d: float | None = None
    price_1w: float | None = None
    price_1m: float | None = None
    change_pct: float | None = None
    change_1d_pct: float | None = None
    change_1w_pct: float | None = None
    change_1m_pct: float | None = None
    status: str = "⏳ Açık"  # ✅ TP Ulaştı | ❌ SL Tetiklendi | ⏳ Açık
    hit_date: str | None = None
    days_to_result: int | None = None


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


def _humanize_signal_date(date_str: str) -> str:
    """Convert date string to 'X gün önce' format."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        delta = datetime.now() - dt
        days = delta.days
        if days == 0:
            return "bugün"
        elif days == 1:
            return "dün"
        elif days < 7:
            return f"{days} gün önce"
        elif days < 30:
            weeks = days // 7
            return f"{weeks} hafta önce"
        elif days < 365:
            months = days // 30
            return f"{months} ay önce"
        else:
            years = days // 365
            return f"{years} yıl önce"
    except (ValueError, TypeError):
        return date_str


@st.cache_data(ttl=900, show_spinner=False)
def _batch_fetch_prices(symbols: tuple, start_date: str, end_date: str) -> dict[str, pd.DataFrame]:
    """Fetch price history for multiple symbols in a single API call."""
    try:
        import yfinance as yf
    except ImportError:
        return {}

    if not symbols:
        return {}

    try:
        data = yf.download(
            list(symbols),
            start=start_date,
            end=end_date,
            interval="1d",
            progress=False,
            auto_adjust=True,
        )
        if data is None or data.empty:
            return {}

        result: dict[str, pd.DataFrame] = {}

        if len(symbols) == 1:
            df = data.copy()
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            result[symbols[0]] = df.reset_index()
            return result

        # Multi-symbol: columns are MultiIndex (metric, symbol)
        if isinstance(data.columns, pd.MultiIndex):
            for sym in symbols:
                try:
                    sym_df = pd.DataFrame(index=data.index)
                    for col in ("Close", "High", "Low", "Open", "Volume"):
                        if (col, sym) in data.columns:
                            sym_df[col] = data[(col, sym)]
                    sym_df = sym_df.dropna(subset=["Close"])
                    if not sym_df.empty:
                        result[sym] = sym_df.reset_index()
                except Exception:  # noqa: S112
                    continue

        return result
    except Exception as e:
        logger.debug(f"Batch price fetch failed: {e}")
        return {}


def calculate_signal_outcomes(
    signals_df: pd.DataFrame,
    max_signals: int = 100,
) -> pd.DataFrame:
    """
    For each signal, fetch subsequent prices and determine outcome.
    Uses batch download for performance (single API call).
    """
    if signals_df.empty:
        return pd.DataFrame()

    # Deduplicate: keep latest signal per symbol per day
    signals_df = signals_df.copy()
    if "timestamp" in signals_df.columns:
        signals_df["date_only"] = pd.to_datetime(signals_df["timestamp"], errors="coerce").dt.date
        signals_df = signals_df.drop_duplicates(subset=["symbol", "date_only"], keep="first")
    elif "scan_date" in signals_df.columns:
        signals_df["date_only"] = pd.to_datetime(signals_df["scan_date"], errors="coerce").dt.date
        signals_df = signals_df.drop_duplicates(subset=["symbol", "date_only"], keep="first")

    signals_df = signals_df.head(max_signals)
    today = datetime.now()

    # ── Phase 1: Collect symbols & date range for batch fetch ──
    symbols_set: set[str] = set()
    earliest_date = today
    prepared: list[dict] = []

    for _, row in signals_df.iterrows():
        symbol = str(row.get("symbol", ""))
        entry_price = float(row.get("price", 0))
        if not symbol or entry_price <= 0:
            continue

        sig_date = row.get("timestamp", row.get("scan_date", None))
        if pd.isna(sig_date):
            continue
        sig_dt = pd.to_datetime(sig_date)

        sl = float(row["stop_loss"]) if pd.notna(row.get("stop_loss")) else None
        tp = float(row["take_profit"]) if pd.notna(row.get("take_profit")) else None
        score = float(row.get("score", row.get("recommendation_score", 0)))
        entry_ok = bool(row.get("entry_ok", False))

        symbols_set.add(symbol)
        if sig_dt < earliest_date:
            earliest_date = sig_dt

        prepared.append(
            {
                "symbol": symbol,
                "sig_dt": sig_dt,
                "entry_price": entry_price,
                "sl": sl,
                "tp": tp,
                "score": score,
                "entry_ok": entry_ok,
            }
        )

    if not prepared:
        return pd.DataFrame()

    # ── Phase 2: Single batch fetch ──
    start_str = earliest_date.strftime("%Y-%m-%d")
    end_str = (today + timedelta(days=1)).strftime("%Y-%m-%d")
    all_prices = _batch_fetch_prices(tuple(sorted(symbols_set)), start_str, end_str)

    # ── Phase 3: Calculate outcomes using pre-fetched data ──
    results: list[SignalOutcome] = []

    for prow in prepared:
        symbol = prow["symbol"]
        sig_dt = prow["sig_dt"]
        entry_price = prow["entry_price"]
        sl = prow["sl"]
        tp = prow["tp"]

        outcome = SignalOutcome(
            symbol=symbol,
            signal_date=sig_dt.strftime("%Y-%m-%d"),
            entry_price=round(entry_price, 2),
            stop_loss=round(sl, 2) if sl else None,
            take_profit=round(tp, 2) if tp else None,
            score=round(prow["score"], 1),
            entry_ok=prow["entry_ok"],
        )

        hist = all_prices.get(symbol, pd.DataFrame())
        if hist.empty or "Close" not in hist.columns:
            results.append(outcome)
            continue

        # Filter to dates on or after signal date
        if "Date" in hist.columns:
            hist = hist[pd.to_datetime(hist["Date"]) >= sig_dt].reset_index(drop=True)
        if hist.empty:
            results.append(outcome)
            continue

        close_series = hist["Close"].values
        date_series = pd.to_datetime(hist["Date"]) if "Date" in hist.columns else hist.index

        outcome.current_price = round(float(close_series[-1]), 2)
        outcome.change_pct = round((outcome.current_price - entry_price) / entry_price * 100, 2)

        if len(close_series) >= 2:
            outcome.price_1d = round(float(close_series[1]), 2)
            outcome.change_1d_pct = round((outcome.price_1d - entry_price) / entry_price * 100, 2)
        if len(close_series) >= 6:
            outcome.price_1w = round(float(close_series[5]), 2)
            outcome.change_1w_pct = round((outcome.price_1w - entry_price) / entry_price * 100, 2)
        if len(close_series) >= 22:
            outcome.price_1m = round(float(close_series[21]), 2)
            outcome.change_1m_pct = round((outcome.price_1m - entry_price) / entry_price * 100, 2)

        # Check SL/TP hit
        if sl and tp:
            high_series = hist["High"].values if "High" in hist.columns else close_series
            low_series = hist["Low"].values if "Low" in hist.columns else close_series
            for i in range(1, len(close_series)):
                if float(low_series[i]) <= sl:
                    outcome.status = "❌ SL"
                    if hasattr(date_series, "iloc"):
                        outcome.hit_date = date_series.iloc[i].strftime("%Y-%m-%d")
                    outcome.days_to_result = i
                    break
                elif float(high_series[i]) >= tp:
                    outcome.status = "✅ TP"
                    if hasattr(date_series, "iloc"):
                        outcome.hit_date = date_series.iloc[i].strftime("%Y-%m-%d")
                    outcome.days_to_result = i
                    break
        elif outcome.change_pct is not None:
            if outcome.change_pct >= 3.0:
                outcome.status = "✅ Kâr"
            elif outcome.change_pct <= -3.0:
                outcome.status = "❌ Zarar"

        results.append(outcome)

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
def calculate_kpis(outcomes_df: pd.DataFrame) -> dict:
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
# Trade Card (Detailed Expander View)
# ---------------------------------------------------------------------------
def _render_trade_card(row: pd.Series) -> None:
    """Render a detailed trade card for a selected signal row."""
    symbol = str(row.get("Sembol", ""))
    signal_date = str(row.get("Sinyal Tarihi", ""))
    entry = row.get("Giriş $", 0)
    current = row.get("Şu An $", "-")
    sl = row.get("SL $", "-")
    tp = row.get("TP $", "-")
    change = pd.to_numeric(row.get("Değişim %"), errors="coerce")
    status = str(row.get("Durum", "⏳ Açık"))
    days = row.get("Sonuç Gün", "-")
    score = row.get("Skor", 0)

    days_ago = _humanize_signal_date(signal_date)

    # Status coloring
    if "TP" in status or "Kâr" in status:
        border_color = "#22c55e"
        status_bg = "rgba(34,197,94,0.15)"
    elif "SL" in status or "Zarar" in status:
        border_color = "#ef4444"
        status_bg = "rgba(239,68,68,0.15)"
    else:
        border_color = "#f59e0b"
        status_bg = "rgba(245,158,11,0.15)"

    change_str = f"{change:+.2f}%" if pd.notna(change) else "-"
    change_color = "#22c55e" if (pd.notna(change) and change > 0) else "#ef4444"

    # Dollar P&L
    pnl_str = "-"
    try:
        e = float(entry)
        c = float(current) if str(current) != "-" else e
        pnl_str = f"${c - e:+.2f}"
    except (ValueError, TypeError):
        pass

    # Progress bar (SL → Entry → Current → TP)
    progress_html = ""
    try:
        e = float(entry)
        c = float(current) if str(current) != "-" else e
        s = float(sl) if str(sl) != "-" else e - (e * 0.03)
        t = float(tp) if str(tp) != "-" else e + (e * 0.05)
        total_range = t - s
        if total_range > 0:
            current_pct = max(0, min(100, (c - s) / total_range * 100))
            entry_pct = max(0, min(100, (e - s) / total_range * 100))
            prog_color = "#22c55e" if c >= e else "#ef4444"
            progress_html = f"""
            <div style="position:relative; height:28px; background:rgba(148,163,184,0.08);
                        border-radius:8px; margin:12px 0; overflow:hidden;">
                <div style="position:absolute; left:0; top:0; bottom:0; width:{entry_pct}%;
                            background:rgba(239,68,68,0.06);"></div>
                <div style="position:absolute; right:0; top:0; bottom:0; width:{100 - entry_pct}%;
                            background:rgba(34,197,94,0.06);"></div>
                <div style="position:absolute; left:{entry_pct}%; top:0; bottom:0; width:2px;
                            background:var(--text-muted, #94a3b8);"></div>
                <div style="position:absolute; left:{current_pct}%; top:3px; bottom:3px; width:10px;
                            transform:translateX(-50%); background:{prog_color};
                            border-radius:3px;"></div>
                <span style="position:absolute; left:4px; top:50%; transform:translateY(-50%);
                            font-size:0.6rem; color:var(--text-muted, #94a3b8);">SL ${s:.2f}</span>
                <span style="position:absolute; right:4px; top:50%; transform:translateY(-50%);
                            font-size:0.6rem; color:var(--text-muted, #94a3b8);">TP ${t:.2f}</span>
            </div>
            """
    except (ValueError, TypeError):
        pass

    # 1G/1H/1A
    g1 = row.get("1G %", "-")
    h1 = row.get("1H %", "-")
    a1 = row.get("1A %", "-")

    st.markdown(
        f"""
    <div style="background:var(--bg-glass, rgba(15,23,42,0.8));
                border:1px solid {border_color}44; border-left:4px solid {border_color};
                border-radius:12px; padding:20px; margin:12px 0;"
         role="region" aria-label="{symbol} trade card">
        <div style="display:flex; justify-content:space-between; align-items:center;
                    margin-bottom:12px;">
            <div>
                <span style="font-size:1.3rem; font-weight:800;
                            color:var(--text-primary, #f8fafc);">{symbol}</span>
                <span style="font-size:0.8rem; color:var(--text-muted, #94a3b8);
                            margin-left:12px;">Skor: {score}</span>
            </div>
            <div style="background:{status_bg}; border:1px solid {border_color}44;
                        border-radius:8px; padding:4px 12px;">
                <span style="font-size:0.85rem; font-weight:600;
                            color:{border_color};">{status}</span>
            </div>
        </div>
        <div style="font-size:0.8rem; color:var(--text-muted, #94a3b8);
                    margin-bottom:16px;">
            📅 {signal_date} ({days_ago})
            {f'&nbsp;&nbsp;•&nbsp;&nbsp;⏱️ {days} gün' if str(days) != '-' else ''}
        </div>
        <div style="display:flex; justify-content:space-around; align-items:center;
                    margin-bottom:4px;">
            <div style="text-align:center;">
                <div style="font-size:0.65rem; color:var(--text-muted, #94a3b8);">GİRİŞ</div>
                <div style="font-size:1.1rem; font-weight:700;
                            color:var(--text-primary, #f8fafc);">${entry}</div>
            </div>
            <div style="font-size:1.2rem; color:var(--text-muted, #94a3b8);">→</div>
            <div style="text-align:center;">
                <div style="font-size:0.65rem; color:var(--text-muted, #94a3b8);">ŞU AN</div>
                <div style="font-size:1.1rem; font-weight:700;
                            color:{change_color};">{f'${current}' if str(current) != '-' else '-'}</div>
            </div>
            <div style="font-size:1.2rem; color:var(--text-muted, #94a3b8);">→</div>
            <div style="text-align:center;">
                <div style="font-size:0.65rem; color:var(--text-muted, #94a3b8);">HEDEF</div>
                <div style="font-size:1.1rem; font-weight:700;
                            color:var(--text-primary, #f8fafc);">{f'${tp}' if str(tp) != '-' else '-'}</div>
            </div>
        </div>
        {progress_html}
        <div style="display:flex; gap:12px; flex-wrap:wrap; margin-top:12px; padding-top:12px;
                    border-top:1px solid var(--border-default, rgba(148,163,184,0.2));">
            <div style="text-align:center; flex:1; min-width:60px;">
                <div style="font-size:0.6rem; color:var(--text-muted, #94a3b8);">DEĞİŞİM</div>
                <div style="font-size:0.95rem; font-weight:700; color:{change_color};">
                    {change_str}</div>
            </div>
            <div style="text-align:center; flex:1; min-width:60px;">
                <div style="font-size:0.6rem; color:var(--text-muted, #94a3b8);">P&amp;L</div>
                <div style="font-size:0.95rem; font-weight:700; color:{change_color};">
                    {pnl_str}</div>
            </div>
            <div style="text-align:center; flex:1; min-width:60px;">
                <div style="font-size:0.6rem; color:var(--text-muted, #94a3b8);">1 GÜN</div>
                <div style="font-size:0.8rem; color:var(--text-primary, #f8fafc);">
                    {g1}{'%' if str(g1) != '-' else ''}</div>
            </div>
            <div style="text-align:center; flex:1; min-width:60px;">
                <div style="font-size:0.6rem; color:var(--text-muted, #94a3b8);">1 HAFTA</div>
                <div style="font-size:0.8rem; color:var(--text-primary, #f8fafc);">
                    {h1}{'%' if str(h1) != '-' else ''}</div>
            </div>
            <div style="text-align:center; flex:1; min-width:60px;">
                <div style="font-size:0.6rem; color:var(--text-muted, #94a3b8);">1 AY</div>
                <div style="font-size:0.8rem; color:var(--text-primary, #f8fafc);">
                    {a1}{'%' if str(a1) != '-' else ''}</div>
            </div>
            <div style="text-align:center; flex:1; min-width:60px;">
                <div style="font-size:0.6rem; color:var(--text-muted, #94a3b8);">STOP</div>
                <div style="font-size:0.8rem; color:#ef4444;">
                    {f'${sl}' if str(sl) != '-' else '-'}</div>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


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

    # --- Results Table (Compact with row selection) ---
    st.markdown("#### 📋 Sinyal Sonuç Tablosu")
    st.caption("Satıra tıklayarak detaylı trade kartını görüntüleyin.")

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
        # Add humanized date column for display
        display_df["Ne Zaman"] = display_df["Sinyal Tarihi"].apply(_humanize_signal_date)

        selection = st.dataframe(
            display_df[
                [
                    "Sembol",
                    "Sinyal Tarihi",
                    "Ne Zaman",
                    "Giriş $",
                    "Şu An $",
                    "Değişim %",
                    "Durum",
                    "Sonuç Gün",
                    "Skor",
                ]
            ],
            column_config={
                "Sembol": st.column_config.TextColumn("Sembol", width="small"),
                "Sinyal Tarihi": st.column_config.TextColumn("Tarih", width="small"),
                "Ne Zaman": st.column_config.TextColumn("Ne Zaman", width="small"),
                "Giriş $": st.column_config.NumberColumn("Giriş $", format="%.2f"),
                "Şu An $": st.column_config.TextColumn("Şu An $"),
                "Değişim %": st.column_config.TextColumn("Değişim %"),
                "Durum": st.column_config.TextColumn("Durum", width="small"),
                "Sonuç Gün": st.column_config.TextColumn("Gün", width="small"),
                "Skor": st.column_config.NumberColumn("Skor", format="%.0f"),
            },
            use_container_width=True,
            hide_index=True,
            height=min(len(display_df) * 38 + 40, 500),
            on_select="rerun",
            selection_mode="single-row",
            key="perf_signal_table",
        )

        # Show detailed trade card for selected row
        if selection.selection.rows:
            selected_idx = selection.selection.rows[0]
            selected_row = display_df.iloc[selected_idx]
            _render_trade_card(selected_row)

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
        days_ago = _humanize_signal_date(str(row["Sinyal Tarihi"]))
        with cols[i]:
            st.markdown(
                f"""
                <div style="
                    background: var(--bg-glass, rgba(15,23,42,0.8));
                    border: 1px solid {color}33;
                    border-radius: 12px;
                    padding: 16px;
                    text-align: center;
                " role="article" aria-label="{row['Sembol']} {change:+.1f}%">
                    <div style="font-size:1.1rem; font-weight:700;
                                color:var(--text-primary, #f8fafc);">
                        {row["Sembol"]}
                    </div>
                    <div style="font-size:1.4rem; font-weight:800; color:{color};
                                margin:8px 0;">
                        {arrow} {change:+.1f}%
                    </div>
                    <div style="font-size:0.75rem;
                                color:var(--text-muted, #94a3b8);">
                        {row["Sinyal Tarihi"]} ({days_ago})
                    </div>
                    <div style="font-size:0.75rem;
                                color:var(--text-muted, #94a3b8);">
                        ${row["Giriş $"]} · {row["Durum"]}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
