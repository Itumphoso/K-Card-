import uuid
from decimal import Decimal

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from shared.authz import AuthContext, get_auth_context, require_roles
from shared.db import Base, engine, get_db
from shared.domain import CabLocation, Merchant, Ride, Vehicle

app = FastAPI(title="K-Card Transport Service", version="0.1.0")


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


class MerchantRegister(BaseModel):
    type: str
    name: str
    phone: str | None = None


class VehicleRegister(BaseModel):
    merchant_id: uuid.UUID
    type: str
    plate_number: str
    model: str | None = None


class LocationRequest(BaseModel):
    lat: Decimal
    lng: Decimal


class RideRequest(BaseModel):
    pickup_lat: Decimal
    pickup_lng: Decimal
    dropoff_lat: Decimal
    dropoff_lng: Decimal
    fare_amount: Decimal = Decimal("0")


class AssignRequest(BaseModel):
    vehicle_id: uuid.UUID


class RideStatusRequest(BaseModel):
    status: str


@app.get('/api/v1/health')
def health() -> dict[str, str]:
    return {"status": "ok", "service": "transport-service"}


@app.post('/api/v1/merchants/register')
def register_merchant(payload: MerchantRegister, ctx: AuthContext = Depends(require_roles('MERCHANT', 'ADMIN')), db: Session = Depends(get_db)) -> dict:
    _ = ctx
    merchant = Merchant(type=payload.type, name=payload.name, phone=payload.phone, payout_methods_enabled={"mpesa": True, "ecocash": True, "bank": True})
    db.add(merchant)
    db.commit()
    return {"id": str(merchant.id), "name": merchant.name}


@app.post('/api/v1/vehicles/register')
def register_vehicle(payload: VehicleRegister, ctx: AuthContext = Depends(require_roles('MERCHANT', 'ADMIN')), db: Session = Depends(get_db)) -> dict:
    _ = ctx
    vehicle = Vehicle(**payload.model_dump())
    db.add(vehicle)
    db.commit()
    return {"id": str(vehicle.id), "plate_number": vehicle.plate_number}


@app.post('/api/v1/cabs/{vehicle_id}/location')
def vehicle_location(vehicle_id: uuid.UUID, payload: LocationRequest, ctx: AuthContext = Depends(require_roles('MERCHANT', 'ADMIN')), db: Session = Depends(get_db)) -> dict:
    _ = ctx
    vehicle = db.scalar(select(Vehicle).where(Vehicle.id == vehicle_id))
    if not vehicle:
        raise HTTPException(404, 'vehicle not found')
    loc = CabLocation(vehicle_id=vehicle_id, lat=payload.lat, lng=payload.lng)
    db.add(loc)
    db.commit()
    return {"vehicle_id": str(vehicle_id), "lat": float(payload.lat), "lng": float(payload.lng)}


@app.post('/api/v1/rides/request')
def request_ride(payload: RideRequest, ctx: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)) -> dict:
    ride = Ride(user_id=ctx.user_id, **payload.model_dump())
    db.add(ride)
    db.commit()
    return {"ride_id": str(ride.id), "status": ride.status}


@app.post('/api/v1/rides/{ride_id}/assign')
def assign_ride(ride_id: uuid.UUID, payload: AssignRequest, ctx: AuthContext = Depends(require_roles('MERCHANT', 'ADMIN')), db: Session = Depends(get_db)) -> dict:
    _ = ctx
    ride = db.scalar(select(Ride).where(Ride.id == ride_id))
    if not ride:
        raise HTTPException(404, 'ride not found')
    ride.vehicle_id = payload.vehicle_id
    ride.status = 'assigned'
    db.commit()
    return {"ride_id": str(ride.id), "status": ride.status}


@app.post('/api/v1/rides/{ride_id}/status')
def ride_status(ride_id: uuid.UUID, payload: RideStatusRequest, ctx: AuthContext = Depends(require_roles('MERCHANT', 'ADMIN')), db: Session = Depends(get_db)) -> dict:
    _ = ctx
    ride = db.scalar(select(Ride).where(Ride.id == ride_id))
    if not ride:
        raise HTTPException(404, 'ride not found')
    ride.status = payload.status
    db.commit()
    return {"ride_id": str(ride.id), "status": ride.status}


@app.get('/api/v1/rides/{ride_id}')
def get_ride(ride_id: uuid.UUID, ctx: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)) -> dict:
    _ = ctx
    ride = db.scalar(select(Ride).where(Ride.id == ride_id))
    if not ride:
        raise HTTPException(404, 'ride not found')
    latest_location = None
    if ride.vehicle_id:
        loc = db.scalar(select(CabLocation).where(CabLocation.vehicle_id == ride.vehicle_id).order_by(CabLocation.recorded_at.desc()))
        if loc:
            latest_location = {"lat": float(loc.lat), "lng": float(loc.lng)}
    return {"ride_id": str(ride.id), "status": ride.status, "fare_amount": float(ride.fare_amount), "driver_location": latest_location}
