# scanner package - Modular stock scanning system
# Refactored from monolithic scanner.py for better maintainability

import os

# Import evaluate functions from main scanner.py (legacy compatibility)
# These are defined in the root scanner.py file
import sys

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
    signal_score_row,
)

# Get the parent directory to import from scanner.py (the file, not this package)
_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_scanner_file = os.path.join(_parent_dir, "scanner.py")

# Load evaluate functions from scanner.py file
if os.path.exists(_scanner_file):
    import importlib.util

    _spec = importlib.util.spec_from_file_location("scanner_main", _scanner_file)
    _scanner_module = importlib.util.module_from_spec(_spec)
    # Don't execute yet - just import the functions we need after package is loaded

    # Lazy import to avoid circular dependency
    def _get_evaluate_symbol():
        if "_scanner_module_loaded" not in globals():
            _spec.loader.exec_module(_scanner_module)
            globals()["_scanner_module_loaded"] = True
        return _scanner_module.evaluate_symbol

    def _get_evaluate_symbols_parallel():
        if "_scanner_module_loaded" not in globals():
            _spec.loader.exec_module(_scanner_module)
            globals()["_scanner_module_loaded"] = True
        return _scanner_module.evaluate_symbols_parallel


# Wrapper functions
def evaluate_symbol(symbol, kelly_fraction=0.5, prefetched_data=None):
    """Evaluate a single symbol. Wrapper for scanner.py evaluate_symbol."""
    return _get_evaluate_symbol()(symbol, kelly_fraction, prefetched_data)


def evaluate_symbols_parallel(
    symbols, kelly_fraction=0.5, progress_callback=None, use_prefetch=True
):
    """Evaluate multiple symbols in parallel. Wrapper for scanner.py evaluate_symbols_parallel."""
    return _get_evaluate_symbols_parallel()(
        symbols, kelly_fraction, progress_callback, use_prefetch
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
    # Evaluation (from scanner.py)
    "evaluate_symbol",
    "evaluate_symbols_parallel",
]
