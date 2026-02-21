from sqlalchemy import select
from sqlalchemy.orm import Session

from shared.auth.jwt import create_token, decode_token
from shared.auth.passwords import hash_password, verify_password
from shared.schemas.common import TokenPair, UserPublic
from shared.settings import get_settings

from app.models.user import Role, User
from app.schemas import LoginRequest, RegisterRequest

settings = get_settings()


class AuthService:
    @staticmethod
    def register(db: Session, payload: RegisterRequest) -> UserPublic:
        existing = db.scalar(select(User).where(User.email == payload.email.lower()))
        if existing:
            raise ValueError("Email already registered")

        user_role = db.scalar(select(Role).where(Role.name == "USER"))
        if not user_role:
            user_role = Role(name="USER")
            db.add(user_role)
            db.flush()

        user = User(
            full_name=payload.full_name,
            email=payload.email.lower(),
            phone=payload.phone,
            password_hash=hash_password(payload.password),
            status="active",
        )
        user.roles.append(user_role)
        db.add(user)
        db.commit()
        db.refresh(user)
        return UserPublic(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            phone=user.phone,
            status=user.status,
            roles=[role.name for role in user.roles],
        )

    @staticmethod
    def login(db: Session, payload: LoginRequest) -> tuple[TokenPair, UserPublic]:
        user = db.scalar(select(User).where(User.email == payload.email.lower()))
        if not user or not verify_password(payload.password, user.password_hash):
            raise ValueError("Invalid credentials")

        roles = [role.name for role in user.roles]
        access = create_token(str(user.id), "access", settings.access_token_expire_minutes, {"roles": roles})
        refresh = create_token(str(user.id), "refresh", settings.refresh_token_expire_minutes, {"roles": roles})
        tokens = TokenPair(access_token=access, refresh_token=refresh)
        return (
            tokens,
            UserPublic(
                id=user.id,
                full_name=user.full_name,
                email=user.email,
                phone=user.phone,
                status=user.status,
                roles=roles,
            ),
        )

    @staticmethod
    def refresh(refresh_token: str) -> TokenPair:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")
        subject = payload["sub"]
        roles = payload.get("roles", [])
        access = create_token(subject, "access", settings.access_token_expire_minutes, {"roles": roles})
        new_refresh = create_token(subject, "refresh", settings.refresh_token_expire_minutes, {"roles": roles})
        return TokenPair(access_token=access, refresh_token=new_refresh)
