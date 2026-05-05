from __future__ import annotations

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


def test_score_two_requires_alignment_ratio_at_or_above_point_66(
    scanner_settings_guard,
    monkeypatch,
    score_two_prefetched_data,
):
    monkeypatch.setattr(
        evaluate_module, "check_timeframe_alignment", lambda *args: (False, 0.65, [])
    )
    monkeypatch.setattr(evaluate_module, "check_momentum_confluence", lambda *args: (False, 0.0))

    blocked = evaluate_symbol("ALIGN", prefetched_data=score_two_prefetched_data)

    monkeypatch.setattr(
        evaluate_module, "check_timeframe_alignment", lambda *args: (False, 0.66, [])
    )

    allowed = evaluate_symbol("ALIGN", prefetched_data=score_two_prefetched_data)

    assert blocked is not None
    assert allowed is not None
    assert blocked["score"] == 2
    assert allowed["score"] == 2
    assert blocked["entry_ok"] is False
    assert allowed["entry_ok"] is True


def test_min_signal_score_setting_does_not_change_runtime_gate(
    scanner_settings_guard,
    monkeypatch,
    score_two_prefetched_data,
):
    monkeypatch.setattr(evaluate_module, "check_timeframe_alignment", lambda *args: (True, 1.0, []))
    monkeypatch.setattr(evaluate_module, "check_momentum_confluence", lambda *args: (False, 0.0))

    scanner_config.SETTINGS["min_signal_score"] = 3
    strict_result = evaluate_symbol("SCORE", prefetched_data=score_two_prefetched_data)

    scanner_config.SETTINGS["min_signal_score"] = 1
    relaxed_result = evaluate_symbol("SCORE", prefetched_data=score_two_prefetched_data)

    assert strict_result is not None
    assert relaxed_result is not None
    assert strict_result["score"] == 2
    assert relaxed_result["score"] == 2
    assert strict_result["entry_ok"] is True
    assert relaxed_result["entry_ok"] is True
