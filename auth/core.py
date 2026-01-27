"""
Core Authentication Module for FinPilot.

Provides JWT-based authentication, user management, and session handling.
"""

from __future__ import annotations

import json
import logging
import os
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# Security packages - Sprint 1
import bcrypt
import jwt

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================


@dataclass
class AuthConfig:
    """Authentication configuration."""

    # JWT Settings
    secret_key: str = field(
        default_factory=lambda: os.getenv("FINPILOT_SECRET_KEY", secrets.token_hex(32))
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
# DATA MODELS
# ============================================================================


class UserRole(Enum):
    """User roles for authorization."""

    GUEST = "guest"
    USER = "user"
    PREMIUM = "premium"
    ADMIN = "admin"


@dataclass
class User:
    """User model."""

    id: str
    email: str
    username: str
    password_hash: str
    salt: str

    # Profile
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None

    # Status
    role: UserRole = UserRole.USER
    is_active: bool = True
    is_verified: bool = False

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

    # Security
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None

    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "display_name": self.display_name or self.username,
            "avatar_url": self.avatar_url,
            "role": self.role.value,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }

        if include_sensitive:
            data["password_hash"] = self.password_hash
            data["salt"] = self.salt
            data["failed_login_attempts"] = self.failed_login_attempts
            data["locked_until"] = self.locked_until.isoformat() if self.locked_until else None

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            email=data["email"],
            username=data["username"],
            password_hash=data.get("password_hash", ""),
            salt=data.get("salt", ""),
            display_name=data.get("display_name"),
            avatar_url=data.get("avatar_url"),
            role=UserRole(data.get("role", "user")),
            is_active=data.get("is_active", True),
            is_verified=data.get("is_verified", False),
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if isinstance(data.get("created_at"), str)
                else data.get("created_at", datetime.utcnow())
            ),
            updated_at=(
                datetime.fromisoformat(data["updated_at"])
                if isinstance(data.get("updated_at"), str)
                else data.get("updated_at", datetime.utcnow())
            ),
            last_login=(
                datetime.fromisoformat(data["last_login"]) if data.get("last_login") else None
            ),
            failed_login_attempts=data.get("failed_login_attempts", 0),
            locked_until=(
                datetime.fromisoformat(data["locked_until"]) if data.get("locked_until") else None
            ),
        )

    @property
    def is_locked(self) -> bool:
        """Check if account is locked."""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until


@dataclass
class Session:
    """User session model."""

    id: str
    user_id: str

    # Token info
    access_token: str
    refresh_token: str

    # Metadata
    device_info: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(days=7))
    last_activity: datetime = field(default_factory=datetime.utcnow)

    # Status
    is_active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "device_info": self.device_info,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        return cls(
            id=data["id"],
            user_id=data["user_id"],
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            device_info=data.get("device_info"),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if isinstance(data.get("created_at"), str)
                else datetime.utcnow()
            ),
            expires_at=(
                datetime.fromisoformat(data["expires_at"])
                if isinstance(data.get("expires_at"), str)
                else datetime.utcnow() + timedelta(days=7)
            ),
            last_activity=(
                datetime.fromisoformat(data["last_activity"])
                if isinstance(data.get("last_activity"), str)
                else datetime.utcnow()
            ),
            is_active=data.get("is_active", True),
        )

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at


@dataclass
class TokenPayload:
    """JWT token payload."""

    sub: str  # user_id
    exp: int  # expiration timestamp
    iat: int  # issued at timestamp
    jti: str  # unique token id
    type: str  # "access" or "refresh"
    role: str  # user role

    @property
    def user_id(self) -> str:
        """Alias for sub field."""
        return self.sub

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sub": self.sub,
            "exp": self.exp,
            "iat": self.iat,
            "jti": self.jti,
            "type": self.type,
            "role": self.role,
        }


# ============================================================================
# PASSWORD UTILITIES
# ============================================================================


