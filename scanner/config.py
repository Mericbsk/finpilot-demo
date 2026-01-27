"""Scanner Configuration Module

Centralized configuration for the stock scanner system.
All thresholds, settings, and tunable parameters are defined here.

NOTE: This module is maintained for backward compatibility.
      New code should use `from core.config import settings` instead.
"""

import warnings
from typing import Any, Dict

# Try to use new centralized config
_core_settings = None
try:
    from core.config import settings as _core_settings

    _USE_CORE_CONFIG = True
except ImportError:
    _USE_CORE_CONFIG = False

# ✨ Default threshold settings (Normal mode)
DEFAULT_SETTINGS: Dict[str, Any] = {
    "vol_multiplier": 1.5,  # Volume spike multiplier
    "momentum_pct": 2.0,  # 3-day momentum percentage
    "trend_gap_pct": 3.0,  # EMA50-EMA200 gap percentage
    "min_alignment_ratio": 0.75,  # Timeframe alignment minimum
    "min_momentum_ratio": 0.6,  # Momentum confluence minimum
    "min_signal_score": 3,  # Minimum signal score
    "min_filter_score": 2,  # Minimum filter score
    "min_price": 2.0,  # Liquidity floor: minimum price ($)
    "min_avg_vol": 300000,  # Liquidity floor: 10-day average volume
    "max_signal_alerts": 3,  # Max alerts per run
    "auto_adjust": True,  # Dividend/split adjusted prices
    "prepost": False,  # Include pre/after-hours
    # Momentum analysis settings
    "momentum_windows": [1, 3, 5],
    "momentum_baseline_window": 60,
    "momentum_z_threshold": 1.5,
    "momentum_dynamic_enabled": True,
    "momentum_dynamic_window": 60,
    "momentum_dynamic_quantile": 0.975,
    "momentum_dynamic_alpha": 0.6,
    "momentum_dynamic_min": 1.1,
    "momentum_dynamic_max": 3.0,
    # Segment-based thresholds by liquidity
    "momentum_segment_thresholds": {
        "high_liquidity": 2.0,
        "mid_liquidity": 1.6,
        "low_liquidity": 1.4,
    },
    "momentum_liquidity_breakpoints": {
        "high": 1_000_000,
        "low": 300_000,
    },
}

# ⚡ Aggressive mode overrides (relaxed thresholds for more signals)
AGGRESSIVE_OVERRIDES: Dict[str, Any] = {
    "vol_multiplier": 1.3,
    "momentum_pct": 1.2,
    "trend_gap_pct": 2.2,
    "min_alignment_ratio": 0.67,
    "min_momentum_ratio": 0.5,
    "min_signal_score": 2,
    "min_filter_score": 1,
    "min_price": 1.5,
    "min_avg_vol": 200_000,
    "momentum_z_threshold": 1.2,
}

# Global settings instance - can be modified at runtime
SETTINGS = DEFAULT_SETTINGS.copy()


def apply_aggressive_mode() -> None:
    """Apply aggressive overrides to current settings."""
    global SETTINGS
    SETTINGS = DEFAULT_SETTINGS.copy()
    SETTINGS.update(AGGRESSIVE_OVERRIDES)


def reset_to_default() -> None:
    """Reset settings to default values."""
    global SETTINGS
    SETTINGS = DEFAULT_SETTINGS.copy()


def get_setting(key: str, default: Any = None) -> Any:
    """Get a setting value safely.

    Falls back to core.config if available.
    """
    # Try core config first for common settings
    if _USE_CORE_CONFIG and _core_settings is not None:
        core_mapping = {
            "min_price": _core_settings.scanner.min_price,
            "rsi_oversold": _core_settings.scanner.rsi_oversold,
            "rsi_overbought": _core_settings.scanner.rsi_overbought,
            "volume_surge_threshold": _core_settings.scanner.volume_surge_threshold,
        }
        if key in core_mapping:
            return core_mapping[key]

    return SETTINGS.get(key, default)
