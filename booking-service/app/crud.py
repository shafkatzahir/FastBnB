from sqlalchemy.orm import Session
from . import models, schemas
import datetime  # <-- Make sure this is imported


def check_booking_conflict(db: Session, property_id: int, start_date: datetime.date, end_date: datetime.date) -> bool:
    """
    Checks if a new booking for a given property and date range conflicts
    with any existing bookings.

    Returns True if a conflict exists, False otherwise.
    """
    # The logic for an overlap is:
    # (Existing Start Date < New End Date) AND (Existing End Date > New Start Date)
    # This correctly finds any overlap, even partial, while allowing
    # bookings that "touch" (e.g., checkout and check-in on the same day).

    existing_booking = db.query(models.Booking).filter(
        models.Booking.property_id == property_id,
        models.Booking.start_date < end_date,  # Existing start is before new end
        models.Booking.end_date > start_date  # Existing end is after new start
    ).first()

    # If we find any booking that matches, a conflict exists.
    return existing_booking is not None

def create_booking(db: Session, booking: schemas.BookingCreate, user_id: int):
    db_booking = models.Booking(
        property_id=booking.property_id,
        user_id=user_id,
        start_date=booking.start_date,
        end_date=booking.end_date
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking

def get_bookings_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Booking).filter(models.Booking.user_id == user_id).offset(skip).limit(limit).all()
