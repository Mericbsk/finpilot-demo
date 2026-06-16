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
        research_data: dict = kwargs.get("research_data", {})  # type: ignore[assignment]
        social_data: dict = kwargs.get("social_data", {})  # type: ignore[assignment]
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
            bull_case: dict = kwargs.get("bull_case", {})  # type: ignore[assignment]
            bear_case: dict = kwargs.get("bear_case", {})  # type: ignore[assignment]
            prompt = _build_prompt(sym, scan_data, research_data, social_data, bull_case, bear_case)
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


def _build_prompt(
    symbol: str,
    data: dict,
    research: dict | None = None,
    social: dict | None = None,
    bull_case: dict | None = None,
    bear_case: dict | None = None,
) -> str:
    """Build a structured Turkish analysis prompt from scanner + research + social data."""
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

    base = (
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
    )

    # --- Research context (news + Reddit + HN) ---
    news_section = ""
    if research:
        news_items = research.get("news", [])
        reddit_items = research.get("reddit", [])
        hn_items = research.get("hacker_news", [])
        if news_items or reddit_items or hn_items:
            news_section = "## Güncel Haber ve Sosyal Medya Verileri\n\n"
            if news_items:
                news_section += "**Son Haberler:**\n"
                for item in news_items[:3]:
                    news_section += f"- [{item.get('title','')}]({item.get('url','')}) ({item.get('date','')})\n"
                    if item.get("body"):
                        news_section += f"  → {item['body'][:150]}\n"
                news_section += "\n"
            if reddit_items:
                news_section += "**Reddit (son 30 gün, en çok oy alan):**\n"
                for post in reddit_items[:3]:
                    news_section += f"- {post.get('title','')} (↑{post.get('score',0)} · r/{post.get('subreddit','')})\n"
                news_section += "\n"
            if hn_items:
                news_section += "**Hacker News:**\n"
                for post in hn_items[:2]:
                    news_section += f"- {post.get('title','')} ({post.get('points',0)} puan)\n"
                news_section += "\n"

    # --- Social sentiment context ---
    sentiment_section = ""
    if social:
        score_val = social.get("sentiment_score")
        buzz = social.get("buzz_level", "")
        poly = social.get("polymarket_markets", [])
        if score_val is not None:
            sentiment_label = (
                "POZİTİF 🟢"
                if score_val >= 0.6
                else "NEGATİF 🔴"
                if score_val <= 0.4
                else "NÖTR ⚪"
            )
            sentiment_section = (
                f"## Sosyal Sentiment\n\n"
                f"Sentiment skoru: **{score_val:.0%}** — {sentiment_label} | "
                f"Buzz seviyesi: **{buzz.upper()}** ({social.get('post_count', 0)} post)\n"
            )
            if poly:
                sentiment_section += "\n**Polymarket Tahminleri:**\n"
                for m in poly[:3]:
                    prob = m.get("yes_probability")
                    prob_str = f"{prob:.0%}" if prob is not None else "N/A"
                    sentiment_section += f"- {m.get('question','')} → Evet: {prob_str}\n"
            sentiment_section += "\n"

    analysis_request = (
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

    # INT-5: Bull/Bear researcher debate synthesis
    debate_section = ""
    if bull_case or bear_case:
        debate_section = "\n## 🔴🟢 Araştırma Tartışması (Bull vs Bear)\n\n"
        if bull_case and bull_case.get("arguments"):
            bull_score = bull_case.get("strength_score", 0.5)
            debate_section += f"**BOĞA ARGÜMANları** (güç: {bull_score:.0%}):\n"
            for arg in bull_case["arguments"][:4]:
                debate_section += f"- {arg}\n"
            if bull_case.get("key_catalysts"):
                debate_section += f"*Temel katalizörler:* {', '.join(bull_case['key_catalysts'])}\n"
            debate_section += "\n"
        if bear_case and bear_case.get("arguments"):
            bear_score = bear_case.get("strength_score", 0.5)
            debate_section += f"**AYI ARGÜMANları** (güç: {bear_score:.0%}):\n"
            for arg in bear_case["arguments"][:4]:
                debate_section += f"- {arg}\n"
            if bear_case.get("key_risks"):
                debate_section += f"*Temel riskler:* {', '.join(bear_case['key_risks'])}\n"
            debate_section += "\n"
        # Compute conviction ratio
        bull_s = float((bull_case or {}).get("strength_score", 0.5))
        bear_s = float((bear_case or {}).get("strength_score", 0.5))
        conviction = bull_s / (bull_s + bear_s) if (bull_s + bear_s) > 0 else 0.5
        debate_section += (
            f"*Tartışma sonucu:* Boğa inancı **{conviction:.0%}** / Ayı inancı **{1-conviction:.0%}**\n\n"
            "**Görevin:** Yukarıdaki boğa/ayı tartışmasını da göz önünde bulundurarak "
            "dengeli bir sentez yap.\n\n"
        )

    return base + news_section + sentiment_section + debate_section + analysis_request
