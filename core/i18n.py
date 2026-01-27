# -*- coding: utf-8 -*-
"""
FinPilot Internationalization (i18n) System
============================================

Professional translation infrastructure with:
- Type-safe translation keys
- Lazy loading of translation files
- Pluralization support
- Variable interpolation
- Fallback chain (requested → default → key)

Usage:
    from core.i18n import t, set_language, get_language, SUPPORTED_LANGUAGES

    # Get translation
    text = t("dashboard.title")

    # With variables
    text = t("scan.results", count=42)

    # With pluralization
    text = t("items.count", n=5)  # Returns plural form
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import streamlit as st

# ============================================
# 🌍 Language Configuration
# ============================================


class Language(str, Enum):
    """Supported languages."""

    TURKISH = "tr"
    ENGLISH = "en"
    GERMAN = "de"


DEFAULT_LANGUAGE = Language.TURKISH
SUPPORTED_LANGUAGES = {
    Language.TURKISH: {"name": "Türkçe", "flag": "🇹🇷", "rtl": False},
    Language.ENGLISH: {"name": "English", "flag": "🇺🇸", "rtl": False},
    Language.GERMAN: {"name": "Deutsch", "flag": "🇩🇪", "rtl": False},
}

# Session state key
I18N_LANGUAGE_KEY = "finpilot_language"


# ============================================
# 📚 Translation Dictionaries
# ============================================

# Core translations - embedded for fast access
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "tr": {
        # Navigation
        "nav.home": "Ana Sayfa",
        "nav.scanner": "Tarayıcı",
        "nav.signals": "Sinyaller",
        "nav.watchlist": "İzleme Listesi",
        "nav.ai_lab": "AI Laboratuvarı",
        "nav.settings": "Ayarlar",
        "nav.help": "Yardım",
        # Dashboard
        "dashboard.title": "FinPilot Kontrol Paneli",
        "dashboard.subtitle": "Yapay Zeka Destekli Hisse Analizi",
        "dashboard.market_pulse": "Piyasa Nabzı",
        "dashboard.quick_settings": "Hızlı Ayarlar",
        "dashboard.aggressive_mode": "Agresif Mod",
        "dashboard.portfolio_size": "Portföy Büyüklüğü",
        "dashboard.risk_percent": "Risk Yüzdesi",
        # Scanner
        "scan.title": "Piyasa Tarayıcısı",
        "scan.start": "Taramayı Başlat",
        "scan.restart": "Yeniden Başlat",
        "scan.stop": "Durdur",
        "scan.loading": "Tarama yapılıyor...",
        "scan.completed": "Tarama tamamlandı",
        "scan.results": "{count} sembol analiz edildi",
        "scan.no_results": "Sonuç bulunamadı",
        "scan.symbols": "Semboller",
        "scan.buyable": "Alınabilir",
        "scan.clear_cache": "Önbelleği Temizle",
        "scan.load_csv": "CSV Yükle",
        # Signals
        "signal.buy": "AL",
        "signal.sell": "SAT",
        "signal.hold": "BEKLE",
        "signal.strong_buy": "GÜÇLÜ AL",
        "signal.strong_sell": "GÜÇLÜ SAT",
        "signal.neutral": "NÖTR",
        "signal.strength": "Sinyal Gücü",
        "signal.target": "Hedef",
        "signal.stop_loss": "Stop Loss",
        "signal.take_profit": "Kar Al",
        "signal.risk_reward": "Risk/Ödül",
        # Regime
        "regime.bull": "Boğa",
        "regime.bear": "Ayı",
        "regime.trend": "Trend",
        "regime.range": "Yatay",
        "regime.sideways": "Yatay",
        "regime.neutral": "Nötr",
        # Watchlist
        "watchlist.title": "İzleme Listem",
        "watchlist.add": "Ekle",
        "watchlist.remove": "Kaldır",
        "watchlist.clear": "Temizle",
        "watchlist.empty": "Liste boş",
        "watchlist.scan": "Listeyi Tara",
        "watchlist.export": "Dışa Aktar",
        "watchlist.popular": "Popüler Semboller",
        # Export
        "export.title": "Dışa Aktar",
        "export.csv": "CSV İndir",
        "export.excel": "Excel İndir",
        "export.pdf": "PDF İndir",
        "export.options": "Dışa Aktarma Seçenekleri",
        "export.all_columns": "Tüm sütunları dahil et",
        "export.buyable_only": "Sadece alınabilir sembolleri dahil et",
        # AI Lab
        "ai.title": "AI Laboratuvarı",
        "ai.analyzing": "Analiz ediliyor...",
        "ai.deep_analysis": "Derin Analiz",
        "ai.research": "Araştırma",
        "ai.news": "Haberler",
        "ai.sentiment": "Duyarlılık",
        "ai.recommendation": "Öneri",
        # Onboarding
        "onboard.welcome": "FinPilot'a Hoş Geldiniz!",
        "onboard.next": "İleri",
        "onboard.back": "Geri",
        "onboard.skip": "Atla",
        "onboard.finish": "Başla!",
        "onboard.step": "Adım {current}/{total}",
        # Settings
        "settings.title": "Ayarlar",
        "settings.language": "Dil",
        "settings.theme": "Tema",
        "settings.notifications": "Bildirimler",
        "settings.telegram": "Telegram Entegrasyonu",
        "settings.save": "Kaydet",
        "settings.reset": "Sıfırla",
        # Common
        "common.loading": "Yükleniyor...",
        "common.error": "Hata",
        "common.success": "Başarılı",
        "common.warning": "Uyarı",
        "common.info": "Bilgi",
        "common.confirm": "Onayla",
        "common.cancel": "İptal",
        "common.save": "Kaydet",
        "common.delete": "Sil",
        "common.edit": "Düzenle",
        "common.close": "Kapat",
        "common.search": "Ara",
        "common.filter": "Filtrele",
        "common.sort": "Sırala",
        "common.refresh": "Yenile",
        "common.download": "İndir",
        "common.upload": "Yükle",
        "common.copy": "Kopyala",
        "common.share": "Paylaş",
        "common.total": "Toplam",
        "common.average": "Ortalama",
        "common.last_update": "Son Güncelleme",
        "common.version": "Versiyon",
        # Time
        "time.now": "Şimdi",
        "time.today": "Bugün",
        "time.yesterday": "Dün",
        "time.days_ago": "{n} gün önce",
        "time.hours_ago": "{n} saat önce",
        "time.minutes_ago": "{n} dakika önce",
        # Errors
        "error.generic": "Bir hata oluştu",
        "error.network": "Ağ hatası",
        "error.no_data": "Veri bulunamadı",
        "error.invalid_input": "Geçersiz giriş",
        "error.try_again": "Lütfen tekrar deneyin",
        # Tips
        "tip.aggressive": "Agresif Mod daha fazla sinyal üretir",
        "tip.watchlist": "İzleme listesini CSV olarak dışa aktarabilirsiniz",
        "tip.ai_lab": "Derin analiz için AI Lab'ı kullanın",
    },
    "en": {
        # Navigation
        "nav.home": "Home",
        "nav.scanner": "Scanner",
        "nav.signals": "Signals",
        "nav.watchlist": "Watchlist",
        "nav.ai_lab": "AI Lab",
        "nav.settings": "Settings",
        "nav.help": "Help",
        # Dashboard
        "dashboard.title": "FinPilot Dashboard",
        "dashboard.subtitle": "AI-Powered Stock Analysis",
        "dashboard.market_pulse": "Market Pulse",
        "dashboard.quick_settings": "Quick Settings",
        "dashboard.aggressive_mode": "Aggressive Mode",
        "dashboard.portfolio_size": "Portfolio Size",
        "dashboard.risk_percent": "Risk Percentage",
        # Scanner
        "scan.title": "Market Scanner",
        "scan.start": "Start Scan",
        "scan.restart": "Restart",
        "scan.stop": "Stop",
        "scan.loading": "Scanning...",
        "scan.completed": "Scan completed",
        "scan.results": "{count} symbols analyzed",
        "scan.no_results": "No results found",
        "scan.symbols": "Symbols",
        "scan.buyable": "Buyable",
        "scan.clear_cache": "Clear Cache",
        "scan.load_csv": "Load CSV",
        # Signals
        "signal.buy": "BUY",
        "signal.sell": "SELL",
        "signal.hold": "HOLD",
        "signal.strong_buy": "STRONG BUY",
        "signal.strong_sell": "STRONG SELL",
        "signal.neutral": "NEUTRAL",
        "signal.strength": "Signal Strength",
        "signal.target": "Target",
        "signal.stop_loss": "Stop Loss",
        "signal.take_profit": "Take Profit",
        "signal.risk_reward": "Risk/Reward",
        # Regime
        "regime.bull": "Bull",
        "regime.bear": "Bear",
        "regime.trend": "Trend",
        "regime.range": "Range",
        "regime.sideways": "Sideways",
        "regime.neutral": "Neutral",
        # Watchlist
        "watchlist.title": "My Watchlist",
        "watchlist.add": "Add",
        "watchlist.remove": "Remove",
        "watchlist.clear": "Clear",
        "watchlist.empty": "List is empty",
        "watchlist.scan": "Scan List",
        "watchlist.export": "Export",
        "watchlist.popular": "Popular Symbols",
        # Export
        "export.title": "Export",
        "export.csv": "Download CSV",
        "export.excel": "Download Excel",
        "export.pdf": "Download PDF",
        "export.options": "Export Options",
        "export.all_columns": "Include all columns",
        "export.buyable_only": "Include buyable symbols only",
        # AI Lab
        "ai.title": "AI Laboratory",
        "ai.analyzing": "Analyzing...",
        "ai.deep_analysis": "Deep Analysis",
        "ai.research": "Research",
        "ai.news": "News",
        "ai.sentiment": "Sentiment",
        "ai.recommendation": "Recommendation",
        # Onboarding
        "onboard.welcome": "Welcome to FinPilot!",
        "onboard.next": "Next",
        "onboard.back": "Back",
        "onboard.skip": "Skip",
        "onboard.finish": "Get Started!",
        "onboard.step": "Step {current}/{total}",
        # Settings
        "settings.title": "Settings",
        "settings.language": "Language",
        "settings.theme": "Theme",
        "settings.notifications": "Notifications",
        "settings.telegram": "Telegram Integration",
        "settings.save": "Save",
        "settings.reset": "Reset",
        # Common
        "common.loading": "Loading...",
        "common.error": "Error",
        "common.success": "Success",
        "common.warning": "Warning",
        "common.info": "Info",
        "common.confirm": "Confirm",
        "common.cancel": "Cancel",
        "common.save": "Save",
        "common.delete": "Delete",
        "common.edit": "Edit",
        "common.close": "Close",
        "common.search": "Search",
        "common.filter": "Filter",
        "common.sort": "Sort",
        "common.refresh": "Refresh",
        "common.download": "Download",
        "common.upload": "Upload",
        "common.copy": "Copy",
        "common.share": "Share",
        "common.total": "Total",
        "common.average": "Average",
        "common.last_update": "Last Update",
        "common.version": "Version",
        # Time
        "time.now": "Now",
        "time.today": "Today",
        "time.yesterday": "Yesterday",
        "time.days_ago": "{n} days ago",
        "time.hours_ago": "{n} hours ago",
        "time.minutes_ago": "{n} minutes ago",
        # Errors
        "error.generic": "An error occurred",
        "error.network": "Network error",
        "error.no_data": "No data found",
        "error.invalid_input": "Invalid input",
        "error.try_again": "Please try again",
        # Tips
        "tip.aggressive": "Aggressive Mode generates more signals",
        "tip.watchlist": "You can export the watchlist as CSV",
        "tip.ai_lab": "Use AI Lab for deep analysis",
    },
    "de": {
        # Navigation
        "nav.home": "Startseite",
        "nav.scanner": "Scanner",
        "nav.signals": "Signale",
        "nav.watchlist": "Merkliste",
        "nav.ai_lab": "KI-Labor",
        "nav.settings": "Einstellungen",
        "nav.help": "Hilfe",
        # Dashboard
        "dashboard.title": "FinPilot Übersicht",
        "dashboard.subtitle": "KI-gestützte Aktienanalyse",
        "dashboard.market_pulse": "Marktpuls",
        "dashboard.quick_settings": "Schnelleinstellungen",
        "dashboard.aggressive_mode": "Aggressiver Modus",
        "dashboard.portfolio_size": "Portfoliogröße",
        "dashboard.risk_percent": "Risikoprozentsatz",
        # Scanner (minimal for brevity)
        "scan.title": "Marktscanner",
        "scan.start": "Scan starten",
        "scan.restart": "Neu starten",
        "scan.loading": "Scanne...",
        "scan.completed": "Scan abgeschlossen",
        "scan.results": "{count} Symbole analysiert",
        # Common
        "common.loading": "Wird geladen...",
        "common.error": "Fehler",
        "common.success": "Erfolgreich",
    },
}


# ============================================
# 🔧 Translation Engine
# ============================================


@dataclass
class TranslationContext:
    """Context for translation operations."""

    language: Language = DEFAULT_LANGUAGE
    fallback_language: Language = Language.ENGLISH
    missing_key_handler: Optional[Callable[[str], str]] = None


# Global context
_context = TranslationContext()


def get_language() -> Language:
    """Get current language from session state or default."""
    if I18N_LANGUAGE_KEY in st.session_state:
        lang_code = st.session_state[I18N_LANGUAGE_KEY]
        try:
            return Language(lang_code)
        except ValueError:
            pass
    return DEFAULT_LANGUAGE


def set_language(language: Union[Language, str]) -> None:
    """Set current language in session state."""
    if isinstance(language, str):
        try:
            language = Language(language)
        except ValueError:
            language = DEFAULT_LANGUAGE

    st.session_state[I18N_LANGUAGE_KEY] = language.value
    _context.language = language


def t(key: str, language: Optional[Union[Language, str]] = None, **kwargs: Any) -> str:
    """
    Get translation for a key.

    Args:
        key: Translation key (e.g., "dashboard.title")
        language: Optional language override
        **kwargs: Variables for interpolation

    Returns:
        Translated string with variables substituted

    Examples:
        >>> t("dashboard.title")
        "FinPilot Kontrol Paneli"

        >>> t("scan.results", count=42)
        "42 sembol analiz edildi"
    """
    # Determine language
    if language is not None:
        if isinstance(language, str):
            try:
                lang = Language(language)
            except ValueError:
                lang = get_language()
        else:
            lang = language
    else:
        lang = get_language()

    # Try to get translation
    translations = TRANSLATIONS.get(lang.value, {})
    text = translations.get(key)

    # Fallback chain
    if text is None and lang != _context.fallback_language:
        fallback_translations = TRANSLATIONS.get(_context.fallback_language.value, {})
        text = fallback_translations.get(key)

    # Return key if not found
    if text is None:
        if _context.missing_key_handler:
            return _context.missing_key_handler(key)
        return key

    # Variable interpolation
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass  # Ignore missing variables

    return text


def tn(key_singular: str, key_plural: str, n: int, **kwargs: Any) -> str:
    """
    Get pluralized translation.

    Args:
        key_singular: Key for singular form
        key_plural: Key for plural form
        n: Count for pluralization
        **kwargs: Additional variables

    Returns:
        Appropriate translation based on count
    """
    key = key_singular if n == 1 else key_plural
    return t(key, n=n, **kwargs)


# ============================================
# 🎨 Language Selector Component
# ============================================


def render_language_selector(
    location: str = "sidebar", show_flags: bool = True
) -> Optional[Language]:
    """
    Render a language selector widget.

    Args:
        location: Where to render ("sidebar", "main", "header")
        show_flags: Whether to show country flags

    Returns:
        Selected language if changed, None otherwise
    """
    current = get_language()

    options = list(SUPPORTED_LANGUAGES.keys())
    labels = [
        (
            f"{SUPPORTED_LANGUAGES[lang]['flag']} {SUPPORTED_LANGUAGES[lang]['name']}"
            if show_flags
            else SUPPORTED_LANGUAGES[lang]["name"]
        )
        for lang in options
    ]

    current_index = options.index(current) if current in options else 0

    container = st.sidebar if location == "sidebar" else st

    selected_label = container.selectbox(
        t("settings.language"), options=labels, index=current_index, key="i18n_language_selector"
    )

    selected_index = labels.index(selected_label)
    selected = options[selected_index]

    if selected != current:
        set_language(selected)
        return selected

    return None


def render_language_toggle() -> Optional[Language]:
    """
    Render a compact language toggle (TR/EN).

    Returns:
        Selected language if changed, None otherwise
    """
    current = get_language()

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "🇹🇷 TR",
            key="lang_tr",
            type="primary" if current == Language.TURKISH else "secondary",
            use_container_width=True,
        ):
            if current != Language.TURKISH:
                set_language(Language.TURKISH)
                return Language.TURKISH

    with col2:
        if st.button(
            "🇺🇸 EN",
            key="lang_en",
            type="primary" if current == Language.ENGLISH else "secondary",
            use_container_width=True,
        ):
            if current != Language.ENGLISH:
                set_language(Language.ENGLISH)
                return Language.ENGLISH

    return None


# ============================================
# 📦 Translation Utilities
# ============================================


def get_all_keys(language: Optional[Language] = None) -> List[str]:
    """Get all translation keys for a language."""
    lang = language or get_language()
    return list(TRANSLATIONS.get(lang.value, {}).keys())


def has_translation(key: str, language: Optional[Language] = None) -> bool:
    """Check if a translation exists for a key."""
    lang = language or get_language()
    return key in TRANSLATIONS.get(lang.value, {})


def get_missing_translations(
    source: Language = Language.ENGLISH, target: Language = Language.TURKISH
) -> List[str]:
    """Find keys that exist in source but not in target."""
    source_keys = set(TRANSLATIONS.get(source.value, {}).keys())
    target_keys = set(TRANSLATIONS.get(target.value, {}).keys())
    return list(source_keys - target_keys)


def add_translation(key: str, translations: Dict[str, str]) -> None:
    """
    Add a translation dynamically.

    Args:
        key: Translation key
        translations: Dict mapping language codes to translations
    """
    for lang_code, text in translations.items():
        if lang_code in TRANSLATIONS:
            TRANSLATIONS[lang_code][key] = text


# ============================================
# 🔄 Integration Helpers
# ============================================


def localized_number(value: float, precision: int = 2) -> str:
    """Format number according to locale."""
    lang = get_language()

    if lang == Language.TURKISH:
        # Turkish uses comma as decimal separator
        formatted = f"{value:,.{precision}f}"
        return formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    elif lang == Language.GERMAN:
        formatted = f"{value:,.{precision}f}"
        return formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    else:
        return f"{value:,.{precision}f}"


def localized_currency(value: float, currency: str = "USD") -> str:
    """Format currency according to locale."""
    lang = get_language()

    if currency == "USD":
        symbol = "$"
    elif currency == "TRY":
        symbol = "₺"
    elif currency == "EUR":
        symbol = "€"
    else:
        symbol = currency

    if lang == Language.TURKISH:
        return f"{localized_number(value)} {symbol}"
    else:
        return f"{symbol}{localized_number(value)}"


def localized_date(date, format: str = "short") -> str:
    """Format date according to locale."""
    from datetime import datetime

    lang = get_language()

    if isinstance(date, str):
        try:
            date = datetime.fromisoformat(date)
        except ValueError:
            return date

    if format == "short":
        if lang == Language.TURKISH:
            return date.strftime("%d.%m.%Y")
        elif lang == Language.GERMAN:
            return date.strftime("%d.%m.%Y")
        else:
            return date.strftime("%m/%d/%Y")
    else:
        if lang == Language.TURKISH:
            return date.strftime("%d %B %Y, %H:%M")
        else:
            return date.strftime("%B %d, %Y, %H:%M")


__all__ = [
    # Enums
    "Language",
    "SUPPORTED_LANGUAGES",
    "DEFAULT_LANGUAGE",
    # Core functions
    "t",
    "tn",
    "get_language",
    "set_language",
    # Components
    "render_language_selector",
    "render_language_toggle",
    # Utilities
    "get_all_keys",
    "has_translation",
    "get_missing_translations",
    "add_translation",
    # Formatting
    "localized_number",
    "localized_currency",
    "localized_date",
]
