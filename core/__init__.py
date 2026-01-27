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
"""

from core.backtest import (
    Backtest,
    BacktestConfig,
    BacktestResult,
    MomentumStrategy,
    Portfolio,
    Signal,
    Strategy,
    Trade,
    TradeDirection,
    TradeStatus,
    TrendFollowingStrategy,
    compare_strategies,
)
from core.cache import cache_manager, cached
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
from core.i18n import (
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
    Language,
    get_language,
    localized_currency,
    localized_date,
    localized_number,
    render_language_selector,
    render_language_toggle,
    set_language,
    t,
    tn,
)
from core.logging import configure_logging, get_logger
from core.plugins import (
    BuiltinHooks,
    DataSourcePlugin,
    HookPriority,
    IndicatorPlugin,
    Plugin,
    PluginInfo,
    PluginManager,
    PluginStatus,
    StrategyPlugin,
    emit_hook,
    get_plugin_manager,
    hook,
    register_plugin,
)
from core.session_state import (  # Enums; Dataclasses; Functions; Convenience
    AuthState,
    NavigationState,
    ScanState,
    ScanStatus,
    SessionState,
    Theme,
    UserPreferences,
    ViewMode,
    WatchlistState,
    get_current_user,
    get_scan_results,
    get_session,
    has_scan_results,
    init_session,
    is_authenticated,
    is_scan_in_progress,
    migrate_legacy_session_state,
    reset_session,
)
from core.social import (
    FeedItem,
    FeedItemType,
    LeaderboardEntry,
    LeaderboardType,
    PerformanceMetrics,
    PublicSignal,
    SignalDirection,
    SignalStatus,
    SocialHub,
    Trader,
    TraderTier,
    get_social_hub,
)
from core.validation import (
    LoginRequest,
    PositionSize,
    PriceTarget,
    RegisterRequest,
    ScanRequest,
    SignalFilter,
    TickerList,
    TickerSymbol,
    UserSettingsInput,
)
from core.websocket_feeds import (
    BarMessage,
    FeedConfig,
    FeedStatus,
    FinnhubFeed,
    MockFeed,
    PolygonFeed,
    QuoteMessage,
    TradeMessage,
    WebSocketFeed,
    create_feed,
    list_providers,
)

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
    # Backtest (Faz 3)
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
    # Plugins (Faz 3)
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
    # WebSocket Feeds (Faz 3)
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
    # Social Trading (Faz 3)
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
