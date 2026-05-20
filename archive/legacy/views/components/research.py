"""
FinPilot Research
=================
Gemini/Groq API ile araştırma ve haber analizi.

Sprint 10: Renamed get_gemini_research → get_ai_research,
print() → logger, cache-skip for error/offline reports.

Sprint 11-12: Parallel DDG fetch via ThreadPoolExecutor, Groq streaming,
disk-based L2 cache, modular refactor (fetch/dedup/llm/fallback helpers).

Sprint 19: Integrated LLM Router (Groq → Claude → Gemini failover).
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import streamlit as st
import yfinance as yf

logger = logging.getLogger(__name__)

# Optional imports
try:
    import google.generativeai as genai  # noqa: F401 — kept for future use
    from duckduckgo_search import DDGS
    from groq import Groq
except ImportError:
    genai = None
    DDGS = None
    Groq = None

try:
    from tavily import TavilyClient  # type: ignore[import-untyped]

    _TAVILY_KEY = os.environ.get("TAVILY_API_KEY", "")
    _HAS_TAVILY = bool(_TAVILY_KEY)
except ImportError:
    TavilyClient = None  # type: ignore[assignment,misc]
    _TAVILY_KEY = ""
    _HAS_TAVILY = False

# LLM Router (Sprint 19)
try:
    from llm import get_router as _get_llm_router
    from llm.base import LLMError as _LLMError

    _LLM_ROUTER_AVAILABLE = True
except ImportError:
    _LLM_ROUTER_AVAILABLE = False
    _get_llm_router = None  # type: ignore[assignment]
    _LLMError = Exception  # type: ignore[misc,assignment]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
RESEARCH_CACHE_TTL = 300  # 5 min in-memory (L1)
_DISK_CACHE_DIR = Path(os.getcwd()) / "data" / "reports_cache"
_DISK_CACHE_MAX_AGE_S = 3600  # 1 hour (L2)

_COMPANY_NAMES: dict[str, str] = {
    "VRTX": "Vertex Pharmaceuticals",
    "AMGN": "Amgen",
    "GILD": "Gilead Sciences",
    "REGN": "Regeneron",
    "MRNA": "Moderna",
    "BIIB": "Biogen",
    "ILMN": "Illumina",
}

_POSITIVE_KW = [
    "surge",
    "jump",
    "high",
    "profit",
    "growth",
    "yükseldi",
    "rekor",
    "kar",
    "büyüme",
    "buy",
    "al",
    "olumlu",
]
_NEGATIVE_KW = [
    "drop",
    "fall",
    "loss",
    "crash",
    "düşüş",
    "zarar",
    "kriz",
    "sat",
    "sell",
    "olumsuz",
    "lawsuit",
    "dava",
]

_ERROR_MARKERS = ("⚠️",)


# ---------------------------------------------------------------------------
# P1: yfinance fallback news
# ---------------------------------------------------------------------------


def get_yfinance_news(symbol: str, max_results: int = 5) -> list:
    """yfinance'dan haber çeker (fallback için)."""
    try:
        ticker = yf.Ticker(symbol)
        news = ticker.news or []
        results = []
        for item in news[:max_results]:
            results.append(
                {
                    "title": item.get("title", ""),
                    "body": item.get("summary", item.get("title", "")),
                    "url": item.get("link", ""),
                    "date": item.get("providerPublishTime", ""),
                    "source": item.get("publisher", "Yahoo Finance"),
                }
            )
        return results
    except Exception as e:
        logger.warning("yfinance news error for %s: %s", symbol, e)
        return []


# ---------------------------------------------------------------------------
# P2: DDG news fetch — parallel  (Sprint 11)
# ---------------------------------------------------------------------------


def _ddg_safe_search(
    query: str,
    region: str = "wt-wt",
    timelimit: str | None = "w",
    max_results: int = 3,
) -> list:
    """Thread-safe, error-guarded DDG news search with timelimit fallback."""
    if not DDGS:
        return []
    try:
        with DDGS() as ddgs:
            res = list(
                ddgs.news(
                    query,
                    region=region,
                    safesearch="off",
                    timelimit=timelimit,
                    max_results=max_results,
                )
            )
            if res:
                return res
            # Fallback: remove time constraint
            if timelimit:
                return list(
                    ddgs.news(
                        query,
                        region=region,
                        safesearch="off",
                        timelimit=None,
                        max_results=max_results,
                    )
                )
    except Exception as e:
        logger.warning("DDG search error (%s): %s", query, e)
    return []


