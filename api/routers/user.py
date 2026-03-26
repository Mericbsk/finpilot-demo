"""User settings & profile API — persists to SQLite via SettingsRepository."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(tags=["user"])

_DEFAULT_USER = "default"


class SettingsPayload(BaseModel):
    user_id: str = Field(_DEFAULT_USER, max_length=128)
    settings: dict[str, Any]


@router.get("/user/settings")
def get_settings(user_id: str = _DEFAULT_USER):
    """Load user settings from the DB."""
    from auth.database import Database, SettingsRepository

    db = Database()
    repo = SettingsRepository(db)
    data = repo.get_by_id(user_id)
    return {"user_id": user_id, "settings": data or {}}


@router.put("/user/settings")
def save_settings(payload: SettingsPayload):
    """Save (upsert) user settings to the DB."""
    from auth.database import Database, SettingsRepository

    db = Database()
    repo = SettingsRepository(db)
    repo.save(payload.settings, payload.user_id)
    return {"ok": True, "user_id": payload.user_id}


@router.patch("/user/settings")
def patch_settings(payload: SettingsPayload):
    """Merge partial updates into existing settings."""
    from auth.database import Database, SettingsRepository

    db = Database()
    repo = SettingsRepository(db)
    merged = repo.update(payload.user_id, payload.settings)
    return {"ok": True, "user_id": payload.user_id, "settings": merged}
