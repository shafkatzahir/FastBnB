from sqlalchemy.orm import Session
from . import models, schemas
import datetime
import json
from .config import settings


def check_booking_conflict(db: Session, property_id: int, start_date: datetime.date, end_date: datetime.date) -> bool:
    """
    Checks if a new booking for a given property and date range conflicts
    with any existing bookings.
    """
    existing_booking = db.query(models.Booking).filter(
        models.Booking.property_id == property_id,
        models.Booking.start_date < end_date,
        models.Booking.end_date > start_date
    ).first()
    return existing_booking is not None


def create_booking(db: Session, booking: schemas.BookingCreate, user_id: int):
    """
    Atomically creates a Booking and its corresponding OutboxEvent.
    """
    try:
        # 1. Create the booking object
        db_booking = models.Booking(
            property_id=booking.property_id,
            user_id=user_id,
            start_date=booking.start_date,
            end_date=booking.end_date
        )

        # 2. Create the message payload
        message_payload = json.dumps({
            "property_id": db_booking.property_id,
            "status": "UNAVAILABLE"
        })

        # 3. Create the outbox event object
        db_outbox_event = models.OutboxEvent(
            topic=settings.KAFKA_PROPERTY_TOPIC,
            payload=message_payload,
            status="PENDING"
        )

        # 4. Add BOTH to the session
        db.add(db_booking)
        db.add(db_outbox_event)

        # 5. Commit the transaction
        # If this fails, *both* the booking and the event are rolled back.
        # This is the core of the pattern.
        db.commit()

        # 6. Refresh the booking to get its ID and return it
        db.refresh(db_booking)
        return db_booking

    except Exception as e:
        # If anything fails, roll back the transaction
        db.rollback()
        # Re-raise the exception to be handled by the router
        raise e


def get_bookings_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Booking).filter(models.Booking.user_id == user_id).offset(skip).limit(limit).all()
