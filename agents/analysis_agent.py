"""Analysis Agent — deep per-symbol LLM analysis via the existing LLMRouter.

Input  : AgentContext.symbols (1+ tickers), AgentContext.scan_results (scanner data)
Process: Build structured prompt from scanner data → LLMRouter.generate()
Output : AgentResult.data = dict[symbol, {report, provider, latency_ms}]

The agent uses the existing ``llm/router.py`` failover chain
(Groq → Claude → Gemini) so no new API keys are required.
"""

from __future__ import annotations

import logging

from agents.base import AgentContext, AgentResult, BaseAgent

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "Sen uzman bir finansal analist ve teknik analistsin. "
    "Verilen hisse senedi teknik verilerine dayanarak kapsamlı, "
    "pratik ve aksiyon odaklı bir analiz yap. "
    "Yanıtını Türkçe, Markdown formatında ver."
)


class AnalysisAgent(BaseAgent):
    """Deep LLM-powered analysis for each symbol in context.

    Uses the existing ``LLMRouter`` with automatic provider failover.
    Generates structured Markdown reports ready to display in the dashboard.
    """

    name = "analysis"

    def run(self, context: AgentContext, **kwargs: object) -> AgentResult:  # noqa: D102
        import time

        t0 = time.perf_counter()
        try:
            from llm import get_router
            from llm.base import LLMMessage, LLMRole
        except ImportError as exc:
            return AgentResult(agent=self.name, success=False, error=f"LLM unavailable: {exc}")

        router = get_router()
        analysis: dict = {}
        errors: list[str] = []

        for sym in context.symbols:
            scan_data = context.scan_results.get(sym, {})
            prompt = _build_prompt(sym, scan_data)
            try:
                response = router.generate_messages(
                    messages=[
                        LLMMessage(role=LLMRole.SYSTEM, content=_SYSTEM_PROMPT),
                        LLMMessage(role=LLMRole.USER, content=prompt),
                    ],
                    temperature=0.3,
                    max_tokens=900,
                )
                analysis[sym] = {
                    "report": response.content,
                    "provider": response.provider,
                    "model": response.model,
                    "latency_ms": response.latency_ms,
                }
                logger.info(
                    "AnalysisAgent: %s analysed via %s in %.0fms",
                    sym,
                    response.provider,
                    response.latency_ms,
                )
            except Exception as exc:
                logger.warning("AnalysisAgent: %s failed: %s", sym, exc)
                errors.append(f"{sym}: {exc}")

        duration = (time.perf_counter() - t0) * 1000
        if not analysis and errors:
            return AgentResult(
                agent=self.name,
                success=False,
                error="; ".join(errors),
                duration_ms=duration,
            )
        return AgentResult(agent=self.name, success=True, data=analysis, duration_ms=duration)


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------


def _build_prompt(symbol: str, data: dict) -> str:
    """Build a structured Turkish analysis prompt from scanner row data."""
    score = data.get("finpilot_score", data.get("composite_score", "N/A"))
    signal = "AL 🟢" if data.get("direction") else "SAT 🔴"
    regime = "Boğa 📈" if data.get("regime") else "Ayı 📉"
    rsi = data.get("rsi", "N/A")
    price = data.get("price", "N/A")
    stop = data.get("stop_loss", "N/A")
    tp1 = data.get("take_profit", data.get("tp1", "N/A"))
    rr = data.get("risk_reward", "N/A")
    volume_spike = "Evet ✅" if data.get("volume_spike") else "Hayır"
    momentum = "Güçlü ✅" if data.get("price_momentum") else "Zayıf"
    alignment = data.get("alignment_ratio", "N/A")
    strategy = data.get("strategy_tag", "Normal")

    return (
        f"## {symbol} Teknik Analiz Raporu\n\n"
        f"| Parametre | Değer |\n"
        f"|-----------|-------|\n"
        f"| Güncel Fiyat | {price} |\n"
        f"| Sinyal | {signal} |\n"
        f"| Piyasa Rejimi | {regime} |\n"
        f"| RSI | {rsi} |\n"
        f"| FinPilot Skoru | {score}/100 |\n"
        f"| Stop Loss | {stop} |\n"
        f"| Hedef Fiyat (TP1) | {tp1} |\n"
        f"| Risk/Ödül | {rr} |\n"
        f"| Hacim Spike | {volume_spike} |\n"
        f"| Momentum | {momentum} |\n"
        f"| Zaman Dilimi Uyumu | {alignment} |\n"
        f"| Strateji Etiketi | {strategy} |\n\n"
        "Yukarıdaki verilere göre lütfen şunları analiz et:\n\n"
        "### 1. Teknik Görünüm\n"
        "Önemli destek/direnç seviyeleri, trend durumu ve teknik oluşumlar.\n\n"
        "### 2. Giriş / Çıkış Stratejisi\n"
        "Riske göre düzeltilmiş optimal giriş noktası, stop-loss mantığı ve "
        "kademeli kar alma planı.\n\n"
        "### 3. Risk Değerlendirmesi\n"
        "Bu işlemde dikkat edilmesi gereken başlıca riskler ve senaryolar.\n\n"
        "### 4. Özet Karar\n"
        "Tek cümleyle net görüş (AL / SAT / BEKLE + neden)."
    )
