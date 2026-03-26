"""
Auth Sessions — Session model.

Extracted from auth/core.py (Sprint P8).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

__all__ = ["Session"]


@dataclass
class Session:
    """User session model."""

    id: str
    user_id: str

    # Token info
    access_token: str
    refresh_token: str

    # Metadata
    device_info: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(days=7))
    last_activity: datetime = field(default_factory=datetime.utcnow)

    # Status
    is_active: bool = True

    def to_dict(self) -> dict[str, Any]:
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
    def from_dict(cls, data: dict[str, Any]) -> Session:
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
