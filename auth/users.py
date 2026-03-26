"""
Auth Users — PasswordHasher, User model & UserRole enum.

Extracted from auth/core.py (Sprint P8).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import bcrypt

__all__ = ["PasswordHasher", "User", "UserRole"]


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
    display_name: str | None = None
    avatar_url: str | None = None

    # Status
    role: UserRole = UserRole.USER
    is_active: bool = True
    is_verified: bool = False

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_login: datetime | None = None

    # Security
    failed_login_attempts: int = 0
    locked_until: datetime | None = None

    def to_dict(self, include_sensitive: bool = False) -> dict[str, Any]:
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
    def from_dict(cls, data: dict[str, Any]) -> User:
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


class PasswordHasher:
    """Secure password hashing using bcrypt."""

    def __init__(self, rounds: int = 12):
        self.rounds = rounds

    def hash(self, password: str, salt: str | None = None) -> tuple[str, str]:
        """Hash a password with bcrypt. Returns (hash, empty_salt)."""
        password_bytes = password.encode("utf-8")
        hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=self.rounds))
        return hashed.decode("utf-8"), ""

    def verify(self, password: str, password_hash: str, salt: str = "") -> bool:
        """Verify a password against stored bcrypt hash."""
        try:
            password_bytes = password.encode("utf-8")
            hash_bytes = password_hash.encode("utf-8")
            return bcrypt.checkpw(password_bytes, hash_bytes)
        except (ValueError, TypeError):
            return False

    @staticmethod
    def validate_strength(password: str, min_length: int = 8) -> tuple[bool, list[str]]:
        """Validate password strength. Returns (is_valid, issues)."""
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
        """Check if hash needs to be rehashed (e.g., old PBKDF2 → bcrypt)."""
        if not password_hash.startswith(("$2a$", "$2b$", "$2y$")):
            return True
        try:
            current_rounds = int(password_hash.split("$")[2])
            return current_rounds < self.rounds
        except (IndexError, ValueError):
            return True
