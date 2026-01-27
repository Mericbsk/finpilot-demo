# ML/DRL state space için alternatif veri vektörü
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf


def _rng_for_symbol(symbol: str) -> np.random.Generator:
    seed = abs(hash(symbol)) % (2**32)
    return np.random.default_rng(seed)


def get_altdata_history(symbol: str, *, periods: int = 24, freq: str = "H") -> pd.DataFrame:
    """Generate alt-data history using Real Market Data (via yfinance) where possible."""

    # Map frequency to yfinance interval
    interval_map = {"H": "1h", "D": "1d", "15T": "15m"}
    yf_interval = interval_map.get(freq, "1h")

    # Calculate start date based on periods
    # Note: 730 hours is approx 1 month (max for 1h interval on yfinance free tier is usually 730 days, but hourly is limited)
    try:
        # Fetch real data
        df = yf.download(symbol, period="1mo", interval=yf_interval, progress=False)

        if not df.empty and len(df) >= periods:
            df = df.tail(periods).copy()

            # 1. Feature: "Sentiment" Proxy -> RSI (Relative Strength Index)
            # Normalized to -1.0 to 1.0 range
            delta = df["Close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            # Normalize RSI (0-100) to (-1 to 1)
            # RSI 50 -> 0.0, RSI 70 -> 0.4, RSI 30 -> -0.4
            sentiment = ((rsi.fillna(50) - 50) / 50.0).values
            sentiment = np.clip(sentiment, -1.0, 1.0)  # Ensure bounds

            # 2. Feature: "Whale Flow" Proxy -> Volume * Close (Dollar Volume)
            # Normalized/Scaled logarithmically
            dollar_vol = (df["Volume"] * df["Close"]).astype(float)
            # Simple Z-score like scaling relative to recent mean, shifted to look like 'flow'
            whale_flow = (dollar_vol / dollar_vol.mean()) * 100.0
            whale_flow = whale_flow.fillna(100.0).values

            # Create the DataFrame with the exact index required
            # Retain the exact timestamp index from yfinance if aligned, or reindex?
            # The current system expects a specific length.
            return pd.DataFrame(
                {
                    "sentiment_score": sentiment,
                    "onchain_tx_volume": whale_flow,
                },
                index=df.index,
            )

    except Exception as e:
        print(
            f"Warning: Failed to fetch real altdata for {symbol}: {e}. Falling back to synthetic."
        )

    # Fallback to Mock Data (Original Logic)
    rng = _rng_for_symbol(symbol)
    index = pd.date_range(end=pd.Timestamp.utcnow(), periods=periods, freq=freq)

    sentiment_noise = rng.normal(0.0, 0.08, size=periods)
    sentiment = np.cumsum(sentiment_noise) + rng.uniform(-0.2, 0.2)
    sentiment = np.clip(sentiment, -1.0, 1.0)

    flow_base = rng.uniform(80, 150)
    flow_noise = rng.normal(0.0, 12.0, size=periods)
    whale_flow = np.cumsum(flow_noise) + flow_base
    whale_flow = np.maximum(whale_flow, 0.0)

    return pd.DataFrame(
        {
            "sentiment_score": sentiment,
            "onchain_tx_volume": whale_flow,
        },
        index=index,
    )


def get_sentiment_score(symbol: str) -> float:
    history = get_altdata_history(symbol)
    return round(float(history["sentiment_score"].iloc[-1]), 2)


def get_onchain_metric(symbol: str) -> float:
    history = get_altdata_history(symbol)
    return round(float(history["onchain_tx_volume"].iloc[-1]), 2)


def get_altdata_state(symbol: str, timestamp: Optional[pd.Timestamp] = None) -> dict:
    if timestamp is None:
        timestamp = pd.Timestamp.utcnow()
    return {
        "symbol": symbol,
        "timestamp": str(timestamp),
        "sentiment": get_sentiment_score(symbol),
        "onchain_metric": get_onchain_metric(symbol),
    }


if __name__ == "__main__":
    syms = ["BTC", "ETH", "SOL"]
    for s in syms:
        hist = get_altdata_history(s)
        print(s, hist.tail(3))
