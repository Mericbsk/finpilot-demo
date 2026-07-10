"""E2 — Günlük market bağlam satırı (template, LLM yok).

Kaynaklar (ikisi de best-effort, bayatsa atlanır — asla uydurma):
  * data/macro_regime.json  (core.macro_regime cache'i: regime/vix/updated)
  * data/price_cache/SPY.json (OHLC listesi -> dünkü % değişim)

İkisi de yoksa boş string döner; şablon satırı tamamen atlar.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

_MACRO_PATH = Path(os.getenv("FINPILOT_MACRO_CACHE", "data/macro_regime.json"))
_SPY_PATH = Path(os.getenv("FINPILOT_SPY_CACHE", "data/price_cache/SPY.json"))

_REGIME_LABELS = {
    "risk_on": {"tr": "risk-iştahı açık", "en": "risk-on"},
    "risk_off": {"tr": "risk-iştahı kapalı", "en": "risk-off"},
    "neutral": {"tr": "nötr", "en": "neutral"},
}


def _regime_part(lang: str) -> str:
    try:
        d = json.loads(_MACRO_PATH.read_text(encoding="utf-8"))
        updated = datetime.fromisoformat(str(d.get("updated")))
        if datetime.now(tz=UTC) - updated > timedelta(days=3):
            return ""
        label = _REGIME_LABELS.get(str(d.get("regime", "")), {}).get(lang, "")
        if not label:
            return ""
        vix = d.get("vix")
        vix_txt = f" (VIX {float(vix):.0f})" if vix else ""
        return f"Rejim: {label}{vix_txt}" if lang == "tr" else f"Regime: {label}{vix_txt}"
    except Exception as exc:
        logger.debug("regime part unavailable: %s", exc)
        return ""


def _spy_part(lang: str) -> str:
    try:
        rows = json.loads(_SPY_PATH.read_text(encoding="utf-8"))
        if not isinstance(rows, list) or len(rows) < 2:
            return ""
        last, prev = rows[-1], rows[-2]
        last_date = datetime.strptime(str(last.get("date")), "%Y-%m-%d").replace(tzinfo=UTC)
        if datetime.now(tz=UTC) - last_date > timedelta(days=5):
            return ""
        c1, c0 = float(last["close"]), float(prev["close"])
        if c0 <= 0:
            return ""
        chg = (c1 - c0) / c0 * 100
        sign = "+" if chg >= 0 else ""
        return f"SPY dün {sign}{chg:.1f}%" if lang == "tr" else f"SPY {sign}{chg:.1f}% yesterday"
    except Exception as exc:
        logger.debug("spy part unavailable: %s", exc)
        return ""


def build_context_line(lang: str = "tr") -> str:
    """1 satırlık bağlam; hiçbir kaynak taze değilse '' (satır basılmaz)."""
    parts = [p for p in (_regime_part(lang), _spy_part(lang)) if p]
    return " · ".join(parts)