def _tavily_news(symbol: str, max_results: int = 8) -> list[dict]:
    """Tavily AI-ranked news search (primary source for research)."""
    if not _HAS_TAVILY or TavilyClient is None:
        return []
    try:
        client = TavilyClient(api_key=_TAVILY_KEY)
        resp = client.search(
            query=f"{symbol} stock market earnings financial analysis",
            search_depth="advanced",
            topic="news",
            max_results=max_results,
            include_answer=False,
        )
        results = []
        for r in resp.get("results", []):
            results.append(
                {
                    "title": r.get("title", ""),
                    "body": r.get("content", ""),
                    "url": r.get("url", ""),
                    "date": r.get("published_date", ""),
                    "source": r.get("url", "").split("/")[2] if r.get("url") else "tavily",
                }
            )
        logger.info("Tavily research: %d results for %s", len(results), symbol)
        return results
    except Exception as e:
        logger.warning("Tavily research error for %s: %s", symbol, e)
        return []


def _fetch_news(symbol: str) -> list[dict]:
    """Tavily (primary) → DDG (fallback) → yfinance (last resort).

    Sprint 11: Uses ThreadPoolExecutor for ~3-4x wall-clock speedup.
    Tavily integration: AI-ranked results as primary source.
    """
    # Primary: Tavily AI-ranked search
    results = _tavily_news(symbol, max_results=8)

    # Fallback: DDG parallel searches if Tavily returned too few
    if len(results) < 3:
        queries = [
            (f"{symbol} stock news finance", "wt-wt", "w", 5),
            (f"{symbol} sec filings lawsuit regulation", "wt-wt", "m", 3),
            (f"{symbol} aktie finanzen", "de-de", "w", 2),
            (f"{symbol} hisse haber borsa", "tr-tr", "w", 3),
        ]
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = {pool.submit(_ddg_safe_search, q, r, t, m): q for q, r, t, m in queries}
            for fut in as_completed(futures):
                try:
                    results.extend(fut.result())
                except Exception as e:
                    logger.warning("DDG future error: %s", e)

    # Company-name fallback if too few results
    if len(results) < 3:
        company_name = _COMPANY_NAMES.get(symbol)
        if company_name:
            results.extend(_ddg_safe_search(f"{company_name} news stock", "wt-wt", "m", 5))

    # yfinance last-resort
    if not results:
        results = get_yfinance_news(symbol, max_results=5)

    return results


# ---------------------------------------------------------------------------
# P3: Deduplication
# ---------------------------------------------------------------------------


def _deduplicate_news(items: list[dict]) -> list[dict]:
    """Remove duplicates by URL, keep first 12."""
    seen: set[str] = set()
    unique = []
    for r in items:
        url = r.get("url")
        if url and url not in seen:
            unique.append(r)
            seen.add(url)
    return unique[:12]


# ---------------------------------------------------------------------------
# P4: LLM report generation (Groq, with streaming support)
# ---------------------------------------------------------------------------

_PROMPTS = {
    "tr": """\
Sen uzman bir borsa ve hukuk analistisin. Asagidaki **guncel** haberleri \
(Ingilizce, Almanca, Turkce) kullanarak {symbol} hissesi icin kapsamli bir \
yatirimci raporu hazirla.

Ozellikle **yasal gelismeler, regulasyonlar, davalar ve resmi bildirimlere \
(SEC/KAP)** dikkat et. Haberlerin tarihlerini goz onunde bulundur ve eski \
haberleri ele.

Haberler:
{news_context}

Istenen Format:
1. **Piyasa Algisi:** (Olumlu/Olumsuz/Notr - Nedenleriyle)
2. **Yasal ve Regulatif Gelismeler:** (Varsa davalar, cezalar, onaylar, basvurular)
3. **One Cikan Finansal Gelismeler:** (Maddeler halinde)
4. **Riskler ve Firsatlar:**
5. **Sonuc Yorumu:** (Yatirimci ne yapmali?)
""",
    "en": """\
You are an expert stock market and legal analyst. Create a comprehensive \
investor report for {symbol} using the **recent** news below.

Pay special attention to **legal developments, regulations, lawsuits, and \
official filings (SEC/KAP)**. Consider the dates of the news and filter out \
outdated information.

News:
{news_context}

Required Format:
1. **Market Sentiment:** (Bullish/Bearish/Neutral - With reasons)
2. **Legal & Regulatory Developments:** (Lawsuits, fines, approvals, filings if any)
3. **Key Financial Developments:** (Bullet points)
4. **Risks & Opportunities:**
5. **Conclusion:** (Actionable advice)
""",
    "de": """\
Sie sind ein erfahrener Boersen- und Rechtsanalyst. Erstellen Sie einen \
umfassenden Investorenbericht fuer {symbol} unter Verwendung der folgenden \
**aktuellen** Nachrichten.

Achten Sie besonders auf **rechtliche Entwicklungen, Vorschriften, Klagen \
und offizielle Meldungen**. Beruecksichtigen Sie die Daten der Nachrichten.

Nachrichten:
{news_context}

Gewuenschtes Format:
1. **Marktstimmung:** (Positiv/Negativ/Neutral)
2. **Rechtliche & Regulatorische Entwicklungen:**
3. **Wichtige Finanzentwicklungen:**
4. **Risiken & Chancen:**
5. **Fazit:**
""",
}


