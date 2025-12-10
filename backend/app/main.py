import asyncio
from fastapi import FastAPI
from .routers import auth_router, property_router
from .database import engine
from . import models
from .kafka_consumer import consume_property_updates
import logging
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi_limiter import FastAPILimiter
from .config import settings

# Set up a logger
logger = logging.getLogger("backend_main")

# This command is not strictly necessary with Alembic but ensures tables are created
models.Base.metadata.create_all(bind=engine)


# --- NEW: Lifespan Manager ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    """
    logger.info("Backend Service starting up...")

    # --- NEW: Initialize Redis and FastAPILimiter ---
    try:
        redis_client = redis.from_url(settings.REDIS_URL, encoding="utf-8")
        await FastAPILimiter.init(redis_client)
        logger.info("FastAPILimiter initialized with Redis.")
    except Exception as e:
        logger.error(f"Failed to initialize FastAPILimiter: {e}")
        # Depending on policy, you might want to exit if limiter fails
    # --- END NEW ---

    # Start the Kafka consumer in the background
    consumer_task = asyncio.create_task(consume_property_updates())

    yield  # The application is now running

    # --- Code to run on shutdown ---
    logger.info("Backend Service shutting down...")
    consumer_task.cancel()  # Request cancellation of the consumer

    # --- NEW: Close Redis connection ---
    await redis_client.close()
    # --- END NEW ---
    try:
        await consumer_task  # Wait for it to shut down
    except asyncio.CancelledError:
        logger.info("Kafka consumer successfully cancelled.")


app = FastAPI(
    title="FastBnB API",
    description="A basic API for an Airbnb-like service.",
    version="1.0.0",
    lifespan=lifespan  # <-- Attach the lifespan here
)

# --- REMOVE OLD STARTUP EVENT ---
# The @app.on_event("startup") decorator is now gone.

app.include_router(auth_router.router)
app.include_router(property_router.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to the FastBnB API"}
