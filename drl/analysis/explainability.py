"""Lightweight explainability helpers for FinPilot.

This module focusses on the education-first UX layer.  It extracts a small
subset of alternative-data signals and prepares concise natural language
summaries that downstream LLM components can extend.  The helpers are designed
so that they can run without any heavy model dependencies – only ``pandas`` and
``numpy`` are required.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence, Tuple

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class AlternativeSignal:
    """Represents a condensed alternative-data insight."""

    name: str
    value: float
    strength: str
    description: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": float(self.value),
            "strength": self.strength,
            "description": self.description,
        }


@dataclass(frozen=True)
class RegimeStats:
    """Minimal statistics required for explainable narratives."""

    name: str
    success_rate: Optional[float] = None  # 0-1 range
    average_reward: Optional[float] = None
    max_drawdown: Optional[float] = None  # expressed as positive fraction, e.g. 0.04


@dataclass(frozen=True)
class NarrativePayload:
    """Structured response that front-ends can render directly."""

    title_1: str
    text_1: str
    title_2: str
    text_2: str
    exit_price: Optional[float]
    signal_strength: Dict[str, str]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "title_1": self.title_1,
            "text_1": self.text_1,
            "title_2": self.title_2,
            "text_2": self.text_2,
            "exit_price": None if self.exit_price is None else float(self.exit_price),
            "signal_strength": dict(self.signal_strength),
        }


def summarize_alternative_signals(
    history: pd.DataFrame,
    *,
    sentiment_column: str = "sentiment_score",
    onchain_column: str = "onchain_tx_volume",
    sentiment_window: int = 4,
    flow_window: int = 24,
) -> Tuple[AlternativeSignal, AlternativeSignal]:
    """Return the primary sentiment and whale-flow signals with one-line text.

    Parameters
    ----------
    history:
        DataFrame containing time-ordered feature values.  Only the two columns
        of interest are accessed; the rest of the frame is ignored.
    sentiment_column:
        Name of the column holding the weighted sentiment score.
    onchain_column:
        Column that approximates whale participation (e.g. on-chain volume).
    sentiment_window / flow_window:
        Look-back horizons used to compute the deltas and z-scores.
    """

    sentiment = _summarize_sentiment(history, sentiment_column, sentiment_window)
    whale = _summarize_whale_flow(history, onchain_column, flow_window)
    return sentiment, whale


def build_narrative_payload(
    regime: RegimeStats,
    sentiment_signal: AlternativeSignal,
    whale_signal: AlternativeSignal,
    *,
    current_price: Optional[float],
    max_allowed_drawdown: Optional[float],
) -> NarrativePayload:
    """Compose a two-paragraph JSON-friendly narrative."""

    regime_name = _format_regime_name(regime.name)
    success_text = _format_success_rate(regime.success_rate)

    paragraph_one = _compose_opportunity_paragraph(
        regime_name,
        success_text,
        sentiment_signal.description,
    )

    exit_level = _determine_exit_level(current_price, regime.max_drawdown, max_allowed_drawdown)
    paragraph_two = _compose_risk_paragraph(
        whale_signal.description,
        exit_level,
    )

    return NarrativePayload(
        title_1="Neden hemen şimdi?",
        text_1=paragraph_one,
        title_2="En kötü senaryo ne?",
        text_2=paragraph_two,
        exit_price=exit_level.price if exit_level else None,
        signal_strength={
            "sentiment": sentiment_signal.strength,
            "whale_flow": whale_signal.strength,
        },
    )


# ---------------------------------------------------------------------------
# Alternative signal helpers
# ---------------------------------------------------------------------------


def _summarize_sentiment(history: pd.DataFrame, column: str, window: int) -> AlternativeSignal:
    series = history.get(column)
    if series is None or series.dropna().empty:
        return AlternativeSignal(
            name="Sentiment (4 saat)",
            value=0.0,
            strength="neutral",
            description="Son 4 saatte duygu verisi eksik; piyasa hissiyatı belirsiz.",
        )

    clean = series.dropna()
    if len(clean) < 2:
        return AlternativeSignal(
            name="Sentiment (4 saat)",
            value=float(clean.iloc[-1]),
            strength="neutral",
            description="Duygu verisi sınırlı; hissiyatı yorumlamak için ek veri bekleyin.",
        )

    current = float(clean.iloc[-1])
    idx = max(0, len(clean) - window - 1)
    reference = float(clean.iloc[idx])
    delta = current - reference
    reference_abs = abs(reference)
    pct_change = (delta / reference_abs * 100.0) if reference_abs > 1e-6 else (delta * 100.0)
    abs_pct = abs(pct_change)

    if abs_pct < 1.0:
        description = (
            "Son 4 saatte duygu skoru anlamlı bir değişim göstermedi; piyasa hissiyatı dengede."
        )
        strength = "neutral"
    else:
        rising = delta >= 0.0
        speed = "hızlı " if abs_pct >= 10.0 else ""
        verb = "yükseldi" if rising else "geriledi"
        impact = "talebin güçlendiğini" if rising else "satış baskısının arttığını"
        description = f"Son 4 saatte duygu skoru %{abs_pct:.1f} {speed}{verb}; bu kısa vadede {impact} gösteriyor."
        if abs_pct >= 10.0:
            strength = "positive_strong" if rising else "negative_strong"
        elif abs_pct >= 3.0:
            strength = "positive_moderate" if rising else "negative_moderate"
        else:
            strength = "positive_light" if rising else "negative_light"

    return AlternativeSignal(
        name="Sentiment (4 saat)",
        value=float(pct_change),
        strength=strength,
        description=description,
    )


def _summarize_whale_flow(history: pd.DataFrame, column: str, window: int) -> AlternativeSignal:
    series = history.get(column)
    if series is None or series.dropna().empty:
        return AlternativeSignal(
            name="Balina akışı",
            value=0.0,
            strength="neutral",
            description="Balina akışı için yeterli veri yok; kurumsal hareketler belirsiz.",
        )

    clean = series.dropna()
    tail = clean.tail(window)
    if len(tail) < 3:
        return AlternativeSignal(
            name="Balina akışı",
            value=float(tail.iloc[-1]),
            strength="neutral",
            description="Balina akışı yorumlanacak kadar uzun bir geçmiş oluşturmamış.",
        )

    current = float(tail.iloc[-1])
    baseline = tail.iloc[:-1]
    mean = float(baseline.mean())
    std = float(baseline.std(ddof=0))
    z_score = (current - mean) / std if std > 1e-6 else 0.0
    magnitude = abs(z_score)

    if magnitude < 1.0:
        description = "Balina akışı normal aralıkta; kurumsal tarafta belirgin bir sinyal yok."
        strength = "neutral"
    else:
        direction = "giriş" if z_score > 0 else "çıkış"
        qualifier = (
            "normalin 2 katından fazla"
            if magnitude >= 2.0
            else f"normalin yaklaşık {magnitude:.1f} katı"
        )
        implication = (
            "kurumsal talebin güçlendiğini"
            if z_score > 0
            else "kurumsal satış baskısının arttığını"
        )
        description = f"Balina cüzdanlarından {qualifier} {direction}; bu {implication} gösteriyor."
        if magnitude >= 2.0:
            strength = "positive_strong" if z_score > 0 else "negative_strong"
        elif magnitude >= 1.5:
            strength = "positive_moderate" if z_score > 0 else "negative_moderate"
        else:
            strength = "positive_light" if z_score > 0 else "negative_light"

    return AlternativeSignal(
        name="Balina akışı",
        value=float(z_score),
        strength=strength,
        description=description,
    )


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _ExitLevel:
    price: float
    drawdown_fraction: float


def _determine_exit_level(
    current_price: Optional[float],
    regime_drawdown: Optional[float],
    user_drawdown: Optional[float],
) -> Optional[_ExitLevel]:
    limits = [
        value for value in (regime_drawdown, user_drawdown) if value is not None and value > 0.0
    ]
    if not limits or current_price is None:
        return None
    drawdown_fraction = min(limits)
    price = current_price * (1.0 - drawdown_fraction)
    return _ExitLevel(price=price, drawdown_fraction=drawdown_fraction)


def _compose_opportunity_paragraph(regime: str, success_text: str, sentiment_sentence: str) -> str:
    parts = []
    if regime:
        base = f"Piyasa şu anda {regime} rejiminde."
        if success_text:
            base = f"Piyasa şu anda {regime} rejiminde ve {success_text}."
        parts.append(base)
    elif success_text:
        parts.append(f"Geçmiş sinyallerin {success_text}.")
    parts.append(sentiment_sentence)
    return " ".join(parts)


def _compose_risk_paragraph(whale_sentence: str, exit_level: Optional[_ExitLevel]) -> str:
    exit_sentence: str
    if exit_level is None:
        exit_sentence = "Belirlediğiniz zarar eşiğine ulaşıldığında pozisyonu gözden geçirin."
    else:
        drop_pct = exit_level.drawdown_fraction * 100.0
        exit_sentence = f"Fiyat %{drop_pct:.1f} gerilerse (yaklaşık {exit_level.price:,.2f}) pozisyonu kapatmayı düşünün."
    return f"{whale_sentence} {exit_sentence}".strip()


def _format_regime_name(name: str) -> str:
    if not name or name.lower() == "unknown":
        return "belirsiz"
    return name.lower()


def _format_success_rate(success_rate: Optional[float]) -> str:
    if success_rate is None:
        return "yeterli geçmiş veri yok"
    pct = max(0.0, min(100.0, success_rate * 100.0))
    return f"geçmiş sinyallerin %{pct:.0f}'i başarılı oldu"


def estimate_regime_success(
    regimes: Sequence[str],
    rewards: Sequence[float],
    target_regime: Optional[str],
) -> RegimeStats:
    """Compute a lightweight success snapshot for the latest regime."""

    regime = target_regime or "unknown"
    if not regimes or target_regime is None:
        return RegimeStats(name=regime)

    rewards_array = np.asarray(
        [r for r, reg in zip(rewards, regimes) if reg == target_regime], dtype=float
    )
    if rewards_array.size == 0:
        return RegimeStats(name=regime)

    success_rate = float(np.mean(rewards_array >= 0))
    average_reward = float(np.mean(rewards_array))
    return RegimeStats(name=regime, success_rate=success_rate, average_reward=average_reward)
