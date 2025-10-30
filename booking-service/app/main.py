from fastapi import FastAPI
from . import models
from .database import engine
from .routers import booking_router
import asyncio
from contextlib import asynccontextmanager

# --- NEW IMPORTS ---
from .outbox_poller import run_outbox_poller, logger

# Create database tables (including the new outbox_events table)
# This runs on startup because it's at the module level
models.Base.metadata.create_all(bind=engine)


# --- NEW: Lifespan Manager ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    """
    logger.info("Booking Service starting up...")

    # Start the outbox poller as a background task
    poller_task = asyncio.create_task(run_outbox_poller())

    yield  # The application is now running

    # --- Code to run on shutdown ---
    logger.info("Booking Service shutting down...")
    poller_task.cancel()  # Request cancellation of the poller
    try:
        await poller_task  # Wait for the poller to shut down gracefully
    except asyncio.CancelledError:
        logger.info("Outbox poller successfully cancelled.")


# Pass the lifespan manager to the FastAPI app
app = FastAPI(
    title="Booking Service API",
    description="Handles property bookings.",
    version="1.0.0",
    lifespan=lifespan  # <-- Attach the lifespan here
)

# --- REMOVE OLD LIFECYCLE EVENTS ---
# The @app.on_event("startup") and @app.on_event("shutdown") are now gone.

app.include_router(booking_router.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to the Booking Service"}
