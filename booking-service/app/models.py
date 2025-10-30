

from sqlalchemy import Column, Integer, Date, TIMESTAMP, String, Text, Index
from .database import Base
import datetime


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)

    # These are just IDs from other services.
    # No direct DB relationship is enforced.
    property_id = Column(Integer, index=True, nullable=False)
    user_id = Column(Integer, index=True, nullable=False)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id = Column(Integer, primary_key=True, index=True)

    # Status to track if the event has been sent
    status = Column(String(20), default="PENDING", nullable=False)

    # The Kafka topic to send the message to
    topic = Column(String(255), nullable=False)

    # The full JSON payload to be sent
    payload = Column(Text, nullable=False)

    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)

    # An index on 'status' will make the poller's query much faster
    __table_args__ = (
        Index('ix_outbox_events_status', 'status'),
    )
