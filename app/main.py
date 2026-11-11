"""App entry point. Run with:  uvicorn app.main:app --reload"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1 import admin, auth, cart, orders, restaurants
from app.core.config import settings
from app.db.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create any missing tables when the server starts.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(restaurants.router, prefix="/api/v1")
app.include_router(cart.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


@app.get("/", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}