def _build_news_context(items: list[dict]) -> str:
    return "\n\n".join(
        f"Tarih: {r.get('date', 'Belirsiz')}\nBaslik: {r['title']}"
        f"\nKaynak: {r['source']}\nOzet: {r['body']}"
        for r in items
    )


def _generate_llm_report(
    symbol: str,
    news_items: list[dict],
    language: str,
    *,
    stream: bool = False,
) -> str:
    """Generate LLM report via Router (Groq → Claude → Gemini failover).

    Sprint 12: Streaming support.
    Sprint 19: LLM Router with automatic failover.
    """
    news_context = _build_news_context(news_items)
    prompt_template = _PROMPTS.get(language, _PROMPTS["tr"])
    prompt = prompt_template.format(symbol=symbol, news_context=news_context)
    system = "You are a senior financial analyst. Answer in Markdown."

    # Sprint 19: Try LLM Router first (handles Groq → Claude → Gemini failover)
    if _LLM_ROUTER_AVAILABLE:
        try:
            router = _get_llm_router()
            if router.available_providers:
                if stream:
                    chunks: list[str] = []
                    for token in router.stream(prompt, system=system):
                        chunks.append(token)
                    return "".join(chunks)
                else:
                    response = router.generate(prompt, system=system)
                    return response.content
        except _LLMError as e:
            logger.warning("LLM Router failed, falling back: %s", e)
        except Exception as e:
            logger.warning("LLM Router unexpected error: %s", e)

    # Legacy fallback: direct Groq call (backward compat)
    if not Groq:
        return _generate_offline_report(
            symbol, news_items, language, reason="LLM kutuphaneleri yuklu degil"
        )

    groq_key: str | None = None
    try:
        groq_key = st.secrets.get("GROQ_API_KEY", "")  # pragma: allowlist secret
    except Exception:
        logger.debug("st.secrets unavailable", exc_info=True)

    if not groq_key:
        return _generate_offline_report(
            symbol,
            news_items,
            language,
            reason="API anahtari tanimlanmamis (GROQ/ANTHROPIC/GOOGLE)",
        )

    try:
        client = Groq(api_key=groq_key)
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]

        if stream:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.3,
                max_tokens=2048,
                top_p=1,
                stream=True,
            )
            chunks_legacy: list[str] = []
            for chunk in completion:
                delta = chunk.choices[0].delta.content or ""
                chunks_legacy.append(delta)
            return "".join(chunks_legacy)

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.3,
            max_tokens=2048,
            top_p=1,
            stream=False,
            stop=None,
        )
        return completion.choices[0].message.content or ""
    except Exception as e:
        return _generate_offline_report(
            symbol,
            news_items,
            language,
            reason=f"LLM API Hatasi: {e}",
        )


# ---------------------------------------------------------------------------
# P5: Offline / fallback report
# ---------------------------------------------------------------------------


def _generate_offline_report(
    symbol: str,
    news_items: list,
    language: str,
    reason: str | None = None,
) -> str:
    """Basit keyword-sentiment raporlayici -- LLM yokken calisir."""
    headers = {
        "tr": ["Piyasa Algisi", "Son Haber Ozeti", "Riskler & Firsatlar"],
        "en": ["Market Sentiment", "Recent News Summary", "Risks & Opportunities"],
        "de": [
            "Marktstimmung",
            "Zusammenfassung aktueller Nachrichten",
            "Risiken & Chancen",
        ],
    }
    h = headers.get(language, headers["tr"])

    combined_text = " ".join(
        n.get("title", "").lower() + " " + n.get("body", "").lower() for n in news_items
    )
    pos_count = sum(1 for k in _POSITIVE_KW if k in combined_text)
    neg_count = sum(1 for k in _NEGATIVE_KW if k in combined_text)

    if pos_count > neg_count:
        sentiment = "🟢 Pozitif / Bullish" if language == "tr" else "🟢 Positive / Bullish"
    elif neg_count > pos_count:
        sentiment = "🔴 Negatif / Bearish" if language == "tr" else "🔴 Negative / Bearish"
    else:
        sentiment = "⚪ Notr / Neutral" if language == "tr" else "⚪ Neutral"

    reason_text = f" ({reason})" if reason else ""

    report = f"""\
### ⚠️ AI Limit Modu (Offline & Fallback)
*Yapay Zeka baglantisi saglanamdigi icin (Groq/Gemini), bu rapor haberlerin \
otomatik ozetlenmesiyle olusturulmustur.*
*{reason_text}*

#### 1. {h[0]}
**{sentiment}**
(Pozitif Anahtar Kelimeler: {pos_count}, Negatif: {neg_count})

#### 2. {h[1]}
"""

    for item in news_items[:8]:
        report += f"- **{item.get('date', '?')}**: {item['title']} ({item.get('source', '?')})\n"

    report += f"""
#### 3. {h[2]}
- **Firsat:** Haber akisina gore kisa vadeli volatilite degerlendirilebilir.
- **Risk:** Otomatik analiz su an devre disi oldugu icin manuel inceleme onerilir.
"""
    return report


