from shared.db import Base, engine
from fastapi import FastAPI

from app.api.routes import router
from app.seed import seed_roles_and_users

app = FastAPI(title="K-Card Auth Service", version="0.1.0")
@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    seed_roles_and_users()

app.include_router(router)
