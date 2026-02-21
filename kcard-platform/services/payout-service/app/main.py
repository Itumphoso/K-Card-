import uuid
from decimal import Decimal

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from shared.authz import AuthContext, require_roles
from shared.db import Base, engine, get_db
from shared.domain import AuditLog, LedgerEntry, Payout, Wallet

app = FastAPI(title="K-Card Payout Service", version="0.1.0")


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


class PayoutRequest(BaseModel):
    merchant_id: uuid.UUID
    amount: Decimal = Field(gt=0)
    destination_type: str
    destination_ref: str


@app.get('/api/v1/health')
def health() -> dict[str, str]:
    return {"status": "ok", "service": "payout-service"}


@app.post('/api/v1/payouts/request')
def request_payout(payload: PayoutRequest, ctx: AuthContext = Depends(require_roles('MERCHANT')), db: Session = Depends(get_db)) -> dict:
    wallet = db.scalar(select(Wallet).where(Wallet.owner_type == 'merchant', Wallet.owner_id == payload.merchant_id))
    if not wallet:
        raise HTTPException(404, 'merchant wallet not found')
    if Decimal(wallet.available_balance) < payload.amount:
        raise HTTPException(400, 'insufficient merchant balance')
    payout = Payout(merchant_id=payload.merchant_id, wallet_id=wallet.id, amount=payload.amount, destination_type=payload.destination_type, destination_ref=payload.destination_ref)
    db.add(payout)
    db.add(AuditLog(actor_user_id=ctx.user_id, action='payout_requested', entity_type='payout', entity_id=str(payout.id), meta_json={"amount": float(payload.amount)}))
    db.commit()
    return {"id": str(payout.id), "status": payout.status}


@app.get('/api/v1/payouts')
def list_payouts(ctx: AuthContext = Depends(require_roles('MERCHANT', 'ADMIN')), db: Session = Depends(get_db)) -> list[dict]:
    _ = ctx
    payouts = db.scalars(select(Payout).order_by(Payout.created_at.desc())).all()
    return [{"id": str(p.id), "merchant_id": str(p.merchant_id), "amount": float(p.amount), "status": p.status} for p in payouts]


@app.post('/api/v1/payouts/{payout_id}/approve')
def approve(payout_id: uuid.UUID, ctx: AuthContext = Depends(require_roles('ADMIN')), db: Session = Depends(get_db)) -> dict:
    _ = ctx
    payout = db.scalar(select(Payout).where(Payout.id == payout_id))
    if not payout:
        raise HTTPException(404, 'payout not found')
    payout.status = 'approved'
    db.commit()
    return {"id": str(payout.id), "status": payout.status}


@app.post('/api/v1/payouts/{payout_id}/mark-paid')
def mark_paid(payout_id: uuid.UUID, ctx: AuthContext = Depends(require_roles('ADMIN')), db: Session = Depends(get_db)) -> dict:
    _ = ctx
    payout = db.scalar(select(Payout).where(Payout.id == payout_id))
    if not payout:
        raise HTTPException(404, 'payout not found')
    wallet = db.scalar(select(Wallet).where(Wallet.id == payout.wallet_id))
    if not wallet:
        raise HTTPException(404, 'wallet not found')
    wallet.available_balance = Decimal(wallet.available_balance) - Decimal(payout.amount)
    payout.status = 'paid'
    db.add(LedgerEntry(wallet_id=wallet.id, direction='debit', amount=payout.amount, currency='USD', type='payout', reference=f'payout-{payout.id}', meta_json={}))
    db.commit()
    return {"id": str(payout.id), "status": payout.status}
