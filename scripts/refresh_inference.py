#!/usr/bin/env python3
"""
Inference Cache Auto-Refresh
=============================
Runs the daily inference pipeline on a schedule (default: every 4 hours).

Usage:
    # One-shot
    python scripts/refresh_inference.py --once

    # Continuous (every 4 hours)
    python scripts/refresh_inference.py

    # Custom interval
    python scripts/refresh_inference.py --interval 3600    # Every 1 hour

Cron alternative (add to crontab):
    0 */4 * * * cd /app && python scripts/refresh_inference.py --once >> logs/inference_refresh.log 2>&1
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import sys
import time
from pathlib import Path

# Ensure project root is on path
_ROOT = str(Path(__file__).resolve().parent.parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(_ROOT, "logs", "inference_refresh.log"), mode="a"),
    ],
)
logger = logging.getLogger(__name__)

OUTPUT_FILE = os.path.join(_ROOT, "data", "inference.json")
DEFAULT_INTERVAL = 4 * 3600  # 4 hours

_running = True


def _signal_handler(_sig: int, _frame: object) -> None:
    global _running
    logger.info("Shutdown signal received, stopping...")
    _running = False


def refresh_once() -> bool:
    """Run one refresh cycle. Returns True on success."""
    logger.info("Starting inference refresh cycle...")
    start = time.time()

    try:
        # Try to use the daily_inference module
        from scripts.daily_inference import main as run_inference

        run_inference()
        elapsed = time.time() - start
        logger.info("Inference refresh completed in %.1fs", elapsed)

        # Validate output
        if os.path.exists(OUTPUT_FILE):
            with open(OUTPUT_FILE) as f:
                data = json.load(f)
            logger.info("Cache contains %d tickers: %s", len(data), ", ".join(data.keys()))
            return True
        else:
            logger.warning("Output file not found at %s", OUTPUT_FILE)
            return False

    except Exception:
        logger.exception("Inference refresh failed")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Inference cache auto-refresh")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_INTERVAL,
        help=f"Refresh interval in seconds (default: {DEFAULT_INTERVAL})",
    )
    args = parser.parse_args()

    os.makedirs(os.path.join(_ROOT, "logs"), exist_ok=True)
    os.makedirs(os.path.join(_ROOT, "data"), exist_ok=True)

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    if args.once:
        success = refresh_once()
        sys.exit(0 if success else 1)

    logger.info(
        "Inference auto-refresh started (interval: %ds = %.1fh)",
        args.interval,
        args.interval / 3600,
    )

    while _running:
        refresh_once()
        logger.info("Next refresh in %ds...", args.interval)

        # Interruptible sleep
        for _ in range(args.interval):
            if not _running:
                break
            time.sleep(1)

    logger.info("Inference auto-refresh stopped.")


if __name__ == "__main__":
    main()
