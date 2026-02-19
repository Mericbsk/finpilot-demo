# scanner package - Modular stock scanning system
# Refactored from monolithic scanner.py for better maintainability
# Sprint 2 B3: evaluate functions moved to scanner/evaluate.py

from .config import AGGRESSIVE_OVERRIDES, DEFAULT_SETTINGS, SETTINGS
from .data_fetcher import (  # Parallel fetching (Faz 2 Performance)
    CACHE_TTL_SECONDS,
    DEFAULT_TIMEFRAMES,
    fetch,
    fetch_multi_timeframe,
    fetch_symbols_batch,
    fetch_with_indicators,
    get_market_regime_status,
    load_symbols,
    prefetch_symbols_multi_timeframe,
)
from .evaluate import (
    CURRENT_MARKET_STATUS,
    STRATEGY_PARAMS,
    calculate_risk_management,
    evaluate_symbol,
    evaluate_symbols_parallel,
)
from .indicators import add_indicators, atr, bbands, ema, macd_hist, rsi
from .signals import (
    analyze_price_momentum,
    build_explanation,
    build_reason,
    check_momentum_confluence,
    check_price_momentum,
    check_timeframe_alignment,
    check_trend_strength,
    check_volume_spike,
    compute_recommendation_score,
    compute_recommendation_strength,
    safe_float,
    signal_score_row,
)

__all__ = [
    # Indicators
    "ema",
    "rsi",
    "macd_hist",
    "bbands",
    "atr",
    "add_indicators",
    # Signals
    "check_volume_spike",
    "check_price_momentum",
    "check_trend_strength",
    "check_timeframe_alignment",
    "check_momentum_confluence",
    "signal_score_row",
    "compute_recommendation_score",
    "compute_recommendation_strength",
    "build_explanation",
    "build_reason",
    "analyze_price_momentum",
    "safe_float",
    # Data (Standard)
    "fetch",
    "load_symbols",
    "get_market_regime_status",
    "fetch_with_indicators",
    # Data (Parallel - Faz 2 Performance)
    "fetch_multi_timeframe",
    "fetch_symbols_batch",
    "prefetch_symbols_multi_timeframe",
    "DEFAULT_TIMEFRAMES",
    "CACHE_TTL_SECONDS",
    # Config
    "SETTINGS",
    "DEFAULT_SETTINGS",
    "AGGRESSIVE_OVERRIDES",
    # Evaluation (scanner.evaluate)
    "evaluate_symbol",
    "evaluate_symbols_parallel",
    "calculate_risk_management",
    "CURRENT_MARKET_STATUS",
    "STRATEGY_PARAMS",
]
