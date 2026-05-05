"""POST /api/v1/llm/analyze — LLM-powered stock analysis via Groq → Claude → Gemini failover."""

from __future__ import annotations

import hashlib
import logging
import re
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.middleware.auth import require_auth
from core.cache import cached

logger = logging.getLogger(__name__)

router = APIRouter(tags=["llm"])

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class AnalyzeRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10, pattern=r"^[A-Z0-9.]+$")
    context: str = Field(default="", max_length=2000)
    language: str = Field(default="en", pattern=r"^(en|tr|de)$")


class AnalyzeSection(BaseModel):
    title: str
    content: str


class AnalyzeResponse(BaseModel):
    symbol: str
    sections: list[AnalyzeSection]
    provider: str
    model: str
    latency_ms: float
    tokens: dict[str, int]


# ---------------------------------------------------------------------------
# Prompt templates (same structure as views/components/research.py)
# ---------------------------------------------------------------------------

_SYSTEM = "You are a senior financial analyst. Answer in Markdown."

_PROMPTS: dict[str, str] = {
    "en": """\
Create a comprehensive investor report for **{symbol}**.
{context_block}

Required Format (use these exact headings):
## 📊 Market Sentiment
(Bullish/Bearish/Neutral — with reasons, social/institutional flow)

## ⚖️ Legal & Regulatory
(Lawsuits, fines, SEC filings, compliance status, ESG rating)

## 💰 Key Financial Developments
(Revenue, margins, EPS, cash position, guidance — bullet points)

## ⚠️ Risks & Opportunities
(Key risk + key opportunity with TAM/growth estimates)

## 🎯 Conclusion
(Actionable recommendation with price targets and stop-loss level)
""",
    "tr": """\
**{symbol}** hissesi için kapsamlı bir yatırımcı raporu hazırla.
{context_block}

Gerekli Format (bu başlıkları kullan):
## 📊 Piyasa Algısı
(Olumlu/Olumsuz/Nötr — nedenleriyle, sosyal/kurumsal akış)

## ⚖️ Yasal ve Regülatif Gelişmeler
(Davalar, cezalar, SEC/KAP bildirimleri, uyumluluk, ESG puanı)

## 💰 Öne Çıkan Finansal Gelişmeler
(Gelir, marjlar, EPS, nakit pozisyonu — maddeler halinde)

## ⚠️ Riskler ve Fırsatlar
(Ana risk + ana fırsat, TAM/büyüme tahminleri)

## 🎯 Sonuç
(Aksiyon önerisi, hedef fiyatlar ve stop-loss seviyesi)
""",
    "de": """\
Erstellen Sie einen umfassenden Investorenbericht für **{symbol}**.
{context_block}

Gewünschtes Format (verwenden Sie diese Überschriften):
## 📊 Marktstimmung
(Positiv/Negativ/Neutral — mit Begründung)

## ⚖️ Rechtliche & Regulatorische Entwicklungen
(Klagen, Strafen, Meldungen, ESG-Rating)

## 💰 Wichtige Finanzentwicklungen
(Umsatz, Margen, EPS, Cash — Stichpunkte)

## ⚠️ Risiken & Chancen
(Hauptrisiko + Hauptchance)

## 🎯 Fazit
(Handlungsempfehlung mit Kurszielen und Stop-Loss)
""",
}


# ---------------------------------------------------------------------------
# Section parser
# ---------------------------------------------------------------------------


def _parse_sections(raw: str) -> list[AnalyzeSection]:
    """Parse markdown with ## headings into sections."""
    parts = re.split(r"(?m)^##\s+", raw)
    sections: list[AnalyzeSection] = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        lines = part.split("\n", 1)
        title = lines[0].strip()
        content = lines[1].strip() if len(lines) > 1 else ""
        if title and content:
            sections.append(AnalyzeSection(title=title, content=content))
    # If parsing failed (no ## headings), return as single section
    if not sections and raw.strip():
        sections.append(AnalyzeSection(title="📊 Analysis", content=raw.strip()))
    return sections


# ---------------------------------------------------------------------------
# LLM router status endpoint
# ---------------------------------------------------------------------------


@router.get("/llm/status")
def llm_status() -> dict[str, Any]:
    """Return LLM router status: available providers, health, stats."""
    try:
        from llm import get_router

        llm_router = get_router()
        return llm_router.get_status()
    except Exception as e:
        return {"error": str(e), "providers": [], "available": []}


# ---------------------------------------------------------------------------
# Cached LLM generation helper
# ---------------------------------------------------------------------------


def _llm_cache_key(symbol: str, language: str, context: str) -> str:
    """Build a stable cache key from request parameters."""
    ctx_digest = hashlib.sha256(context[:500].encode()).hexdigest()[:12]
    return f"llm:analyze:{symbol}:{language}:{ctx_digest}"


@cached(
    ttl=1800,
    prefix="llm",
    key_builder=_llm_cache_key,
    skip_cache_if=lambda symbol, language, context: any(
        kw in context.lower() for kw in ("force", "refresh", "yenile")
    ),
)
def _generate_report(symbol: str, language: str, context: str) -> dict[str, Any]:
    """Generate and cache an LLM research report. Returns a plain dict for serialization."""
    from llm import get_router

    llm_router = get_router()
    template = _PROMPTS.get(language, _PROMPTS["en"])
    context_block = f"\nAdditional context:\n{context}" if context else ""
    prompt = template.format(symbol=symbol, context_block=context_block)

    response = llm_router.generate(prompt, system=_SYSTEM, max_tokens=2048)
    sections = _parse_sections(response.content)

    return {
        "symbol": symbol,
        "sections": [{"title": s.title, "content": s.content} for s in sections],
        "provider": response.provider,
        "model": response.model,
        "latency_ms": round(response.latency_ms, 1),
        "tokens": {"input": response.input_tokens, "output": response.output_tokens},
    }


# ---------------------------------------------------------------------------
# Main analyze endpoint
# ---------------------------------------------------------------------------


@router.post("/llm/analyze", response_model=AnalyzeResponse, dependencies=[Depends(require_auth)])
def analyze_symbol(req: AnalyzeRequest) -> AnalyzeResponse:
    """Generate an LLM-powered research report for a stock symbol.

    Results are cached for 30 minutes. Include "force" or "refresh" in context to bypass cache.
    Uses Groq → Claude → Gemini failover via llm.router.
    """
    try:
        from llm import get_router
    except ImportError as err:
        raise HTTPException(status_code=503, detail="LLM module not available") from err

    llm_router = get_router()
    if not llm_router.available_providers:
        raise HTTPException(
            status_code=503,
            detail="No LLM providers available. Set GROQ_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY.",
        )

    try:
        data = _generate_report(req.symbol, req.language, req.context)
    except Exception as e:
        logger.error("LLM generation failed for %s: %s", req.symbol, e)
        raise HTTPException(status_code=502, detail=f"LLM generation failed: {e}") from e

    return AnalyzeResponse(
        symbol=data["symbol"],
        sections=[AnalyzeSection(**s) for s in data["sections"]],
        provider=data["provider"],
        model=data["model"],
        latency_ms=data["latency_ms"],
        tokens=data["tokens"],
    )
