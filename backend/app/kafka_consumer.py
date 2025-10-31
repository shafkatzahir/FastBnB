import json
import logging
import asyncio
from aiokafka import AIOKafkaConsumer
from sqlalchemy.orm import Session
from redis import Redis  # <-- NEW IMPORT

# Import the main session factory AND the redis_pool
from .database import SessionLocal, redis_pool  # <-- UPDATED IMPORT
from .config import settings
from . import crud, models

# Set up logger
logger = logging.getLogger("backend_consumer")


async def consume_property_updates():
    """
    Consumes messages from the property updates topic and updates the DB.
    """
    consumer = AIOKafkaConsumer(
        settings.KAFKA_PROPERTY_TOPIC,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="property_status_updater_group",
        auto_offset_reset="earliest"
    )

    logger.info("Starting Kafka consumer...")
    await consumer.start()
    logger.info("Kafka consumer started. Listening for messages...")

    # --- NEW: Manually create a Redis client from the pool ---
    # We can't use FastAPI's 'Depends' here, so we create it manually.
    redis_client: Redis | None = None
    try:
        redis_client = Redis(connection_pool=redis_pool)
        redis_client.ping()
        logger.info("Kafka consumer connected to Redis.")
    except Exception as e:
        logger.error(f"Kafka consumer FAILED to connect to Redis: {e}. Cache invalidation will be skipped.")

    try:
        async for msg in consumer:
            try:
                message = json.loads(msg.value.decode("utf-8"))
                property_id = message.get("property_id")
                status = message.get("status")

                if property_id is None or status is None:
                    logger.warning(f"Skipping malformed message: {message}")
                    continue

                logger.info(f"Received message: {message}")

                # Create a new DB session for this task
                db: Session = SessionLocal()
                try:
                    # Get the status enum from the string
                    status_enum = models.PropertyStatus[status.upper()]

                    # Call CRUD function to update the property
                    success = crud.update_property_status(
                        db=db,
                        property_id=property_id,
                        status=status_enum
                    )

                    if success:
                        logger.info(f"Successfully updated property {property_id} to {status}")

                        # --- THIS IS THE FIX ---
                        # If the DB update worked, invalidate the cache.
                        if redis_client:
                            try:
                                redis_client.delete(f"property_{property_id}")  # Delete specific property cache
                                redis_client.delete("all_properties")  # Delete the main list cache
                                logger.info(f"Invalidated Redis cache for property {property_id} and all_properties.")
                            except Exception as e:
                                logger.error(f"Failed to invalidate Redis cache: {e}")
                        # --- END OF FIX ---

                    else:
                        logger.warning(f"Property {property_id} not found for update.")
                finally:
                    db.close()

            except json.JSONDecodeError:
                logger.error(f"Failed to decode message: {msg.value}")
            except Exception as e:
                logger.error(f"Error processing message: {e}")
    finally:
        logger.info("Stopping Kafka consumer...")
        await consumer.stop()
        if redis_client:
            redis_client.close()  # Clean up the Redis client
