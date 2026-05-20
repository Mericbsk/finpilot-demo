"""POST /api/v1/ai/explain — AI-generated simple explanation for financial terms.

Returns simple_explanation, why_important, and common_mistake for a given
dictionary slug. If the term already has these fields pre-populated, they are
returned immediately (source="json"). Otherwise the LLM generates them on the
fly and the result is cached for 24 hours.
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ai"])

# ---------------------------------------------------------------------------
# Dictionary loading (cached in process memory)
# ---------------------------------------------------------------------------

_DICT_PATH = Path(__file__).resolve().parent.parent.parent / "web" / "public" / "dictionary.json"


@lru_cache(maxsize=1)
def _load_dictionary() -> list[dict]:
    """Load and cache dictionary.json once per process lifetime."""
    if not _DICT_PATH.exists():
        logger.warning("dictionary.json not found at %s", _DICT_PATH)
        return []
    return json.loads(_DICT_PATH.read_text(encoding="utf-8"))


def _find_entry(slug: str) -> dict | None:
    for entry in _load_dictionary():
        if entry.get("slug") == slug:
            return entry
    return None


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class ExplainRequest(BaseModel):
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9\-]+$")
    lang: Literal["tr", "en"] = "tr"


class ExplainResponse(BaseModel):
    slug: str
    term: str
    simple_explanation: str
    why_important: str
    common_mistake: str
    source: Literal["json", "llm"]


# ---------------------------------------------------------------------------
# LLM prompt templates
# ---------------------------------------------------------------------------

_EXPLAIN_PROMPT_TR = """\
Sen bir kişisel finans eğitmenisin. Aşağıdaki finansal terim hakkında **Türkçe** olarak 3 kısa bilgi üret:

**Terim:** {term}
**Tanım:** {definition}

Lütfen şu formatta cevap ver (başka hiçbir şey yazma):
SIMPLE: [Max 2 cümle, sade dil, jargon yok]
IMPORTANT: [Max 2 cümle, neden önemli?]
MISTAKE: [Max 2 cümle, en sık yapılan hata nedir?]
"""

_EXPLAIN_PROMPT_EN = """\
You are a personal finance educator. Generate 3 short pieces of information about the financial term below in **English**:

**Term:** {term_en}
**Definition:** {definition_en}

Reply ONLY in this exact format (nothing else):
SIMPLE: [Max 2 sentences, plain language, no jargon]
IMPORTANT: [Max 2 sentences, why does it matter?]
MISTAKE: [Max 2 sentences, what is the most common mistake?]
"""


def _parse_llm_response(text: str) -> tuple[str, str, str]:
    """Extract SIMPLE / IMPORTANT / MISTAKE lines from LLM output."""
    simple = why = mistake = ""
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("SIMPLE:"):
            simple = line[len("SIMPLE:") :].strip()
        elif line.startswith("IMPORTANT:"):
            why = line[len("IMPORTANT:") :].strip()
        elif line.startswith("MISTAKE:"):
            mistake = line[len("MISTAKE:") :].strip()
    return simple, why, mistake


# ---------------------------------------------------------------------------
# In-memory LLM result cache (slug + lang → dict, survives restarts if
# the process isn't restarted, but that's fine — it's a best-effort cache)
# ---------------------------------------------------------------------------

_llm_cache: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post("/ai/explain", response_model=ExplainResponse)
def explain_term(req: ExplainRequest) -> ExplainResponse:
    """Return a simplified explanation, importance, and common mistake for a financial term.

    - If the term has pre-populated fields in dictionary.json, they are returned instantly.
    - Otherwise the LLM generates the content and the result is cached in-process.
    - No authentication required so the FinSense public Academy page can call it freely.
    """
    entry = _find_entry(req.slug)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Term '{req.slug}' not found in dictionary.")

    term_name = entry.get("term", req.slug)

    # ── Fast path: pre-enriched JSON fields ──────────────────────────────────
    if (
        entry.get("simple_explanation")
        and entry.get("why_important")
        and entry.get("common_mistake")
    ):
        return ExplainResponse(
            slug=req.slug,
            term=term_name,
            simple_explanation=entry["simple_explanation"],
            why_important=entry["why_important"],
            common_mistake=entry["common_mistake"],
            source="json",
        )

    # ── Check in-process LLM cache ────────────────────────────────────────────
    cache_key = f"{req.slug}:{req.lang}"
    if cache_key in _llm_cache:
        cached = _llm_cache[cache_key]
        return ExplainResponse(
            slug=req.slug,
            term=term_name,
            simple_explanation=cached["simple_explanation"],
            why_important=cached["why_important"],
            common_mistake=cached["common_mistake"],
            source="llm",
        )

    # ── LLM generation ───────────────────────────────────────────────────────
    try:
        from llm import get_router as get_llm_router  # type: ignore
    except ImportError as err:
        raise HTTPException(status_code=503, detail="LLM module not available.") from err

    llm_router = get_llm_router()
    if not llm_router.available_providers:
        raise HTTPException(
            status_code=503,
            detail="No LLM providers configured. Set GROQ_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY.",
        )

    if req.lang == "en":
        prompt = _EXPLAIN_PROMPT_EN.format(
            term_en=entry.get("term_en") or term_name,
            definition_en=entry.get("definition_en") or entry.get("definition", ""),
        )
    else:
        prompt = _EXPLAIN_PROMPT_TR.format(
            term=term_name,
            definition=entry.get("definition", ""),
        )

    try:
        response = llm_router.generate(prompt, max_tokens=400)
    except Exception as e:
        logger.error("LLM explain failed for slug=%s: %s", req.slug, e)
        raise HTTPException(status_code=502, detail=f"LLM generation failed: {e}") from e

    simple, why, mistake = _parse_llm_response(response.content)

    if not simple:
        raise HTTPException(status_code=502, detail="LLM returned an unexpected format.")

    result = {
        "simple_explanation": simple,
        "why_important": why or "—",
        "common_mistake": mistake or "—",
    }
    _llm_cache[cache_key] = result

    return ExplainResponse(
        slug=req.slug,
        term=term_name,
        simple_explanation=result["simple_explanation"],
        why_important=result["why_important"],
        common_mistake=result["common_mistake"],
        source="llm",
    )
