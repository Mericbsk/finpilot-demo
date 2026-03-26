#!/usr/bin/env python3
"""
Automated Scanner & Trader — Sprint 21.

Runs a full NASDAQ scan, records BUY signals to DB,
and places orders on Alpaca paper trading.

Can be run:
  1. Manually:        python scripts/auto_scan_trade.py
  2. Scheduled:       python scripts/auto_scan_trade.py --schedule 14:00
  3. One-shot scan:   python scripts/auto_scan_trade.py --once

Environment variables:
    ALPACA_API_KEY     — Alpaca paper trading API key
    ALPACA_SECRET_KEY  — Alpaca paper trading secret key
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import date, datetime
from pathlib import Path

# Ensure project root on path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/auto_scan_trade.log", mode="a"),
    ],
)
logger = logging.getLogger("auto_scan_trade")


# ===========================================================================
# Scan Engine
# ===========================================================================


def run_scan(preset_name: str = "tech_giants") -> list[dict]:
    """
    Run the FinPilot scanner on a preset and return BUY signals.

    Returns list of dicts with: symbol, price, stop_loss, take_profit,
    score, strength, regime, entry_ok, risk_reward, position_size, etc.
    """
    from scanner.evaluate import evaluate_symbols_parallel
    from views.components.stock_presets import STOCK_PRESETS

    # Load symbols
    if preset_name in STOCK_PRESETS:
        symbols = STOCK_PRESETS[preset_name].symbols
        logger.info(f"Scanning preset '{preset_name}': {len(symbols)} symbols")
    else:
        # Default fallback
        symbols = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA", "META", "AMD", "AMZN"]
        logger.info(f"Scanning default symbols: {len(symbols)}")

    results = evaluate_symbols_parallel(symbols, kelly_fraction=0.5)
    logger.info(f"Scan complete: {len(results)} results")

    # Filter to BUY signals only (entry_ok=True)
    buy_signals = [r for r in results if r.get("entry_ok")]
    logger.info(f"BUY signals: {len(buy_signals)}")

    return buy_signals


def get_all_unique_symbols() -> list[str]:
    """Collect all unique symbols from every preset."""
    from views.components.stock_presets import STOCK_PRESETS

    seen = set()
    symbols = []
    for preset in STOCK_PRESETS.values():
        for s in preset.symbols:
            if s not in seen:
                seen.add(s)
                symbols.append(s)
    return symbols


def run_multi_preset_scan(presets: list[str] | None = None) -> list[dict]:
    """Run scan across multiple presets and deduplicate."""
    if presets is None:
        presets = ["tech_giants", "semiconductors", "cloud_saas"]

    all_signals = {}
    for preset in presets:
        try:
            signals = run_scan(preset)
            for s in signals:
                sym = s["symbol"]
                # Keep the highest-scoring signal per symbol
                if sym not in all_signals or s.get("score", 0) > all_signals[sym].get("score", 0):
                    s["scan_source"] = preset
                    all_signals[sym] = s
        except Exception as e:
            logger.error(f"Scan failed for preset '{preset}': {e}")

    return list(all_signals.values())


def run_full_scan(chunk_size: int = 100) -> list[dict]:
    """
    Scan ALL symbols from every preset in one go.

    Splits into chunks to avoid yfinance rate limits and memory issues.
    Deduplicates by symbol — keeps the highest-scoring signal.

    Args:
        chunk_size: Number of symbols per batch (default 100).

    Returns:
        List of BUY signal dicts, deduplicated by symbol.
    """
    from scanner.evaluate import evaluate_symbols_parallel

    all_symbols = get_all_unique_symbols()
    total = len(all_symbols)
    logger.info(f"🔍 FULL SCAN: {total} unique symbols across all presets")

    # Split into chunks
    chunks = [all_symbols[i : i + chunk_size] for i in range(0, total, chunk_size)]
    logger.info(f"   Split into {len(chunks)} chunks of ~{chunk_size}")

    all_signals: dict[str, dict] = {}
    scanned = 0

    for idx, chunk in enumerate(chunks, 1):
        t0 = time.time()
        logger.info(f"\n   ▶ Chunk {idx}/{len(chunks)}: {len(chunk)} symbols ...")

        try:
            results = evaluate_symbols_parallel(chunk, kelly_fraction=0.5)
            buy_signals = [r for r in results if r.get("entry_ok")]

            for s in buy_signals:
                sym = s["symbol"]
                if sym not in all_signals or s.get("score", 0) > all_signals[sym].get("score", 0):
                    s["scan_source"] = "full_scan"
                    all_signals[sym] = s

            scanned += len(chunk)
            elapsed = round(time.time() - t0, 1)
            logger.info(
                f"     ✓ {len(buy_signals)} BUY / {len(results)} total "
                f"({elapsed}s) — running total: {len(all_signals)} BUY, "
                f"{scanned}/{total} scanned"
            )
        except Exception as e:
            logger.error(f"     ✗ Chunk {idx} failed: {e}")
            scanned += len(chunk)

        # Brief pause between chunks to be kind to yfinance
        if idx < len(chunks):
            time.sleep(2)

    logger.info(f"\n🏁 FULL SCAN DONE: {len(all_signals)} BUY signals from {scanned} symbols")
    return list(all_signals.values())


# ===========================================================================
# Save to DB
# ===========================================================================


def record_buy_signals(signals: list[dict]) -> list[dict]:
    """
    Record BUY signals to the buy_signals table.

    Returns list of saved signals with their DB IDs.
    """
    from auth.database import BuySignalRepository, get_database

    db = get_database()
    repo = BuySignalRepository(db)
    today = date.today().isoformat()
    saved = []

    for s in signals:
        record = {
            "date": today,
            "symbol": s["symbol"],
            "entry_price": s["price"],
            "stop_loss": s.get("stop_loss"),
            "take_profit": s.get("take_profit"),
            "risk_reward": s.get("risk_reward"),
            "score": s.get("score"),
            "strength": s.get("filter_score", s.get("strength")),
            "regime": str(s.get("regime", "")),
            "sentiment": s.get("sentiment"),
            "position_size": s.get("position_size"),
            "kelly_fraction": s.get("kelly_fraction"),
            "reason": _build_reason(s),
            "scan_source": s.get("scan_source", ""),
        }
        row_id = repo.save(record)
        if row_id:
            record["id"] = row_id
            saved.append(record)
            logger.info(
                f"  📝 {s['symbol']}: ${s['price']:.2f} "
                f"SL=${s.get('stop_loss', 0):.2f} "
                f"TP=${s.get('take_profit', 0):.2f} "
                f"Score={s.get('score')}"
            )

    logger.info(f"Recorded {len(saved)} buy signals for {today}")
    return saved


def _build_reason(signal: dict) -> str:
    """Build a human-readable reason string."""
    parts = []
    if signal.get("direction"):
        parts.append("Trend UP")
    if signal.get("volume_spike"):
        parts.append("Volume Spike")
    if signal.get("momentum_confluence"):
        parts.append("Momentum Confluence")
    if signal.get("timeframe_aligned"):
        parts.append(f"MTF Aligned ({signal.get('alignment_ratio', 0):.0%})")
    rr = signal.get("risk_reward")
    if rr:
        parts.append(f"R/R {rr:.1f}")
    return " | ".join(parts) if parts else "Signal conditions met"


# ===========================================================================
# Place Orders on Alpaca
# ===========================================================================


def place_alpaca_orders(signals: list[dict]) -> list[dict]:
    """
    Place BUY orders on Alpaca paper trading for each signal.

    Uses limit orders at current price with stop-loss protection.
    """
    from broker import AlpacaBroker

    broker = AlpacaBroker()
    if not broker.is_available:
        logger.warning("❌ Alpaca not configured — skipping order placement")
        logger.warning("   Set ALPACA_API_KEY and ALPACA_SECRET_KEY env vars")
        return []

    # Check account
    try:
        acct = broker.get_account()
        logger.info(
            f"💰 Alpaca Account: ${acct['portfolio_value']:,.2f} (Cash: ${acct['cash']:,.2f})"
        )
    except Exception as e:
        logger.error(f"Cannot connect to Alpaca: {e}")
        return []

    orders = []
    for s in signals:
        symbol = s["symbol"]
        entry_price = s["entry_price"]
        stop_loss = s.get("stop_loss")
        take_profit = s.get("take_profit")
        signal_id = s.get("id")

        # Calculate position size (risk 2% per trade, max 10% per position)
        if stop_loss:
            qty = broker.calculate_position_size(entry_price, stop_loss)
        else:
            # Fallback: buy ~$500 worth
            qty = max(1, int(500 / entry_price))

        try:
            order = broker.place_buy_order(
                symbol=symbol,
                qty=qty,
                limit_price=round(entry_price * 1.005, 2),  # slight buffer
                stop_loss=stop_loss,
                take_profit=take_profit,
                buy_signal_id=signal_id,
                time_in_force="day",
            )
            orders.append(order)
            logger.info(
                f"  ✅ {symbol}: BUY {qty} shares @ ${entry_price:.2f} "
                f"(order: {order['order_id'][:8]}...)"
            )
        except Exception as e:
            logger.error(f"  ❌ {symbol}: Order failed — {e}")

    logger.info(f"Placed {len(orders)} orders on Alpaca")
    return orders


# ===========================================================================
# Also log to CSV + DB signals table for backward compat
# ===========================================================================


def log_to_legacy_systems(signals: list[dict]) -> None:
    """Also save to the Sprint 20 signals table and CSV for compat."""
    try:
        from auth.database import SignalRepository, get_database

        db = get_database()
        repo = SignalRepository(db)
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        batch = []
        for s in signals:
            batch.append(
                {
                    "timestamp": now,
                    "symbol": s["symbol"],
                    "price": s.get("entry_price", s.get("price")),
                    "stop_loss": s.get("stop_loss"),
                    "take_profit": s.get("take_profit"),
                    "score": s.get("score"),
                    "strength": s.get("strength"),
                    "regime": s.get("regime"),
                    "sentiment": s.get("sentiment"),
                    "entry_ok": True,
                    "summary": s.get("reason", ""),
                    "reason": s.get("scan_source", ""),
                }
            )

        if batch:
            repo.save_batch(batch)
            logger.info(f"Also logged {len(batch)} to signals table")
    except Exception as e:
        logger.warning(f"Legacy logging failed: {e}")


# ===========================================================================
# Full Pipeline
# ===========================================================================


def run_full_pipeline(
    presets: list[str] | None = None,
    place_orders: bool = True,
) -> dict:
    """
    Complete pipeline: scan → record → trade.

    Returns summary dict.
    """
    start = time.time()
    today = date.today().isoformat()

    logger.info("=" * 60)
    logger.info(f"🚀 AUTO SCAN & TRADE — {today}")
    logger.info("=" * 60)

    # 1. Scan
    logger.info("\n📊 Phase 1: Scanning...")
    buy_signals = run_full_scan() if presets == ["__ALL__"] else run_multi_preset_scan(presets)
    if not buy_signals:
        logger.info("No BUY signals found today.")
        return {"date": today, "signals": 0, "orders": 0, "elapsed": 0}

    # 2. Record to DB
    logger.info(f"\n📝 Phase 2: Recording {len(buy_signals)} signals...")
    saved_signals = record_buy_signals(buy_signals)

    # 3. Legacy compat
    log_to_legacy_systems(buy_signals)

    # 4. Place orders
    orders = []
    if place_orders and saved_signals:
        logger.info(f"\n📈 Phase 3: Placing {len(saved_signals)} orders on Alpaca...")
        orders = place_alpaca_orders(saved_signals)

    elapsed = round(time.time() - start, 1)

    # Summary
    summary = {
        "date": today,
        "signals": len(saved_signals),
        "orders": len(orders),
        "elapsed": elapsed,
        "symbols": [s["symbol"] for s in saved_signals],
    }

    logger.info("\n" + "=" * 60)
    logger.info(f"✅ DONE — {summary['signals']} signals, {summary['orders']} orders, {elapsed}s")
    logger.info("=" * 60)

    # Save summary JSON
    _save_summary(summary)
    return summary


def _save_summary(summary: dict) -> None:
    """Save daily summary to logs."""
    log_dir = Path("logs/auto_trade")
    log_dir.mkdir(parents=True, exist_ok=True)
    fpath = log_dir / f"summary_{summary['date']}.json"
    with open(fpath, "w") as f:
        json.dump(summary, f, indent=2, default=str)


# ===========================================================================
# Scheduler
# ===========================================================================


def start_scheduler(scan_time: str = "14:00", presets: list[str] | None = None) -> None:
    """
    Start APScheduler to run the pipeline at a specific time daily.

    Args:
        scan_time: HH:MM format (24h), e.g. "14:00"
        presets: Stock preset names to scan
    """
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger

    hour, minute = map(int, scan_time.split(":"))

    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_full_pipeline,
        CronTrigger(
            day_of_week="mon-fri",
            hour=hour,
            minute=minute,
            timezone="America/New_York",
        ),
        kwargs={"presets": presets, "place_orders": True},
        id="daily_scan_trade",
        name=f"Daily Scan & Trade @ {scan_time} ET",
        misfire_grace_time=3600,
    )

    logger.info(f"⏰ Scheduler started — scanning at {scan_time} ET (Mon-Fri)")
    logger.info("   Press Ctrl+C to stop")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")
        scheduler.shutdown()


# ===========================================================================
# CLI
# ===========================================================================


def main():
    os.makedirs("logs", exist_ok=True)

    parser = argparse.ArgumentParser(description="FinPilot Auto Scanner & Trader")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run one scan immediately and exit",
    )
    parser.add_argument(
        "--schedule",
        type=str,
        default=None,
        help="Schedule daily scan at HH:MM (e.g. --schedule 14:00)",
    )
    parser.add_argument(
        "--presets",
        nargs="+",
        default=["tech_giants", "semiconductors", "cloud_saas"],
        help="Stock presets to scan",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Scan ALL symbols from every preset (~1500 symbols)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=100,
        help="Symbols per batch when using --all (default: 100)",
    )
    parser.add_argument(
        "--no-trade",
        action="store_true",
        help="Scan and record signals only, don't place orders",
    )
    parser.add_argument(
        "--scan-only",
        action="store_true",
        help="Alias for --no-trade",
    )

    args = parser.parse_args()
    place_orders = not (args.no_trade or args.scan_only)

    # --all overrides --presets
    if getattr(args, "all", False):
        args.presets = ["__ALL__"]

    if args.schedule:
        # Scheduled mode
        start_scheduler(args.schedule, args.presets)
    else:
        # One-shot mode (default or --once)
        run_full_pipeline(presets=args.presets, place_orders=place_orders)


if __name__ == "__main__":
    main()
