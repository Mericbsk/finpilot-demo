"""Factor -> sentence rationale engine (template-based, no LLM in v1).

Rule: a rationale sentence may ONLY be assembled from fields that exist in
the scan result. Numbers come from the data, never from free generation.
This is the 'factor-constrained generation' guard from the audit.
"""

from __future__ import annotations

from typing import Any

# Badge id -> (TR fragment, EN fragment). Fragments are composable clauses.
_FRAGMENTS_TR: dict[str, str] = {
    "squeeze": "short oranı yüksek (squeeze potansiyeli)",
    "catalyst": "yakın tarihli bir katalizör/dosyalama var",
    "rvol": "hacim ivmesi ortalamanın üzerinde",
    "gap": "güne belirgin bir fiyat boşluğuyla başladı",
    "momentum": "kısa vadeli momentum güçlü",
    "volume": "hacim sıçraması görüldü",
    "contraction": "sıkışma sonrası genişleme sinyali veriyor",
    "regime": "genel piyasa rejimi destekleyici",
    "early_tier": "erken-yakalama merdiveninde üst basamakta",
}

_FRAGMENTS_EN: dict[str, str] = {
    "squeeze": "elevated short interest (squeeze potential)",
    "catalyst": "a recent catalyst/filing is present",
    "rvol": "volume acceleration above average",
    "gap": "opened with a notable price gap",
    "momentum": "strong short-term momentum",
    "volume": "a volume spike was observed",
    "contraction": "signals expansion after contraction",
    "regime": "the broad market regime is supportive",
    "early_tier": "high on the early-detection ladder",
}

_OPENER_TR = {
    "A": "Bugünün en yüksek konviksiyonlu adayı:",
    "B": "Güçlü aday:",
    "C": "İzleme adayı:",
}
_OPENER_EN = {
    "A": "Today's highest-conviction candidate:",
    "B": "Strong candidate:",
    "C": "Watch candidate:",
}

_CLOSER_TR = "Bu bir izleme adayıdır; karar ve risk yönetimi okuyucuya aittir."
_CLOSER_EN = "This is a watch candidate; decisions and risk management remain yours."


def extract_badges(result: dict[str, Any]) -> list[str]:
    """Derive badge ids from a scan-result row (tolerant to missing fields)."""
    badges: list[str] = []

    def num(key: str) -> float:
        try:
            return float(result.get(key) or 0.0)
        except (TypeError, ValueError):
            return 0.0

    if num("squeeze_factor") >= 0.5:
        badges.append("squeeze")
    if num("catalyst_factor") >= 0.3:
        badges.append("catalyst")
    if num("rvol_acceleration") > 0 or result.get("volume_spike"):
        badges.append("rvol")
    if num("overnight_gap_factor") >= 0.5 or num("gap_pct") >= 1.0:
        badges.append("gap")
    if result.get("price_momentum") or str(result.get("momentum_bias", "")).lower() in (
        "bullish",
        "positive",
        "up",
    ):
        badges.append("momentum")
    if num("contraction_factor") >= 0.5:
        badges.append("contraction")
    if str(result.get("tier", "")).upper() in ("TRIGGER", "CONFIRM"):
        badges.append("early_tier")
    if result.get("regime") is True:
        badges.append("regime")

    # de-dup preserving order, cap at 4 (readability)
    seen: set[str] = set()
    out = []
    for b in badges:
        if b not in seen:
            seen.add(b)
            out.append(b)
    return out[:4]


def build_rationale(
    ticker: str,
    grade: str,
    badges: list[str],
    lang: str = "tr",
) -> str:
    """Assemble a 1-2 sentence rationale from validated fragments only."""
    frags = _FRAGMENTS_TR if lang == "tr" else _FRAGMENTS_EN
    opener = (_OPENER_TR if lang == "tr" else _OPENER_EN).get(grade, "")
    closer = _CLOSER_TR if lang == "tr" else _CLOSER_EN

    parts = [frags[b] for b in badges if b in frags]
    if not parts:
        body = (
            "kompozit skoru bugünkü evrende üst dilimde"
            if lang == "tr"
            else "composite score in the top decile of today's universe"
        )
    else:
        joiner = "; " if lang == "tr" else "; "
        body = joiner.join(parts)

    sentence = f"{opener} {ticker} — {body}." if opener else f"{ticker} — {body}."
    return f"{sentence} {closer}"


def prob_band(prob: float) -> str:
    """Calibrated probability -> honest coarse band (never false precision)."""
    if prob <= 0:
        return "—"
    pct = int(round(prob * 100 / 5.0) * 5)
    pct = max(5, min(95, pct))
    return f"~{pct}%"
