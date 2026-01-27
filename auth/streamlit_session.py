"""
Streamlit Session Integration for FinPilot.

Provides Streamlit session state management, authentication decorators,
and UI components for login/register/profile.
"""

from __future__ import annotations

import logging
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple

import streamlit as st

from .core import (
    AccountLockedError,
    AuthConfig,
    AuthError,
    AuthManager,
    InvalidCredentialsError,
    Session,
    TokenExpiredError,
    TokenInvalidError,
    User,
    UserExistsError,
    UserNotFoundError,
)
from .database import (
    Database,
    PortfolioRepository,
    SessionRepository,
    SettingsRepository,
    UserRepository,
)
from .portfolio import Portfolio, PortfolioManager

logger = logging.getLogger(__name__)


# ============================================================================
# SESSION STATE MANAGER
# ============================================================================


class StreamlitSessionManager:
    """
    Manages Streamlit session state for authentication.

    Example:
        >>> session_mgr = StreamlitSessionManager()
        >>> session_mgr.initialize()
        >>>
        >>> if session_mgr.is_authenticated:
        ...     st.write(f"Welcome, {session_mgr.current_user.display_name}")
        ... else:
        ...     session_mgr.render_login_page()
    """

    SESSION_KEYS = [
        "user",
        "session",
        "access_token",
        "refresh_token",
        "portfolio",
        "settings",
        "is_authenticated",
        "auth_error",
    ]

    def __init__(self, db_path: str = "data/finpilot.db", config: Optional[AuthConfig] = None):
        """
        Initialize session manager.

        Args:
            db_path: Path to SQLite database
            config: Auth configuration
        """
        self.db = Database(db_path)
        self.db.initialize()

        self.user_repo = UserRepository(self.db)
        self.session_repo = SessionRepository(self.db)
        self.portfolio_repo = PortfolioRepository(self.db)
        self.settings_repo = SettingsRepository(self.db)

        self.auth = AuthManager(
            config=config, user_repository=self.user_repo, session_repository=self.session_repo
        )

        self.portfolio_mgr = PortfolioManager(self.portfolio_repo)

    def initialize(self) -> None:
        """Initialize session state."""
        for key in self.SESSION_KEYS:
            if key not in st.session_state:
                st.session_state[key] = None

        if "is_authenticated" not in st.session_state:
            st.session_state.is_authenticated = False

    @property
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return st.session_state.get("is_authenticated", False)

    @property
    def current_user(self) -> Optional[User]:
        """Get current user."""
        return st.session_state.get("user")

    @property
    def current_session(self) -> Optional[Session]:
        """Get current session."""
        return st.session_state.get("session")

    @property
    def user_portfolio(self) -> Optional[Portfolio]:
        """Get user's portfolio."""
        return st.session_state.get("portfolio")

    @property
    def user_settings(self) -> Dict[str, Any]:
        """Get user settings."""
        return st.session_state.get("settings") or {}

    def login(
        self, email: str, password: str, remember_me: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Login user.

        Args:
            email: User email
            password: User password
            remember_me: Extend session duration

        Returns:
            (success, error_message)
        """
        try:
            session = self.auth.login(email, password, remember_me=remember_me)

            user = self.auth.get_current_user(session.access_token)

            # Guard against None user
            if user is None:
                raise AuthError("Failed to retrieve user information")

            # Store in session state
            st.session_state.user = user
            st.session_state.session = session
            st.session_state.access_token = session.access_token
            st.session_state.refresh_token = session.refresh_token
            st.session_state.is_authenticated = True
            st.session_state.auth_error = None

            # Load user data
            self._load_user_data(user.id)

            logger.info(f"User logged in: {user.email}")
            return True, None

        except InvalidCredentialsError:
            st.session_state.auth_error = "Geçersiz e-posta veya şifre"
            return False, st.session_state.auth_error

        except AccountLockedError as e:
            st.session_state.auth_error = str(e)
            return False, st.session_state.auth_error

        except AuthError as e:
            st.session_state.auth_error = str(e)
            return False, st.session_state.auth_error

    def register(
        self, email: str, username: str, password: str, display_name: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Register new user.

        Args:
            email: User email
            username: Username
            password: Password
            display_name: Display name

        Returns:
            (success, error_message)
        """
        try:
            user = self.auth.register(email, username, password, display_name)

            # Auto-login after registration
            return self.login(email, password)

        except UserExistsError:
            return False, "Bu e-posta adresi zaten kayıtlı"

        except AuthError as e:
            return False, str(e)

    def logout(self) -> None:
        """Logout current user."""
        if self.current_session:
            try:
                self.auth.logout(self.current_session.id)
            except Exception as e:
                logger.warning(f"Logout error: {e}")

        # Clear session state
        for key in self.SESSION_KEYS:
            st.session_state[key] = None

        st.session_state.is_authenticated = False
        logger.info("User logged out")

    def verify_session(self) -> bool:
        """
        Verify current session is valid.

        Returns:
            True if session is valid
        """
        token = st.session_state.get("access_token")
        if not token:
            return False

        try:
            payload = self.auth.verify_token(token)
            return True
        except TokenExpiredError:
            # Try to refresh
            return self._refresh_session()
        except TokenInvalidError:
            return False

    def _refresh_session(self) -> bool:
        """Refresh access token."""
        refresh_token = st.session_state.get("refresh_token")
        if not refresh_token:
            return False

        try:
            new_access, new_refresh = self.auth.refresh_tokens(refresh_token)
            st.session_state.access_token = new_access
            st.session_state.refresh_token = new_refresh
            return True
        except Exception:
            self.logout()
            return False

    def _load_user_data(self, user_id: str) -> None:
        """Load user's portfolio and settings."""
        # Load portfolio
        portfolio = self.portfolio_mgr.get_user_portfolio(user_id)
        if not portfolio:
            # Create default portfolio
            portfolio = self.portfolio_mgr.create_portfolio(user_id, initial_cash=0)
        st.session_state.portfolio = portfolio

        # Load settings
        settings = self.settings_repo.get_by_id(user_id)
        st.session_state.settings = settings or {}

    def save_settings(self, settings: Dict[str, Any]) -> None:
        """Save user settings."""
        if not self.current_user:
            return

        self.settings_repo.save(settings, self.current_user.id)  # entity first, then user_id
        st.session_state.settings = settings


# ============================================================================
# AUTH UI COMPONENTS
# ============================================================================


def render_login_form(session_mgr: StreamlitSessionManager) -> None:
    """Render login form."""
    st.markdown("### 🔐 Giriş Yap")

    with st.form("login_form"):
        email = st.text_input("E-posta", placeholder="ornek@email.com")
        password = st.text_input("Şifre", type="password")
        remember_me = st.checkbox("Beni Hatırla")

        col1, col2 = st.columns([1, 1])
        with col1:
            submitted = st.form_submit_button("Giriş Yap", use_container_width=True)
        with col2:
            if st.form_submit_button("Şifremi Unuttum", use_container_width=True):
                st.info("Şifre sıfırlama özelliği yakında eklenecek.")

        if submitted:
            if not email or not password:
                st.error("E-posta ve şifre gerekli")
            else:
                success, error = session_mgr.login(email, password, remember_me)
                if success:
                    st.success("Giriş başarılı!")
                    st.rerun()
                else:
                    st.error(error or "Giriş başarısız")


def render_register_form(session_mgr: StreamlitSessionManager) -> None:
    """Render registration form."""
    st.markdown("### 📝 Kayıt Ol")

    with st.form("register_form"):
        email = st.text_input("E-posta*", placeholder="ornek@email.com")
        username = st.text_input("Kullanıcı Adı*", placeholder="kullanici123")
        display_name = st.text_input("Görünen Ad", placeholder="Ahmet Yılmaz")
        password = st.text_input(
            "Şifre*",
            type="password",
            help="En az 8 karakter, büyük/küçük harf, rakam ve özel karakter içermeli",
        )
        password_confirm = st.text_input("Şifre Tekrar*", type="password")

        terms = st.checkbox("Kullanım şartlarını kabul ediyorum")

        submitted = st.form_submit_button("Kayıt Ol", use_container_width=True)

        if submitted:
            if not all([email, username, password, password_confirm]):
                st.error("Zorunlu alanları doldurun")
            elif password != password_confirm:
                st.error("Şifreler eşleşmiyor")
            elif not terms:
                st.error("Kullanım şartlarını kabul etmelisiniz")
            else:
                success, error = session_mgr.register(email, username, password, display_name)
                if success:
                    st.success("Kayıt başarılı! Hoş geldiniz.")
                    st.rerun()
                else:
                    st.error(error or "Kayıt başarısız")


def render_auth_page(session_mgr: StreamlitSessionManager) -> None:
    """Render combined auth page with login/register tabs."""
    st.title("🚀 FinPilot")
    st.caption("Akıllı Yatırım Asistanınız")

    tab1, tab2 = st.tabs(["🔐 Giriş Yap", "📝 Kayıt Ol"])

    with tab1:
        render_login_form(session_mgr)

    with tab2:
        render_register_form(session_mgr)

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        "© 2025 FinPilot. Tüm hakları saklıdır."
        "</div>",
        unsafe_allow_html=True,
    )


