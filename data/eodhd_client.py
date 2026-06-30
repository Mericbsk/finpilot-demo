"""EODHD API Client
=================

FinPilot'un tüm EODHD veri ihtiyaçlarını karşılayan merkezi istemci.

Desteklenen endpoint'ler:
  • real_time(symbols)          – Anlık fiyat (15-20 dk gecikme), OHLCV
  • eod_history(symbol, days)   – Günlük OHLCV geçmişi (sınırsız)
  • fundamentals(symbol)        – PE, EPS, gelir, bilanço, analist hedefleri
  • news(symbol, limit)         – Haber başlıkları + sentiment skoru
  • sentiment(symbol, days)     – Günlük sentiment serisi (-1 … +1)
  • earnings_calendar(symbols)  – Yaklaşan kazanç tarihleri

Konfigürasyon (env değişkenleri):
  EODHD_API_KEY          – API anahtarı (zorunlu)
  EODHD_CACHE_TTL_RT     – Real-time cache süresi saniye (varsayılan: 300)
  EODHD_CACHE_TTL_EOD    – EOD cache süresi saniye (varsayılan: 3600)
  EODHD_CACHE_TTL_FUND   – Fundamental cache süresi saniye (varsayılan: 86400)
  EODHD_CACHE_TTL_NEWS   – Haber cache süresi saniye (varsayılan: 1800)
  EODHD_TIMEOUT          – HTTP timeout saniye (varsayılan: 15)

Kullanım:
    from data.eodhd_client import get_client

    client = get_client()
    quote   = client.real_time(["AAPL", "MSFT"])
    hist    = client.eod_history("NVDA", days=365)
    fund    = client.fundamentals("TSLA")
    news    = client.news("AMZN", limit=5)
    earn    = client.earnings_calendar(["AAPL", "GOOG"])
"""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

# ── Sabitler ──────────────────────────────────────────────────────────────────
BASE_URL = "https://eodhd.com/api"
_DEFAULT_EXCHANGE = "US"

# ── Yardımcı: sembol formatı ──────────────────────────────────────────────────


def _fmt(symbol: str, exchange: str = _DEFAULT_EXCHANGE) -> str:
    """AAPL → AAPL.US  (zaten nokta içeriyorsa dokunma)."""
    return symbol if "." in symbol else f"{symbol}.{exchange}"


# ── Cache girdisi ──────────────────────────────────────────────────────────────


class _CacheEntry:
    __slots__ = ("data", "expires_at")

    def __init__(self, data: Any, ttl: int) -> None:
        self.data = data
        self.expires_at = time.monotonic() + ttl

    def is_valid(self) -> bool:
        return time.monotonic() < self.expires_at


# ── Ana istemci ────────────────────────────────────────────────────────────────


