"""Alert Agent — Telegram notifications for entry-ok BUY signals.

Input  : AgentContext.symbols + AgentContext.scan_results
Process: Filter entry_ok=True signals → format message → POST Telegram API
Output : AgentResult.data = list[str]  (symbols for which alerts were sent)

Requires env vars:
    TELEGRAM_BOT_TOKEN   — bot token from @BotFather
    TELEGRAM_CHAT_ID     — target chat or channel ID

If env vars are missing the agent succeeds silently with an empty sent list
so it never blocks the workflow in development.
"""

from __future__ import annotations

import logging
import os

from agents.base import AgentContext, AgentResult, BaseAgent

logger = logging.getLogger(__name__)

_TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


class AlertAgent(BaseAgent):
    """Send Telegram alerts for entry-confirmed BUY signals.

    Gracefully skips when TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID are absent
    (returns success=True, data=[]) so the overall workflow is never blocked.
    """

    name = "alert"

    def run(self, context: AgentContext, **kwargs: object) -> AgentResult:  # noqa: D102
        import time

        t0 = time.perf_counter()

        bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")

        if not bot_token or not chat_id:
            logger.debug("AlertAgent: Telegram not configured — skipping silently")
            return AgentResult(agent=self.name, success=True, data=[], duration_ms=0.0)

        import requests

        sent: list[str] = []
        url = _TELEGRAM_API.format(token=bot_token)

        for sym in context.symbols:
            row = context.scan_results.get(sym, {})
            if not row.get("entry_ok"):
                continue

            message = _format_alert(sym, row)
            try:
                resp = requests.post(
                    url,
                    json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"},
                    timeout=10,
                )
                if resp.status_code == 200:
                    sent.append(sym)
                    logger.info("AlertAgent: alert sent for %s", sym)
                else:
                    logger.warning(
                        "AlertAgent: Telegram rejected %s — %s %s",
                        sym,
                        resp.status_code,
                        resp.text[:200],
                    )
            except requests.RequestException as exc:
                logger.warning("AlertAgent: HTTP error for %s: %s", sym, exc)

        duration = (time.perf_counter() - t0) * 1000
        logger.info("AlertAgent: %d alerts sent in %.0fms", len(sent), duration)
        return AgentResult(agent=self.name, success=True, data=sent, duration_ms=duration)


# ---------------------------------------------------------------------------
# Message formatter
# ---------------------------------------------------------------------------


def _format_alert(symbol: str, data: dict) -> str:
    """Build a structured Telegram Markdown alert message."""
    direction = data.get("direction", False)
    signal_emoji = "🟢 AL" if direction else "🔴 SAT"
    score = data.get("finpilot_score", data.get("composite_score", "?"))
    price = data.get("price", "?")
    stop = data.get("stop_loss", "?")
    tp = data.get("take_profit", data.get("tp1", "?"))
    rr = data.get("risk_reward", "?")
    regime = "📈 Boğa" if data.get("regime") else "📉 Ayı"
    strategy = data.get("strategy_tag", "Normal")

    return (
        f"🤖 *FinPilot Sinyal*\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"*{symbol}*  —  {signal_emoji}\n"
        f"Fiyat: `{price}`\n"
        f"Rejim: {regime}\n"
        f"Strateji: `{strategy}`\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"Stop Loss:  `{stop}`\n"
        f"Hedef:       `{tp}`\n"
        f"Risk/Ödül: `{rr}`\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"FinPilot Skoru: *{score}/100*"
    )
