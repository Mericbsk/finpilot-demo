# polygon_live.py
# Polygon.io canlı veri çekme yardımcı fonksiyonları

import pandas as pd
from polygon import RESTClient

API_KEY = "59apKccpWYf308fTpaTdxINGK2impMyc"

client = RESTClient(API_KEY)


def get_polygon_last_quote(symbol: str):
    try:
        from datetime import timedelta, timezone

        import pandas as pd
        import pytz

        quote = client.get_last_quote(symbol)
        ts = quote.timestamp
        # Polygon bazen ns, bazen ms döndürebilir. 1970'ten bu yana çok büyükse ns'dir.
        if ts > 1e15:
            dt = pd.to_datetime(ts, unit="ns")
        else:
            dt = pd.to_datetime(ts, unit="ms")
        # Türkiye saati (UTC+3)
        dt = dt.tz_localize("UTC").tz_convert("Europe/Istanbul")
        return {
            "symbol": symbol,
            "ask": quote.askprice,
            "bid": quote.bidprice,
            "price": quote.askprice or quote.bidprice,
            "timestamp": dt.strftime("%Y-%m-%d %H:%M:%S"),
        }
    except Exception as e:
        return {"symbol": symbol, "error": str(e)}


def get_polygon_last_trade(symbol: str):
    try:
        trade = client.get_last_trade(symbol)
        return {
            "symbol": symbol,
            "price": trade.price,
            "size": trade.size,
            "timestamp": pd.to_datetime(trade.timestamp, unit="ms"),
        }
    except Exception as e:
        return {"symbol": symbol, "error": str(e)}
