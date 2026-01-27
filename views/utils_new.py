# -*- coding: utf-8 -*-
"""
FinPilot Views Utils - Backward Compatibility Layer
====================================================

Bu modül geriye dönük uyumluluk için korunmaktadır.
Tüm fonksiyonlar artık views/components/ altındaki modüllerden import edilmektedir.

Yeni kod için doğrudan views/components/ modüllerini kullanın:
    from views.components.chips import build_status_chip
    from views.components.cards import render_buyable_cards
    from views.components.helpers import format_decimal
"""

from views.components.cards import (
    render_buyable_cards,
    render_mobile_recommendation_cards,
    render_mobile_symbol_cards,
    render_signal_history_overview,
    render_symbol_snapshot,
)

# Re-export everything from components for backward compatibility
from views.components.chips import (
    build_regime_chip,
    build_risk_reward_chip,
    build_signal_strength_chip,
    build_status_chip,
    build_zscore_chip,
    compose_signal_chips,
)
from views.components.demo import get_demo_scan_results
from views.components.helpers import (
    HTML_TAG_RE,
    REGIME_HINT_CATALOG,
    SENTIMENT_HINT_CATALOG,
    WHITESPACE_RE,
    detect_symbol_column,
    extract_symbols_from_df,
    format_decimal,
    get_regime_hint,
    get_sentiment_hint,
    is_advanced_view,
    normalize_narrative,
    trigger_rerun,
)
from views.components.panels import render_progress_tracker, render_summary_panel
from views.components.research import get_gemini_research
from views.components.settings import load_settingscard_markup, render_settings_card
from views.components.tables import render_buyable_table

# Backward compatibility: DEMO_MODE_ENABLED flag
DEMO_MODE_ENABLED = True

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
    "REGIME_HINT_CATALOG",
    "SENTIMENT_HINT_CATALOG",
    "HTML_TAG_RE",
    "WHITESPACE_RE",
    # Research
    "get_gemini_research",
    # Settings
    "render_settings_card",
    "load_settingscard_markup",
    # Demo
    "get_demo_scan_results",
    # Flags
    "DEMO_MODE_ENABLED",
]
