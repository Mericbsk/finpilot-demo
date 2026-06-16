"""FinBERT Sentiment Provider — INT-4 (Financial NLP)

Provides ``classify_texts(texts)`` which returns a -1.0..+1.0 sentiment
score for a list of financial text snippets.

Priority chain (first available wins):
    1. HuggingFace ``transformers`` + ``ProsusAI/finbert`` (local GPU/CPU)
    2. HuggingFace Inference API (env: HF_API_TOKEN)
    3. Enhanced keyword scoring (pure Python, always available)

The top-level ``score_texts()`` function normalises all three sources to the
same 0.0–1.0 output so callers don't need to handle provider differences.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)

_FINBERT_MODEL = "ProsusAI/finbert"
_HF_API_URL = f"https://api-inference.huggingface.co/models/{_FINBERT_MODEL}"

# ── Enhanced keyword dictionaries (fallback) ─────────────────────────────────
_POSITIVE = {
    "buy",
    "bull",
    "bullish",
    "moon",
    "growth",
    "strong",
    "profit",
    "breakout",
    "undervalued",
    "rally",
    "rise",
    "gain",
    "opportunity",
    "long",
    "calls",
    "beat",
    "outperform",
    "upgrade",
    "record",
    "surge",
    "soar",
    "upside",
    "positive",
    "recommend",
    "overweight",
    "accumulate",
    "al",
    "yükseliş",
    "kazanç",
    "fırsat",
    "güçlü",
    "büyüme",
    "artış",
    "hedef",
    "yukarı",
    "olumlu",
}
_NEGATIVE = {
    "sell",
    "bear",
    "bearish",
    "crash",
    "dump",
    "short",
    "fraud",
    "scam",
    "overvalued",
    "decline",
    "fall",
    "drop",
    "loss",
    "risk",
    "warning",
    "danger",
    "miss",
    "downgrade",
    "underperform",
    "underweight",
    "reduce",
    "lawsuit",
    "probe",
    "investigation",
    "margin",
    "debt",
    "bankrupt",
    "recession",
    "layoff",
    "cut",
    "below",
    "concern",
    "headwind",
    "pressure",
    "weak",
    "slowdown",
    "sat",
    "kayıp",
    "tehlike",
    "tehdit",
    "çöküş",
    "düşüş",
    "olumsuz",
    "zayıf",
    "baskı",
}

# Negation context words that flip the polarity of the next keyword
_NEGATIONS = {"not", "no", "never", "without", "despite", "against", "fail", "failed", "fails"}


def _keyword_score(texts: list[str]) -> float:
    """Enhanced keyword scorer with simple negation handling.

    Returns score in [-1.0, +1.0].
    """
    if not texts:
        return 0.0
    pos = neg = 0
    for text in texts:
        tokens = text.lower().split()
        negate = False
        for i, tok in enumerate(tokens):
            # Check if previous token was a negation word
            if i > 0 and tokens[i - 1] in _NEGATIONS:
                negate = True
            else:
                negate = False
            clean = tok.rstrip(".,!?;:")
            if clean in _POSITIVE:
                if negate:
                    neg += 1
                else:
                    pos += 1
            elif clean in _NEGATIVE:
                if negate:
                    pos += 1
                else:
                    neg += 1
    total = pos + neg
    if total == 0:
        return 0.0
    return round((pos - neg) / total, 3)


# ── Local transformers FinBERT ────────────────────────────────────────────────


@lru_cache(maxsize=1)
def _get_local_pipeline():
    """Load FinBERT pipeline once and cache it (lazy init)."""
    try:
        from transformers import pipeline  # type: ignore[import]

        pipe = pipeline(
            "text-classification",
            model=_FINBERT_MODEL,
            truncation=True,
            max_length=512,
            device=-1,  # CPU; set device=0 for GPU
        )
        logger.info("FinBERT: local transformers pipeline loaded (%s)", _FINBERT_MODEL)
        return pipe
    except Exception as exc:
        logger.info("FinBERT: local pipeline unavailable (%s)", exc)
        return None


def _local_finbert_score(texts: list[str]) -> float | None:
    """Score texts with local FinBERT. Returns None if unavailable."""
    pipe = _get_local_pipeline()
    if pipe is None:
        return None
    try:
        batch = texts[:16]  # cap batch size for CPU
        results: list[dict[str, Any]] = pipe(batch)
        scores: list[float] = []
        for r in results:
            label = r.get("label", "neutral").lower()
            conf = float(r.get("score", 0.5))
            if label == "positive":
                scores.append(conf)
            elif label == "negative":
                scores.append(-conf)
            else:
                scores.append(0.0)
        return sum(scores) / len(scores) if scores else 0.0
    except Exception as exc:
        logger.debug("FinBERT local inference failed: %s", exc)
        return None


# ── HuggingFace Inference API ─────────────────────────────────────────────────


def _hf_api_score(texts: list[str]) -> float | None:
    """Score via HuggingFace Inference API.  Requires HF_API_TOKEN env var."""
    token = os.getenv("HF_API_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")
    if not token:
        return None
    try:
        import requests  # noqa: PLC0415

        headers = {"Authorization": f"Bearer {token}"}
        payload = {"inputs": texts[:10]}
        resp = requests.post(_HF_API_URL, headers=headers, json=payload, timeout=10)
        if resp.status_code != 200:
            return None
        data = resp.json()
        # HF API returns list of list of {label, score}
        if not isinstance(data, list):
            return None
        total_score = 0.0
        count = 0
        for item in data:
            if isinstance(item, list):
                # Find best label
                best = max(item, key=lambda x: x.get("score", 0))
                label = best.get("label", "neutral").lower()
                conf = float(best.get("score", 0.5))
                if label == "positive":
                    total_score += conf
                elif label == "negative":
                    total_score -= conf
                count += 1
            elif isinstance(item, dict):
                label = item.get("label", "neutral").lower()
                conf = float(item.get("score", 0.5))
                if label == "positive":
                    total_score += conf
                elif label == "negative":
                    total_score -= conf
                count += 1
        return total_score / count if count > 0 else 0.0
    except Exception as exc:
        logger.debug("FinBERT HF API failed: %s", exc)
        return None


# ── Public API ────────────────────────────────────────────────────────────────


def score_texts(texts: list[str]) -> float:
    """Score a list of financial text strings.

    Returns a value in 0.0–1.0 where:
        0.0 = very negative
        0.5 = neutral
        1.0 = very positive

    Provider priority: local FinBERT → HF API → enhanced keyword fallback.
    """
    if not texts:
        return 0.5

    # Try local FinBERT first (most accurate)
    raw = _local_finbert_score(texts)

    # Try HF API (medium accuracy, requires token)
    if raw is None:
        raw = _hf_api_score(texts)

    # Fall back to enhanced keyword scoring (always available)
    if raw is None:
        raw = _keyword_score(texts)

    # Normalise from [-1, +1] → [0, 1]
    return round(max(0.0, min(1.0, (raw + 1.0) / 2.0)), 3)


def active_provider() -> str:
    """Return the name of the currently active sentiment provider."""
    if _get_local_pipeline() is not None:
        return "finbert-local"
    if os.getenv("HF_API_TOKEN") or os.getenv("HUGGINGFACE_TOKEN"):
        return "finbert-hf-api"
    return "keyword-enhanced"


__all__ = ["score_texts", "active_provider", "_keyword_score"]
