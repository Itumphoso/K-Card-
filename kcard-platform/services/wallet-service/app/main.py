import uuid
from decimal import Decimal

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from shared.authz import AuthContext, get_auth_context
from shared.db import Base, engine, get_db
from shared.domain import AuditLog, LedgerEntry, Merchant, PaymentIntent, Wallet

app = FastAPI(title="K-Card Wallet Service", version="0.1.0")


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


class TopupRequest(BaseModel):
    provider: str
    amount: Decimal = Field(gt=0)


class PayRequest(BaseModel):
    merchant_id: uuid.UUID | None = None
    qr_payload: str | None = None
    amount: Decimal = Field(gt=0)


class QRRequest(BaseModel):
    merchant_id: uuid.UUID | None = None
    amount: Decimal | None = None


def ensure_wallet(db: Session, owner_type: str, owner_id: uuid.UUID) -> Wallet:
    wallet = db.scalar(select(Wallet).where(Wallet.owner_type == owner_type, Wallet.owner_id == owner_id))
    if wallet:
        return wallet
    wallet = Wallet(owner_type=owner_type, owner_id=owner_id, currency="USD", available_balance=0, credit_balance=0)
    db.add(wallet)
    db.flush()
    return wallet


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "wallet-service"}


@app.get("/api/v1/wallets/me")
def me(ctx: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)) -> dict:
    wallet = ensure_wallet(db, "user", ctx.user_id)
    db.commit()
    return {"id": str(wallet.id), "available_balance": float(wallet.available_balance), "credit_balance": float(wallet.credit_balance)}


@app.get("/api/v1/wallets/{wallet_id}/ledger")
def ledger(wallet_id: uuid.UUID, ctx: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)) -> list[dict]:
    _ = ctx
    entries = db.scalars(select(LedgerEntry).where(LedgerEntry.wallet_id == wallet_id).order_by(LedgerEntry.created_at.desc())).all()
    return [{"id": str(e.id), "type": e.type, "direction": e.direction, "amount": float(e.amount), "reference": e.reference, "created_at": e.created_at} for e in entries]


@app.post("/api/v1/wallets/topup-intent")
def topup(payload: TopupRequest, ctx: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)) -> dict:
    wallet = ensure_wallet(db, "user", ctx.user_id)
    ref = f"topup-{uuid.uuid4()}"
    wallet.available_balance = Decimal(wallet.available_balance) + payload.amount
    db.add(LedgerEntry(wallet_id=wallet.id, direction="credit", amount=payload.amount, currency="USD", type="topup", reference=ref, meta_json={"provider": payload.provider}))
    db.add(AuditLog(actor_user_id=ctx.user_id, action="wallet_topup", entity_type="wallet", entity_id=str(wallet.id), meta_json={"amount": float(payload.amount)}))
    db.commit()
    return {"status": "succeeded", "reference": ref, "balance": float(wallet.available_balance)}


@app.post("/api/v1/wallets/pay")
def pay(payload: PayRequest, ctx: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)) -> dict:
    payer = ensure_wallet(db, "user", ctx.user_id)
    merchant_id = payload.merchant_id
    if payload.qr_payload and not merchant_id:
        try:
            merchant_id = uuid.UUID(payload.qr_payload.split(":")[-1])
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail="Invalid QR payload") from exc
    if not merchant_id:
        raise HTTPException(status_code=400, detail="merchant_id or qr_payload required")
    merchant_wallet = ensure_wallet(db, "merchant", merchant_id)
    if Decimal(payer.available_balance) < payload.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    ref = f"pay-{uuid.uuid4()}"
    payer.available_balance = Decimal(payer.available_balance) - payload.amount
    merchant_wallet.available_balance = Decimal(merchant_wallet.available_balance) + payload.amount
    db.add(LedgerEntry(wallet_id=payer.id, direction="debit", amount=payload.amount, currency="USD", type="payment", reference=ref, meta_json={"to": str(merchant_id)}))
    db.add(LedgerEntry(wallet_id=merchant_wallet.id, direction="credit", amount=payload.amount, currency="USD", type="payment", reference=ref, meta_json={"from": str(ctx.user_id)}))
    db.add(PaymentIntent(payer_wallet_id=payer.id, payee_wallet_id=merchant_wallet.id, amount=payload.amount, provider="card", status="succeeded", idempotency_key=f"{ctx.user_id}:{ref}"))
    db.commit()
    return {"status": "paid", "reference": ref}


@app.post("/api/v1/wallets/qr/generate")
def generate_qr(payload: QRRequest, ctx: AuthContext = Depends(get_auth_context)) -> dict:
    merchant_or_user = payload.merchant_id or ctx.user_id
    return {"qr_payload": f"kcard:merchant:{merchant_or_user}", "amount": float(payload.amount or 0)}
