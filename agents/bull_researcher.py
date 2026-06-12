"""Bull Researcher Agent — INT-5 (TradingAgents Bull/Bear Debate)

Generates 3-5 bullish arguments for a symbol based on scanner + research data.
Runs in parallel with BearResearcherAgent inside the CEO LangGraph workflow.

Output shape per symbol::

    {
        "arguments": list[str],     # 3–5 concise bullish points
        "strength_score": float,    # 0.0–1.0  (LLM-assessed conviction)
        "key_catalysts": list[str], # top 1–2 near-term catalysts
        "provider": str,
        "latency_ms": float,
    }
"""

from __future__ import annotations

import logging
import time
from typing import Any

from agents.base import AgentContext, AgentResult, BaseAgent

logger = logging.getLogger(__name__)


def _extract_json(raw: str, fallback_key: str = "arguments") -> dict:
    """Robustly extract the first JSON object from an LLM response.

    Handles: plain JSON, markdown code fences (```json ... ```),
    prose-wrapped JSON, and truncated responses.
    """
    import json as _json
    import re

    text = raw.strip()
    # Strip markdown code fences
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"```\s*$", "", text, flags=re.MULTILINE)
    text = text.strip()
    # Try direct parse first
    try:
        return _json.loads(text)
    except Exception:
        pass
    # Find first {...} block (handles prose before/after JSON)
    m = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, re.DOTALL)
    if m:
        try:
            return _json.loads(m.group())
        except Exception:
            pass
    # Final fallback: return raw text as a single item
    return {fallback_key: [text[:300]], "strength_score": 0.5}


_SYSTEM_PROMPT = (
    "Sen deneyimli bir yatırım bankası BULL araştırma analistisin. "
    "Görevin: verilen hisse için en güçlü ALICI / YÜKSELİŞ argümanlarını üretmek. "
    "Teknik ve temel göstergeleri, haberleri ve piyasa bağlamını kullanarak "
    "3-5 maddeli kısa, net, kanıta dayalı boğa argümanları yaz. "
    "Sadece güçlü yönleri ve katalizörleri vurgula. "
    "Yanıtını YALNIZCA JSON formatında ver:\n"
    '{"arguments": [...], "strength_score": 0.0-1.0, "key_catalysts": [...]}'
)


def _build_bull_prompt(symbol: str, scan: dict[str, Any], research: dict[str, Any]) -> str:
    price = scan.get("price", "N/A")
    rsi = scan.get("rsi", "N/A")
    score = scan.get("finpilot_score", scan.get("composite_score", "N/A"))
    regime = "Boğa" if scan.get("regime") else "Ayı"
    alignment = scan.get("alignment_ratio", "N/A")
    volume_spike = "Evet" if scan.get("volume_spike") else "Hayır"
    momentum = "Güçlü" if scan.get("price_momentum") else "Zayıf"
    sentiment = scan.get("sentiment_score", 0.5)
    news_items = research.get("news", [])[:3]

    news_text = ""
    if news_items:
        news_text = "Son haberler:\n" + "\n".join(
            f"- {n.get('title', '')} ({n.get('date', '')})"
            for n in news_items
        )

    return (
        f"Hisse: {symbol}\n"
        f"Fiyat: {price} | RSI: {rsi} | FinPilot Skoru: {score}/100\n"
        f"Rejim: {regime} | Zaman Dilimi Uyumu: {alignment}\n"
        f"Hacim Spike: {volume_spike} | Momentum: {momentum}\n"
        f"Sosyal Sentiment: {sentiment:.0%}\n"
        f"{news_text}\n\n"
        f"{symbol} için en güçlü ALICI argümanları üret."
    )


class BullResearcherAgent(BaseAgent):
    """Generates bull-case arguments for each symbol using the LLM router."""

    name = "bull_researcher"

    def run(self, context: AgentContext, **kwargs: object) -> AgentResult:  # noqa: D102
        t0 = time.perf_counter()
        research_data: dict = kwargs.get("research_data", {})  # type: ignore[assignment]
        try:
            from llm import get_router
            from llm.base import LLMMessage, LLMRole
        except ImportError as exc:
            return AgentResult(agent=self.name, success=False, error=f"LLM unavailable: {exc}")

        import json as _json

        router = get_router()
        results: dict[str, Any] = {}
        errors: list[str] = []

        for sym in context.symbols:
            scan = context.scan_results.get(sym, {})
            research = research_data.get(sym, {})
            prompt = _build_bull_prompt(sym, scan, research)
            try:
                response = router.generate_messages(
                    messages=[
                        LLMMessage(role=LLMRole.SYSTEM, content=_SYSTEM_PROMPT),
                        LLMMessage(role=LLMRole.USER, content=prompt),
                    ],
                    temperature=0.4,
                    max_tokens=400,
                )
                raw = response.content.strip()
                parsed = _extract_json(raw, fallback_key="arguments")
                parsed.setdefault("key_catalysts", [])

                results[sym] = {
                    "arguments": parsed.get("arguments", [])[:5],
                    "strength_score": float(parsed.get("strength_score", 0.5)),
                    "key_catalysts": parsed.get("key_catalysts", [])[:2],
                    "provider": response.provider,
                    "latency_ms": response.latency_ms,
                }
                logger.info(
                    "BullResearcher: %s — %d args, strength=%.2f via %s",
                    sym,
                    len(results[sym]["arguments"]),
                    results[sym]["strength_score"],
                    response.provider,
                )
            except Exception as exc:
                logger.warning("BullResearcher: %s failed: %s", sym, exc)
                errors.append(f"{sym}: {exc}")
                results[sym] = {
                    "arguments": [],
                    "strength_score": 0.5,
                    "key_catalysts": [],
                    "provider": "error",
                    "latency_ms": 0.0,
                }

        duration = (time.perf_counter() - t0) * 1000
        return AgentResult(agent=self.name, success=True, data=results, duration_ms=duration)