class EODHDClient:
    """EODHD REST API istemcisi — dahili in-memory cache ile."""

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.getenv("EODHD_API_KEY", "")
        if not self._api_key:
            logger.warning("eodhd: EODHD_API_KEY ayarlanmamış — tüm çağrılar başarısız olacak.")

        # TTL'ler (env override destekli)
        self._ttl_rt = int(os.getenv("EODHD_CACHE_TTL_RT", "300"))  # 5 dk
        self._ttl_eod = int(os.getenv("EODHD_CACHE_TTL_EOD", "3600"))  # 1 saat
        self._ttl_fund = int(os.getenv("EODHD_CACHE_TTL_FUND", "86400"))  # 1 gün
        self._ttl_news = int(os.getenv("EODHD_CACHE_TTL_NEWS", "1800"))  # 30 dk

        self._timeout = int(os.getenv("EODHD_TIMEOUT", "15"))
        self._cache: dict[str, _CacheEntry] = {}

    # ── HTTP çekirdek ──────────────────────────────────────────────────────────

    def _get(
        self,
        path: str,
        params: dict | None = None,
        cache_key: str | None = None,
        ttl: int = 300,
    ) -> Any:
        """GET isteği yap, cache'ten dön veya cache'e kaydet."""
        if cache_key:
            entry = self._cache.get(cache_key)
            if entry and entry.is_valid():
                return entry.data

        try:
            import requests  # geç import — temel bağımlılık
        except ImportError:  # pragma: no cover
            logger.error("eodhd: 'requests' kütüphanesi bulunamadı.")
            return None

        all_params = {"api_token": self._api_key, "fmt": "json"}
        if params:
            all_params.update(params)

        url = f"{BASE_URL}/{path.lstrip('/')}"
        try:
            resp = requests.get(url, params=all_params, timeout=self._timeout)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.HTTPError as exc:
            logger.warning("eodhd: HTTP hata %s → %s", exc.response.status_code, url)
            return None
        except requests.exceptions.Timeout:
            logger.warning("eodhd: Zaman aşımı → %s", url)
            return None
        except Exception as exc:  # noqa: BLE001
            logger.warning("eodhd: İstek başarısız → %s: %s", url, exc)
            return None

        if cache_key:
            self._cache[cache_key] = _CacheEntry(data, ttl)

        return data

    # ── Anlık fiyat ───────────────────────────────────────────────────────────

    def real_time(
        self,
        symbols: list[str],
        exchange: str = _DEFAULT_EXCHANGE,
    ) -> dict[str, dict]:
        """Anlık fiyat snapshot'ı (15-20 dk gecikme).

        EODHD'nin multi-ticker syntax'ı: /api/real-time/{sym0}?s=sym1,sym2
        → Maksimum 15-20 sembol per çağrı önerilir.

        Returns:
            {ticker: {open, high, low, close, volume, change, change_p, ...}}
        """
        if not symbols:
            return {}

        formatted = [_fmt(s, exchange) for s in symbols]
        primary = formatted[0]
        extra = formatted[1:] if len(formatted) > 1 else []

        params: dict[str, Any] = {}
        if extra:
            params["s"] = ",".join(extra)

        cache_key = f"rt:{'|'.join(sorted(formatted))}"
        raw = self._get(
            f"real-time/{primary}",
            params=params,
            cache_key=cache_key,
            ttl=self._ttl_rt,
        )

        if raw is None:
            return {}

        # Tek sembol dict dönebilir; çoklu sembol list dönebilir
        records: list[dict] = raw if isinstance(raw, list) else [raw]
        result: dict[str, dict] = {}
        for rec in records:
            code = rec.get("code", "").split(".")[0]  # "AAPL.US" → "AAPL"
            result[code] = rec
        return result

    # ── EOD tarihsel veri ─────────────────────────────────────────────────────

    def eod_history(
        self,
        symbol: str,
        days: int = 365,
        exchange: str = _DEFAULT_EXCHANGE,
        period: str = "d",
    ) -> list[dict]:
        """Günlük OHLCV geçmişi.

        Args:
            symbol:   "AAPL" veya "AAPL.US"
            days:     kaç gün geriye gidilecek
            period:   'd' günlük, 'w' haftalık, 'm' aylık

        Returns:
            [{"date": "YYYY-MM-DD", "open": ..., "high": ..., "low": ...,
              "close": ..., "adjusted_close": ..., "volume": ...}, ...]
        """
        sym = _fmt(symbol, exchange)
        from_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        to_date = datetime.utcnow().strftime("%Y-%m-%d")

        cache_key = f"eod:{sym}:{from_date}:{period}"
        data = self._get(
            f"eod/{sym}",
            params={"from": from_date, "to": to_date, "period": period},
            cache_key=cache_key,
            ttl=self._ttl_eod,
        )
        return data or []

    # ── Fundamental veriler ───────────────────────────────────────────────────

    def fundamentals(
        self,
        symbol: str,
        exchange: str = _DEFAULT_EXCHANGE,
        sections: str = "Highlights,Valuation,Technicals,AnalystRatings",
    ) -> dict:
        """Fundamental veriler — PE, EPS, gelir trendi, analist hedefleri.

        Args:
            sections: virgülle ayrılmış EODHD bölüm adları
                      → "Highlights,Valuation,Technicals,AnalystRatings"
                      → Tam veri için sections=None

        Returns:
            {
              "Highlights": {PERatio, EarningsShare, RevenueTTM, ...},
              "Valuation":  {TrailingPE, ForwardPE, PriceSalesTTM, ...},
              "Technicals": {Beta, 52WeekHigh, 50DayMA, ...},
              "AnalystRatings": {Rating, TargetPrice, StrongBuy, Buy, Hold, ...}
            }
        """
        sym = _fmt(symbol, exchange)
        params: dict[str, Any] = {}
        if sections:
            params["filter"] = sections

        cache_key = f"fund:{sym}:{sections}"
        data = self._get(
            f"v1.1/fundamentals/{sym}",
            params=params,
            cache_key=cache_key,
            ttl=self._ttl_fund,
        )
        return data or {}

    # ── Haberler + sentiment ───────────────────────────────────────────────────

    def news(
        self,
        symbol: str,
        limit: int = 10,
        days: int = 7,
        exchange: str = _DEFAULT_EXCHANGE,
    ) -> list[dict]:
        """Son haberler + polarity sentiment skoru.

        Returns:
            [{"date": ..., "title": ..., "content": ...,
              "sentiment": {"polarity": 0-1, "neg": ..., "neu": ..., "pos": ...}
              }, ...]
        """
        sym = _fmt(symbol, exchange)
        from_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")

        cache_key = f"news:{sym}:{from_date}:{limit}"
        data = self._get(
            "news",
            params={"s": sym, "limit": limit, "from": from_date},
            cache_key=cache_key,
            ttl=self._ttl_news,
        )
        return data or []

    def sentiment(
        self,
        symbol: str,
        days: int = 14,
        exchange: str = _DEFAULT_EXCHANGE,
    ) -> list[dict]:
        """Günlük normalize sentiment serisi (-1 çok negatif … +1 çok pozitif).

        Returns:
            [{"date": "YYYY-MM-DD", "count": int, "normalized": float}, ...]
        """
        sym = _fmt(symbol, exchange)
        from_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        to_date = datetime.utcnow().strftime("%Y-%m-%d")

        cache_key = f"sent:{sym}:{from_date}"
        raw = self._get(
            "sentiments",
            params={"s": sym, "from": from_date, "to": to_date},
            cache_key=cache_key,
            ttl=self._ttl_news,
        )
        if not raw:
            return []
        # API {ticker: [entries]} döndürür
        if isinstance(raw, dict):
            for v in raw.values():
                if isinstance(v, list):
                    return v
        return []

    # ── Kazanç takvimi ─────────────────────────────────────────────────────────

    def earnings_calendar(
        self,
        symbols: list[str] | None = None,
        days_ahead: int = 14,
        exchange: str = _DEFAULT_EXCHANGE,
    ) -> list[dict]:
        """Yaklaşan / geçmiş kazanç (EPS) tarihleri.

        Args:
            symbols:    sembol listesi — None ise tarihe göre sorgular
            days_ahead: symbols=None iken kaç gün ilerisi

        Returns:
            [{"code": "AAPL.US", "report_date": "YYYY-MM-DD",
              "actual": float, "estimate": float, "difference": float,
              "percent": float, "before_after_market": str}, ...]
        """
        params: dict[str, Any] = {}
        if symbols:
            formatted = [_fmt(s, exchange) for s in symbols]
            params["symbols"] = ",".join(formatted)
            cache_key = f"earn:{'|'.join(sorted(formatted))}"
        else:
            today = datetime.utcnow().strftime("%Y-%m-%d")
            to_date = (datetime.utcnow() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
            params["from"] = today
            params["to"] = to_date
            cache_key = f"earn:window:{today}:{days_ahead}"

        data = self._get(
            "calendar/earnings",
            params=params,
            cache_key=cache_key,
            ttl=3600,  # 1 saat
        )
        if not data:
            return []
        return data.get("earnings", [])

    # ── Toplu fiyat (US exchange bulk) ────────────────────────────────────────

    def bulk_eod(self, exchange: str = "US", date: str | None = None) -> list[dict]:
        """Tüm exchange için tek çağrıda EOD fiyatları (1 API call).

        date: "YYYY-MM-DD" — None ise bugün. Sadece US exchange için önerilir.

        Returns:
            [{"code": "AAPL", "close": ..., "volume": ..., ...}, ...]
        """
        params: dict[str, Any] = {}
        if date:
            params["date"] = date
        cache_key = f"bulk:{exchange}:{date or 'today'}"
        data = self._get(
            f"eod-bulk-last-day/{exchange}",
            params=params,
            cache_key=cache_key,
            ttl=self._ttl_eod,
        )
        return data or []

    # ── Temel sinyal özeti (scanner için) ─────────────────────────────────────

    def fundamental_signals(self, symbol: str, exchange: str = _DEFAULT_EXCHANGE) -> dict:
        """Scanner için özet fundamental sinyal paketi.

        Returns:
            {
              "pe_ratio":           float | None,   # trailing PE
              "forward_pe":         float | None,
              "eps_growth_yoy":     float | None,   # QuarterlyEarningsGrowthYOY
              "revenue_growth_yoy": float | None,   # QuarterlyRevenueGrowthYOY
              "profit_margin":      float | None,
              "return_on_equity":   float | None,
              "analyst_target":     float | None,   # analist fiyat hedefi
              "analyst_rating":     float | None,   # 1(güçlü al) … 5(güçlü sat)
              "beta":               float | None,
              "week52_high":        float | None,
              "week52_low":         float | None,
              "data_quality":       str,             # "high"|"medium"|"low"
            }
        """
        fund = self.fundamentals(symbol, exchange)
        if not fund:
            return {"data_quality": "low"}

        h = fund.get("Highlights", {}) or {}
        v = fund.get("Valuation", {}) or {}
        t = fund.get("Technicals", {}) or {}
        a = fund.get("AnalystRatings", {}) or {}

        def _f(d: dict, key: str) -> float | None:
            val = d.get(key)
            try:
                return float(val) if val not in (None, "None", "N/A", "") else None
            except (TypeError, ValueError):
                return None

        pe = _f(v, "TrailingPE")
        forward = _f(v, "ForwardPE")
        eps_g = _f(h, "QuarterlyEarningsGrowthYOY")
        rev_g = _f(h, "QuarterlyRevenueGrowthYOY")
        margin = _f(h, "ProfitMargin")
        roe = _f(h, "ReturnOnEquityTTM")
        target = _f(a, "TargetPrice")
        rating = _f(a, "Rating")
        beta = _f(t, "Beta")
        hi52 = _f(t, "52WeekHigh")
        lo52 = _f(t, "52WeekLow")

        # Veri kalitesi: yüksek = 3+ alan dolu
        filled = sum(x is not None for x in [pe, forward, eps_g, rev_g, margin, roe])
        quality = "high" if filled >= 4 else "medium" if filled >= 2 else "low"

        return {
            "pe_ratio": pe,
            "forward_pe": forward,
            "eps_growth_yoy": eps_g,
            "revenue_growth_yoy": rev_g,
            "profit_margin": margin,
            "return_on_equity": roe,
            "analyst_target": target,
            "analyst_rating": rating,
            "beta": beta,
            "week52_high": hi52,
            "week52_low": lo52,
            "data_quality": quality,
        }

    # ── Cache yönetimi ─────────────────────────────────────────────────────────

    def clear_cache(self, prefix: str | None = None) -> int:
        """Cache'i temizle. prefix verilmezse tümünü temizle."""
        if prefix is None:
            n = len(self._cache)
            self._cache.clear()
            return n
        keys = [k for k in self._cache if k.startswith(prefix)]
        for k in keys:
            del self._cache[k]
        return len(keys)

    def cache_stats(self) -> dict:
        now = time.monotonic()
        valid = sum(1 for e in self._cache.values() if e.expires_at > now)
        return {"total": len(self._cache), "valid": valid, "expired": len(self._cache) - valid}


# ── Modül seviyesi singleton ───────────────────────────────────────────────────

_client: EODHDClient | None = None


def get_client() -> EODHDClient:
    """Thread-safe olmayan (GIL korumalı) singleton erişimi."""
    global _client
    if _client is None:
        _client = EODHDClient()
    return _client


# ── Kısayol fonksiyonlar (direct import için) ─────────────────────────────────


def real_time(symbols: list[str], **kw) -> dict[str, dict]:
    return get_client().real_time(symbols, **kw)


def eod_history(symbol: str, days: int = 365, **kw) -> list[dict]:
    return get_client().eod_history(symbol, days, **kw)


def fundamentals(symbol: str, **kw) -> dict:
    return get_client().fundamentals(symbol, **kw)


def fundamental_signals(symbol: str, **kw) -> dict:
    return get_client().fundamental_signals(symbol, **kw)


def news(symbol: str, limit: int = 10, **kw) -> list[dict]:
    return get_client().news(symbol, limit, **kw)


def sentiment(symbol: str, days: int = 14, **kw) -> list[dict]:
    return get_client().sentiment(symbol, days, **kw)


def earnings_calendar(symbols: list[str] | None = None, **kw) -> list[dict]:
    return get_client().earnings_calendar(symbols, **kw)
