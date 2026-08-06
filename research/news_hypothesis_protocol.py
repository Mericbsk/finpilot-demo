"""Pre-registered news-only research hypothesis for FinPilot.

This manifest is research-only. It does not authorize scanner, scoring, risk,
entry/exit, or publication changes.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NewsHypothesisProtocol:
    protocol_id: str
    hypothesis: str
    features: tuple[str, ...]
    targets: tuple[str, ...]
    windows_days: tuple[int, ...]
    cost_model_version: str
    cost_pct: float
    source_fields: tuple[str, ...]
    excluded_fields: tuple[str, ...]
    status: str = "proposed"

    def validate(self) -> None:
        if not self.protocol_id.strip():
            raise ValueError("protocol_id is required")
        if not self.hypothesis.strip():
            raise ValueError("hypothesis is required")
        if not self.features or not self.targets:
            raise ValueError("features and targets are required")
        if any(window < 1 for window in self.windows_days):
            raise ValueError("news windows must be positive")
        if not self.cost_model_version.strip() or self.cost_pct < 0:
            raise ValueError("valid cost model is required")
        if self.status not in {"proposed", "completed", "rejected"}:
            raise ValueError(f"unsupported status: {self.status}")


NEWS_HYPOTHESIS = NewsHypothesisProtocol(
    protocol_id="news-pre-scan-v1",
    hypothesis=(
        "News volume and centered polarity observed on or before scan_date "
        "may explain honest next-bar-open T+5/T+20 net returns."
    ),
    features=(
        "news_count_5d",
        "news_count_20d",
        "news_sentiment_5d",
        "news_sentiment_20d",
    ),
    targets=("c2c5_net", "c2c20_net"),
    windows_days=(5, 20),
    cost_model_version="fixed-round-trip-v1",
    cost_pct=0.5,
    source_fields=("article_date", "polarity"),
    excluded_fields=("headline", "publisher", "publication_timestamp", "event_type"),
)

NEWS_HYPOTHESIS.validate()
