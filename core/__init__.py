"""
FinPilot Core Infrastructure
=============================

Lean infra: config, exceptions, cache, logging, session, backtest, tracing.
Experimental modules (i18n, social, plugins, validation, websocket_feeds)
moved to archive/core_legacy/ — they had no production callers (audit 2026-05).
"""

import importlib as _importlib

from core.config import Settings, settings
from core.exceptions import (
    AuthError,
    CacheError,
    ConfigError,
    DataError,
    FinPilotError,
    MarketError,
    ModelError,
)

_LAZY_MODULES = {
    "cache_manager": "core.cache",
    "cached": "core.cache",
    "configure_logging": "core.logging",
    "get_logger": "core.logging",
    "AuthState": "core.session_state",
    "NavigationState": "core.session_state",
    "ScanState": "core.session_state",
    "ScanStatus": "core.session_state",
    "SessionState": "core.session_state",
    "Theme": "core.session_state",
    "UserPreferences": "core.session_state",
    "ViewMode": "core.session_state",
    "WatchlistState": "core.session_state",
    "get_current_user": "core.session_state",
    "get_scan_results": "core.session_state",
    "get_session": "core.session_state",
    "has_scan_results": "core.session_state",
    "init_session": "core.session_state",
    "is_authenticated": "core.session_state",
    "is_scan_in_progress": "core.session_state",
    "migrate_legacy_session_state": "core.session_state",
    "reset_session": "core.session_state",
    "Backtest": "core.backtest",
    "BacktestConfig": "core.backtest",
    "BacktestResult": "core.backtest",
    "MomentumStrategy": "core.backtest",
    "Portfolio": "core.backtest",
    "Signal": "core.backtest",
    "Strategy": "core.backtest",
    "Trade": "core.backtest",
    "TradeDirection": "core.backtest",
    "TradeStatus": "core.backtest",
    "TrendFollowingStrategy": "core.backtest",
    "compare_strategies": "core.backtest",
}


def __getattr__(name: str):
    if name in _LAZY_MODULES:
        mod = _importlib.import_module(_LAZY_MODULES[name])
        return getattr(mod, name)
    raise AttributeError(f"module 'core' has no attribute {name!r}")


__all__ = [
    "settings",
    "Settings",
    "FinPilotError",
    "ConfigError",
    "DataError",
    "AuthError",
    "MarketError",
    "ModelError",
    "CacheError",
    "cache_manager",
    "cached",
    "get_logger",
    "configure_logging",
    "ScanStatus",
    "ViewMode",
    "Theme",
    "SessionState",
    "ScanState",
    "UserPreferences",
    "WatchlistState",
    "NavigationState",
    "AuthState",
    "get_session",
    "init_session",
    "reset_session",
    "migrate_legacy_session_state",
    "is_scan_in_progress",
    "get_scan_results",
    "has_scan_results",
    "is_authenticated",
    "get_current_user",
    "TradeDirection",
    "TradeStatus",
    "Trade",
    "Signal",
    "Strategy",
    "MomentumStrategy",
    "TrendFollowingStrategy",
    "Portfolio",
    "BacktestConfig",
    "Backtest",
    "BacktestResult",
    "compare_strategies",
]

__version__ = "1.8.0"
