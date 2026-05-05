"""FastAPI JWT authentication dependency.

Usage:
    from api.middleware.auth import require_auth, optional_auth, require_admin

    @router.get("/protected")
    def protected(user: TokenPayload = Depends(require_auth)):
        return {"user": user.sub}

    @router.get("/public-with-user")
    def public(user: TokenPayload | None = Depends(optional_auth)):
        ...
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from auth.core import AuthConfig, TokenExpiredError, TokenInvalidError
from auth.tokens import JWTHandler, TokenPayload

_bearer = HTTPBearer(auto_error=False)

_config = AuthConfig()
_jwt = JWTHandler(secret_key=_config.secret_key, algorithm=_config.algorithm)


def _extract_payload(
    credentials: HTTPAuthorizationCredentials | None,
) -> TokenPayload | None:
    """Decode Bearer token → TokenPayload or None."""
    if credentials is None:
        return None
    try:
        data = _jwt.decode(credentials.credentials)
        return TokenPayload(**{k: data[k] for k in TokenPayload.__dataclass_fields__})
    except (TokenExpiredError, TokenInvalidError, KeyError):
        return None


def require_auth(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> TokenPayload:
    """Dependency that **requires** a valid JWT.  Returns 401 otherwise."""
    payload = _extract_payload(credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if payload.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    return payload


def optional_auth(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> TokenPayload | None:
    """Dependency that optionally extracts a JWT.  Returns None if absent."""
    return _extract_payload(credentials)


def require_roles(*allowed_roles: str):
    """Build a dependency that requires one of the provided roles."""
    normalized_roles = {role.lower() for role in allowed_roles}

    def _require_role(
        payload: Annotated[TokenPayload, Depends(require_auth)],
    ) -> TokenPayload:
        if payload.role.lower() not in normalized_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This endpoint requires one of the following roles: {', '.join(sorted(normalized_roles))}",
            )
        return payload

    return _require_role


def require_admin(
    payload: Annotated[TokenPayload, Depends(require_auth)],
) -> TokenPayload:
    """Dependency that requires the caller to have the admin role."""
    return require_roles("admin")(payload)
