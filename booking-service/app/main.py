from fastapi import FastAPI
from . import models
from .database import engine
from .routers import booking_router # <-- UPDATED: import router module
from .kafka_producer import connect_to_kafka, close_kafka_connection # <-- NEW

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Booking Service API",
    description="Handles property bookings.",
    version="1.0.0"
)

# --- NEW LIFECYCLE EVENTS ---
@app.on_event("startup")
async def startup_event():
    await connect_to_kafka()

@app.on_event("shutdown")
async def shutdown_event():
    await close_kafka_connection()
# --- END NEW ---

app.include_router(booking_router.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Booking Service"}
