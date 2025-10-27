from sqlalchemy import Column, Integer, Date, TIMESTAMP
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
