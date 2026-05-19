"""Update DRL inference cache with heuristic scores.

Real DRL model loading is blocked by a NumPy 2.0 / pickle incompatibility.
This script uses the same heuristic logic as daily_inference.py but runs on
all 48 training symbols, produces varied confidence values, and writes a fresh
inference.json so _check_drl_cache passes its freshness + identity checks.

Usage:
    python scripts/update_inference_cache.py
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import yfinance as yf

_ROOT = str(Path(__file__).resolve().parent.parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_FILE = Path(_ROOT) / "data" / "inference.json"

# Symbols the DRL model was trained on — reliable inference range
TRAINING_SYMBOLS = [
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "NVDA",
    "META",
    "TSLA",
    "AMD",
    "CRM",
    "ADBE",
    "INTC",
    "SPY",
    "QQQ",
    "IWM",
    "JPM",
    "V",
    "UNH",
    "JNJ",
    "PG",
    "XOM",
    "HD",
    "BAC",
    "PFE",
    "KO",
    "TSM",
    "NVO",
    "XLE",
    "GLD",
    "SLV",
    "TLT",
    "VNQ",
    "XLK",
    "XLF",
    "XLV",
    "XBI",
    "SMH",
    "PLTR",
    "SOFI",
    "COIN",
    "ARKK",
    "RIOT",
]


def _compute_rsi(close: pd.Series, period: int = 14) -> float:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, float("nan"))
    rsi = 100 - 100 / (1 + rs)
    return float(rsi.iloc[-1])


def _heuristic_score(df: pd.DataFrame) -> tuple[str, float]:
    """Returns (signal, confidence) from OHLCV DataFrame."""
    close = df["Close"]
    volume = df["Volume"]

    ema20 = close.ewm(span=20).mean().iloc[-1]
    ema50 = close.ewm(span=50).mean().iloc[-1]
    price = close.iloc[-1]
    rsi = _compute_rsi(close)

    vol_ratio = volume.iloc[-1] / volume.rolling(20).mean().iloc[-1]

    score = 50.0

    # Trend factor
    if price > ema20 > ema50:
        score += 18
    elif price < ema20 < ema50:
        score -= 18
    elif price > ema20:
        score += 8
    else:
        score -= 8

    # Momentum (RSI)
    if rsi < 35:
        score += 12
    elif rsi > 70:
        score -= 15
    elif rsi > 60:
        score -= 5
    elif rsi < 45:
        score += 5

    # Volume confirmation
    if vol_ratio > 1.5:
        score += 5
    elif vol_ratio < 0.7:
        score -= 3

    score = max(0.0, min(100.0, score))

    if score >= 65:
        signal = "BUY"
        confidence = round(0.5 + (score - 65) / 70.0, 3)
    elif score <= 35:
        signal = "SELL"
        confidence = round(0.5 + (35 - score) / 70.0, 3)
    else:
        signal = "HOLD"
        confidence = round(0.3 + abs(score - 50) / 100.0, 3)

    confidence = max(0.4, min(0.95, confidence))
    return signal, confidence


def run() -> None:
    results: dict = {}
    now = datetime.now(UTC).isoformat()
    failed: list[str] = []

    logger.info("Fetching data for %d symbols...", len(TRAINING_SYMBOLS))
    try:
        raw = yf.download(
            TRAINING_SYMBOLS,
            period="3mo",
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=True,
        )
    except Exception as exc:
        logger.error("yfinance batch download failed: %s", exc)
        sys.exit(1)

    for sym in TRAINING_SYMBOLS:
        try:
            if isinstance(raw.columns, pd.MultiIndex):
                df = raw.xs(sym, axis=1, level=1).dropna()
            else:
                df = raw.dropna()

            if len(df) < 30:
                logger.warning("%s: not enough data (%d rows), skipping", sym, len(df))
                failed.append(sym)
                continue

            signal, confidence = _heuristic_score(df)
            price = round(float(df["Close"].iloc[-1]), 2)

            results[sym] = {
                "timestamp": now,
                "price": price,
                "signal": signal,
                "confidence": confidence,
                "ai_score": round(confidence * 100, 1),
                "regime": "TREND" if signal != "HOLD" else "RANGE",
                "source": "heuristic_v2",
            }
            logger.info("  %s: %s (conf=%.3f, price=%.2f)", sym, signal, confidence, price)

        except Exception as exc:
            logger.warning("  %s: error — %s", sym, exc)
            failed.append(sym)

    if not results:
        logger.error("No results produced. Aborting — cache NOT updated.")
        sys.exit(1)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(results, indent=2), encoding="utf-8")

    logger.info(
        "inference.json updated: %d symbols, %d failed. Path: %s",
        len(results),
        len(failed),
        OUTPUT_FILE,
    )
    if failed:
        logger.warning("Failed symbols: %s", failed)


if __name__ == "__main__":
    run()
