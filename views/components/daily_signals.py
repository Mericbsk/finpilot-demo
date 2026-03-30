"""
Daily Signal Tracker — Sprint 22.

Redesigned signal performance view with:
  1. Horizontal daily timeline strip (last 14 days)
  2. Accordion per day (expandable signal details)
  3. Score-grouped signal cards inside each day
  4. Daily stats: scanned count, BUY count, success rate

Replaces the flat table approach with a date-first design
for scanning rhythm visibility and less eye fatigue.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# DB integration
# ---------------------------------------------------------------------------
try:
    from auth.database import get_database  # noqa: F401

    _DB_AVAILABLE = True
except ImportError:
    _DB_AVAILABLE = False


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------
@dataclass
class DailySignalSummary:
    """Aggregated stats for one day."""

    date: str  # YYYY-MM-DD
    date_label: str  # "1 Mart 2026, Pzt"
    total_scanned: int = 0
    buy_count: int = 0
    buy_ratio_pct: float = 0.0
    avg_score: float = 0.0
    strong_count: int = 0  # score >= 3
    medium_count: int = 0  # score == 2
    weak_count: int = 0  # score <= 1
    tp_count: int = 0
    sl_count: int = 0
    open_count: int = 0
    win_rate: float = 0.0
    signals: list[dict] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Turkish helpers
# ---------------------------------------------------------------------------
_TR_MONTHS = {
    1: "Ocak",
    2: "Şubat",
    3: "Mart",
    4: "Nisan",
    5: "Mayıs",
    6: "Haziran",
    7: "Temmuz",
    8: "Ağustos",
    9: "Eylül",
    10: "Ekim",
    11: "Kasım",
    12: "Aralık",
}
_TR_DAYS = {
    0: "Pzt",
    1: "Sal",
    2: "Çar",
    3: "Per",
    4: "Cum",
    5: "Cmt",
    6: "Paz",
}


def _format_turkish_date(dt: datetime) -> str:
    """Return '2 Mart 2026, Pzt' style string."""
    return f"{dt.day} {_TR_MONTHS[dt.month]} {dt.year}, {_TR_DAYS[dt.weekday()]}"


def _days_ago_label(date_str: str) -> str:
    """Return human-friendly relative time label."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        diff = (datetime.now() - dt).days
        if diff == 0:
            return "bugün"
        elif diff == 1:
            return "dün"
        elif diff < 7:
            return f"{diff} gün önce"
        elif diff < 30:
            return f"{diff // 7} hafta önce"
        else:
            return f"{diff // 30} ay önce"
    except (ValueError, TypeError):
        return date_str


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
@st.cache_data(ttl=120, show_spinner=False)
def _load_daily_summaries() -> list[DailySignalSummary]:
    """Load signals grouped by date from DB. Cached for 120s."""
    if not _DB_AVAILABLE:
        return []

    import sqlite3

    try:
        conn = sqlite3.connect("data/finpilot.db")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Get daily scan stats from signals table
        cur.execute("""
            SELECT substr(timestamp, 1, 10) as dt,
                   COUNT(*) as total_scanned,
                   SUM(CASE WHEN entry_ok = 1 THEN 1 ELSE 0 END) as buy_count
            FROM signals
            GROUP BY dt
            ORDER BY dt DESC
        """)
        scan_stats = {r["dt"]: dict(r) for r in cur.fetchall()}

        # Get buy signals grouped by date with details
        cur.execute("""
            SELECT id, date, symbol, entry_price, stop_loss, take_profit,
                   risk_reward, score, reason, scan_source, status,
                   exit_price, pnl_pct, alpaca_order_id
            FROM buy_signals
            ORDER BY date DESC, score DESC, symbol
        """)
        all_signals = [dict(r) for r in cur.fetchall()]
        conn.close()

        # Group by date
        by_date: dict[str, list[dict]] = {}
        for s in all_signals:
            dt = s["date"]
            by_date.setdefault(dt, []).append(s)

        # Also include dates from signals table that don't have buy_signals
        # but only if they had actual buy signals (entry_ok > 0)
        for dt in scan_stats:
            if dt not in by_date:
                scan_buy = scan_stats[dt].get("buy_count", 0)
                if scan_buy > 0:
                    # Scan had buy signals but not yet in buy_signals table
                    by_date[dt] = []
                # Skip dates with 0 buy signals (scan-only, no pills needed)

        # Build summaries
        summaries = []
        for dt in sorted(by_date.keys(), reverse=True):
            signals = by_date[dt]
            scan = scan_stats.get(dt, {})

            try:
                dt_obj = datetime.strptime(dt, "%Y-%m-%d")
                date_label = _format_turkish_date(dt_obj)
            except ValueError:
                date_label = dt

            total_scanned = scan.get("total_scanned", 0)
            buy_count = len(signals) if signals else scan.get("buy_count", 0)

            strong = sum(1 for s in signals if (s.get("score") or 0) >= 3)
            medium = sum(1 for s in signals if 1 < (s.get("score") or 0) < 3)
            weak = sum(1 for s in signals if (s.get("score") or 0) <= 1)

            tp = sum(
                1
                for s in signals
                if "tp" in str(s.get("status", "")).lower()
                or "profit" in str(s.get("status", "")).lower()
            )
            sl = sum(
                1
                for s in signals
                if "sl" in str(s.get("status", "")).lower()
                or "loss" in str(s.get("status", "")).lower()
            )
            active = sum(1 for s in signals if str(s.get("status", "")).lower() == "active")

            closed = tp + sl
            win_rate = (tp / closed * 100) if closed > 0 else 0.0

            avg_score = 0.0
            scores = [s.get("score", 0) for s in signals if s.get("score")]
            if scores:
                avg_score = sum(scores) / len(scores)

            summaries.append(
                DailySignalSummary(
                    date=dt,
                    date_label=date_label,
                    total_scanned=total_scanned,
                    buy_count=buy_count,
                    buy_ratio_pct=round(buy_count / total_scanned * 100, 1)
                    if total_scanned > 0
                    else 0,
                    avg_score=round(avg_score, 1),
                    strong_count=strong,
                    medium_count=medium,
                    weak_count=weak,
                    tp_count=tp,
                    sl_count=sl,
                    open_count=active,
                    win_rate=round(win_rate, 1),
                    signals=signals,
                )
            )

        return summaries

    except Exception as e:
        logger.error(f"Failed to load daily summaries: {e}")
        return []


