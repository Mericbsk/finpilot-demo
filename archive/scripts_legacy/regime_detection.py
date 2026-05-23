import hashlib

import numpy as np
import pandas as pd
from hmmlearn import hmm

# HMM model cache — avoids expensive re-fitting for the same price series
_hmm_cache: dict = {}


def _series_hash(prices: pd.Series) -> str:
    """Produce a fast hash of price series for cache keying."""
    raw = prices.values.tobytes()
    return hashlib.md5(raw).hexdigest()  # nosec B324 — cache key, not security


def detect_market_regime(prices: pd.Series, n_components: int = 2) -> int:
    """
    Fiyat serisinden log getirileri ile HMM tabanlı piyasa rejimi tespiti.
    n_components: 2 (trend/aralık) veya 3 (trend/aralık/kaotik)
    Dönüş: Son günün rejim etiketi (int)

    Caching: Aynı fiyat serisi ile tekrar çağrılırsa model yeniden
    fit edilmez — Sprint 3 D4 performans iyileştirmesi.
    """
    cache_key = (_series_hash(prices), n_components)
    if cache_key in _hmm_cache:
        return _hmm_cache[cache_key]

    returns = np.log(prices / prices.shift(1)).dropna().values.reshape(-1, 1)
    model = hmm.GaussianHMM(n_components=n_components, covariance_type="diag", n_iter=100)
    model.fit(returns)
    hidden_states = model.predict(returns)
    result = int(hidden_states[-1])

    _hmm_cache[cache_key] = result
    return result


# Panel ve scanner entegrasyonu için örnek kullanım:
if __name__ == "__main__":
    import yfinance as yf

    symbol = "AAPL"
    df = yf.download(symbol, period="6mo", interval="1d")
    regime = detect_market_regime(df["Close"])
    print(f"{symbol} son rejim etiketi: {regime}")
