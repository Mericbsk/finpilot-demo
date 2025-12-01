import pandas as pd
import pytest

from drl.analysis import (
    RegimeStats,
    build_narrative_payload,
    estimate_regime_success,
    summarize_alternative_signals,
)


def _sample_history():
    idx = pd.date_range("2025-01-01", periods=8, freq="H", tz="UTC")
    return pd.DataFrame(
        {
            "sentiment_score": [0.1, 0.1, 0.12, 0.2, 0.24, 0.28, 0.32, 0.36],
            "onchain_tx_volume": [100, 110, 105, 120, 135, 140, 155, 210],
        },
        index=idx,
    )


def test_summarize_alternative_signals_positive_momentum():
    sentiment, whale = summarize_alternative_signals(_sample_history())

    assert sentiment.strength.startswith("positive")
    assert "duygu skoru" in sentiment.description
    assert whale.strength.startswith("positive")
    assert "Balina cüzdanlarından" in whale.description


def test_build_narrative_payload_generates_exit_price():
    sentiment, whale = summarize_alternative_signals(_sample_history())
    regime = RegimeStats(name="trend", success_rate=0.75, max_drawdown=0.04)

    payload = build_narrative_payload(
        regime,
        sentiment,
        whale,
        current_price=40_000.0,
        max_allowed_drawdown=0.05,
    )

    assert payload.title_1 == "Neden hemen şimdi?"
    assert payload.title_2 == "En kötü senaryo ne?"
    assert payload.exit_price == 40_000.0 * (1 - 0.04)
    assert "trend" in payload.text_1
    assert "%4.0" in payload.text_2


def test_estimate_regime_success_handles_rewards():
    regimes = ["trend", "trend", "range", "trend"]
    rewards = [0.1, -0.2, 0.5, 0.0]
    stats = estimate_regime_success(regimes, rewards, "trend")

    assert stats.name == "trend"
    assert stats.success_rate == pytest.approx(2 / 3)
    assert stats.average_reward == pytest.approx((0.1 - 0.2 + 0.0) / 3)