# ---------------------------------------------------------------------------
# Outcome checker — evaluates active signals against real price data
# ---------------------------------------------------------------------------
def _update_signal_outcomes() -> dict[str, int]:
    """Check active buy_signals against actual price data via yfinance.

    For each active signal:
      - Fetch daily OHLC from entry date to today
      - If High ≥ take_profit  →  status='tp_hit'
      - If Low  ≤ stop_loss    →  status='sl_hit'
      - If both hit same candle →  SL takes priority (conservative)
      - Update exit_price, exit_date, pnl_pct in DB

    Returns dict with counts: {'checked': N, 'tp': N, 'sl': N, 'errors': N}
    """
    import sqlite3

    import yfinance as yf

    stats = {"checked": 0, "tp": 0, "sl": 0, "errors": 0, "still_active": 0}

    try:
        conn = sqlite3.connect("data/finpilot.db")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("""
            SELECT id, symbol, date, entry_price, stop_loss, take_profit
            FROM buy_signals
            WHERE status = 'active'
              AND entry_price IS NOT NULL
              AND stop_loss IS NOT NULL
              AND take_profit IS NOT NULL
        """)
        active = [dict(r) for r in cur.fetchall()]

        if not active:
            conn.close()
            return stats

        # Group by symbol
        by_sym: dict[str, list[dict]] = {}
        for sig in active:
            by_sym.setdefault(sig["symbol"], []).append(sig)

        symbols = list(by_sym.keys())
        stats["checked"] = len(active)

        # Find earliest date to minimize download range
        all_dates = [s["date"] for s in active if s["date"]]
        if not all_dates:
            conn.close()
            return stats
        earliest = min(all_dates)

        # Batch download — yfinance multi-ticker
        try:
            data = yf.download(
                symbols,
                start=earliest,
                progress=False,
                auto_adjust=True,
                threads=True,
                timeout=30,
            )
        except Exception as e:
            logger.error(f"yfinance download failed: {e}")
            stats["errors"] = len(active)
            conn.close()
            return stats

        if data.empty:
            stats["errors"] = len(active)
            conn.close()
            return stats

        # Process each symbol
        updates: list[tuple] = []  # (status, exit_price, exit_date, pnl_pct, id)
        multi = len(symbols) > 1

        for sym, sigs in by_sym.items():
            try:
                # Extract OHLC for this symbol
                if multi:
                    if ("High", sym) in data.columns:
                        sym_high = data[("High", sym)].dropna()
                        sym_low = data[("Low", sym)].dropna()
                    elif "High" in data.columns and sym in data["High"].columns:
                        sym_high = data["High"][sym].dropna()
                        sym_low = data["Low"][sym].dropna()
                    else:
                        stats["errors"] += len(sigs)
                        continue
                else:
                    # Single symbol — no MultiIndex
                    if "High" in data.columns:
                        sym_high = data["High"].dropna()
                        sym_low = data["Low"].dropna()
                    else:
                        stats["errors"] += len(sigs)
                        continue

                for sig in sigs:
                    entry_date = sig["date"]
                    tp = sig["take_profit"]
                    sl = sig["stop_loss"]
                    entry = sig["entry_price"]

                    # Filter to dates >= entry date
                    mask = sym_high.index >= pd.Timestamp(entry_date)
                    highs = sym_high[mask]
                    lows = sym_low[mask]

                    if highs.empty:
                        stats["still_active"] += 1
                        continue

                    # Find first TP and SL hit dates
                    tp_hits = highs[highs >= tp]
                    sl_hits = lows[lows <= sl]

                    tp_date = tp_hits.index[0] if not tp_hits.empty else None
                    sl_date = sl_hits.index[0] if not sl_hits.empty else None

                    if tp_date is None and sl_date is None:
                        stats["still_active"] += 1
                        continue

                    # Determine which hit first
                    if tp_date is not None and sl_date is not None:
                        if sl_date <= tp_date:
                            # SL hit first (or same day — conservative)
                            status = "sl_hit"
                            exit_price = sl
                            exit_dt = sl_date.strftime("%Y-%m-%d")
                        else:
                            status = "tp_hit"
                            exit_price = tp
                            exit_dt = tp_date.strftime("%Y-%m-%d")
                    elif tp_date is not None:
                        status = "tp_hit"
                        exit_price = tp
                        exit_dt = tp_date.strftime("%Y-%m-%d")
                    else:
                        status = "sl_hit"
                        exit_price = sl
                        exit_dt = sl_date.strftime("%Y-%m-%d")

                    pnl_pct = round((exit_price - entry) / entry * 100, 2)

                    if status == "tp_hit":
                        stats["tp"] += 1
                    else:
                        stats["sl"] += 1

                    updates.append((status, exit_price, exit_dt, pnl_pct, sig["id"]))

            except Exception as e:
                logger.warning(f"Outcome check failed for {sym}: {e}")
                stats["errors"] += len(sigs)

        # Batch update DB
        if updates:
            cur.executemany(
                """
                UPDATE buy_signals
                SET status = ?, exit_price = ?, exit_date = ?, pnl_pct = ?
                WHERE id = ?
            """,
                updates,
            )
            conn.commit()

        conn.close()
        return stats

    except Exception as e:
        logger.error(f"Outcome update failed: {e}")
        return stats


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
_DAILY_CSS = """
<style>
/* Timeline strip */
.ds-timeline {
    display: flex;
    gap: 10px;
    overflow-x: auto;
    padding: 8px 4px 12px 4px;
    scrollbar-width: thin;
    scrollbar-color: var(--color-primary, #00e6e6) transparent;
}
.ds-timeline::-webkit-scrollbar { height: 4px; }
.ds-timeline::-webkit-scrollbar-thumb {
    background: var(--color-primary, #00e6e6);
    border-radius: 2px;
}

.ds-day-pill {
    flex-shrink: 0;
    min-width: 110px;
    padding: 10px 14px;
    border-radius: 12px;
    background: var(--bg-glass, rgba(15,23,42,0.72));
    border: 1px solid var(--border-default, rgba(148,163,184,0.18));
    cursor: default;
    text-align: center;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.ds-day-pill:hover {
    border-color: var(--color-primary, #00e6e6);
}
.ds-day-pill.active {
    border-color: var(--color-primary, #00e6e6);
    box-shadow: 0 0 12px rgba(0,230,230,0.15);
}
.ds-day-pill .date {
    font-size: 0.7rem;
    color: var(--text-muted, rgba(148,163,184,0.75));
    margin-bottom: 4px;
}
.ds-day-pill .count {
    font-size: 1.3rem;
    font-weight: 800;
    color: var(--text-primary, #f8fafc);
    line-height: 1.2;
}
.ds-day-pill .label {
    font-size: 0.6rem;
    color: var(--text-muted, rgba(148,163,184,0.75));
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.ds-day-pill .bar-wrap {
    height: 4px;
    border-radius: 2px;
    background: rgba(148,163,184,0.12);
    margin-top: 6px;
    overflow: hidden;
    display: flex;
}
.ds-day-pill .bar-tp { background: #22c55e; height: 100%; }
.ds-day-pill .bar-sl { background: #ef4444; height: 100%; }
.ds-day-pill .bar-open { background: #f59e0b; height: 100%; }

/* Accordion header */
.ds-accordion-hdr {
    background: var(--bg-glass, rgba(15,23,42,0.72));
    border: 1px solid var(--border-default, rgba(148,163,184,0.18));
    border-radius: 14px;
    padding: 18px 22px;
    margin-bottom: 8px;
}
.ds-accordion-hdr .top-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
}
.ds-accordion-hdr .day-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: var(--text-primary, #f8fafc);
}
.ds-accordion-hdr .day-ago {
    font-size: 0.75rem;
    color: var(--text-muted, rgba(148,163,184,0.75));
    margin-left: 8px;
}
.ds-accordion-hdr .badges {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}
.ds-badge {
    font-size: 0.7rem;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 20px;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}
.ds-badge-scan {
    background: rgba(59,130,246,0.15);
    color: #60a5fa;
    border: 1px solid rgba(59,130,246,0.25);
}
.ds-badge-buy {
    background: rgba(0,230,230,0.12);
    color: #00e6e6;
    border: 1px solid rgba(0,230,230,0.25);
}
.ds-badge-score {
    background: rgba(139,92,246,0.12);
    color: #a78bfa;
    border: 1px solid rgba(139,92,246,0.25);
}

.ds-progress-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-top: 12px;
}
.ds-progress-bar {
    flex: 1;
    height: 6px;
    border-radius: 3px;
    background: rgba(148,163,184,0.1);
    overflow: hidden;
    display: flex;
}
.ds-progress-bar .seg-tp { background: #22c55e; height: 100%; }
.ds-progress-bar .seg-sl { background: #ef4444; height: 100%; }
.ds-progress-bar .seg-open { background: rgba(245,158,11,0.5); height: 100%; }

.ds-progress-labels {
    display: flex;
    gap: 12px;
    font-size: 0.68rem;
    color: var(--text-muted, rgba(148,163,184,0.75));
}
.ds-progress-labels .lbl-tp { color: #4ade80; }
.ds-progress-labels .lbl-sl { color: #fca5a5; }
.ds-progress-labels .lbl-open { color: #fbbf24; }

/* Signal cards (score groups) */
.ds-score-section {
    margin-top: 14px;
    margin-bottom: 6px;
}
.ds-score-label {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 8px;
    padding-left: 4px;
}
.ds-score-label.strong { color: #4ade80; }
.ds-score-label.medium { color: #fbbf24; }
.ds-score-label.weak   { color: #94a3b8; }

.ds-signal-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(155px, 1fr));
    gap: 8px;
}
.ds-signal-card {
    background: var(--bg-secondary, #1e293b);
    border: 1px solid var(--border-default, rgba(148,163,184,0.18));
    border-radius: 10px;
    padding: 12px;
    transition: border-color 0.2s, transform 0.15s;
    position: relative;
    overflow: hidden;
}
.ds-signal-card:hover {
    border-color: rgba(0,230,230,0.3);
    transform: translateY(-1px);
}
.ds-signal-card .score-dot {
    position: absolute;
    top: 8px;
    right: 8px;
    width: 8px;
    height: 8px;
    border-radius: 50%;
}
.ds-signal-card .sym {
    font-size: 0.9rem;
    font-weight: 700;
    color: var(--text-primary, #f8fafc);
    margin-bottom: 2px;
}
.ds-signal-card .price-row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 4px;
}
.ds-signal-card .entry {
    font-size: 0.8rem;
    color: var(--text-secondary, #94a3b8);
}
.ds-signal-card .rr {
    font-size: 0.65rem;
    color: var(--text-muted, rgba(148,163,184,0.75));
}
.ds-signal-card .targets {
    display: flex;
    justify-content: space-between;
    font-size: 0.6rem;
    color: var(--text-muted, rgba(148,163,184,0.75));
    margin-top: 4px;
    padding-top: 4px;
    border-top: 1px solid rgba(148,163,184,0.08);
}
.ds-signal-card .targets .sl { color: rgba(239,68,68,0.7); }
.ds-signal-card .targets .tp { color: rgba(34,197,94,0.7); }

.ds-signal-card .status-bar {
    height: 3px;
    border-radius: 2px;
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
}
.ds-signal-card .status-bar.active  { background: #f59e0b; }
.ds-signal-card .status-bar.tp-hit  { background: #22c55e; }
.ds-signal-card .status-bar.sl-hit  { background: #ef4444; }

.ds-signal-card .alpaca-tag {
    position: absolute;
    top: 8px;
    left: 8px;
    font-size: 0.5rem;
    font-weight: 700;
    background: rgba(0,230,230,0.12);
    color: #00e6e6;
    padding: 1px 6px;
    border-radius: 4px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Empty state */
.ds-empty {
    text-align: center;
    padding: 40px 20px;
    color: var(--text-muted, rgba(148,163,184,0.75));
}
.ds-empty .icon { font-size: 2rem; margin-bottom: 8px; }
.ds-empty .msg { font-size: 0.85rem; }

/* No-buy day row */
.ds-no-buy {
    text-align: center;
    padding: 12px;
    font-size: 0.8rem;
    color: var(--text-muted, rgba(148,163,184,0.75));
    font-style: italic;
}
</style>
"""


