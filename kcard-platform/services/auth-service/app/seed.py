from decimal import Decimal

from sqlalchemy import select

from shared.auth.passwords import hash_password
from shared.db import SessionLocal
from shared.domain import LedgerEntry, Merchant, MerchantUser, Vehicle, Wallet

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
        users = {}

        for email, full_name, password, assigned_roles in seed_users:
            user = db.scalar(select(User).where(User.email == email))
            if not user:
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
                db.flush()
            users[email] = user

        normal_user = users["user@kcard.local"]
        merchant_user = users["merchant@kcard.local"]

        merchant = db.scalar(select(Merchant).where(Merchant.name == "K-Card Demo Cabs"))
        if not merchant:
            merchant = Merchant(type="cab_owner", name="K-Card Demo Cabs", phone="+26370000000", payout_methods_enabled={"mpesa": True, "ecocash": True, "bank": True})
            db.add(merchant)
            db.flush()

        link = db.scalar(select(MerchantUser).where(MerchantUser.merchant_id == merchant.id, MerchantUser.user_id == merchant_user.id))
        if not link:
            db.add(MerchantUser(merchant_id=merchant.id, user_id=merchant_user.id, role_in_merchant="owner"))

        user_wallet = db.scalar(select(Wallet).where(Wallet.owner_type == "user", Wallet.owner_id == normal_user.id))
        if not user_wallet:
            user_wallet = Wallet(owner_type="user", owner_id=normal_user.id, currency="USD", available_balance=Decimal("120.00"), credit_balance=Decimal("0.00"))
            db.add(user_wallet)
            db.flush()

        merchant_wallet = db.scalar(select(Wallet).where(Wallet.owner_type == "merchant", Wallet.owner_id == merchant.id))
        if not merchant_wallet:
            merchant_wallet = Wallet(owner_type="merchant", owner_id=merchant.id, currency="USD", available_balance=Decimal("300.00"), credit_balance=Decimal("0.00"))
            db.add(merchant_wallet)
            db.flush()

        vehicle = db.scalar(select(Vehicle).where(Vehicle.plate_number == "KCD-001"))
        if not vehicle:
            db.add(Vehicle(merchant_id=merchant.id, type="cab", plate_number="KCD-001", model="Toyota Prius", active=True))

        existing_ledger = db.scalar(select(LedgerEntry).where(LedgerEntry.reference == "seed-topup-1"))
        if not existing_ledger:
            db.add(LedgerEntry(wallet_id=user_wallet.id, direction="credit", amount=Decimal("120.00"), currency="USD", type="topup", reference="seed-topup-1", meta_json={"provider": "card"}))

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed_roles_and_users()