# ---------------------------------------------------------------------------
# P6: Disk L2 cache  (Sprint 12)
# ---------------------------------------------------------------------------


def _cache_key(symbol: str, language: str) -> str:
    return hashlib.sha256(f"{symbol}:{language}".encode()).hexdigest()[:16]


def _read_disk_cache(symbol: str, language: str) -> str | None:
    """Return cached report if fresh enough, else None."""
    try:
        path = _DISK_CACHE_DIR / f"{_cache_key(symbol, language)}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text())
        age = time.time() - data.get("ts", 0)
        if age > _DISK_CACHE_MAX_AGE_S:
            return None
        report = data.get("report", "")
        # Never serve cached error reports
        if any(m in report for m in _ERROR_MARKERS):
            return None
        return report
    except Exception:
        return None


def _write_disk_cache(symbol: str, language: str, report: str) -> None:
    """Persist report to disk (L2)."""
    if any(m in report for m in _ERROR_MARKERS):
        return  # don't cache errors
    try:
        _DISK_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path = _DISK_CACHE_DIR / f"{_cache_key(symbol, language)}.json"
        path.write_text(
            json.dumps(
                {
                    "symbol": symbol,
                    "language": language,
                    "ts": time.time(),
                    "report": report,
                },
                ensure_ascii=False,
            )
        )
    except Exception as e:
        logger.warning("Disk cache write error: %s", e)


# ---------------------------------------------------------------------------
# P7: Main entry-point  (Sprint 10-12 unified)
# ---------------------------------------------------------------------------


def get_ai_research(symbol: str, language: str = "tr") -> str:
    """Fetch DDG news in parallel -> deduplicate -> LLM report.

    Pipeline:
    1. Check disk L2 cache
    2. Parallel DDG fetch (4 queries) + yfinance fallback
    3. Deduplicate by URL, keep top 12
    4. Generate LLM report via Groq (or offline fallback)
    5. Write to disk L2 cache
    """
    # L2 disk cache hit?
    cached = _read_disk_cache(symbol, language)
    if cached:
        logger.debug("L2 cache hit for %s/%s", symbol, language)
        return cached

    # Validate prerequisites
    if not DDGS:
        return "⚠️ Gerekli kutuphaneler (duckduckgo-search) yuklu degil."

    # Fetch -> Dedup -> LLM
    raw_news = _fetch_news(symbol)
    if not raw_news:
        return (
            f"⚠️ {symbol} icin kaynaklarda erisilebilir haber bulunamadi. "
            "(Baglanti sorunu veya veri eksikligi olabilir)"
        )

    unique_news = _deduplicate_news(raw_news)

    try:
        report = _generate_llm_report(symbol, unique_news, language)
    except Exception:
        logger.exception("LLM report generation failed for %s", symbol)
        report = _generate_offline_report(symbol, unique_news, language, reason="LLM hatasi")

    # Persist to L2 if successful
    _write_disk_cache(symbol, language, report)

    return report


# ---------------------------------------------------------------------------
# Cache wrappers  (Sprint 10)
# ---------------------------------------------------------------------------


@st.cache_data(ttl=RESEARCH_CACHE_TTL, show_spinner="🔍 Arastirma yapiliyor...")
def _cached_ai_research(symbol: str, language: str = "tr") -> str:
    """Internal L1 in-memory cache -- delegates to get_ai_research."""
    return get_ai_research(symbol, language)


def cached_ai_research(symbol: str, language: str = "tr") -> str:
    """Public entry-point with L1+L2 caching.

    Error/offline reports (containing ⚠️) are evicted from L1 so the next
    call retries rather than serving stale failure text for 300 seconds.
    """
    result = _cached_ai_research(symbol, language)
    if any(marker in result for marker in _ERROR_MARKERS):
        _cached_ai_research.clear()
    return result


# Backward-compat alias (Sprint 10 -- will be removed Sprint 13)
get_gemini_research = get_ai_research
