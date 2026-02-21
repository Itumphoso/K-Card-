from sqlalchemy import select

from shared.auth.passwords import hash_password
from shared.db import SessionLocal

from app.models.user import Role, User


def seed_roles_and_users() -> None:
    db = SessionLocal()
    try:
        role_names = ["ADMIN", "USER", "MERCHANT"]
        roles: dict[str, Role] = {}

        for role_name in role_names:
            role = db.scalar(select(Role).where(Role.name == role_name))
            if not role:
                role = Role(name=role_name)
                db.add(role)
                db.flush()
            roles[role_name] = role

        seed_users = [
            ("admin@kcard.local", "Admin User", "Admin123!", ["ADMIN"]),
            ("user@kcard.local", "Normal User", "User123!", ["USER"]),
            ("merchant@kcard.local", "Merchant User", "Merchant123!", ["MERCHANT"]),
        ]

        for email, full_name, password, assigned_roles in seed_users:
            user = db.scalar(select(User).where(User.email == email))
            if user:
                continue
            user = User(
                email=email,
                full_name=full_name,
                phone=None,
                status="active",
                password_hash=hash_password(password),
            )
            for role_name in assigned_roles:
                user.roles.append(roles[role_name])
            db.add(user)

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed_roles_and_users()
