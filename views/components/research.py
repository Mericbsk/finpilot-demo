"""
FinPilot Research Engine
========================
Multi-provider LLM research with DuckDuckGo news aggregation.

Provider chain: Groq → Gemini → Offline fallback
News sources:   DuckDuckGo (parallel) → yfinance (fallback)

Sprint 8: Complete rewrite — google-genai SDK, parallel DDG, Gemini fallback.
"""

from __future__ import annotations

import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from textwrap import dedent

import streamlit as st
import yfinance as yf

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional imports with granular availability flags
# ---------------------------------------------------------------------------
try:
    from duckduckgo_search import DDGS

    _DDG_AVAILABLE = True
except ImportError:
    _DDG_AVAILABLE = False

try:
    from groq import Groq

    _GROQ_AVAILABLE = True
except ImportError:
    _GROQ_AVAILABLE = False

try:
    from google import genai as google_genai

    _GEMINI_AVAILABLE = True
except ImportError:
    _GEMINI_AVAILABLE = False


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
RESEARCH_CACHE_TTL = 300  # 5 minutes
REPORT_CACHE_DIR = os.path.join(os.getcwd(), "data", "reports_cache")
REPORT_CACHE_MAX_AGE = 3600 * 6  # 6 hours

_SYSTEM_PROMPT = "You are a senior financial analyst. Answer in Markdown."

_PROMPTS = {
    "tr": (
        "Sen uzman bir borsa ve hukuk analistisin. Aşağıdaki **güncel** haberleri "
        "(İngilizce, Almanca, Türkçe) kullanarak {symbol} hissesi için kapsamlı bir "
        "yatırımcı raporu hazırla.\n\n"
        "Özellikle **yasal gelişmeler, regülasyonlar, davalar ve resmi bildirimlere "
        "(SEC/KAP)** dikkat et. Haberlerin tarihlerini göz önünde bulundur.\n\n"
        "Haberler:\n{news_context}\n\n"
        "Format:\n"
        "1. **Piyasa Algısı:** (Olumlu/Olumsuz/Nötr - Nedenleriyle)\n"
        "2. **Yasal ve Regülatif Gelişmeler:**\n"
        "3. **Öne Çıkan Finansal Gelişmeler:** (Maddeler halinde)\n"
        "4. **Riskler ve Fırsatlar:**\n"
        "5. **Sonuç Yorumu:** (Yatırımcı ne yapmalı?)"
    ),
    "en": (
        "You are an expert stock market and legal analyst. Create a comprehensive "
        "investor report for {symbol} using the **recent** news below.\n\n"
        "Pay special attention to **legal developments, regulations, lawsuits, and "
        "official filings (SEC/KAP)**.\n\n"
        "News:\n{news_context}\n\n"
        "Format:\n"
        "1. **Market Sentiment:** (Bullish/Bearish/Neutral)\n"
        "2. **Legal & Regulatory Developments:**\n"
        "3. **Key Financial Developments:** (Bullet points)\n"
        "4. **Risks & Opportunities:**\n"
        "5. **Conclusion:** (Actionable advice)"
    ),
    "de": (
        "Sie sind ein erfahrener Börsen- und Rechtsanalyst. Erstellen Sie einen "
        "umfassenden Investorenbericht für {symbol}.\n\n"
        "Achten Sie besonders auf **rechtliche Entwicklungen, Vorschriften, Klagen "
        "und offizielle Meldungen**.\n\n"
        "Nachrichten:\n{news_context}\n\n"
        "Format:\n"
        "1. **Marktstimmung:** (Positiv/Negativ/Neutral)\n"
        "2. **Rechtliche & Regulatorische Entwicklungen:**\n"
        "3. **Wichtige Finanzentwicklungen:**\n"
        "4. **Risiken & Chancen:**\n"
        "5. **Fazit:**"
    ),
}


# ---------------------------------------------------------------------------
# P9: Disk-based report cache
# ---------------------------------------------------------------------------


def _disk_cache_key(symbol: str, language: str) -> str:
    """Disk cache dosya adı üretir."""
    today = datetime.now(UTC).strftime("%Y%m%d")
    return os.path.join(REPORT_CACHE_DIR, f"{symbol}_{language}_{today}.md")


def _load_from_disk_cache(symbol: str, language: str) -> str | None:
    """Disk cache'den rapor yükler (varsa ve taze ise)."""
    path = _disk_cache_key(symbol, language)
    try:
        if os.path.exists(path):
            age = datetime.now(UTC).timestamp() - os.path.getmtime(path)
            if age < REPORT_CACHE_MAX_AGE:
                with open(path, encoding="utf-8") as f:
                    content = f.read()
                if content.strip():
                    logger.info("Disk cache hit: %s", path)
                    return content
    except Exception as e:
        logger.warning("Disk cache read error: %s", e)
    return None


