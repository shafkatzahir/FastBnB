# from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, TIMESTAMP
# from sqlalchemy.orm import relationship
# from app.database import Base
# from enum import Enum as PyEnum
# from sqlalchemy import Enum as SQLEnum
# import datetime
#
#
# # --- ENUM for User Roles ---
# class UserRole(PyEnum):
#     USER = "user"
#     ADMIN = "admin"
#
#
# # --- User Model ---
# class User(Base):
#     __tablename__ = "users"
#
#     id = Column(Integer, primary_key=True, index=True)
#     username = Column(String, unique=True, index=True, nullable=False)
#     hashed_password = Column(String, nullable=False)
#
#     # Store the user's role using an SQLAlchemy Enum, mapping to our Python Enum
#     role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
#
#     # For refresh token revocation/storage
#     refresh_token_hash = Column(String, nullable=True)
#
#     # Relationship to properties (if a property needs to track its owner/admin)
#     properties = relationship("Property", back_populates="owner")
#
#     # Relationship to future Bookings model (for users' past/current bookings)
#     # bookings = relationship("Booking", back_populates="user")
#
#
# # --- Property Model (Airbnb Listing) ---
# class Property(Base):
#     __tablename__ = "properties"
#
#     id = Column(Integer, primary_key=True, index=True)
#
#     # Property Details
#     location = Column(String, index=True, nullable=False)
#     description = Column(Text, nullable=False)
#     size_sqft = Column(Integer, nullable=False)
#     price_per_night = Column(Float, nullable=False)
#
#     # Renter's Name (We'll change this to the Admin's ID who listed it)
#     owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
#
#     # Metadata
#     created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
#
#     # Relationship back to the User who listed it
#     owner = relationship("User", back_populates="properties")

from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
#from backend.app.database import Base
from enum import Enum as PyEnum
from sqlalchemy import Enum as SQLEnum
import datetime

from app.database import Base


# --- ENUM for User Roles ---
class UserRole(PyEnum):
    USER = "user"
    ADMIN = "admin"


# +++ NEW: ENUM for Property Status +++
class PropertyStatus(PyEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


# --- User Model ---
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    refresh_token_hash = Column(String, nullable=True)
    properties = relationship("Property", back_populates="owner")


# --- Property Model (Airbnb Listing) ---
class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)

    # Property Details
    location = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=False)
    size_sqft = Column(Integer, nullable=False)
    price_per_night = Column(Float, nullable=False)

    # +++ NEW: Status column with a default value +++
    status = Column(SQLEnum(PropertyStatus), default=PropertyStatus.AVAILABLE, nullable=False)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    owner = relationship("User", back_populates="properties")

