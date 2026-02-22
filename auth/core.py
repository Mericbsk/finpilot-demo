"""
Core Authentication Module for FinPilot.

Provides JWT-based authentication, user management, and session handling.

Sub-modules (Sprint P8 split):
    auth.tokens   — JWTHandler, TokenPayload
    auth.users    — PasswordHasher, User, UserRole
    auth.sessions — Session
"""

from __future__ import annotations

import logging
import os
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


def _require_secret_key() -> str:
    """Return FINPILOT_SECRET_KEY from env or raise immediately.

    In development (no .env), a deterministic dev-only key is generated from
    the machine hostname so sessions survive restarts.  In production the env
    var MUST be set explicitly.
    """
    key = os.getenv("FINPILOT_SECRET_KEY")
    if key:
        return key

    # Dev fallback — deterministic but clearly not for production
    import hashlib
    import socket

    dev_key = hashlib.sha256(
        f"finpilot-dev-{socket.gethostname()}".encode()
    ).hexdigest()
    logger.warning(
        "⚠️  FINPILOT_SECRET_KEY not set! Using dev-only key derived from hostname. "
        "Set FINPILOT_SECRET_KEY in .env for production."
    )
    return dev_key


# ============================================================================
# CONFIGURATION
# ============================================================================


@dataclass
class AuthConfig:
    """Authentication configuration."""

    # JWT Settings — Güvenli anahtar: .env'deki FINPILOT_SECRET_KEY zorunludur.
    # Eksikse uygulama başlatılmaz (fail-fast). Production'da mutlaka güçlü anahtar kullanılmalıdır.
    secret_key: str = field(
        default_factory=lambda: _require_secret_key()
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours
    refresh_token_expire_days: int = 30

    # Password Settings
    min_password_length: int = 8
    bcrypt_rounds: int = 12  # bcrypt work factor (12 = ~250ms, each +1 doubles time)

    # Session Settings
    max_sessions_per_user: int = 5
    session_timeout_minutes: int = 60 * 24 * 7  # 7 days

    # Rate Limiting
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15


# ============================================================================
# EXCEPTIONS
# ============================================================================


class AuthError(Exception):
    """Base authentication error."""

    pass


class InvalidCredentialsError(AuthError):
    """Invalid username or password."""

    pass


class TokenExpiredError(AuthError):
    """JWT token has expired."""

    pass


class TokenInvalidError(AuthError):
    """JWT token is invalid."""

    pass


class UserExistsError(AuthError):
    """User already exists."""

    pass


class UserNotFoundError(AuthError):
    """User not found."""

    pass


class SessionExpiredError(AuthError):
    """Session has expired."""

    pass


class AccountLockedError(AuthError):
    """Account is locked due to too many failed attempts."""

    pass


# ============================================================================
# DATA MODELS (imported from sub-modules — Sprint P8)
# ============================================================================

from .sessions import Session  # noqa: E402
from .users import PasswordHasher, User, UserRole  # noqa: E402


# ============================================================================
# JWT UTILITIES (imported from sub-modules — Sprint P8)
# ============================================================================

from .tokens import JWTHandler, TokenPayload  # noqa: E402


# ============================================================================
# AUTH MANAGER
# ============================================================================


class AuthManager:
    """
    Main authentication manager.

    Handles user registration, login, session management, and token operations.

    Example:
        >>> auth = AuthManager()
        >>>
        >>> # Register
        >>> user = auth.register("user@example.com", "username", "Password123!")
        >>>
        >>> # Login
        >>> session = auth.login("user@example.com", "Password123!")
        >>> print(session.access_token)
        >>>
        >>> # Verify token
        >>> payload = auth.verify_token(session.access_token)
        >>> print(payload.sub)  # user_id
    """

    def __init__(
        self, config: Optional[AuthConfig] = None, user_repository=None, session_repository=None
    ):
        self.config = config or AuthConfig()
        self.hasher = PasswordHasher(self.config.bcrypt_rounds)
        self.jwt = JWTHandler(self.config.secret_key, self.config.algorithm)

        # Repositories (can be injected for different storage backends)
        self._user_repo = user_repository
        self._session_repo = session_repository

        # In-memory fallback (for testing/simple usage)
        self._users: Dict[str, User] = {}
        self._sessions: Dict[str, Session] = {}

    def _get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        if self._user_repo:
            return self._user_repo.get_by_email(email)

        for user in self._users.values():
            if user.email.lower() == email.lower():
                return user
        return None

    def _get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        if self._user_repo:
            return self._user_repo.get_by_id(user_id)
        return self._users.get(user_id)

    def _save_user(self, user: User) -> None:
        """Save user."""
        if self._user_repo:
            self._user_repo.save(user)
        else:
            self._users[user.id] = user

    def _save_session(self, session: Session) -> None:
        """Save session."""
        if self._session_repo:
            self._session_repo.save(session)
        else:
            self._sessions[session.id] = session

    def _get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID."""
        if self._session_repo:
            return self._session_repo.get_by_id(session_id)
        return self._sessions.get(session_id)

    def _delete_session(self, session_id: str) -> None:
        """Delete session."""
        if self._session_repo:
            self._session_repo.delete(session_id)
        elif session_id in self._sessions:
            del self._sessions[session_id]

    def register(
        self, email: str, username: str, password: str, display_name: Optional[str] = None
    ) -> User:
        """
        Register a new user.

        Args:
            email: User email
            username: Username
            password: Password (will be hashed)
            display_name: Display name (optional)

        Returns:
            Created User object

        Raises:
            UserExistsError: If email already registered
            AuthError: If password doesn't meet requirements
        """
        # Check if user exists
        if self._get_user_by_email(email):
            raise UserExistsError(f"Email already registered: {email}")

        # Validate password
        is_valid, issues = PasswordHasher.validate_strength(
            password, self.config.min_password_length
        )
        if not is_valid:
            raise AuthError(f"Weak password: {', '.join(issues)}")

        # Hash password
        password_hash, salt = self.hasher.hash(password)

        # Create user
        user = User(
            id=secrets.token_hex(16),
            email=email.lower(),
            username=username,
            password_hash=password_hash,
            salt=salt,
            display_name=display_name or username,
            role=UserRole.USER,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self._save_user(user)
        logger.info(f"User registered: {user.id} ({email})")

        return user

    def login(
        self,
        email: str,
        password: str,
        device_info: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        remember_me: bool = False,
    ) -> Session:
        """
        Authenticate user and create session.

        Args:
            email: User email
            password: User password
            device_info: Device information
            ip_address: Client IP address
            user_agent: Browser user agent

        Returns:
            Session with access and refresh tokens

        Raises:
            InvalidCredentialsError: If credentials are wrong
            AccountLockedError: If account is locked
        """
        user = self._get_user_by_email(email)

        if not user:
            raise InvalidCredentialsError("Invalid email or password")

        # Check if account is locked
        if user.is_locked and user.locked_until is not None:
            remaining = (user.locked_until - datetime.utcnow()).seconds // 60
            raise AccountLockedError(f"Account locked. Try again in {remaining} minutes.")

        # Verify password
        if not self.hasher.verify(password, user.password_hash, user.salt):
            # Increment failed attempts
            user.failed_login_attempts += 1

            if user.failed_login_attempts >= self.config.max_login_attempts:
                user.locked_until = datetime.utcnow() + timedelta(
                    minutes=self.config.lockout_duration_minutes
                )
                self._save_user(user)
                raise AccountLockedError(
                    f"Too many failed attempts. Account locked for {self.config.lockout_duration_minutes} minutes."
                )

            self._save_user(user)
            raise InvalidCredentialsError("Invalid email or password")

        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()
        self._save_user(user)

        # Create tokens
        access_token = self._create_access_token(user)
        refresh_token = self._create_refresh_token(user)

        # Create session
        session = Session(
            id=secrets.token_hex(16),
            user_id=user.id,
            access_token=access_token,
            refresh_token=refresh_token,
            device_info=device_info,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=self.config.refresh_token_expire_days),
        )

        self._save_session(session)
        logger.info(f"User logged in: {user.id} ({email})")

        return session

    def logout(self, session_id: str) -> bool:
        """
        Logout user (invalidate session).

        Args:
            session_id: Session ID to invalidate

        Returns:
            True if session was found and deleted
        """
        session = self._get_session(session_id)
        if session:
            self._delete_session(session_id)
            logger.info(f"Session logged out: {session_id}")
            return True
        return False

    def logout_all(self, user_id: str) -> int:
        """
        Logout all sessions for a user.

        Returns:
            Number of sessions invalidated
        """
        count = 0

        if self._session_repo:
            count = self._session_repo.delete_all_for_user(user_id)
        else:
            to_delete = [sid for sid, s in self._sessions.items() if s.user_id == user_id]
            for sid in to_delete:
                del self._sessions[sid]
            count = len(to_delete)

        logger.info(f"Logged out {count} sessions for user: {user_id}")
        return count

    def _create_access_token(self, user: User) -> str:
        """Create JWT access token."""
        now = int(time.time())
        expires = now + (self.config.access_token_expire_minutes * 60)

        payload = TokenPayload(
            sub=user.id,
            exp=expires,
            iat=now,
            jti=secrets.token_hex(16),
            type="access",
            role=user.role.value,
        )

        return self.jwt.encode(payload.to_dict())

    def _create_refresh_token(self, user: User) -> str:
        """Create JWT refresh token."""
        now = int(time.time())
        expires = now + (self.config.refresh_token_expire_days * 24 * 60 * 60)

        payload = TokenPayload(
            sub=user.id,
            exp=expires,
            iat=now,
            jti=secrets.token_hex(16),
            type="refresh",
            role=user.role.value,
        )

        return self.jwt.encode(payload.to_dict())

    def verify_token(self, token: str) -> TokenPayload:
        """
        Verify and decode a JWT token.

        Args:
            token: JWT token string

        Returns:
            TokenPayload with user info

        Raises:
            TokenInvalidError: If token is invalid
            TokenExpiredError: If token has expired
        """
        payload = self.jwt.decode(token)

        return TokenPayload(
            sub=payload["sub"],
            exp=payload["exp"],
            iat=payload["iat"],
            jti=payload["jti"],
            type=payload["type"],
            role=payload["role"],
        )

    def refresh_tokens(self, refresh_token: str) -> Tuple[str, str]:
        """
        Refresh access and refresh tokens.

        Args:
            refresh_token: Current refresh token

        Returns:
            (new_access_token, new_refresh_token)

        Raises:
            TokenExpiredError: If refresh token expired
            TokenInvalidError: If token is invalid
        """
        payload = self.verify_token(refresh_token)

        if payload.type != "refresh":
            raise TokenInvalidError("Not a refresh token")

        user = self._get_user_by_id(payload.sub)
        if not user:
            raise UserNotFoundError("User not found")

        new_access = self._create_access_token(user)
        new_refresh = self._create_refresh_token(user)

        return new_access, new_refresh

    def get_current_user(self, token: str) -> Optional[User]:
        """
        Get current user from token.

        Args:
            token: JWT access token

        Returns:
            User object or None
        """
        try:
            payload = self.verify_token(token)
            return self._get_user_by_id(payload.sub)
        except (TokenExpiredError, TokenInvalidError):
            return None

    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """
        Change user password.

        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password

        Returns:
            True if password changed successfully
        """
        user = self._get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError("User not found")

        # Verify old password
        if not self.hasher.verify(old_password, user.password_hash, user.salt):
            raise InvalidCredentialsError("Current password is incorrect")

        # Validate new password
        is_valid, issues = PasswordHasher.validate_strength(
            new_password, self.config.min_password_length
        )
        if not is_valid:
            raise AuthError(f"Weak password: {', '.join(issues)}")

        # Hash new password
        new_hash, new_salt = self.hasher.hash(new_password)
        user.password_hash = new_hash
        user.salt = new_salt
        user.updated_at = datetime.utcnow()

        self._save_user(user)

        # Logout all sessions for security
        self.logout_all(user_id)

        logger.info(f"Password changed for user: {user_id}")
        return True


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

_default_auth_manager: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    """Get or create default auth manager."""
    global _default_auth_manager
    if _default_auth_manager is None:
        _default_auth_manager = AuthManager()
    return _default_auth_manager


def set_auth_manager(manager: AuthManager) -> None:
    """Set the default auth manager."""
    global _default_auth_manager
    _default_auth_manager = manager


__all__ = [
    "AuthConfig",
    "AuthManager",
    "User",
    "UserRole",
    "Session",
    "TokenPayload",
    "PasswordHasher",
    "JWTHandler",
    "AuthError",
    "InvalidCredentialsError",
    "TokenExpiredError",
    "TokenInvalidError",
    "UserExistsError",
    "UserNotFoundError",
    "SessionExpiredError",
    "AccountLockedError",
    "get_auth_manager",
    "set_auth_manager",
]
