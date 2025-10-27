import json
import logging
from aiokafka import AIOKafkaProducer
from fastapi import Depends
from .config import settings

# Set up logger
logger = logging.getLogger("booking_service")

# Global producer instance
producer: AIOKafkaProducer | None = None

async def get_kafka_producer() -> AIOKafkaProducer:
    if producer is None:
        raise Exception("Kafka producer is not initialized")
    return producer

async def connect_to_kafka():
    global producer
    logger.info("Connecting to Kafka...")
    try:
        producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS
        )
        await producer.start()
        logger.info("Connected to Kafka successfully.")
    except Exception as e:
        logger.error(f"Failed to connect to Kafka: {e}")
        # In a real app, you might want to handle this more gracefully
        # (e.g., retry connection)
        raise

async def close_kafka_connection():
    global producer
    if producer:
        logger.info("Closing Kafka connection...")
        await producer.stop()
        logger.info("Kafka connection closed.")

async def send_property_update(property_id: int, status: str):
    """
    Sends a message to Kafka to update a property's status.
    """
    producer = await get_kafka_producer()
    message = {
        "property_id": property_id,
        "status": status
    }
    try:
        await producer.send_and_wait(
            settings.KAFKA_PROPERTY_TOPIC,
            json.dumps(message).encode("utf-8")
        )
        logger.info(f"Sent message to topic {settings.KAFKA_PROPERTY_TOPIC}: {message}")
    except Exception as e:
        logger.error(f"Failed to send message to Kafka: {e}")