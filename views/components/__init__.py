# -*- coding: utf-8 -*-
"""
FinPilot Views Components
=========================
Modüler UI bileşenleri.

Refactored from views/utils.py for better maintainability.
"""

from views.components.cache import (
    CACHE_TTL_LONG,
    CACHE_TTL_MEDIUM,
    CACHE_TTL_SHORT,
    cached_badge_html,
    cached_compute_scores,
    cached_filter_buyable,
    cached_format_currency,
    cached_format_number,
    cached_format_percentage,
    cached_progress_bar_html,
    cached_regime_color_map,
    cached_score_color,
    clear_component_cache,
    prepare_for_cache,
)
from views.components.cards import (
    render_buyable_cards,
    render_mobile_recommendation_cards,
    render_mobile_symbol_cards,
    render_signal_history_overview,
    render_symbol_snapshot,
)
from views.components.chips import (
    build_regime_chip,
    build_risk_reward_chip,
    build_signal_strength_chip,
    build_status_chip,
    build_zscore_chip,
    compose_signal_chips,
)
from views.components.demo import get_demo_scan_results
from views.components.export import (
    export_to_csv,
    export_to_excel,
    export_to_pdf,
    render_export_button_row,
    render_export_panel,
)
from views.components.grid import (
    GRID_COMPACT,
    GRID_FEATURED,
    GRID_STANDARD,
    GRID_WIDE,
    GridConfig,
    inject_grid_styles,
    render_card_html,
    render_grid_end,
    render_grid_start,
    render_metric_grid,
    render_signal_cards_grid,
)
from views.components.helpers import (
    BADGE_STYLE_BUY,
    BADGE_STYLE_HOLD,
    build_badge_html,
    detect_symbol_column,
    extract_symbols_from_df,
    format_decimal,
    format_timestamp_display,
    get_badge_style,
    get_regime_hint,
    get_sentiment_hint,
    is_advanced_view,
    normalize_narrative,
    trigger_rerun,
)
from views.components.onboarding import (
    ONBOARDING_STEPS,
    complete_onboarding,
    get_onboarding_state,
    render_feature_highlight,
    render_onboarding_modal,
    render_onboarding_sidebar_trigger,
    render_quick_tips,
    reset_onboarding,
    should_show_onboarding,
    skip_onboarding,
)
from views.components.panels import render_progress_tracker, render_summary_panel
from views.components.research import get_gemini_research
from views.components.settings import load_settingscard_markup, render_settings_card
from views.components.tables import render_buyable_table
from views.components.watchlist import (
    get_watchlist_scan_symbols,
    get_watchlist_symbols,
    initialize_watchlist,
    is_watchlist_scan_triggered,
    render_watchlist_panel,
    render_watchlist_sidebar,
)

__all__ = [
    # Chips
    "build_status_chip",
    "build_zscore_chip",
    "build_signal_strength_chip",
    "build_regime_chip",
    "build_risk_reward_chip",
    "compose_signal_chips",
    # Cards
    "render_buyable_cards",
    "render_symbol_snapshot",
    "render_signal_history_overview",
    "render_mobile_symbol_cards",
    "render_mobile_recommendation_cards",
    # Tables
    "render_buyable_table",
    # Panels
    "render_summary_panel",
    "render_progress_tracker",
    # Helpers
    "trigger_rerun",
    "is_advanced_view",
    "normalize_narrative",
    "format_decimal",
    "get_regime_hint",
    "get_sentiment_hint",
    "detect_symbol_column",
    "extract_symbols_from_df",
    "build_badge_html",
    "format_timestamp_display",
    "get_badge_style",
    "BADGE_STYLE_BUY",
    "BADGE_STYLE_HOLD",
    # Research
    "get_gemini_research",
    # Settings
    "render_settings_card",
    "load_settingscard_markup",
    # Demo
    "get_demo_scan_results",
    # Watchlist
    "render_watchlist_panel",
    "render_watchlist_sidebar",
    "get_watchlist_symbols",
    "is_watchlist_scan_triggered",
    "get_watchlist_scan_symbols",
    "initialize_watchlist",
    # Export
    "export_to_csv",
    "export_to_excel",
    "export_to_pdf",
    "render_export_panel",
    "render_export_button_row",
    # Cache
    "CACHE_TTL_SHORT",
    "CACHE_TTL_MEDIUM",
    "CACHE_TTL_LONG",
    "cached_compute_scores",
    "cached_filter_buyable",
    "cached_regime_color_map",
    "cached_score_color",
    "cached_badge_html",
    "cached_progress_bar_html",
    "cached_format_number",
    "cached_format_currency",
    "cached_format_percentage",
    "prepare_for_cache",
    "clear_component_cache",
    # Grid
    "GridConfig",
    "GRID_COMPACT",
    "GRID_STANDARD",
    "GRID_WIDE",
    "GRID_FEATURED",
    "inject_grid_styles",
    "render_grid_start",
    "render_grid_end",
    "render_card_html",
    "render_signal_cards_grid",
    "render_metric_grid",
    # Onboarding
    "ONBOARDING_STEPS",
    "should_show_onboarding",
    "render_onboarding_modal",
    "render_onboarding_sidebar_trigger",
    "render_quick_tips",
    "render_feature_highlight",
    "complete_onboarding",
    "skip_onboarding",
    "reset_onboarding",
    "get_onboarding_state",
]
