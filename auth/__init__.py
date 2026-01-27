"""
FinPilot Authentication & Session Management Module.

Provides:
- User authentication (JWT-based)
- Session management
- Portfolio persistence
- Settings synchronization
- Streamlit UI components
"""

from .core import (
    AuthError,
    AuthManager,
    InvalidCredentialsError,
    Session,
    TokenExpiredError,
    User,
    UserExistsError,
)
from .database import (
    Database,
    PortfolioRepository,
    SessionRepository,
    SettingsRepository,
    UserRepository,
)
from .portfolio import Portfolio, PortfolioManager, Position, Trade, TradeSide
from .streamlit_session import (
    StreamlitSessionManager,
    get_session_manager,
    render_auth_page,
    render_login_form,
    render_register_form,
    render_settings_panel,
    render_user_profile,
    require_auth,
)

__all__ = [
    # Core
    "AuthManager",
    "User",
    "Session",
    "AuthError",
    "InvalidCredentialsError",
    "TokenExpiredError",
    "UserExistsError",
    # Database
    "Database",
    "UserRepository",
    "SessionRepository",
    "PortfolioRepository",
    "SettingsRepository",
    # Portfolio
    "Portfolio",
    "Position",
    "Trade",
    "TradeSide",
    "PortfolioManager",
    # Streamlit Session
    "StreamlitSessionManager",
    "render_login_form",
    "render_register_form",
    "render_auth_page",
    "render_user_profile",
    "render_settings_panel",
    "require_auth",
    "get_session_manager",
]
