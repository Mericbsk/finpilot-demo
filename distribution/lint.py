"""Forbidden-language linter for all outbound financial text.

Rule source: GTM plan §9 / Demo Spec §9 / Telegram Ops §8.5.
A draft that fails lint is BLOCKED from the broadcast queue.

The framing FinPilot is allowed to use: research / education / watch
candidates / past-frequency probability. Never: buy-sell advice, price
targets, guarantees, urgency-scarcity marketing, personalised advice.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Each rule: (id, compiled pattern, explanation). Turkish + English surface.
_RULES: list[tuple[str, re.Pattern[str], str]] = [
    (
        "advice_verb",
        re.compile(
            r"\b(al[ıi]n(?!t[ıi])|sat[ıi]n\s+al|hemen\s+al|kesin\s+al|"
            r"buy\s+now|sell\s+now|strong\s+buy|strong\s+sell)\b",
            re.IGNORECASE,
        ),
        "Al/sat emri dili yasak — 'izleme adayı' çerçevesi kullan.",
    ),
    (
        "price_target",
        re.compile(
            r"\b(hedef\s+fiyat|price\s+target|take[\s-]?profit|stop[\s-]?loss|"
            r"tp:\s*\$?\d|sl:\s*\$?\d)\b",
            re.IGNORECASE,
        ),
        "Hedef fiyat / stop-TP seviyesi dış yüzeyde gösterilmez.",
    ),
    (
        "guarantee",
        re.compile(
            r"\b(garanti(li)?|kesin\s+(kazan|getiri|sonu[cç])|guarantee[ds]?|"
            r"risk[\s-]?free|can'?t\s+lose|surefire)\b",
            re.IGNORECASE,
        ),
        "Garanti/kesinlik dili yasak.",
    ),
    (
        "fomo",
        re.compile(
            r"\b(ka[cç][ıi]rma(y[ıi]n)?|son\s+f[ıi]rsat|acele\s+et|"
            r"don'?t\s+miss|last\s+chance|act\s+now|limited\s+time\s+only)\b",
            re.IGNORECASE,
        ),
        "FOMO/kıtlık pazarlaması yasak.",
    ),
    (
        "personalised",
        re.compile(
            r"\b(sana\s+[oö]zel\s+(tavsiye|öneri|sinyal)|size\s+[oö]zel\s+(tavsiye|öneri)|"
            r"personal(ised|ized)\s+(advice|recommendation))\b",
            re.IGNORECASE,
        ),
        "Kişiye özel tavsiye görünümü — compliance sınırı.",
    ),
    (
        "profit_promise",
        re.compile(
            r"(%\s*\d+\s*(kazan[cç]|getiri)\s*(garanti|kesin)|"
            r"\bx\d+\s*(kazan[cç]|return)\b|kazand[ıi]r[ıi]r\b)",
            re.IGNORECASE,
        ),
        "Getiri vaadi yasak.",
    ),
]

DISCLAIMER_TR = (
    "Bu içerik araştırma ve eğitim amaçlıdır; yatırım tavsiyesi değildir. "
    "Geçmiş performans gelecek sonuçların garantisi değildir."
)
DISCLAIMER_EN = (
    "This content is for research and educational purposes only and is not "
    "investment advice. Past performance does not guarantee future results."
)


@dataclass
class LintViolation:
    rule_id: str
    match: str
    explanation: str

    def __str__(self) -> str:  # pragma: no cover - convenience
        return f"[{self.rule_id}] '{self.match}' — {self.explanation}"


def check_text(text: str) -> list[LintViolation]:
    """Return all violations found in ``text`` (empty list == clean)."""
    violations: list[LintViolation] = []
    for rule_id, pattern, explanation in _RULES:
        for m in pattern.finditer(text):
            violations.append(LintViolation(rule_id, m.group(0), explanation))
    return violations


def require_disclaimer(text: str) -> bool:
    """True if the text carries one of the standard disclaimers."""
    return ("yatırım tavsiyesi değildir" in text.lower()) or (
        "not investment advice" in text.lower()
    )


def assert_publishable(text: str) -> None:
    """Raise ValueError with all problems if the text may not be published."""
    problems = [str(v) for v in check_text(text)]
    if not require_disclaimer(text):
        problems.append("[disclaimer] Zorunlu disclaimer satırı eksik.")
    if problems:
        raise ValueError("Lint failed:\n" + "\n".join(problems))
