"""User settings & profile API — persists to SQLite via SettingsRepository."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.middleware.auth import optional_auth
from auth.tokens import TokenPayload

router = APIRouter(tags=["user"])

_DEFAULT_USER = "default"


def _get_settings_repo():
    from auth.database import Database, SettingsRepository

    db = Database()
    db.initialize()
    return SettingsRepository(db)


def _resolve_user_id(
    requested_user_id: str,
    user: TokenPayload | None,
) -> str:
    if user is not None:
        return user.user_id

    if requested_user_id != _DEFAULT_USER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Anonymous access is limited to the default demo profile.",
        )

    return _DEFAULT_USER


class SettingsPayload(BaseModel):
    user_id: str = Field(_DEFAULT_USER, max_length=128)
    settings: dict[str, Any]


@router.get("/user/settings")
def get_settings(
    user_id: str = _DEFAULT_USER,
    user: Annotated[TokenPayload | None, Depends(optional_auth)] = None,
):
    """Load user settings from the DB."""
    repo = _get_settings_repo()
    effective_user_id = _resolve_user_id(user_id, user)
    data = repo.get_by_id(effective_user_id)
    return {"user_id": effective_user_id, "settings": data or {}}


@router.put("/user/settings")
def save_settings(
    payload: SettingsPayload,
    user: Annotated[TokenPayload | None, Depends(optional_auth)] = None,
):
    """Save (upsert) user settings to the DB."""
    repo = _get_settings_repo()
    effective_user_id = _resolve_user_id(payload.user_id, user)
    repo.save(payload.settings, effective_user_id)
    return {"ok": True, "user_id": effective_user_id}


@router.patch("/user/settings")
def patch_settings(
    payload: SettingsPayload,
    user: Annotated[TokenPayload | None, Depends(optional_auth)] = None,
):
    """Merge partial updates into existing settings."""
    repo = _get_settings_repo()
    effective_user_id = _resolve_user_id(payload.user_id, user)
    merged = repo.update(effective_user_id, payload.settings)
    return {"ok": True, "user_id": effective_user_id, "settings": merged}
