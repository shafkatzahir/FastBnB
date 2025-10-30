import asyncio
import logging
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError  # Import the error
from sqlalchemy.orm import Session
from sqlalchemy.sql import select

from .database import SessionLocal
from .models import OutboxEvent
from .config import settings

logger = logging.getLogger("outbox_poller")


async def run_outbox_poller(poll_interval: int = 5, retry_delay: int = 5, max_retries: int = 5):  # Add retry parameters
    """
    Continuously polls the OutboxEvent table and sends pending messages to Kafka.
    Includes retries for initial Kafka connection.
    """
    logger.info("Starting outbox poller...")

    producer = None
    retries = 0
    while producer is None and retries < max_retries:
        try:
            # Initialize producer
            producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS
            )
            await producer.start()
            logger.info(f"Outbox poller connected to Kafka on attempt {retries + 1}.")
            break  # Exit loop on success
        except KafkaConnectionError as e:
            retries += 1
            logger.warning(
                f"Kafka connection attempt {retries}/{max_retries} failed: {e}. Retrying in {retry_delay} seconds...")
            if producer:  # Ensure producer is stopped if start failed partially
                await producer.stop()
                producer = None
            if retries >= max_retries:
                logger.error("Outbox poller failed to connect to Kafka after multiple retries. Exiting.")
                return  # Exit the poller task if connection fails permanently
            await asyncio.sleep(retry_delay)  # Wait before retrying
        except Exception as e:  # Catch other potential errors during start
            logger.error(f"Unexpected error starting Kafka producer: {e}")
            if producer:
                await producer.stop()
            return  # Exit on unexpected error

    # If producer is still None after retries, exit
    if producer is None:
        return

    # --- Main polling loop (starts only if connection succeeded) ---
    try:
        while True:
            db: Session = SessionLocal()
            events_processed = 0
            try:
                stmt = select(OutboxEvent).where(
                    OutboxEvent.status == "PENDING"
                ).limit(100).with_for_update()

                result = db.execute(stmt)
                pending_events = result.scalars().all()

                if pending_events:
                    logger.info(f"Found {len(pending_events)} pending events in outbox.")

                    for event in pending_events:
                        try:
                            await producer.send_and_wait(
                                topic=event.topic,
                                value=event.payload.encode("utf-8")
                            )
                            db.delete(event)
                            events_processed += 1
                        except Exception as e:
                            logger.error(f"Failed to send event {event.id} to Kafka: {e}")
                            # Don't delete, will be retried next loop

                    if events_processed > 0:
                        db.commit()
                        logger.info(f"Successfully processed {events_processed} events.")

            except Exception as e:
                logger.error(f"Error in poller loop: {e}")
                db.rollback()
            finally:
                db.close()

            await asyncio.sleep(poll_interval)

    except asyncio.CancelledError:
        logger.info("Outbox poller task cancelled.")
    finally:
        if producer:  # Ensure producer exists before stopping
            logger.info("Stopping Kafka producer...")
            await producer.stop()
        logger.info("Outbox poller shut down.")




