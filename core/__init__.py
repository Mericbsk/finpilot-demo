"""
FinPilot Core Infrastructure
=============================

Merkezi altyapı modülleri:
- config: Pydantic Settings ile merkezi konfigürasyon
- exceptions: Standart exception hiyerarşisi
- cache: Multi-layer cache sistemi
- logging: Structured logging
- validation: Input validation models
- session_state: Type-safe session state management
- i18n: Internationalization support
- backtest: Historical strategy backtesting engine
- plugins: Modular plugin architecture
- websocket_feeds: Real-time price feeds
- social: Social trading and signal sharing

Author: FinPilot Team
Version: 1.7.0

NOTE: Most modules are lazy-loaded via __getattr__ to keep dashboard startup fast.
      Only config and exceptions are loaded eagerly.
"""

import importlib as _importlib

# ---------------------------------------------------------------------------
# Lightweight imports — loaded eagerly (no heavy deps like pandas/streamlit)
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Everything else — lazy-loaded on first access
# ---------------------------------------------------------------------------
_LAZY_MODULES = {
    # cache
    "cache_manager": "core.cache",
    "cached": "core.cache",
    # logging
    "configure_logging": "core.logging",
    "get_logger": "core.logging",
    # validation
    "LoginRequest": "core.validation",
    "PositionSize": "core.validation",
    "PriceTarget": "core.validation",
    "RegisterRequest": "core.validation",
    "ScanRequest": "core.validation",
    "SignalFilter": "core.validation",
    "TickerList": "core.validation",
    "TickerSymbol": "core.validation",
    "UserSettingsInput": "core.validation",
    # session_state
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
    # i18n
    "DEFAULT_LANGUAGE": "core.i18n",
    "SUPPORTED_LANGUAGES": "core.i18n",
    "Language": "core.i18n",
    "get_language": "core.i18n",
    "localized_currency": "core.i18n",
    "localized_date": "core.i18n",
    "localized_number": "core.i18n",
    "render_language_selector": "core.i18n",
    "render_language_toggle": "core.i18n",
    "set_language": "core.i18n",
    "t": "core.i18n",
    "tn": "core.i18n",
    # backtest
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
    # plugins
    "BuiltinHooks": "core.plugins",
    "DataSourcePlugin": "core.plugins",
    "HookPriority": "core.plugins",
    "IndicatorPlugin": "core.plugins",
    "Plugin": "core.plugins",
    "PluginInfo": "core.plugins",
    "PluginManager": "core.plugins",
    "PluginStatus": "core.plugins",
    "StrategyPlugin": "core.plugins",
    "emit_hook": "core.plugins",
    "get_plugin_manager": "core.plugins",
    "hook": "core.plugins",
    "register_plugin": "core.plugins",
    # websocket_feeds
    "BarMessage": "core.websocket_feeds",
    "FeedConfig": "core.websocket_feeds",
    "FeedStatus": "core.websocket_feeds",
    "FinnhubFeed": "core.websocket_feeds",
    "MockFeed": "core.websocket_feeds",
    "PolygonFeed": "core.websocket_feeds",
    "QuoteMessage": "core.websocket_feeds",
    "TradeMessage": "core.websocket_feeds",
    "WebSocketFeed": "core.websocket_feeds",
    "create_feed": "core.websocket_feeds",
    "list_providers": "core.websocket_feeds",
    # social
    "FeedItem": "core.social",
    "FeedItemType": "core.social",
    "LeaderboardEntry": "core.social",
    "LeaderboardType": "core.social",
    "PerformanceMetrics": "core.social",
    "PublicSignal": "core.social",
    "SignalDirection": "core.social",
    "SignalStatus": "core.social",
    "SocialHub": "core.social",
    "Trader": "core.social",
    "TraderTier": "core.social",
    "get_social_hub": "core.social",
}


def __getattr__(name: str):
    """Lazy-load heavy submodule symbols on first access."""
    if name in _LAZY_MODULES:
        mod = _importlib.import_module(_LAZY_MODULES[name])
        return getattr(mod, name)
    raise AttributeError(f"module 'core' has no attribute {name!r}")


__all__ = [
    # Config
    "settings",
    "Settings",
    # Exceptions
    "FinPilotError",
    "ConfigError",
    "DataError",
    "AuthError",
    "MarketError",
    "ModelError",
    "CacheError",
    # Cache
    "cache_manager",
    "cached",
    # Logging
    "get_logger",
    "configure_logging",
    # Validation
    "TickerSymbol",
    "TickerList",
    "ScanRequest",
    "UserSettingsInput",
    "LoginRequest",
    "RegisterRequest",
    "PriceTarget",
    "PositionSize",
    "SignalFilter",
    # Session State (Faz 2)
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
    # i18n (Faz 3)
    "Language",
    "SUPPORTED_LANGUAGES",
    "DEFAULT_LANGUAGE",
    "t",
    "tn",
    "get_language",
    "set_language",
    "render_language_selector",
    "render_language_toggle",
    "localized_number",
    "localized_currency",
    "localized_date",
    # Backtest (Faz 3) — lazy
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
    # Plugins (Faz 3) — lazy
    "PluginStatus",
    "HookPriority",
    "PluginInfo",
    "Plugin",
    "StrategyPlugin",
    "IndicatorPlugin",
    "DataSourcePlugin",
    "hook",
    "BuiltinHooks",
    "PluginManager",
    "get_plugin_manager",
    "register_plugin",
    "emit_hook",
    # WebSocket Feeds (Faz 3) — lazy
    "FeedStatus",
    "TradeMessage",
    "QuoteMessage",
    "BarMessage",
    "FeedConfig",
    "WebSocketFeed",
    "PolygonFeed",
    "FinnhubFeed",
    "MockFeed",
    "create_feed",
    "list_providers",
    # Social Trading (Faz 3) — lazy
    "SignalDirection",
    "SignalStatus",
    "TraderTier",
    "LeaderboardType",
    "FeedItemType",
    "PerformanceMetrics",
    "PublicSignal",
    "Trader",
    "LeaderboardEntry",
    "FeedItem",
    "SocialHub",
    "get_social_hub",
]

__version__ = "1.7.0"
