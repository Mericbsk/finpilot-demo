"""
FinPilot Views Components
=========================
Modüler UI bileşenleri.

Refactored from views/utils.py for better maintainability.
Lazy-loaded (Sprint P-) — sub-modules are imported on first attribute access
so that `import views.components` stays fast even in CLI / test contexts.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

# ------------------------------------------------------------------
# Mapping: attribute name → (sub-module dotted path, attribute name)
# ------------------------------------------------------------------
_LAZY_MAP: dict[str, tuple[str, str]] = {}

def _register(module: str, *names: str) -> None:
    """Helper to populate _LAZY_MAP for many names from one module."""
    for n in names:
        _LAZY_MAP[n] = (module, n)


_register(
    "views.components.cache",
    "CACHE_TTL_LONG", "CACHE_TTL_MEDIUM", "CACHE_TTL_SHORT",
    "cached_badge_html", "cached_compute_scores", "cached_filter_buyable",
    "cached_format_currency", "cached_format_number", "cached_format_percentage",
    "cached_progress_bar_html", "cached_regime_color_map", "cached_score_color",
    "clear_component_cache", "prepare_for_cache",
)
_register(
    "views.components.cards",
    "render_buyable_cards", "render_mobile_recommendation_cards",
    "render_mobile_symbol_cards", "render_signal_history_overview",
    "render_symbol_snapshot",
)
_register(
    "views.components.chips",
    "build_regime_chip", "build_risk_reward_chip", "build_signal_strength_chip",
    "build_status_chip", "build_zscore_chip", "compose_signal_chips",
)
_register("views.components.demo", "get_demo_scan_results")
_register(
    "views.components.export",
    "export_to_csv", "export_to_excel", "export_to_pdf",
    "render_export_button_row", "render_export_panel",
)
_register(
    "views.components.grid",
    "GRID_COMPACT", "GRID_FEATURED", "GRID_STANDARD", "GRID_WIDE",
    "GridConfig", "inject_grid_styles", "render_card_html",
    "render_grid_end", "render_grid_start", "render_metric_grid",
    "render_signal_cards_grid",
)
_register(
    "views.components.helpers",
    "BADGE_STYLE_BUY", "BADGE_STYLE_HOLD", "build_badge_html",
    "detect_symbol_column", "extract_symbols_from_df", "format_decimal",
    "format_timestamp_display", "get_badge_style", "get_regime_hint",
    "get_sentiment_hint", "is_advanced_view", "normalize_narrative",
    "trigger_rerun",
)
_register(
    "views.components.onboarding",
    "ONBOARDING_STEPS", "complete_onboarding", "get_onboarding_state",
    "render_feature_highlight", "render_onboarding_modal",
    "render_onboarding_sidebar_trigger", "render_quick_tips",
    "reset_onboarding", "should_show_onboarding", "skip_onboarding",
)
_register(
    "views.components.panels",
    "render_progress_tracker", "render_summary_panel",
)
_register("views.components.research", "get_gemini_research")
_register(
    "views.components.settings",
    "load_settingscard_markup", "render_settings_card",
)
_register("views.components.tables", "render_buyable_table")
_register(
    "views.components.watchlist",
    "get_watchlist_scan_symbols", "get_watchlist_symbols",
    "initialize_watchlist", "is_watchlist_scan_triggered",
    "render_watchlist_panel", "render_watchlist_sidebar",
)


# ------------------------------------------------------------------
# Lazy __getattr__ (PEP 562)
# ------------------------------------------------------------------

def __getattr__(name: str):
    if name in _LAZY_MAP:
        module_path, attr = _LAZY_MAP[name]
        mod = importlib.import_module(module_path)
        value = getattr(mod, attr)
        # Cache on the package so subsequent accesses are instant
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return list(__all__) + list(_LAZY_MAP.keys())


# ------------------------------------------------------------------
# TYPE_CHECKING: explicit imports for IDE autocompletion / mypy
# ------------------------------------------------------------------
if TYPE_CHECKING:
    from views.components.cache import (  # noqa: F401
        CACHE_TTL_LONG as CACHE_TTL_LONG,
        CACHE_TTL_MEDIUM as CACHE_TTL_MEDIUM,
        CACHE_TTL_SHORT as CACHE_TTL_SHORT,
        cached_badge_html as cached_badge_html,
        cached_compute_scores as cached_compute_scores,
        cached_filter_buyable as cached_filter_buyable,
        cached_format_currency as cached_format_currency,
        cached_format_number as cached_format_number,
        cached_format_percentage as cached_format_percentage,
        cached_progress_bar_html as cached_progress_bar_html,
        cached_regime_color_map as cached_regime_color_map,
        cached_score_color as cached_score_color,
        clear_component_cache as clear_component_cache,
        prepare_for_cache as prepare_for_cache,
    )
    from views.components.cards import (  # noqa: F401
        render_buyable_cards as render_buyable_cards,
        render_mobile_recommendation_cards as render_mobile_recommendation_cards,
        render_mobile_symbol_cards as render_mobile_symbol_cards,
        render_signal_history_overview as render_signal_history_overview,
        render_symbol_snapshot as render_symbol_snapshot,
    )
    from views.components.chips import (  # noqa: F401
        build_regime_chip as build_regime_chip,
        build_risk_reward_chip as build_risk_reward_chip,
        build_signal_strength_chip as build_signal_strength_chip,
        build_status_chip as build_status_chip,
        build_zscore_chip as build_zscore_chip,
        compose_signal_chips as compose_signal_chips,
    )
    from views.components.demo import get_demo_scan_results as get_demo_scan_results  # noqa: F401
    from views.components.export import (  # noqa: F401
        export_to_csv as export_to_csv,
        export_to_excel as export_to_excel,
        export_to_pdf as export_to_pdf,
        render_export_button_row as render_export_button_row,
        render_export_panel as render_export_panel,
    )
    from views.components.grid import (  # noqa: F401
        GRID_COMPACT as GRID_COMPACT,
        GRID_FEATURED as GRID_FEATURED,
        GRID_STANDARD as GRID_STANDARD,
        GRID_WIDE as GRID_WIDE,
        GridConfig as GridConfig,
        inject_grid_styles as inject_grid_styles,
        render_card_html as render_card_html,
        render_grid_end as render_grid_end,
        render_grid_start as render_grid_start,
        render_metric_grid as render_metric_grid,
        render_signal_cards_grid as render_signal_cards_grid,
    )
    from views.components.helpers import (  # noqa: F401
        BADGE_STYLE_BUY as BADGE_STYLE_BUY,
        BADGE_STYLE_HOLD as BADGE_STYLE_HOLD,
        build_badge_html as build_badge_html,
        detect_symbol_column as detect_symbol_column,
        extract_symbols_from_df as extract_symbols_from_df,
        format_decimal as format_decimal,
        format_timestamp_display as format_timestamp_display,
        get_badge_style as get_badge_style,
        get_regime_hint as get_regime_hint,
        get_sentiment_hint as get_sentiment_hint,
        is_advanced_view as is_advanced_view,
        normalize_narrative as normalize_narrative,
        trigger_rerun as trigger_rerun,
    )
    from views.components.onboarding import (  # noqa: F401
        ONBOARDING_STEPS as ONBOARDING_STEPS,
        complete_onboarding as complete_onboarding,
        get_onboarding_state as get_onboarding_state,
        render_feature_highlight as render_feature_highlight,
        render_onboarding_modal as render_onboarding_modal,
        render_onboarding_sidebar_trigger as render_onboarding_sidebar_trigger,
        render_quick_tips as render_quick_tips,
        reset_onboarding as reset_onboarding,
        should_show_onboarding as should_show_onboarding,
        skip_onboarding as skip_onboarding,
    )
    from views.components.panels import (  # noqa: F401
        render_progress_tracker as render_progress_tracker,
        render_summary_panel as render_summary_panel,
    )
    from views.components.research import get_gemini_research as get_gemini_research  # noqa: F401
    from views.components.settings import (  # noqa: F401
        load_settingscard_markup as load_settingscard_markup,
        render_settings_card as render_settings_card,
    )
    from views.components.tables import render_buyable_table as render_buyable_table  # noqa: F401
    from views.components.watchlist import (  # noqa: F401
        get_watchlist_scan_symbols as get_watchlist_scan_symbols,
        get_watchlist_symbols as get_watchlist_symbols,
        initialize_watchlist as initialize_watchlist,
        is_watchlist_scan_triggered as is_watchlist_scan_triggered,
        render_watchlist_panel as render_watchlist_panel,
        render_watchlist_sidebar as render_watchlist_sidebar,
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
