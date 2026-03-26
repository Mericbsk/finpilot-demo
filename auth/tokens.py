"""
Auth Tokens — JWT handling & TokenPayload model.

Extracted from auth/core.py (Sprint P8).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import jwt

from .core import TokenExpiredError, TokenInvalidError

__all__ = ["JWTHandler", "TokenPayload"]


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

    def to_dict(self) -> dict[str, Any]:
        return {
            "sub": self.sub,
            "exp": self.exp,
            "iat": self.iat,
            "jti": self.jti,
            "type": self.type,
            "role": self.role,
        }


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
        if algorithm not in self.SUPPORTED_ALGORITHMS:
            raise ValueError(f"Algorithm must be one of {self.SUPPORTED_ALGORITHMS}")
        self.secret_key = secret_key
        self.algorithm = algorithm

    def encode(self, payload: dict[str, Any]) -> str:
        """Create JWT token."""
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode(self, token: str, verify_exp: bool = True) -> dict[str, Any]:
        """Decode and verify JWT token."""
        try:
            options = {"verify_exp": verify_exp}
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm], options=options)
        except jwt.ExpiredSignatureError as exc:
            raise TokenExpiredError("Token has expired") from exc
        except jwt.InvalidSignatureError as exc:
            raise TokenInvalidError("Invalid token signature") from exc
        except jwt.DecodeError as e:
            raise TokenInvalidError(f"Invalid token format: {e}") from e
        except jwt.PyJWTError as e:
            raise TokenInvalidError(f"Token validation failed: {e}") from e

    def decode_without_verification(self, token: str) -> dict[str, Any]:
        """Decode token without signature verification. Only for debugging."""
        try:
            return jwt.decode(token, options={"verify_signature": False, "verify_exp": False})
        except jwt.DecodeError as e:
            raise TokenInvalidError(f"Invalid token format: {e}") from e
