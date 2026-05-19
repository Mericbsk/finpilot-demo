"""Report Agent — generates a structured daily Markdown report from scan results.

Input  : AgentContext.scan_results + AgentContext.symbols
Process: Format scan data + analysis data into a Markdown report
Output : AgentResult.data = {"report": str, "symbol_count": int, "generated_at": str}
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from agents.base import AgentContext, AgentResult, BaseAgent

logger = logging.getLogger(__name__)

_SIGNAL_EMOJI = {
    True: "🟢 AL",
    False: "🔴 SAT",
}
_REGIME_EMOJI = {
    True: "📈 Boğa",
    False: "📉 Ayı",
}


class ReportAgent(BaseAgent):
    """Generate a structured daily Markdown report from multi-agent scan data."""

    name = "report"

    def run(self, context: AgentContext, **kwargs: object) -> AgentResult:  # noqa: D102
        import time

        t0 = time.perf_counter()

        scan = context.scan_results
        analysis: dict[str, Any] = context.metadata.get("analysis_results", {})
        risk: dict[str, Any] = context.metadata.get("risk_results", {})

        if not scan:
            return AgentResult(
                agent=self.name,
                success=False,
                error="No scan_results in context",
            )

        now = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC")
        lines: list[str] = [
            f"# FinPilot Günlük Rapor — {now}",
            "",
            f"**Taranan sembol sayısı:** {len(scan)}",
            "",
        ]

        # ── Summary table ──────────────────────────────────────────────
        buy_count = sum(1 for d in scan.values() if d.get("direction"))
        sell_count = len(scan) - buy_count
        entry_ok_count = sum(1 for d in scan.values() if d.get("entry_ok"))

        lines += [
            "## Özet",
            "",
            "| Metrik | Değer |",
            "|--------|-------|",
            f"| AL sinyali | {buy_count} |",
            f"| SAT sinyali | {sell_count} |",
            f"| Giriş uygun (entry_ok) | {entry_ok_count} |",
            "",
        ]

        # ── Top signals ────────────────────────────────────────────────
        top = sorted(
            scan.items(),
            key=lambda kv: kv[1].get("finpilot_score", kv[1].get("composite_score", 0)),
            reverse=True,
        )[:10]

        lines += [
            "## En İyi 10 Sinyal",
            "",
            "| Sembol | Fiyat | FP Skor | Sinyal | Rejim | Entry | R/R | Stop | TP |",
            "|--------|-------|---------|--------|-------|-------|-----|------|----|",
        ]

        for sym, d in top:
            price = d.get("price", 0)
            score = d.get("finpilot_score", d.get("composite_score", 0))
            signal = _SIGNAL_EMOJI.get(bool(d.get("direction")), "—")
            regime = _REGIME_EMOJI.get(bool(d.get("regime")), "—")
            entry = "✅" if d.get("entry_ok") else "❌"
            rr = d.get("risk_reward", 0)
            sl = d.get("stop_loss", 0)
            tp = d.get("take_profit", 0)
            lines.append(
                f"| {sym} | {price:.2f} | {score} | {signal} | {regime} | {entry} | {rr:.1f} | {sl:.2f} | {tp:.2f} |"
            )

        lines.append("")

        # ── Risk summary ───────────────────────────────────────────────
        if risk:
            lines += ["## Risk Özeti", ""]
            for sym, r in risk.items():
                tp1 = r.get("tp1", r.get("take_profit", "—"))
                tp2 = r.get("tp2", "—")
                lines.append(
                    f"- **{sym}**: SL={r.get('stop_loss','—')} | TP1={tp1} | TP2={tp2} | R/R={r.get('risk_reward_ratio','—')} | {r.get('strategy_tag','')}"
                )
            lines.append("")

        # ── LLM Analysis snippets ──────────────────────────────────────
        if analysis:
            lines += ["## LLM Analiz Özetleri", ""]
            for sym, a in analysis.items():
                report_text: str = a.get("report", "")
                snippet = report_text[:500] + "..." if len(report_text) > 500 else report_text
                provider = a.get("provider", "unknown")
                latency = a.get("latency_ms", 0)
                lines += [
                    f"### {sym} _(via {provider}, {latency:.0f}ms)_",
                    "",
                    snippet,
                    "",
                ]

        report_md = "\n".join(lines)
        duration = (time.perf_counter() - t0) * 1000

        logger.info("ReportAgent: report generated — %d symbols, %.0fms", len(scan), duration)

        return AgentResult(
            agent=self.name,
            success=True,
            data={
                "report": report_md,
                "symbol_count": len(scan),
                "generated_at": now,
            },
            duration_ms=duration,
        )
