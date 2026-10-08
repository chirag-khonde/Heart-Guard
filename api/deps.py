"""FastAPI dependencies for authentication, authorization, and rate limiting."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from config.settings import SECRET_KEY

bearer_scheme = HTTPBearer(auto_error=False)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


class TokenPayload(BaseModel):
    user_id: int
    role: str
    name: str
    email: str
    exp: datetime | None = None


class CurrentUser(BaseModel):
    user_id: int
    role: str
    name: str
    email: str


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        role = payload.get("role")
        name = payload.get("name")
        email = payload.get("email")
        if user_id is None or role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
        return CurrentUser(user_id=int(user_id), role=str(role), name=str(name or ""), email=str(email or ""))
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


def require_role(*allowed_roles: str):
    allowed_upper = {r.upper() for r in allowed_roles}
    async def _check(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role.upper() not in allowed_upper:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' is not authorized for this endpoint",
            )
        return user
    return _check


_in_memory_rate_store: dict[str, list[float]] = {}


async def rate_limit_middleware(request: Request, call_next):
    from src.security.rate_limiter import check_rate_limit

    client_ip = request.client.host if request.client else "unknown"
    action = f"{request.method}:{request.url.path}"
    allowed, msg = check_rate_limit(action, client_ip)
    if not allowed:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=429, content={"detail": msg})

    response = await call_next(request)
    return response
