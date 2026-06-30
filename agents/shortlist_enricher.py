"""
Shortlist Enricher Agent
========================

Tarama sonrası top-N shortlist için TEK birleşik yerel-LLM çağrısıyla
zenginleştirme üretir: açıklama + katalizör triage + kısa boğa/ayı notu.

Tasarım ilkeleri (yerel/CPU-öncelikli):
  - Yalnız shortlist (top-N) üzerinde çalışır; sıcak tarama döngüsüne girmez.
  - Sembol başına TEK LLM çağrısı (CPU'da maliyeti minimumda tutar).
  - Yapılandırılmış JSON çıktı → makine-okunur, cache'lenebilir, doğrulanabilir.
  - LLM yoksa zarif düşer (AgentResult.success=False); sistem AI'sız çalışmaya devam eder.

Backend ``llm.get_router`` üzerinden gelir → FINPILOT_LLM_BACKEND=ollama ile yerel.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from agents.base import AgentContext, AgentResult, BaseAgent

logger = logging.getLogger(__name__)


def _extract_json(raw: str) -> dict:
    """LLM çıktısından ilk JSON nesnesini sağlam biçimde ayıkla."""
    import json as _json
    import re

    text = raw.strip()
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"```\s*$", "", text, flags=re.MULTILINE).strip()
    try:
        return _json.loads(text)
    except Exception:
        pass
    m = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, re.DOTALL)
    if m:
        try:
            return _json.loads(m.group())
        except Exception:
            pass
    return {}


_SYSTEM_PROMPT = (
    "Sen bir hisse tarama asistanısın. Verilen ADAY hisse için KISA, kanıta dayalı "
    "bir zenginleştirme üret. Fiyat TAHMİNİ yapma; yalnız mevcut sinyali yorumla. "
    "Sentiment/mention verisi varsa social_read ile sosyal ilgiyi sınıfla: "
    "organik gerçek ilgi mi, yoksa yüzeysel/pump mı. "
    "Yanıtını YALNIZCA şu JSON şemasıyla ver:\n"
    '{"explanation": "tek cümle neden listede", '
    '"catalyst_strength": 0-10 tamsayı, '
    '"catalyst_summary": "kısa", '
    '"bull_point": "tek satır", '
    '"bear_point": "tek satır", '
    '"social_read": "organic|pump|neutral|bearish", '
    '"verdict": "strong|watch|skip"}'
)


def _build_prompt(symbol: str, scan: dict[str, Any]) -> str:
    parts = [f"Hisse: {symbol}"]
    for key, label in (
        ("composite_score", "composite"),
        ("finpilot_score", "finpilot_skor"),
        ("direction", "yön"),
        ("rvol", "RVOL"),
        ("rsi", "RSI"),
        ("price", "fiyat"),
        ("sentiment_score", "sentiment"),
        ("mention_delta", "mention_delta"),
    ):
        if key in scan and scan[key] is not None:
            parts.append(f"{label}={scan[key]}")
    return "Aday verisi: " + ", ".join(parts) + "\nBu adayı yukarıdaki JSON şemasıyla zenginleştir."


def _coerce_strength(value: Any) -> int:
    try:
        return max(0, min(10, int(round(float(value)))))
    except Exception:  # noqa: BLE001
        return 0


class ShortlistEnricherAgent(BaseAgent):
    """Top-N shortlist için yerel-LLM zenginleştirmesi (açıklama + katalizör + tez)."""

    name = "shortlist_enricher"

    def run(self, context: AgentContext, **kwargs: object) -> AgentResult:  # noqa: D102
        t0 = time.perf_counter()
        try:
            from llm import get_router
            from llm.base import LLMMessage, LLMRole
        except ImportError as exc:
            return AgentResult(agent=self.name, success=False, error=f"LLM unavailable: {exc}")

        router = get_router()
        results: dict[str, Any] = {}
        errors: list[str] = []

        for sym in context.symbols:
            scan = context.scan_results.get(sym, {})
            prompt = _build_prompt(sym, scan)
            try:
                response = router.generate_messages(
                    messages=[
                        LLMMessage(role=LLMRole.SYSTEM, content=_SYSTEM_PROMPT),
                        LLMMessage(role=LLMRole.USER, content=prompt),
                    ],
                    temperature=0.3,
                    max_tokens=300,
                )
                parsed = _extract_json(response.content or "")
                results[sym] = {
                    "explanation": str(parsed.get("explanation", "")).strip(),
                    "catalyst_strength": _coerce_strength(parsed.get("catalyst_strength", 0)),
                    "catalyst_summary": str(parsed.get("catalyst_summary", "")).strip(),
                    "bull_point": str(parsed.get("bull_point", "")).strip(),
                    "bear_point": str(parsed.get("bear_point", "")).strip(),
                    "social_read": str(parsed.get("social_read", "neutral")).strip().lower(),
                    "verdict": str(parsed.get("verdict", "watch")).strip().lower(),
                    "provider": response.provider,
                    "latency_ms": response.latency_ms,
                }
                logger.info(
                    "ShortlistEnricher: %s — verdict=%s catalyst=%d via %s",
                    sym,
                    results[sym]["verdict"],
                    results[sym]["catalyst_strength"],
                    response.provider,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("ShortlistEnricher: %s failed: %s", sym, exc)
                errors.append(f"{sym}: {exc}")
                results[sym] = {
                    "explanation": "",
                    "catalyst_strength": 0,
                    "catalyst_summary": "",
                    "bull_point": "",
                    "bear_point": "",
                    "social_read": "neutral",
                    "verdict": "watch",
                    "provider": "error",
                    "latency_ms": 0.0,
                }

        duration = (time.perf_counter() - t0) * 1000
        success = (
            any(r.get("provider") not in ("error", None) for r in results.values())
            or not context.symbols
        )
        return AgentResult(
            agent=self.name,
            success=success,
            data=results,
            error="; ".join(errors) if errors and not success else None,
            duration_ms=duration,
        )
