import numpy as np
import pandas as pd
from hmmlearn import hmm


def detect_market_regime(prices: pd.Series, n_components=2) -> int:
    """
    Fiyat serisinden log getirileri ile HMM tabanlı piyasa rejimi tespiti.
    n_components: 2 (trend/aralık) veya 3 (trend/aralık/kaotik)
    Dönüş: Son günün rejim etiketi (int)
    """
    returns = np.log(prices / prices.shift(1)).dropna().values.reshape(-1, 1)
    model = hmm.GaussianHMM(n_components=n_components, covariance_type="diag", n_iter=100)
    model.fit(returns)
    hidden_states = model.predict(returns)
    return hidden_states[-1]


# Panel ve scanner entegrasyonu için örnek kullanım:
if __name__ == "__main__":
    import yfinance as yf

    symbol = "AAPL"
    df = yf.download(symbol, period="6mo", interval="1d")
    regime = detect_market_regime(df["Close"])
    print(f"{symbol} son rejim etiketi: {regime}")
