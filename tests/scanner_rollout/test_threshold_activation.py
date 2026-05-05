from __future__ import annotations

import pandas as pd
import scanner.evaluate as evaluate_module
from scanner import config as scanner_config
from scanner.evaluate import evaluate_symbol
from scanner.signals import (
    SETTINGS,
    analyze_price_momentum,
    check_momentum_confluence,
    check_timeframe_alignment,
)


def test_min_alignment_ratio_setting_is_ignored_by_alignment_function(scanner_settings_guard):
    df_1h = pd.DataFrame({"Close": list(range(30, 0, -1))})
    df_4h = pd.DataFrame({"Close": list(range(1, 61)), "ema50": [20.0] * 60})
    df_1d = pd.DataFrame({"Close": list(range(1, 251)), "ema200": [50.0] * 250})

    scanner_config.SETTINGS["min_alignment_ratio"] = 0.5
    aligned, ratio, _ = check_timeframe_alignment(df_1h, df_4h, df_1d)

    assert round(ratio, 2) == 0.67
    assert aligned is False


def test_min_momentum_ratio_setting_is_ignored_by_confluence_function(scanner_settings_guard):
    df_15m = pd.DataFrame({"rsi": [50.0] * 29 + [55.0], "macd_hist": [0.0] * 30})
    df_4h = pd.DataFrame({"rsi": [50.0] * 29 + [55.0], "macd_hist": [0.0] * 30})

    scanner_config.SETTINGS["min_momentum_ratio"] = 0.95
    has_confluence, ratio = check_momentum_confluence(df_15m, df_4h)

    assert ratio == 0.5
    assert has_confluence is True


def test_momentum_z_threshold_changes_momentum_analysis(scanner_settings_guard):
    close = pd.Series([100 + ((i % 5) - 2) * 0.1 + i * 0.01 for i in range(120)])
    close.iloc[-1] += 0.8
    df = pd.DataFrame({"Close": close, "vol_avg10": [1_000_000.0] * len(close)})

    original = SETTINGS.copy()
    SETTINGS["momentum_dynamic_enabled"] = False
    SETTINGS["momentum_segment_thresholds"] = {}
    SETTINGS["momentum_dynamic_min"] = 0.0
    SETTINGS["momentum_dynamic_max"] = 20.0

    SETTINGS["momentum_z_threshold"] = 10.0
    strict_result = analyze_price_momentum(df)

    SETTINGS["momentum_z_threshold"] = 2.0
    relaxed_result = analyze_price_momentum(df)

    SETTINGS.clear()
    SETTINGS.update(original)

    assert strict_result["dominant_zscore"] > 2.0
    assert strict_result["positive"] is False
    assert relaxed_result["positive"] is True


def test_min_filter_score_setting_does_not_change_entry_gate(
    scanner_settings_guard,
    monkeypatch,
    score_three_prefetched_data,
    neutral_momentum_analysis,
):
    monkeypatch.setattr(evaluate_module, "check_timeframe_alignment", lambda *args: (True, 1.0, []))
    monkeypatch.setattr(evaluate_module, "check_momentum_confluence", lambda *args: (False, 0.0))
    monkeypatch.setattr(evaluate_module, "check_volume_spike", lambda *args: False)
    monkeypatch.setattr(evaluate_module, "check_trend_strength", lambda *args: False)
    monkeypatch.setattr(
        evaluate_module, "analyze_price_momentum", lambda *args, **kwargs: neutral_momentum_analysis
    )

    scanner_config.SETTINGS["min_filter_score"] = 99
    strict_result = evaluate_symbol("FILTER", prefetched_data=score_three_prefetched_data)

    scanner_config.SETTINGS["min_filter_score"] = 0
    relaxed_result = evaluate_symbol("FILTER", prefetched_data=score_three_prefetched_data)

    assert strict_result is not None
    assert relaxed_result is not None
    assert strict_result["filter_score"] == 0
    assert relaxed_result["filter_score"] == 0
    assert strict_result["entry_ok"] is True
    assert relaxed_result["entry_ok"] is True
