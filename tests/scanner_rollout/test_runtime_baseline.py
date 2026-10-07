from __future__ import annotations

import pytest
import scanner.evaluate as evaluate_module
from scanner import config as scanner_config
from scanner.evaluate import evaluate_symbol

from core.config import settings as core_settings


def test_effective_min_price_comes_from_core_config(scanner_settings_guard):
    scanner_config.reset_to_default()
    core_settings.scanner.min_price = 5.0

    assert scanner_config.SETTINGS["min_price"] == 2.0
    assert scanner_config.get_setting("min_price", 2.0) == 5.0


def test_aggressive_mode_does_not_change_effective_min_price(scanner_settings_guard):
    core_settings.scanner.min_price = 5.0

    scanner_config.apply_aggressive_mode()

    assert scanner_config.SETTINGS["min_price"] == 1.5
    assert scanner_config.get_setting("min_price", 2.0) == 5.0


@pytest.mark.parametrize("alignment_ratio", [0.65, 0.66, 1.0])
@pytest.mark.parametrize(
    ("prefetched_fixture", "expected_score", "expected_entry"),
    [
        ("score_two_prefetched_data", 2, False),
        ("score_three_prefetched_data", 3, True),
    ],
)
def test_runtime_gate_uses_score_three_not_alignment(
    scanner_settings_guard,
    monkeypatch,
    request,
    alignment_ratio,
    prefetched_fixture,
    expected_score,
    expected_entry,
):
    monkeypatch.setattr(
        evaluate_module, "check_timeframe_alignment", lambda *args: (False, alignment_ratio, [])
    )
    monkeypatch.setattr(evaluate_module, "check_momentum_confluence", lambda *args: (False, 0.0))

    result = evaluate_symbol("ALIGN", prefetched_data=request.getfixturevalue(prefetched_fixture))

    assert result is not None
    assert result["score"] == expected_score
    assert result["entry_ok"] is expected_entry


@pytest.mark.parametrize(
    ("prefetched_fixture", "expected_score", "expected_entry"),
    [
        ("score_two_prefetched_data", 2, False),
        ("score_three_prefetched_data", 3, True),
    ],
)
def test_min_signal_score_setting_does_not_change_runtime_gate(
    scanner_settings_guard,
    monkeypatch,
    request,
    prefetched_fixture,
    expected_score,
    expected_entry,
):
    monkeypatch.setattr(evaluate_module, "check_timeframe_alignment", lambda *args: (True, 1.0, []))
    monkeypatch.setattr(evaluate_module, "check_momentum_confluence", lambda *args: (False, 0.0))

    prefetched_data = request.getfixturevalue(prefetched_fixture)
    scanner_config.SETTINGS["min_signal_score"] = 3
    strict_result = evaluate_symbol("SCORE", prefetched_data=prefetched_data)

    scanner_config.SETTINGS["min_signal_score"] = 1
    relaxed_result = evaluate_symbol("SCORE", prefetched_data=prefetched_data)

    assert strict_result is not None
    assert relaxed_result is not None
    assert strict_result["score"] == expected_score
    assert relaxed_result["score"] == expected_score
    assert strict_result["entry_ok"] is expected_entry
    assert relaxed_result["entry_ok"] is expected_entry