def render_user_profile(session_mgr: StreamlitSessionManager) -> None:
    """Render user profile section."""
    user = session_mgr.current_user
    if not user:
        return

    with st.expander("👤 Profil", expanded=False):
        col1, col2 = st.columns([1, 3])

        with col1:
            # Avatar placeholder
            st.markdown(
                f"""
                <div style='
                    width: 80px;
                    height: 80px;
                    border-radius: 50%;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 32px;
                    color: white;
                    margin: 10px;
                '>
                    {user.username[0].upper()}
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(f"**{user.display_name or user.username}**")
            st.caption(user.email)
            st.caption(f"Üyelik: {user.created_at.strftime('%d.%m.%Y')}")
            st.caption(f"Rol: {user.role.value.title()}")

        st.markdown("---")

        if st.button("🚪 Çıkış Yap", use_container_width=True):
            session_mgr.logout()
            st.rerun()


def render_settings_panel(session_mgr: StreamlitSessionManager) -> None:
    """Render settings panel."""
    settings = session_mgr.user_settings.copy()

    st.markdown("### ⚙️ Ayarlar")

    with st.form("settings_form"):
        # Theme
        theme = st.selectbox(
            "Tema",
            ["light", "dark", "auto"],
            index=["light", "dark", "auto"].index(settings.get("theme", "auto")),
        )

        # Language
        language = st.selectbox(
            "Dil",
            ["tr", "en"],
            index=["tr", "en"].index(settings.get("language", "tr")),
            format_func=lambda x: "Türkçe" if x == "tr" else "English",
        )

        # Notifications
        notifications = st.checkbox(
            "E-posta Bildirimleri", value=settings.get("notifications", True)
        )

        # Default cash
        default_cash = st.number_input(
            "Varsayılan Başlangıç Bakiyesi ($)",
            min_value=0,
            value=settings.get("default_cash", 10000),
            step=1000,
        )

        submitted = st.form_submit_button("Kaydet", use_container_width=True)

        if submitted:
            new_settings = {
                "theme": theme,
                "language": language,
                "notifications": notifications,
                "default_cash": default_cash,
            }
            session_mgr.save_settings(new_settings)
            st.success("Ayarlar kaydedildi!")


# ============================================================================
# DECORATORS
# ============================================================================


def require_auth(session_mgr: StreamlitSessionManager):
    """
    Decorator to require authentication.

    Usage:
        @require_auth(session_mgr)
        def protected_page():
            st.write("Protected content")
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            session_mgr.initialize()

            if not session_mgr.is_authenticated:
                render_auth_page(session_mgr)
                return

            if not session_mgr.verify_session():
                st.warning("Oturumunuz sona erdi. Lütfen tekrar giriş yapın.")
                render_auth_page(session_mgr)
                return

            return func(*args, **kwargs)

        return wrapper

    return decorator


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

_session_manager: Optional[StreamlitSessionManager] = None


def get_session_manager(db_path: str = "data/finpilot.db") -> StreamlitSessionManager:
    """Get or create session manager singleton."""
    global _session_manager
    if _session_manager is None:
        _session_manager = StreamlitSessionManager(db_path)
    return _session_manager


__all__ = [
    "StreamlitSessionManager",
    "render_login_form",
    "render_register_form",
    "render_auth_page",
    "render_user_profile",
    "render_settings_panel",
    "require_auth",
    "get_session_manager",
]
