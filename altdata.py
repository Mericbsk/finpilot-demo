# ML/DRL state space için alternatif veri vektörü
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd


def _rng_for_symbol(symbol: str) -> np.random.Generator:
    seed = abs(hash(symbol)) % (2**32)
    return np.random.default_rng(seed)


def get_altdata_history(symbol: str, *, periods: int = 24, freq: str = "H") -> pd.DataFrame:
    """Generate a deterministic pseudo-history for sentiment and whale flow."""

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
