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

        # Sprint 5 (S5-3): Suppress BUY alerts when quality gate is degraded
        try:
            from core.quality_gate import is_degraded

            if is_degraded():
                logger.warning("AlertAgent: quality gate DEGRADED — suppressing alerts")
                return AgentResult(
                    agent=self.name,
                    success=True,
                    data=[],
                    duration_ms=(time.perf_counter() - t0) * 1000,
                )
        except Exception:  # noqa: BLE001
            pass

        import requests

        sent: list[str] = []
        url = _TELEGRAM_API.format(token=bot_token)

        for sym, row in _select_signals(context):
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
# Konviksiyon-tier gunluk tavan (env-gated)
# ---------------------------------------------------------------------------
# Sinyal kalitesi labi (2026-06): tum entry_ok sinyalleri gostermek yerine
# konviksiyon tier'ina gore SUN: Tier A (short+gap, ~%73 isabet) HEPSI +
# Tier B/C'den skorca en iyiler, gunluk tavana kadar. Skoru/sinyali degistirmez,
# yalniz KAC sinyalin kullaniciya gosterildigini sinirlar.
# FINPILOT_ENABLE_CONVICTION_TIERS=0 iken eski davranis (tum entry_ok).


def _select_signals(context) -> list[tuple[str, dict]]:
    cand: list[tuple[str, dict]] = []
    for sym in context.symbols:
        row = context.scan_results.get(sym, {})
        if row.get("entry_ok"):
            cand.append((sym, row))

    if os.environ.get("FINPILOT_ENABLE_CONVICTION_TIERS", "0") != "1":
        return cand  # eski davranis: hepsi

    try:
        max_total = int(os.environ.get("FINPILOT_ALERT_MAX_PER_RUN", "5"))
    except ValueError:
        max_total = 5

    def _rank(item: tuple[str, dict]):
        row = item[1]
        return (
            float(row.get("conviction_prob", 0.0) or 0.0),
            float(row.get("composite_score", 0.0) or 0.0),
        )

    A = sorted([c for c in cand if c[1].get("conviction_tier") == "A"], key=_rank, reverse=True)
    B = sorted([c for c in cand if c[1].get("conviction_tier") == "B"], key=_rank, reverse=True)
    C = sorted([c for c in cand if c[1].get("conviction_tier") == "C"], key=_rank, reverse=True)

    out = list(A)  # Tier A hepsi (nadir + yuksek isabet)
    for grp in (B, C):
        for c in grp:
            if len(out) >= max_total:
                break
            out.append(c)
    return out


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
    tier = data.get("conviction_tier", "")
    prob = data.get("conviction_prob", 0.0)
    tier_line = ""
    if tier:
        _lbl = {"A": "🅰️ Elite", "B": "🅱️ Güçlü", "C": "🅲 Orta"}.get(tier, tier)
        tier_line = f"Konviksiyon: *{_lbl}*  (~%{prob * 100:.0f} >=%5)\n"

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
        f"{tier_line}"
        f"FinPilot Skoru: *{score}/100*"
    )
