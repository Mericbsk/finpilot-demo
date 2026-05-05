from __future__ import annotations

import sys
from copy import deepcopy
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scanner import config as scanner_config

from core.config import settings as core_settings


def _build_timeframe_frame(periods: int, freq: str, *, base_price: float = 100.0) -> pd.DataFrame:
    dates = pd.date_range(end="2025-04-18", periods=periods, freq=freq)
    close = np.linspace(base_price - 5, base_price + 5, periods)
    high = close + 1.0
    low = close - 1.0
    volume = np.full(periods, 1_200_000.0)

    df = pd.DataFrame(
        {
            "Open": close,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": volume,
        },
        index=dates,
    )
    df["ema50"] = df["Close"].ewm(span=min(50, periods)).mean()
    df["ema200"] = df["Close"].ewm(span=min(200, periods)).mean()
    df["rsi"] = 55.0
    df["atr"] = (df["High"] - df["Low"]).rolling(14).mean().bfill()
    df["macd_hist"] = 0.2
    df["vol_avg10"] = df["Volume"].rolling(10).mean().bfill()
    df["vol_med20"] = df["Volume"].rolling(20).median().bfill()
    return df


def _set_daily_score(df_1d: pd.DataFrame, *, score: int) -> pd.DataFrame:
    df = df_1d.copy()

    df.iloc[-1, df.columns.get_loc("rsi")] = 55.0
    df.iloc[-1, df.columns.get_loc("Volume")] = df.iloc[-1]["vol_med20"] * 1.4

    if score >= 3:
        df.iloc[-2, df.columns.get_loc("macd_hist")] = -0.1
        df.iloc[-1, df.columns.get_loc("macd_hist")] = 0.2
    else:
        df.iloc[-2, df.columns.get_loc("macd_hist")] = 0.3
        df.iloc[-1, df.columns.get_loc("macd_hist")] = 0.1

    return df


def _neutral_momentum_analysis() -> dict[str, object]:
    return {
        "metrics": [],
        "best": None,
        "positive": False,
        "negative": False,
        "dominant_zscore": 0.0,
        "dominant_return_pct": 0.0,
        "dominant_direction": 0,
        "z_threshold_effective": 1.5,
        "z_threshold_base": 1.5,
        "z_threshold_segment": None,
        "z_threshold_dynamic": None,
        "liquidity_segment": None,
        "baseline_window": 60,
        "dynamic_threshold_samples": 0,
    }


@pytest.fixture
def scanner_settings_guard():
    original_settings = deepcopy(scanner_config.SETTINGS)
    original_use_core = scanner_config._USE_CORE_CONFIG
    original_min_price = core_settings.scanner.min_price

    yield

    scanner_config.SETTINGS.clear()
    scanner_config.SETTINGS.update(original_settings)
    scanner_config._USE_CORE_CONFIG = original_use_core
    core_settings.scanner.min_price = original_min_price


@pytest.fixture
def baseline_prefetched_data() -> dict[str, pd.DataFrame]:
    return {
        "15m": _build_timeframe_frame(60, "15min"),
        "1h": _build_timeframe_frame(40, "1h"),
        "4h": _build_timeframe_frame(60, "4h"),
        "1d": _build_timeframe_frame(250, "D"),
    }


@pytest.fixture
def score_two_prefetched_data(
    baseline_prefetched_data: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    data = deepcopy(baseline_prefetched_data)
    data["1d"] = _set_daily_score(data["1d"], score=2)
    return data


@pytest.fixture
def score_three_prefetched_data(
    baseline_prefetched_data: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    data = deepcopy(baseline_prefetched_data)
    data["1d"] = _set_daily_score(data["1d"], score=3)
    return data


@pytest.fixture
def neutral_momentum_analysis() -> dict[str, object]:
    return _neutral_momentum_analysis()
