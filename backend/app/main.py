import asyncio

from fastapi import FastAPI
from .routers import auth_router, property_router
from .database import engine
from . import models
from .kafka_consumer import consume_property_updates

# This command is not strictly necessary with Alembic but ensures tables are created if DB starts empty without migrations
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FastBnB API",
    description="A basic API for an Airbnb-like service.",
    version="1.0.0"
)
# --- NEW STARTUP EVENT ---
@app.on_event("startup")
async def startup_event():
    # Start the Kafka consumer in the background
    asyncio.create_task(consume_property_updates())

app.include_router(auth_router.router)
app.include_router(property_router.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the FastBnB API"}