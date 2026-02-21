import uuid

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from shared.db import Base, engine, get_db
from shared.domain import PaymentIntent

app = FastAPI(title="K-Card Payments Service", version="0.1.0")


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


class ConfirmRequest(BaseModel):
    intent_id: uuid.UUID
    status: str


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "payments-service"}


@app.post("/api/v1/payments/confirm")
def confirm(payload: ConfirmRequest, db: Session = Depends(get_db)) -> dict:
    intent = db.scalar(select(PaymentIntent).where(PaymentIntent.id == payload.intent_id))
    if not intent:
        raise HTTPException(status_code=404, detail="intent not found")
    intent.status = payload.status
    db.commit()
    return {"id": str(intent.id), "status": intent.status}


@app.get("/api/v1/payments/{intent_id}")
def get_payment(intent_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    intent = db.scalar(select(PaymentIntent).where(PaymentIntent.id == intent_id))
    if not intent:
        raise HTTPException(status_code=404, detail="intent not found")
    return {"id": str(intent.id), "amount": float(intent.amount), "provider": intent.provider, "status": intent.status, "idempotency_key": intent.idempotency_key}
