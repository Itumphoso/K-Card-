from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from shared.auth.jwt import decode_token

security = HTTPBearer(auto_error=True)


@dataclass
class AuthContext:
    user_id: UUID
    roles: list[str]


def get_auth_context(credentials: HTTPAuthorizationCredentials = Depends(security)) -> AuthContext:
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise ValueError("wrong token type")
        return AuthContext(user_id=UUID(payload["sub"]), roles=payload.get("roles", []))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth token") from exc


def require_roles(*allowed: str):
    def checker(ctx: AuthContext = Depends(get_auth_context)) -> AuthContext:
        if not any(role in ctx.roles for role in allowed):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return ctx

    return checker