class PasswordHasher:
    """
    Secure password hashing using bcrypt.

    bcrypt automatically handles salt generation and includes it in the hash,
    making it resistant to rainbow table attacks and timing attacks.

    The work factor (rounds) determines computational cost:
    - Default 12 = ~250ms on modern hardware
    - Each +1 doubles the time
    """

    def __init__(self, rounds: int = 12):
        """
        Initialize password hasher.

        Args:
            rounds: bcrypt work factor (12 = recommended, 10-14 = acceptable)
        """
        self.rounds = rounds

    def hash(self, password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """
        Hash a password with bcrypt.

        Note: bcrypt generates its own salt internally. The salt parameter
        is ignored but kept for backward compatibility with existing code.

        Returns:
            (hash, empty_salt) tuple - salt is embedded in hash
        """
        password_bytes = password.encode("utf-8")
        hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=self.rounds))

        # bcrypt hash includes salt, return empty string for salt field
        return hashed.decode("utf-8"), ""

    def verify(self, password: str, password_hash: str, salt: str = "") -> bool:
        """
        Verify a password against stored bcrypt hash.

        Args:
            password: Plain text password to verify
            password_hash: bcrypt hash string
            salt: Ignored (kept for backward compatibility)

        Returns:
            True if password matches
        """
        try:
            password_bytes = password.encode("utf-8")
            hash_bytes = password_hash.encode("utf-8")
            return bcrypt.checkpw(password_bytes, hash_bytes)
        except (ValueError, TypeError):
            # Invalid hash format
            return False

    @staticmethod
    def validate_strength(password: str, min_length: int = 8) -> Tuple[bool, List[str]]:
        """
        Validate password strength.

        Returns:
            (is_valid, list of issues)
        """
        issues = []

        if len(password) < min_length:
            issues.append(f"En az {min_length} karakter olmalı")

        if not any(c.isupper() for c in password):
            issues.append("En az bir büyük harf içermeli")

        if not any(c.islower() for c in password):
            issues.append("En az bir küçük harf içermeli")

        if not any(c.isdigit() for c in password):
            issues.append("En az bir rakam içermeli")

        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            issues.append("En az bir özel karakter içermeli (!@#$%^&*...)")

        return len(issues) == 0, issues

    def needs_rehash(self, password_hash: str) -> bool:
        """
        Check if password hash needs to be rehashed.

        Useful for migrating from old PBKDF2 hashes to bcrypt.

        Args:
            password_hash: Current hash to check

        Returns:
            True if hash is not a valid bcrypt hash or uses old settings
        """
        # bcrypt hashes start with $2a$, $2b$, or $2y$
        if not password_hash.startswith(("$2a$", "$2b$", "$2y$")):
            return True

        try:
            # Check if rounds match current setting
            current_rounds = int(password_hash.split("$")[2])
            return current_rounds < self.rounds
        except (IndexError, ValueError):
            return True


# ============================================================================
# JWT UTILITIES
# ============================================================================


class JWTHandler:
    """
    JWT handling using PyJWT library.

    PyJWT provides secure, standards-compliant JWT implementation with:
    - Proper signature verification
    - Automatic expiration checking
    - Support for multiple algorithms
    """

    SUPPORTED_ALGORITHMS = {"HS256", "HS384", "HS512"}

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        """
        Initialize JWT handler.

        Args:
            secret_key: Secret key for signing tokens (min 32 chars recommended)
            algorithm: Signing algorithm (HS256, HS384, HS512)
        """
        if algorithm not in self.SUPPORTED_ALGORITHMS:
            raise ValueError(f"Algorithm must be one of {self.SUPPORTED_ALGORITHMS}")

        self.secret_key = secret_key
        self.algorithm = algorithm

    def encode(self, payload: Dict[str, Any]) -> str:
        """
        Create JWT token.

        Args:
            payload: Token payload data (must include 'exp' for expiration)

        Returns:
            JWT token string
        """
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode(self, token: str, verify_exp: bool = True) -> Dict[str, Any]:
        """
        Decode and verify JWT token.

        Args:
            token: JWT token string
            verify_exp: Whether to verify expiration (default True)

        Returns:
            Decoded payload

        Raises:
            TokenInvalidError: If token is malformed or signature invalid
            TokenExpiredError: If token has expired
        """
        try:
            options = {"verify_exp": verify_exp}

            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm], options=options)

        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token has expired")
        except jwt.InvalidSignatureError:
            raise TokenInvalidError("Invalid token signature")
        except jwt.DecodeError as e:
            raise TokenInvalidError(f"Invalid token format: {e}")
        except jwt.PyJWTError as e:
            raise TokenInvalidError(f"Token validation failed: {e}")

    def decode_without_verification(self, token: str) -> Dict[str, Any]:
        """
        Decode token without signature verification.

        WARNING: Only use for debugging or reading expired token claims.
        Never trust data from this method for authentication!

        Args:
            token: JWT token string

        Returns:
            Decoded payload (unverified)
        """
        try:
            return jwt.decode(token, options={"verify_signature": False, "verify_exp": False})
        except jwt.DecodeError as e:
            raise TokenInvalidError(f"Invalid token format: {e}")


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
