# In FastBnB/booking-service/routers/booking_router.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Annotated
from jose import jwt, JWTError
import httpx

# --- NEW/CHANGED IMPORTS ---
# We will use APIKeyHeader to get a simple text box for the token
from fastapi.security import APIKeyHeader

from .. import schemas, crud
from ..database import get_db
from ..config import settings
from ..kafka_producer import send_property_update

router = APIRouter(prefix="/bookings", tags=["Bookings"])

# --- NEW: Define the security scheme ---
# This tells FastAPI we expect an "Authorization" header.
# This will give us the simple "Authorize" button and text box.
api_key_header = APIKeyHeader(name="Authorization")


# --- UPDATED FUNCTION ---
async def get_current_user_id_from_token(
        # Depend on the new header scheme
        token: Annotated[str, Depends(api_key_header)]
):
    """
    Decodes the JWT from the 'Authorization: Bearer ...' header to get the user ID.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # The token will be passed as "Bearer eyJhbGci..."
        # We must split it.
        scheme, jwt_token = token.split()
        if scheme.lower() != "bearer":
            raise credentials_exception

        payload = jwt.decode(jwt_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(payload.get("sub"))
        if user_id is None:
            raise credentials_exception
        return user_id
    except (JWTError, ValueError, AttributeError):
        raise credentials_exception


@router.post("/", response_model=schemas.BookingRead, status_code=status.HTTP_201_CREATED)
async def create_booking(
        booking: schemas.BookingCreate,
        user_id: Annotated[int, Depends(get_current_user_id_from_token)],
        db: Session = Depends(get_db)
):
    """
    Create a new booking for the authenticated user.
    """

    # 1. Basic date validation
    if booking.start_date >= booking.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking end date must be after start date."
        )

    # 2. Check for booking conflicts
    conflict_exists = crud.check_booking_conflict(
        db=db,
        property_id=booking.property_id,
        start_date=booking.start_date,
        end_date=booking.end_date
    )

    if conflict_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Booking conflict: The property is already booked for these dates."
        )

    # 3. If no conflict, create the booking
    db_booking = crud.create_booking(db=db, booking=booking, user_id=user_id)

    # 4. Send Kafka message
    try:
        await send_property_update(
            property_id=db_booking.property_id,
            status="UNAVAILABLE"
        )
    except Exception as e:
        print(f"Error sending Kafka message: {e}")

    return db_booking


@router.get("/", response_model=List[schemas.BookingRead])
def read_user_bookings(
        user_id: Annotated[int, Depends(get_current_user_id_from_token)],
        db: Session = Depends(get_db),
        skip: int = 0,
        limit: int = 100
):
    """
    Get all bookings for the authenticated user.
    """
    return crud.get_bookings_by_user(db=db, user_id=user_id, skip=skip, limit=limit)