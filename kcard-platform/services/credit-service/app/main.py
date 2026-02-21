import uuid
from decimal import Decimal

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from shared.authz import AuthContext, get_auth_context
from shared.db import Base, engine, get_db
from shared.domain import AuditLog, CreditEvent, CreditLine, LedgerEntry, Wallet

app = FastAPI(title="K-Card Credit Service", version="0.1.0")


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


class CreditRequest(BaseModel):
    limit_amount: Decimal = Field(gt=0)


class DrawRepayRequest(BaseModel):
    amount: Decimal = Field(gt=0)


def ensure_user_wallet(db: Session, user_id: uuid.UUID) -> Wallet:
    wallet = db.scalar(select(Wallet).where(Wallet.owner_type == 'user', Wallet.owner_id == user_id))
    if wallet:
        return wallet
    wallet = Wallet(owner_type='user', owner_id=user_id, currency='USD', available_balance=0, credit_balance=0)
    db.add(wallet)
    db.flush()
    return wallet


@app.get('/api/v1/health')
def health() -> dict[str, str]:
    return {"status": "ok", "service": "credit-service"}


@app.post('/api/v1/credit/eligibility-check')
def eligibility(ctx: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)) -> dict:
    _ = db
    return {"user_id": str(ctx.user_id), "eligible": True, "max_limit": 150.0, "reason": "MVP long-term heuristic"}


@app.post('/api/v1/credit/request')
def request_credit(payload: CreditRequest, ctx: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)) -> dict:
    line = db.scalar(select(CreditLine).where(CreditLine.user_id == ctx.user_id))
    if line:
        raise HTTPException(400, 'credit line exists')
    line = CreditLine(user_id=ctx.user_id, limit_amount=payload.limit_amount, available_amount=payload.limit_amount, status='approved', risk_tier='standard')
    db.add(line)
    db.add(CreditEvent(credit_line_id=line.id, event_type='approved', amount=payload.limit_amount, meta_json={}))
    db.commit()
    return {"credit_line_id": str(line.id), "status": line.status, "available_amount": float(line.available_amount)}


@app.post('/api/v1/credit/{credit_line_id}/draw')
def draw(credit_line_id: uuid.UUID, payload: DrawRepayRequest, ctx: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)) -> dict:
    line = db.scalar(select(CreditLine).where(CreditLine.id == credit_line_id, CreditLine.user_id == ctx.user_id))
    if not line:
        raise HTTPException(404, 'credit line not found')
    if Decimal(line.available_amount) < payload.amount:
        raise HTTPException(400, 'insufficient credit available')
    wallet = ensure_user_wallet(db, ctx.user_id)
    line.available_amount = Decimal(line.available_amount) - payload.amount
    wallet.credit_balance = Decimal(wallet.credit_balance) + payload.amount
    wallet.available_balance = Decimal(wallet.available_balance) + payload.amount
    db.add(CreditEvent(credit_line_id=line.id, event_type='draw', amount=payload.amount, meta_json={}))
    db.add(LedgerEntry(wallet_id=wallet.id, direction='credit', amount=payload.amount, currency='USD', type='credit_draw', reference=f'credit-draw-{uuid.uuid4()}', meta_json={}))
    db.add(AuditLog(actor_user_id=ctx.user_id, action='credit_draw', entity_type='credit_line', entity_id=str(line.id), meta_json={"amount": float(payload.amount)}))
    db.commit()
    return {"credit_line_id": str(line.id), "available_amount": float(line.available_amount)}


@app.post('/api/v1/credit/{credit_line_id}/repay')
def repay(credit_line_id: uuid.UUID, payload: DrawRepayRequest, ctx: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)) -> dict:
    line = db.scalar(select(CreditLine).where(CreditLine.id == credit_line_id, CreditLine.user_id == ctx.user_id))
    wallet = ensure_user_wallet(db, ctx.user_id)
    if not line:
        raise HTTPException(404, 'credit line not found')
    if Decimal(wallet.available_balance) < payload.amount:
        raise HTTPException(400, 'insufficient wallet balance')
    wallet.available_balance = Decimal(wallet.available_balance) - payload.amount
    wallet.credit_balance = max(Decimal('0'), Decimal(wallet.credit_balance) - payload.amount)
    line.available_amount = min(Decimal(line.limit_amount), Decimal(line.available_amount) + payload.amount)
    db.add(CreditEvent(credit_line_id=line.id, event_type='repay', amount=payload.amount, meta_json={}))
    db.add(LedgerEntry(wallet_id=wallet.id, direction='debit', amount=payload.amount, currency='USD', type='credit_repay', reference=f'credit-repay-{uuid.uuid4()}', meta_json={}))
    db.commit()
    return {"credit_line_id": str(line.id), "available_amount": float(line.available_amount)}


@app.get('/api/v1/credit/me')
def my_credit(ctx: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)) -> dict:
    line = db.scalar(select(CreditLine).where(CreditLine.user_id == ctx.user_id))
    if not line:
        return {"has_credit_line": False}
    events = db.scalars(select(CreditEvent).where(CreditEvent.credit_line_id == line.id).order_by(CreditEvent.created_at.desc())).all()
    return {"has_credit_line": True, "credit_line_id": str(line.id), "limit_amount": float(line.limit_amount), "available_amount": float(line.available_amount), "events": [{"event_type": e.event_type, "amount": float(e.amount)} for e in events]}