def _save_to_disk_cache(symbol: str, language: str, report: str) -> None:
    """Raporu disk cache'e kaydeder."""
    try:
        os.makedirs(REPORT_CACHE_DIR, exist_ok=True)
        path = _disk_cache_key(symbol, language)
        with open(path, "w", encoding="utf-8") as f:
            f.write(report)
        logger.info("Disk cache saved: %s", path)
    except Exception as e:
        logger.warning("Disk cache write error: %s", e)


# ---------------------------------------------------------------------------
# News gathering helpers
# ---------------------------------------------------------------------------


def get_yfinance_news(symbol: str, max_results: int = 5) -> list[dict]:
    """yfinance'dan haber çeker (fallback)."""
    try:
        ticker = yf.Ticker(symbol)
        news = ticker.news or []
        return [
            {
                "title": item.get("title", ""),
                "body": item.get("summary", item.get("title", "")),
                "url": item.get("link", ""),
                "date": item.get("providerPublishTime", ""),
                "source": item.get("publisher", "Yahoo Finance"),
            }
            for item in news[:max_results]
        ]
    except Exception as e:
        logger.warning("yfinance news error for %s: %s", symbol, e)
        return []


def _safe_ddg_search(
    query: str,
    region: str = "wt-wt",
    timelimit: str | None = "w",
    max_results: int = 3,
) -> list[dict]:
    """Tek bir DDG arama sorgusu — thread-safe, fallback'li."""
    if not _DDG_AVAILABLE:
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
            # Fallback: zaman kısıtını kaldır
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


def _gather_news_parallel(symbol: str) -> list[dict]:
    """4 DDG sorguyu paralel çalıştır, sonuçları birleştir."""
    search_tasks = [
        (f"{symbol} stock news finance", "wt-wt", "w", 5),
        (f"{symbol} sec filings lawsuit regulation", "wt-wt", "m", 3),
        (f"{symbol} aktie finanzen", "de-de", "w", 2),
        (f"{symbol} hisse haber borsa", "tr-tr", "w", 3),
    ]

    results: list[dict] = []

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(_safe_ddg_search, q, r, t, m): q for q, r, t, m in search_tasks}
        for future in as_completed(futures):
            try:
                results.extend(future.result())
            except Exception as e:
                logger.warning("DDG parallel task error: %s", e)

    # Ek fallback: yetersiz haber varsa şirket ismiyle ara
    if len(results) < 3:
        company_names = {
            "VRTX": "Vertex Pharmaceuticals",
            "AMGN": "Amgen",
            "GILD": "Gilead Sciences",
            "REGN": "Regeneron",
            "MRNA": "Moderna",
            "BIIB": "Biogen",
            "ILMN": "Illumina",
        }
        company_name = company_names.get(symbol)
        if company_name:
            extra = _safe_ddg_search(f"{company_name} news stock", "wt-wt", "m", 5)
            results.extend(extra)

    # Son fallback: yfinance haberleri
    if not results:
        results = get_yfinance_news(symbol, max_results=5)

    # Deduplicate by URL
    seen: set[str] = set()
    unique: list[dict] = []
    for r in results:
        url = r.get("url", "")
        if url not in seen:
            unique.append(r)
            seen.add(url)

    return unique[:12]


# ---------------------------------------------------------------------------
# LLM provider functions
# ---------------------------------------------------------------------------


def _get_secret(key: str) -> str | None:
    """Güvenli secret okuma."""
    try:
        val = st.secrets.get(key, "")
        return val if val else None
    except Exception:
        return None


def _call_groq(prompt: str) -> str | None:
    """Groq Cloud LLM çağrısı (llama-3.3-70b)."""
    if not _GROQ_AVAILABLE:
        return None

    api_key = _get_secret("GROQ_API_KEY")
    if not api_key:
        logger.info("GROQ_API_KEY not configured — skipping Groq")
        return None

    try:
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=2048,
            top_p=1,
            stream=False,
        )
        result = completion.choices[0].message.content
        if result:
            return result
    except Exception as e:
        logger.warning("Groq API error: %s", e)

    return None


def _call_gemini(prompt: str) -> str | None:
    """Google Gemini LLM çağrısı (yeni google-genai SDK)."""
    if not _GEMINI_AVAILABLE:
        return None

    api_key = _get_secret("GOOGLE_API_KEY")
    if not api_key:
        logger.info("GOOGLE_API_KEY not configured — skipping Gemini")
        return None

    try:
        client = google_genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"{_SYSTEM_PROMPT}\n\n{prompt}",
        )
        if response and response.text:
            return response.text
    except Exception as e:
        logger.warning("Gemini API error: %s", e)

    return None