# ---------------------------------------------------------------------------
# Render: Timeline strip (top)
# ---------------------------------------------------------------------------
def _render_timeline_strip(summaries: list[DailySignalSummary]) -> None:
    """Render the horizontal day pills across the top."""
    if not summaries:
        return

    pills_html = []
    for day in summaries[:14]:  # Last 14 days max
        ago = _days_ago_label(day.date)
        total = day.buy_count or 0

        # Bar segments (proportional — open = remainder to always sum to 100%)
        if total > 0:
            tp_w = round(day.tp_count / total * 100, 1)
            sl_w = round(day.sl_count / total * 100, 1)
            open_w = round(100.0 - tp_w - sl_w, 1)
            if open_w < 0:
                open_w = 0
        else:
            tp_w = sl_w = open_w = 0

        # Tooltip summary
        tip = f"✅ TP: {day.tp_count}  ❌ SL: {day.sl_count}  ⏳ Açık: {total - day.tp_count - day.sl_count}"

        pills_html.append(f"""
        <div class="ds-day-pill" title="{tip}">
            <div class="date">{ago}</div>
            <div class="count">{total}</div>
            <div class="label">AL sinyal</div>
            <div class="bar-wrap">
                <div class="bar-tp" style="width:{tp_w}%"></div>
                <div class="bar-sl" style="width:{sl_w}%"></div>
                <div class="bar-open" style="width:{open_w}%"></div>
            </div>
        </div>
        """)

    st.markdown(
        f'<div class="ds-timeline">{"".join(pills_html)}</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Render: Global KPIs
# ---------------------------------------------------------------------------
def _render_global_kpis(summaries: list[DailySignalSummary]) -> None:
    """Show high-level stats across all days."""
    total_days = len(summaries)
    total_scanned = sum(d.total_scanned for d in summaries)
    total_buy = sum(d.buy_count for d in summaries)
    total_tp = sum(d.tp_count for d in summaries)
    total_sl = sum(d.sl_count for d in summaries)
    total_open = sum(d.open_count for d in summaries)
    total_closed = total_tp + total_sl
    overall_wr = round(total_tp / total_closed * 100, 1) if total_closed > 0 else 0

    cols = st.columns(5)
    cols[0].metric("Tarama Günü", total_days)
    cols[1].metric("Taranan Sembol", f"{total_scanned:,}")
    cols[2].metric("AL Sinyali", total_buy)
    cols[3].metric(
        "Başarı Oranı",
        f"%{overall_wr}" if total_closed > 0 else "—",
        delta=f"{total_tp} TP / {total_sl} SL" if total_closed > 0 else "henüz sonuç yok",
    )
    cols[4].metric("Açık Pozisyon", total_open)


# ---------------------------------------------------------------------------
# Render: Accordion header for a single day
# ---------------------------------------------------------------------------
def _render_day_accordion_header(day: DailySignalSummary) -> str:
    """Return HTML for the accordion header of one day."""
    ago = _days_ago_label(day.date)
    total = day.buy_count

    # Progress bar segments
    if total > 0:
        tp_w = day.tp_count / total * 100
        sl_w = day.sl_count / total * 100
        open_w = day.open_count / total * 100
    else:
        tp_w = sl_w = open_w = 0

    # Labels
    tp_lbl = f'<span class="lbl-tp">✅ {day.tp_count} TP</span>' if day.tp_count else ""
    sl_lbl = f'<span class="lbl-sl">❌ {day.sl_count} SL</span>' if day.sl_count else ""
    open_lbl = f'<span class="lbl-open">⏳ {day.open_count} açık</span>' if day.open_count else ""

    return f"""
    <div class="ds-accordion-hdr">
        <div class="top-row">
            <div>
                <span class="day-title">📅 {day.date_label}</span>
                <span class="day-ago">({ago})</span>
            </div>
            <div class="badges">
                <span class="ds-badge ds-badge-scan">{day.total_scanned} taranan</span>
                <span class="ds-badge ds-badge-buy">{total} AL</span>
                <span class="ds-badge ds-badge-score">⌀ {day.avg_score}</span>
            </div>
        </div>
        <div class="ds-progress-row">
            <div class="ds-progress-bar">
                <div class="seg-tp" style="width:{tp_w}%"></div>
                <div class="seg-sl" style="width:{sl_w}%"></div>
                <div class="seg-open" style="width:{open_w}%"></div>
            </div>
            <div class="ds-progress-labels">
                {tp_lbl}{sl_lbl}{open_lbl}
            </div>
        </div>
    </div>
    """


# ---------------------------------------------------------------------------
# Render: Signal cards within a day
# ---------------------------------------------------------------------------
def _render_signal_cards(signals: list[dict]) -> str:
    """Return HTML for the signal card grid of a single day's signals."""
    if not signals:
        return '<div class="ds-no-buy">Bu gün AL sinyali üretilmedi</div>'

    # Group by score
    strong = [s for s in signals if (s.get("score") or 0) >= 3]
    medium = [s for s in signals if 1 < (s.get("score") or 0) < 3]
    weak = [s for s in signals if (s.get("score") or 0) <= 1]

    html_parts = []

    for group, label, css_cls in [
        (strong, "Güçlü Sinyal", "strong"),
        (medium, "Orta Sinyal", "medium"),
        (weak, "Zayıf Sinyal", "weak"),
    ]:
        if not group:
            continue

        html_parts.append(
            f'<div class="ds-score-section">'
            f'<div class="ds-score-label {css_cls}">'
            f'{"🟢" if css_cls == "strong" else "🟡" if css_cls == "medium" else "⚪"} '
            f'{label} ({len(group)})'
            f'</div>'
            f'<div class="ds-signal-grid">'
        )

        for s in group:
            score = s.get("score") or 0
            score_color = "#22c55e" if score >= 3 else "#f59e0b" if score == 2 else "#94a3b8"
            entry = s.get("entry_price") or 0
            sl_val = s.get("stop_loss") or 0
            tp_val = s.get("take_profit") or 0
            rr = s.get("risk_reward") or 0
            status = str(s.get("status", "active")).lower()
            has_alpaca = bool(s.get("alpaca_order_id"))

            # Status bar class
            if "tp" in status or "profit" in status:
                bar_cls = "tp-hit"
            elif "sl" in status or "loss" in status:
                bar_cls = "sl-hit"
            else:
                bar_cls = "active"

            # Reason → tooltip
            reason = s.get("reason", "")
            reason[:50] + "…" if len(reason) > 50 else reason

            alpaca_tag = '<div class="alpaca-tag">alpaca</div>' if has_alpaca else ""

            # PnL badge for closed signals
            pnl = s.get("pnl_pct")
            if pnl is not None and bar_cls != "active":
                pnl_color = "#22c55e" if pnl >= 0 else "#ef4444"
                pnl_badge = (
                    f'<div style="font-size:0.65rem;font-weight:700;'
                    f'color:{pnl_color};margin-top:2px;">'
                    f"{pnl:+.1f}%</div>"
                )
            else:
                pnl_badge = ""

            # Status label
            if bar_cls == "tp-hit":
                status_label = (
                    '<div style="font-size:0.55rem;color:#22c55e;font-weight:600;">✅ TP</div>'
                )
            elif bar_cls == "sl-hit":
                status_label = (
                    '<div style="font-size:0.55rem;color:#ef4444;font-weight:600;">❌ SL</div>'
                )
            else:
                status_label = ""

            html_parts.append(f"""
            <div class="ds-signal-card" title="{reason}">
                <div class="score-dot" style="background:{score_color}"></div>
                {alpaca_tag}
                <div class="sym">{s.get("symbol", "?")}</div>
                <div class="price-row">
                    <span class="entry">${entry:,.2f}</span>
                    <span class="rr">R/R {rr:.1f}x</span>
                </div>
                <div class="targets">
                    <span class="sl">SL ${sl_val:,.2f}</span>
                    <span class="tp">TP ${tp_val:,.2f}</span>
                </div>
                {status_label}
                {pnl_badge}
                <div class="status-bar {bar_cls}"></div>
            </div>
            """)

        html_parts.append("</div></div>")

    return "\n".join(html_parts)


# ---------------------------------------------------------------------------
# Render: Day detail (expandable content)
# ---------------------------------------------------------------------------
def _render_day_detail_table(day: DailySignalSummary) -> None:
    """Render compact dataframe table for one day (optional detail)."""
    if not day.signals:
        return

    records = []
    for s in day.signals:
        score = s.get("score") or 0
        score_badge = "🟢" if score >= 3 else "🟡" if score == 2 else "⚪"
        status_raw = str(s.get("status", "active")).lower()
        if "tp" in status_raw or "profit" in status_raw:
            status_display = "✅ TP"
        elif "sl" in status_raw or "loss" in status_raw:
            status_display = "❌ SL"
        else:
            status_display = "⏳ Açık"

        pnl = s.get("pnl_pct")
        pnl_str = f"{pnl:+.1f}%" if pnl is not None else "—"

        records.append(
            {
                "Sembol": s.get("symbol", ""),
                "Giriş $": s.get("entry_price", 0),
                "SL $": s.get("stop_loss", 0),
                "TP $": s.get("take_profit", 0),
                "R/R": round(s.get("risk_reward", 0), 1),
                "Skor": f"{score_badge} {score:.0f}",
                "Durum": status_display,
                "P&L": pnl_str,
                "Alpaca": "✓" if s.get("alpaca_order_id") else "—",
            }
        )

    df = pd.DataFrame(records)
    st.dataframe(
        df,
        column_config={
            "Sembol": st.column_config.TextColumn("Sembol", width="small"),
            "Giriş $": st.column_config.NumberColumn("Giriş $", format="$%.2f"),
            "SL $": st.column_config.NumberColumn("SL $", format="$%.2f"),
            "TP $": st.column_config.NumberColumn("TP $", format="$%.2f"),
            "R/R": st.column_config.NumberColumn("R/R", format="%.1f"),
            "Skor": st.column_config.TextColumn("Skor", width="small"),
            "Durum": st.column_config.TextColumn("Durum", width="small"),
            "P&L": st.column_config.TextColumn("P&L", width="small"),
            "Alpaca": st.column_config.TextColumn("", width="small"),
        },
        use_container_width=True,
        hide_index=True,
        height=min(len(records) * 38 + 40, 400),
    )


# ---------------------------------------------------------------------------
# Render: Recent scans summary (bottom)
# ---------------------------------------------------------------------------
def _render_recent_scans_summary(summaries: list[DailySignalSummary]) -> None:
    """Compact table of recent scan days with key stats."""
    st.markdown("##### 📋 Tarama Özeti")
    st.caption("Son tarama günlerinin karşılaştırması")

    records = []
    for day in summaries[:10]:
        ago = _days_ago_label(day.date)
        records.append(
            {
                "Tarih": day.date_label,
                "Ne Zaman": ago,
                "Taranan": day.total_scanned,
                "AL Sinyali": day.buy_count,
                "Güçlü 🟢": day.strong_count,
                "Orta 🟡": day.medium_count,
                "Oran": f"%{day.buy_ratio_pct}" if day.total_scanned > 0 else "—",
                "Ort. Skor": day.avg_score,
            }
        )

    if not records:
        return

    df = pd.DataFrame(records)
    st.dataframe(
        df,
        column_config={
            "Tarih": st.column_config.TextColumn("Tarih"),
            "Ne Zaman": st.column_config.TextColumn("Ne Zaman", width="small"),
            "Taranan": st.column_config.NumberColumn("Taranan", format="%d"),
            "AL Sinyali": st.column_config.NumberColumn("AL", format="%d"),
            "Güçlü 🟢": st.column_config.NumberColumn("Güçlü", format="%d", width="small"),
            "Orta 🟡": st.column_config.NumberColumn("Orta", format="%d", width="small"),
            "Oran": st.column_config.TextColumn("Oran", width="small"),
            "Ort. Skor": st.column_config.NumberColumn("Skor", format="%.1f", width="small"),
        },
        use_container_width=True,
        hide_index=True,
        height=min(len(records) * 38 + 40, 420),
    )

    # En çok sinyal veren hisseler (top 5)
    all_symbols: dict[str, int] = {}
    for day in summaries:
        for s in day.signals:
            sym = s.get("symbol", "")
            if sym:
                all_symbols[sym] = all_symbols.get(sym, 0) + 1

    if all_symbols:
        top5 = sorted(all_symbols.items(), key=lambda x: -x[1])[:5]
        st.markdown("##### 🏆 En Çok Sinyal Veren Hisseler")
        cols = st.columns(min(5, len(top5)))
        for i, (sym, cnt) in enumerate(top5):
            with cols[i]:
                st.metric(sym, f"{cnt} sinyal")


# ---------------------------------------------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------------------------------------------
def render_daily_signals_tab():
    """
    Render the full Daily Signal Tracker tab.

    Layout:
      1. Global KPIs (tarama günü, toplam sinyal, başarı oranı)
      2. Horizontal timeline strip (last 14 days)
      3. Accordion per day (expand for details)
      4. Recent scans summary table
    """
    st.markdown(_DAILY_CSS, unsafe_allow_html=True)

    st.markdown("### 📊 Günlük Sinyal Takibi")

    # --- Outcome refresh button ---
    refresh_col1, refresh_col2 = st.columns([3, 1])
    with refresh_col1:
        st.caption(
            "Her gün kaç sembol tarandı, kaç AL sinyali üretildi, " "ve bu sinyallerin durumu."
        )
    with refresh_col2:
        if st.button(
            "🔄 Sonuçları Güncelle",
            help="Aktif sinyallerin TP/SL durumunu gerçek fiyatlarla kontrol et",
            use_container_width=True,
        ):
            with st.spinner("Fiyat verileri kontrol ediliyor…"):
                result = _update_signal_outcomes()
            tp = result.get("tp", 0)
            sl = result.get("sl", 0)
            checked = result.get("checked", 0)
            still = result.get("still_active", 0)
            errs = result.get("errors", 0)
            if tp + sl > 0:
                st.success(
                    f"✅ {checked} sinyal kontrol edildi — "
                    f"**{tp} TP**, **{sl} SL** tespit, "
                    f"{still} hâlâ açık" + (f", {errs} hata" if errs else "")
                )
            elif checked > 0:
                st.info(f"📊 {checked} sinyal kontrol edildi — henüz TP/SL tetiklenmedi.")
            else:
                st.info("Kontrol edilecek aktif sinyal yok.")
            # Clear cache so fresh data loads
            _load_daily_summaries.clear()

    # Load data
    summaries = _load_daily_summaries()

    if not summaries:
        st.markdown(
            '<div class="ds-empty">'
            '<div class="icon">📡</div>'
            '<div class="msg">Henüz tarama verisi yok.<br>'
            "İlk taramayı yaptığınızda sinyaller burada görünecek.</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    # 1. Global KPIs
    _render_global_kpis(summaries)

    st.markdown("---")

    # 2. Timeline strip
    st.markdown("##### 📅 Son Taramalar")
    _render_timeline_strip(summaries)

    # Bar legend
    st.markdown(
        '<div style="display:flex; gap:16px; justify-content:center; '
        'font-size:0.7rem; color:rgba(148,163,184,0.75); margin: 4px 0 8px;">'
        '<span><span style="display:inline-block;width:10px;height:10px;'
        'border-radius:2px;background:#22c55e;margin-right:4px;vertical-align:middle;"></span>TP Hedefi</span>'
        '<span><span style="display:inline-block;width:10px;height:10px;'
        'border-radius:2px;background:#ef4444;margin-right:4px;vertical-align:middle;"></span>Stop Loss</span>'
        '<span><span style="display:inline-block;width:10px;height:10px;'
        'border-radius:2px;background:#f59e0b;margin-right:4px;vertical-align:middle;"></span>Açık</span>'
        "</div>",
        unsafe_allow_html=True,
    )

    # 3. Accordion per day
    for day in summaries:
        # Header always visible
        st.markdown(
            _render_day_accordion_header(day),
            unsafe_allow_html=True,
        )

        # Expandable detail
        if day.buy_count > 0:
            with st.expander(
                f"📋 {day.buy_count} sinyali gör — {day.date}",
                expanded=(day == summaries[0]),  # first day expanded by default
            ):
                # Card grid
                st.markdown(
                    _render_signal_cards(day.signals),
                    unsafe_allow_html=True,
                )

                # Optional: compact table toggle
                if len(day.signals) > 6 and st.toggle(
                    "Tablo görünümüne geç",
                    key=f"tbl_toggle_{day.date}",
                    value=False,
                ):
                    _render_day_detail_table(day)

    # 4. Son taramalar özet tablosu
    st.markdown("---")
    _render_recent_scans_summary(summaries)
