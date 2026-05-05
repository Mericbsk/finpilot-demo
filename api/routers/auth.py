"""Authentication endpoints for the web client and admin tooling."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from api.middleware.auth import require_auth
from auth.core import (
    AccountLockedError,
    AuthConfig,
    AuthError,
    AuthManager,
    InvalidCredentialsError,
    TokenExpiredError,
    TokenInvalidError,
    UserExistsError,
)
from auth.database import Database, SessionRepository, UserRepository
from auth.tokens import TokenPayload
from core.monitoring import metrics

router = APIRouter(tags=["auth"])


def _get_auth_manager() -> AuthManager:
    db = Database()
    db.initialize()
    user_repo = UserRepository(db)
    session_repo = SessionRepository(db)
    return AuthManager(
        config=AuthConfig(),
        user_repository=user_repo,
        session_repository=session_repo,
    )


def _get_user_by_id(user_id: str):
    db = Database()
    db.initialize()
    return UserRepository(db).get_by_id(user_id)


def _request_metadata(request: Request) -> dict[str, str | None]:
    client_host = request.client.host if request.client else None
    return {
        "device_info": request.headers.get("sec-ch-ua-platform") or request.headers.get("host"),
        "ip_address": client_host,
        "user_agent": request.headers.get("user-agent"),
    }


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=8, max_length=256)
    display_name: str | None = Field(default=None, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=8, max_length=256)
    remember_me: bool = False


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=16)


def _serialize_session(session, user) -> dict[str, object]:
    return {
        "session_id": session.id,
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
        "expires_at": session.expires_at.isoformat(),
        "user": user.to_dict(),
    }


@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, request: Request):
    auth = _get_auth_manager()

    try:
        user = auth.register(
            email=payload.email,
            username=payload.username,
            password=payload.password,
            display_name=payload.display_name,
        )
        session = auth.login(
            payload.email,
            payload.password,
            remember_me=True,
            **_request_metadata(request),
        )
    except UserExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    metrics.registrations.inc()
    metrics.login_attempts.inc(status="success")
    return _serialize_session(session, user)


@router.post("/auth/login")
def login(payload: LoginRequest, request: Request):
    auth = _get_auth_manager()

    try:
        session = auth.login(
            payload.email,
            payload.password,
            remember_me=payload.remember_me,
            **_request_metadata(request),
        )
        user = auth.get_current_user(session.access_token)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authenticated session created but user lookup failed.",
            )
    except AccountLockedError as exc:
        metrics.login_attempts.inc(status="locked")
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail=str(exc)) from exc
    except InvalidCredentialsError as exc:
        metrics.login_attempts.inc(status="failure")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    metrics.login_attempts.inc(status="success")
    return _serialize_session(session, user)


@router.post("/auth/refresh")
def refresh(payload: RefreshRequest):
    auth = _get_auth_manager()

    try:
        access_token, refresh_token = auth.refresh_tokens(payload.refresh_token)
        user = auth.get_current_user(access_token)
    except (TokenExpiredError, TokenInvalidError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user.to_dict(),
    }


@router.get("/auth/me")
def me(payload: Annotated[TokenPayload, Depends(require_auth)]):
    user = _get_user_by_id(payload.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user.to_dict()
