import json
import datetime
from sqlalchemy.orm import Session
from . import models, schemas
from .config import settings  # Need this for the topic name


def check_booking_conflict(db: Session, property_id: int, start_date: datetime.date, end_date: datetime.date) -> bool:
    """
    Checks if a new booking for a given property and date range conflicts
    with any existing bookings.

    Returns True if a conflict exists, False otherwise.
    """
    # The logic for an overlap is:
    # (Existing Start Date < New End Date) AND (Existing End Date > New Start Date)
    existing_booking = db.query(models.Booking).filter(
        models.Booking.property_id == property_id,
        models.Booking.start_date < end_date,  # Existing start is before new end
        models.Booking.end_date > start_date  # Existing end is after new start
    ).first()

    return existing_booking is not None


def create_booking(db: Session, booking: schemas.BookingCreate, user_id: int):
    """
    Atomically creates a new booking and an outbox event.
    """
    # 1. Create the booking object
    db_booking = models.Booking(
        property_id=booking.property_id,
        user_id=user_id,
        start_date=booking.start_date,
        end_date=booking.end_date
    )

    # 2. Create the Kafka message payload
    payload = {
        "property_id": db_booking.property_id,
        "status": "UNAVAILABLE"
    }

    # 3. Create the outbox event object
    db_outbox_event = models.OutboxEvent(
        topic=settings.KAFKA_PROPERTY_TOPIC,
        payload=json.dumps(payload),
        status="PENDING"
    )

    # 4. Add BOTH to the session
    db.add(db_booking)
    db.add(db_outbox_event)

    # 5. Commit the transaction (atomically)
    db.commit()

    # 6. Refresh the booking object to get its ID
    db.refresh(db_booking)
    return db_booking


def get_bookings_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Booking).filter(models.Booking.user_id == user_id).offset(skip).limit(limit).all()


# --- New functions for the scheduler ---

def get_bookings_ending_on_date(db: Session, end_date: datetime.date) -> list[models.Booking]:
    """
    Retrieves all bookings that officially ended on the specified date.
    """
    return db.query(models.Booking).filter(models.Booking.end_date == end_date).all()


def create_available_event_in_outbox(db: Session, property_id: int):
    """
    Creates an 'AVAILABLE' event in the outbox table.
    Note: Does NOT commit. The calling scheduler function is responsible for the commit.
    """
    # 1. Create the Kafka message payload
    payload = {
        "property_id": property_id,
        "status": "AVAILABLE"
    }

    # 2. Create the outbox event object
    db_outbox_event = models.OutboxEvent(
        topic=settings.KAFKA_PROPERTY_TOPIC,
        payload=json.dumps(payload),
        status="PENDING"
    )

    # 3. Add to the session
    db.add(db_outbox_event)

