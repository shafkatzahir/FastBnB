import asyncio
import logging
from datetime import date, timedelta  # Import timedelta
from sqlalchemy.orm import Session
from .database import SessionLocal
from . import crud

# Get the logger
logger = logging.getLogger("booking_service")  # Use the main service logger

# --- THIS IS THE FIX FOR TESTING ---
# Set to 60 seconds for testing. Change back to 3600 (1 hour) for production.
POLL_INTERVAL_SECONDS = 60


async def check_and_update_expired_bookings(db: Session):
    """
    Checks for bookings that ended yesterday and sends an "AVAILABLE"
    event if the property has no other conflicting bookings.
    """

    # --- THIS IS THE LOGIC FIX ---
    # We check for bookings that ended *yesterday*, not today.
    target_date = date.today() - timedelta(days=1)

    logger.info(f"Checking for bookings that ended on {target_date}...")

    # 1. Find all bookings that ended yesterday
    expired_bookings = crud.get_bookings_ending_on_date(db, target_date)

    if not expired_bookings:
        logger.info("No bookings ended yesterday.")
        return

    logger.info(f"Found {len(expired_bookings)} bookings that ended yesterday.")

    properties_to_check = {b.property_id for b in expired_bookings}
    events_created = 0

    for prop_id in properties_to_check:
        # 2. Check if this property has any *future* bookings
        # We check from today onwards into the future.
        has_future_bookings = crud.check_booking_conflict(
            db,
            property_id=prop_id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365 * 10)  # 10 years in future
        )

        if not has_future_bookings:
            # 3. If no future bookings, this property is now AVAILABLE.
            # Create an outbox event to notify the backend service.
            try:
                crud.create_available_event_in_outbox(db, prop_id)
                events_created += 1
                logger.info(f"Property {prop_id} is now free. Creating 'AVAILABLE' event.")
            except Exception as e:
                logger.error(f"Failed to create 'AVAILABLE' event for property {prop_id}: {e}")
                db.rollback()  # Rollback this specific event creation
                continue  # Go to the next property
        else:
            logger.info(f"Property {prop_id} has other future bookings. Leaving as 'UNAVAILABLE'.")

    if events_created > 0:
        db.commit()  # Commit all new outbox events at once
        logger.info(f"Created {events_created} 'AVAILABLE' events in outbox.")
    else:
        db.rollback()  # No events, just rollback


async def run_booking_scheduler():
    """
    Main background loop for the scheduler.
    """
    while True:
        # Add a log to show the scheduler is waking up
        logger.info("Scheduler waking up to check for expired bookings...")
        db: Session = SessionLocal()
        try:
            await check_and_update_expired_bookings(db)
        except Exception as e:
            logger.error(f"Error in booking scheduler loop: {e}")
            db.rollback()
        finally:
            db.close()

        # Wait for the next poll interval
        await asyncio.sleep(POLL_INTERVAL_SECONDS)

