import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from . import models
from .database import engine
from .routers import booking_router
from .outbox_poller import run_outbox_poller
from .booking_scheduler import run_booking_scheduler

# Setup logger
logger = logging.getLogger("booking_service")

# Create database tables on startup
# This will create both 'bookings' and 'outbox_events' if they don't exist
models.Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown events.
    """
    logger.info("Starting background tasks...")

    # Start the outbox poller as a background task
    poller_task = asyncio.create_task(run_outbox_poller())

    # Start the booking scheduler as a background task
    scheduler_task = asyncio.create_task(run_booking_scheduler())

    yield  # The application is now running

    # --- Code to run on shutdown ---
    logger.info("Shutting down background tasks...")

    # Cancel both tasks
    poller_task.cancel()
    scheduler_task.cancel()

    # Await their cancellation to allow for graceful shutdown
    try:
        await poller_task
    except asyncio.CancelledError:
        logger.info("Outbox poller task successfully cancelled.")
    except Exception as e:
        logger.error(f"Error during outbox poller shutdown: {e}")

    try:
        await scheduler_task
    except asyncio.CancelledError:
        logger.info("Booking scheduler task successfully cancelled.")
    except Exception as e:
        logger.error(f"Error during booking scheduler shutdown: {e}")


# Create the FastAPI app instance, passing the lifespan manager
app = FastAPI(
    title="Booking Service API",
    description="Handles property bookings.",
    version="1.0.0",
    lifespan=lifespan  # Use the new lifespan manager
)

# Include the API routes from booking_router.py
app.include_router(booking_router.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to the Booking Service"}

