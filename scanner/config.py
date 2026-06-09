"""Scanner Configuration Module

Centralized configuration for the stock scanner system.
All thresholds, settings, and tunable parameters are defined here.

NOTE: This module is maintained for backward compatibility.
      New code should use `from core.config import settings` instead.
"""

from typing import Any

# Try to use new centralized config
_core_settings = None
try:
    from core.config import settings as _core_settings

    _USE_CORE_CONFIG = True
except ImportError:
    _USE_CORE_CONFIG = False

# ✨ Default threshold settings (Normal mode)
DEFAULT_SETTINGS: dict[str, Any] = {
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
AGGRESSIVE_OVERRIDES: dict[str, Any] = {
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


# ── Known-delisted symbols (acquired/merged/bankrupt) ──────────────────────────
# Add symbols here to permanently exclude them from scanning.
# Format: {TICKER: "reason"} — reason shown in logs at INFO level.
DELISTED_SYMBOLS: dict[str, str] = {
    # Cisco acquisitions
    "SPLK": "Acquired by Cisco (2024)",
    "SUMO": "Acquired by Cisco (2023)",
    # Vista Equity acquisitions
    "NEWR": "Acquired by Vista Equity (2024)",
    # Other M&A
    "SGEN": "Acquired by Pfizer (2024)",
    "LVGO": "Merged with Teladoc (2020)",
    "ONEM": "Acquired by Amazon (2023)",
    "MAXR": "Acquired by Advent (2023)",
    "ANTM": "Renamed to ELV (Elevance Health)",
    "WLTW": "Merged into AON/rebranded",
    "ATVI": "Acquired by Microsoft (2023)",
    # Bankrupt / liquidated
    "SBNY": "Signature Bank — bankrupt (2023)",
    "FFIE": "Faraday Future — liquidation risk",
    "RIDE": "Lordstown Motors — bankrupt (2023)",
    "NKLA": "Nikola — high delist risk",
    "GOEV": "Canoo — bankrupt (2024)",
    "FREYR": "Delisted (2024)",
    "FSR": "Fisker — bankrupt (2024)",
    "ARVL": "Arrival — delisted (2024)",
    "DCFC": "Tritium DCFC — delisted (2024)",
    "VORB": "Virgin Orbit — bankrupt (2023)",
    "ASTR": "Astra Space — delisted",
    # Acquisitions / mergers (others)
    "CLR": "Continental Resources — taken private (2022)",
    "HES": "Acquired by Chevron (2024)",
    "PXD": "Pioneer Natural Resources — acquired by Exxon (2024)",
    "MRO": "Marathon Oil — acquired by ConocoPhillips (2024)",
    "SWN": "Southwestern Energy — acquired by Chesapeake (2024)",
    "CMA": "Comerica — acquisition target",
    "ORCC": "Blue Owl Capital — rebranded",
    "VMW": "Acquired by Broadcom (2023)",
    "CTXS": "Citrix — acquired (2022)",
    "XLNX": "Acquired by AMD (2022)",
    "ATXS": "Astex Pharmaceuticals — delisted",
    "BLUE": "bluebird bio — delisted",
    "ACCD": "Accolade — taken private",
    "ADAP": "Adaptimmune — clinical stage",
    "ADVM": "Adverum — delisted",
    "AKRO": "Akero Therapeutics — delisted",
    "AMEH": "ApolloMed — delisted",
    "PTRA": "Proterra — bankrupt (2023)",
    "VERV": "Verve Therapeutics — acquired",
    "VLNC": "Valence Technology — inactive",
    "NOVA": "Sunnova Energy — bankrupt (2025)",
    "AMODW": "Warrant — not a stock",
    "AREBW": "Warrant — not a stock",
    "CMPO": "Compounders — inactive",
    "RNWWW": "Warrant",
    "RVSNW": "Warrant",
    "MOBBW": "Warrant",
    "GIPRW": "Warrant",
    "FGIWW": "Warrant",
    "WLDSW": "Warrant",
    "ESLGW": "Warrant",
    "SENEB": "Senior note — not equity",
    "WHLRL": "Wheeler REIT — delisted",
    # 2025-2026 delistings
    "EKSO": "Ekso Bionics — delisted (2026)",
    "ALIGN": "Not a valid ticker (possibly ALGN)",
    "FILTER": "Not a valid ticker",
    "SCORE": "Not a valid ticker",
    "INVALID_SYMBOL_XYZ": "Test/placeholder symbol",
    "BAERW": "Warrant — not equity",
    "QSIAW": "Warrant — not equity",
}

# Fast lookup set for O(1) membership tests
DELISTED_SYMBOLS_SET: frozenset[str] = frozenset(DELISTED_SYMBOLS.keys())


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
