# -*- coding: utf-8 -*-
"""
FinPilot Session State Management
==================================

Type-safe session state management using dataclasses.
Provides centralized state management with validation and defaults.

Usage:
    from core.session_state import get_session, SessionState

    # Get typed session state
    session = get_session()

    # Access with type hints
    df = session.scan_df
    session.scan_status = "completed"

    # Update multiple fields
    session.update(scan_status="completed", scan_message="Done")
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field, fields
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar

import pandas as pd

try:
    import streamlit as st

    HAS_STREAMLIT = True
except ImportError:
    st = None  # type: ignore
    HAS_STREAMLIT = False


# ============================================
# 📊 Enums for Type Safety
# ============================================


class ScanStatus(str, Enum):
    """Scan operation status."""

    IDLE = "idle"
    LOADING = "loading"
    COMPLETED = "completed"
    ERROR = "error"


class ViewMode(str, Enum):
    """Dashboard view mode."""

    SIMPLE = "simple"
    ADVANCED = "advanced"


class Theme(str, Enum):
    """UI theme."""

    DARK = "dark"
    LIGHT = "light"
    SYSTEM = "system"


# ============================================
# 📦 Session State Dataclasses
# ============================================


@dataclass
class ScanState:
    """State for scan operations."""

    status: ScanStatus = ScanStatus.IDLE
    message: Optional[str] = None
    df: pd.DataFrame = field(default_factory=pd.DataFrame)
    source: Optional[str] = None
    timestamp: Optional[datetime.datetime] = None
    symbols_count: int = 0
    buyable_count: int = 0

    def reset(self) -> None:
        """Reset scan state to defaults."""
        self.status = ScanStatus.IDLE
        self.message = None
        self.df = pd.DataFrame()
        self.source = None
        self.timestamp = None
        self.symbols_count = 0
        self.buyable_count = 0

    def set_loading(self, message: str = "Tarama başlatıldı...") -> None:
        """Set loading state."""
        self.status = ScanStatus.LOADING
        self.message = message

    def set_completed(self, df: pd.DataFrame, source: str, message: Optional[str] = None) -> None:
        """Set completed state with results."""
        self.status = ScanStatus.COMPLETED
        self.df = df
        self.source = source
        self.timestamp = datetime.datetime.now()
        self.symbols_count = len(df)
        self.buyable_count = int(df["entry_ok"].sum()) if "entry_ok" in df.columns else 0
        self.message = message or f"{self.symbols_count} sembol analiz edildi."

    def set_error(self, message: str) -> None:
        """Set error state."""
        self.status = ScanStatus.ERROR
        self.message = message


@dataclass
class UserPreferences:
    """User preferences and settings."""

    view_mode: ViewMode = ViewMode.ADVANCED
    theme: Theme = Theme.DARK
    language: str = "tr"
    guide_tooltip_shown: bool = False
    sidebar_expanded: bool = True

    # Trading preferences
    risk_score: int = 5
    portfolio_size: float = 10000.0
    max_loss_pct: float = 10.0
    strategy: str = "Normal"
    market: str = "US"

    # Notifications
    telegram_active: bool = False
    telegram_id: str = ""


@dataclass
class WatchlistState:
    """User watchlist state."""

    symbols: List[str] = field(default_factory=list)
    last_updated: Optional[datetime.datetime] = None

    def add_symbol(self, symbol: str) -> bool:
        """Add symbol to watchlist. Returns True if added."""
        symbol = symbol.upper().strip()
        if symbol and symbol not in self.symbols:
            self.symbols.append(symbol)
            self.last_updated = datetime.datetime.now()
            return True
        return False

    def remove_symbol(self, symbol: str) -> bool:
        """Remove symbol from watchlist. Returns True if removed."""
        symbol = symbol.upper().strip()
        if symbol in self.symbols:
            self.symbols.remove(symbol)
            self.last_updated = datetime.datetime.now()
            return True
        return False

    def clear(self) -> None:
        """Clear all symbols."""
        self.symbols.clear()
        self.last_updated = datetime.datetime.now()


@dataclass
class NavigationState:
    """Navigation and routing state."""

    current_page: str = "dashboard"
    previous_page: Optional[str] = None
    selected_symbol: Optional[str] = None
    active_tab: int = 0

    def navigate_to(self, page: str) -> None:
        """Navigate to a page."""
        self.previous_page = self.current_page
        self.current_page = page

    def go_back(self) -> None:
        """Go back to previous page."""
        if self.previous_page:
            self.current_page = self.previous_page
            self.previous_page = None


@dataclass
class AuthState:
    """Authentication state."""

    is_authenticated: bool = False
    user_id: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    role: str = "user"
    session_token: Optional[str] = None
    expires_at: Optional[datetime.datetime] = None

    def is_session_valid(self) -> bool:
        """Check if session is still valid."""
        if not self.is_authenticated:
            return False
        if self.expires_at and datetime.datetime.now() > self.expires_at:
            return False
        return True

    def logout(self) -> None:
        """Clear auth state."""
        self.is_authenticated = False
        self.user_id = None
        self.username = None
        self.email = None
        self.role = "user"
        self.session_token = None
        self.expires_at = None


@dataclass
class SessionState:
    """
    Main session state container.

    Provides type-safe access to all session state with
    automatic persistence to st.session_state.
    """

    scan: ScanState = field(default_factory=ScanState)
    preferences: UserPreferences = field(default_factory=UserPreferences)
    watchlist: WatchlistState = field(default_factory=WatchlistState)
    navigation: NavigationState = field(default_factory=NavigationState)
    auth: AuthState = field(default_factory=AuthState)

    # Backward compatibility properties
    @property
    def scan_status(self) -> str:
        """Backward compatible scan_status."""
        return self.scan.status.value

    @scan_status.setter
    def scan_status(self, value: str) -> None:
        """Backward compatible scan_status setter."""
        try:
            self.scan.status = ScanStatus(value)
        except ValueError:
            self.scan.status = ScanStatus.IDLE

    @property
    def scan_df(self) -> pd.DataFrame:
        """Backward compatible scan_df."""
        return self.scan.df

    @scan_df.setter
    def scan_df(self, value: pd.DataFrame) -> None:
        """Backward compatible scan_df setter."""
        self.scan.df = value

    @property
    def scan_message(self) -> Optional[str]:
        """Backward compatible scan_message."""
        return self.scan.message

    @scan_message.setter
    def scan_message(self, value: Optional[str]) -> None:
        """Backward compatible scan_message setter."""
        self.scan.message = value

    @property
    def scan_src(self) -> Optional[str]:
        """Backward compatible scan_src."""
        return self.scan.source

    @scan_src.setter
    def scan_src(self, value: Optional[str]) -> None:
        """Backward compatible scan_src setter."""
        self.scan.source = value

    @property
    def scan_time(self) -> Optional[datetime.datetime]:
        """Backward compatible scan_time."""
        return self.scan.timestamp

    @scan_time.setter
    def scan_time(self, value: Optional[datetime.datetime]) -> None:
        """Backward compatible scan_time setter."""
        self.scan.timestamp = value

    @property
    def guide_tooltip_shown(self) -> bool:
        """Backward compatible guide_tooltip_shown."""
        return self.preferences.guide_tooltip_shown

    @guide_tooltip_shown.setter
    def guide_tooltip_shown(self, value: bool) -> None:
        """Backward compatible guide_tooltip_shown setter."""
        self.preferences.guide_tooltip_shown = value

    @property
    def view_mode(self) -> str:
        """Backward compatible view_mode."""
        return self.preferences.view_mode.value

    @view_mode.setter
    def view_mode(self, value: str) -> None:
        """Backward compatible view_mode setter."""
        try:
            self.preferences.view_mode = ViewMode(value)
        except ValueError:
            self.preferences.view_mode = ViewMode.ADVANCED


# ============================================
# 🔧 Session State Manager
# ============================================

_SESSION_KEY = "_finpilot_session"


def get_session() -> SessionState:
    """
    Get the current session state.

    Returns a typed SessionState object that persists across reruns.
    Creates a new session if none exists.

    Returns:
        SessionState instance

    Example:
        >>> session = get_session()
        >>> session.scan.set_loading("Scanning...")
        >>> df = session.scan.df
    """
    if not HAS_STREAMLIT or st is None:
        # Return a non-persisted session for non-Streamlit usage
        return SessionState()

    if _SESSION_KEY not in st.session_state:
        st.session_state[_SESSION_KEY] = SessionState()

    return st.session_state[_SESSION_KEY]


def init_session() -> SessionState:
    """
    Initialize session state with defaults.

    Should be called at app startup. Safe to call multiple times.

    Returns:
        SessionState instance
    """
    return get_session()


def reset_session() -> SessionState:
    """
    Reset session state to defaults.

    Clears all state and returns a fresh SessionState.

    Returns:
        Fresh SessionState instance
    """
    if HAS_STREAMLIT and st is not None:
        st.session_state[_SESSION_KEY] = SessionState()
        return st.session_state[_SESSION_KEY]
    return SessionState()


def migrate_legacy_session_state() -> None:
    """
    Migrate legacy session state keys to new typed structure.

    Call this once at app startup to migrate old session state
    to the new dataclass-based structure.
    """
    if not HAS_STREAMLIT or st is None:
        return

    session = get_session()

    # Migrate scan state
    legacy_mappings = {
        "scan_status": ("scan", "status", lambda v: ScanStatus(v) if v else ScanStatus.IDLE),
        "scan_message": ("scan", "message", lambda v: v),
        "scan_df": ("scan", "df", lambda v: v if isinstance(v, pd.DataFrame) else pd.DataFrame()),
        "scan_src": ("scan", "source", lambda v: v),
        "scan_time": ("scan", "timestamp", lambda v: v),
        "guide_tooltip_shown": ("preferences", "guide_tooltip_shown", lambda v: bool(v)),
        "view_mode": (
            "preferences",
            "view_mode",
            lambda v: ViewMode(v) if v else ViewMode.ADVANCED,
        ),
    }

    for old_key, (container, attr, converter) in legacy_mappings.items():
        if old_key in st.session_state and old_key != _SESSION_KEY:
            try:
                value = st.session_state[old_key]
                container_obj = getattr(session, container)
                setattr(container_obj, attr, converter(value))
            except (ValueError, TypeError, AttributeError):
                pass  # Skip failed migrations


# ============================================
# 🔗 Convenience Functions
# ============================================


def is_scan_in_progress() -> bool:
    """Check if a scan is currently in progress."""
    return get_session().scan.status == ScanStatus.LOADING


def get_scan_results() -> pd.DataFrame:
    """Get current scan results DataFrame."""
    return get_session().scan.df


def has_scan_results() -> bool:
    """Check if there are scan results available."""
    session = get_session()
    return session.scan.status == ScanStatus.COMPLETED and not session.scan.df.empty


def is_authenticated() -> bool:
    """Check if user is authenticated."""
    return get_session().auth.is_session_valid()


def get_current_user() -> Optional[str]:
    """Get current username if authenticated."""
    session = get_session()
    return session.auth.username if session.auth.is_authenticated else None


__all__ = [
    # Enums
    "ScanStatus",
    "ViewMode",
    "Theme",
    # Dataclasses
    "ScanState",
    "UserPreferences",
    "WatchlistState",
    "NavigationState",
    "AuthState",
    "SessionState",
    # Functions
    "get_session",
    "init_session",
    "reset_session",
    "migrate_legacy_session_state",
    # Convenience
    "is_scan_in_progress",
    "get_scan_results",
    "has_scan_results",
    "is_authenticated",
    "get_current_user",
]