# ---------------------------------------------------------------------------
# Offline fallback report
# ---------------------------------------------------------------------------

_POSITIVE_KW = [
    "surge",
    "jump",
    "high",
    "profit",
    "growth",
    "buy",
    "yükseldi",
    "rekor",
    "kar",
    "büyüme",
    "al",
    "olumlu",
]
_NEGATIVE_KW = [
    "drop",
    "fall",
    "loss",
    "crash",
    "sell",
    "lawsuit",
    "düşüş",
    "zarar",
    "kriz",
    "sat",
    "olumsuz",
    "dava",
]


def _generate_offline_report(
    symbol: str, news_items: list[dict], language: str, reason: str | None = None
) -> str:
    """Keyword-based fallback rapor — LLM yoksa devreye girer."""
    headers = {
        "tr": ["Piyasa Algısı", "Son Haber Özeti", "Riskler & Fırsatlar"],
        "en": ["Market Sentiment", "Recent News Summary", "Risks & Opportunities"],
        "de": ["Marktstimmung", "Aktuelle Nachrichten", "Risiken & Chancen"],
    }
    h = headers.get(language, headers["tr"])

    combined_text = " ".join(
        f"{n.get('title', '')} {n.get('body', '')}".lower() for n in news_items
    )
    pos_count = sum(1 for k in _POSITIVE_KW if k in combined_text)
    neg_count = sum(1 for k in _NEGATIVE_KW if k in combined_text)

    if pos_count > neg_count:
        sentiment = "🟢 Pozitif / Bullish" if language == "tr" else "🟢 Positive / Bullish"
    elif neg_count > pos_count:
        sentiment = "🔴 Negatif / Bearish" if language == "tr" else "🔴 Negative / Bearish"
    else:
        sentiment = "⚪ Nötr / Neutral" if language == "tr" else "⚪ Neutral"

    reason_text = f"\n*Neden: {reason}*" if reason else ""

    news_lines = "\n".join(
        f"- **{item.get('date', '?')}**: {item.get('title', '')} ({item.get('source', '?')})"
        for item in news_items[:8]
    )

    return dedent(f"""\
### ⚠️ AI Limit Modu (Offline Fallback)
*LLM bağlantısı sağlanamadığı için bu rapor haberlerin otomatik özetlenmesiyle oluşturulmuştur.*{reason_text}

#### 1. {h[0]}
**{sentiment}**
(Pozitif kelimeler: {pos_count}, Negatif: {neg_count})

#### 2. {h[1]}
{news_lines if news_lines else "- Haber bulunamadı."}

#### 3. {h[2]}
- **Fırsat:** Haber akışına göre kısa vadeli volatilite değerlendirilebilir.
- **Risk:** Otomatik analiz devre dışı — manuel inceleme önerilir.
""")


# ---------------------------------------------------------------------------
# Main public API
# ---------------------------------------------------------------------------


@st.cache_data(ttl=RESEARCH_CACHE_TTL, show_spinner="🔍 Araştırma yapılıyor...")
def get_gemini_research(symbol: str, language: str = "tr") -> str:
    """
    Multi-provider research pipeline.

    Chain: Disk cache → DDG news (parallel) → Groq LLM → Gemini LLM → Offline fallback
    P9: Reports are persisted to data/reports_cache/ for 6-hour reuse.
    """
    # P9: Check disk cache first
    cached = _load_from_disk_cache(symbol, language)
    if cached:
        return cached

    # 1) Gather news (parallel DDG + yfinance fallback)
    news_items = _gather_news_parallel(symbol)
    if not news_items:
        return (
            f"⚠️ {symbol} için erişilebilir haber bulunamadı. "
            "(Bağlantı sorunu veya veri eksikliği olabilir)"
        )

    # 2) Build prompt
    news_context = "\n\n".join(
        f"Tarih: {r.get('date', '?')}\nBaşlık: {r['title']}\n"
        f"Kaynak: {r.get('source', '?')}\nÖzet: {r.get('body', '')}"
        for r in news_items
    )
    template = _PROMPTS.get(language, _PROMPTS["tr"])
    prompt = template.format(symbol=symbol, news_context=news_context)

    # 3) Try LLM providers in order: Groq → Gemini → Offline
    result = _call_groq(prompt)
    if result:
        _save_to_disk_cache(symbol, language, result)
        return result

    result = _call_gemini(prompt)
    if result:
        _save_to_disk_cache(symbol, language, result)
        return result

    # 4) All LLMs failed → offline keyword report (don't disk-cache offline reports)
    return _generate_offline_report(
        symbol, news_items, language, reason="Tüm LLM sağlayıcıları başarısız"
    )
