"""
Script to generate AI signals for valid symbols.
Can be run daily via Cron.
"""

import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
from datetime import datetime

import numpy as np
import pandas as pd

from drl.config import DEFAULT_CONFIG, MarketEnvConfig
from drl.data_loader import prepare_inference_frame

# Symbols to scan
SYMBOLS = ["AAPL", "BTC-USD", "NVDA", "TSLA", "ETH-USD"]
OUTPUT_FILE = "data/inference.json"


def calculate_heuristic_score(row):
    """
    A smart heuristic to simulate DRL agent thinking until model is trained.
    Returns: Score (0-100), Signal (BUY/SELL/HOLD), Confidence (0-1)
    """
    score = 50.0  # Neutral

    # 1. Trend Factor (Trend Following)
    if row["regime_trend"] == 1.0:
        score += 20
        # If in trend and pullback to EMA20?
        if row["close"] > row["ema_20"]:
            score += 5

    # 2. Momentum Factor (RSI)
    rsi = row["rsi"]
    if rsi < 30:
        score += 15  # Oversold -> Buy
    elif rsi > 70:
        score -= 15  # Overbought -> Sell

    # 3. AI/Alt Data Factor
    sentiment = row["sentiment_score"]  # -1 to 1
    score += sentiment * 15  # Sentiment impact

    # 4. Volatility Penalty
    if row["regime_volatility"] == 1.0:
        score -= 10  # Safer to stay out

    # Clamp
    score = max(0, min(100, score))

    # Determine Signal
    if score >= 75:
        signal = "BUY"
        confidence = (score - 50) / 50.0
    elif score <= 25:
        signal = "SELL"
        confidence = (50 - score) / 50.0
    else:
        signal = "HOLD"
        confidence = 1.0 - (abs(score - 50) / 25.0)

    return score, signal, round(confidence, 2)


def main():
    print(f"Starting AI Inference Service at {datetime.now()}...")

    results = {}
    config = DEFAULT_CONFIG  # Use default config

    for symbol in SYMBOLS:
        try:
            print(f"Analyzing {symbol}...")
            df = prepare_inference_frame(symbol, config)

            if df.empty:
                print(f"Skipping {symbol}, no data.")
                continue

            # Take the very last row (Current State)
            latest_row = df.iloc[-1]

            ai_score, signal, conf = calculate_heuristic_score(latest_row)

            # Construct Result Object
            results[symbol] = {
                "timestamp": datetime.now().isoformat(),
                "price": round(latest_row["close"], 2),
                "ai_score": round(ai_score, 1),
                "signal": signal,
                "confidence": conf,
                "regime": (
                    "TREND"
                    if latest_row["regime_trend"]
                    else ("VOLATILE" if latest_row["regime_volatility"] else "RANGE")
                ),
                "features": {
                    "rsi": round(latest_row["rsi"], 2),
                    "sentiment": round(latest_row["sentiment_score"], 2),
                    "w_flow": round(latest_row["onchain_tx_volume"], 2),
                },
            }
            print(f"-> {symbol}: {signal} (Score: {ai_score})")

        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")

    # Save to JSON
    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Inference complete. Results saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
