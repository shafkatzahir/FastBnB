from fastapi import APIRouter, Depends, HTTPException, status,Request
from sqlalchemy.orm import Session
from typing import List, Annotated
from jose import jwt, JWTError
import httpx
from fastapi.security import APIKeyHeader

from .. import schemas, crud
from ..database import get_db
from ..config import settings

from fastapi_limiter.depends import RateLimiter



router = APIRouter(prefix="/bookings", tags=["Bookings"])

api_key_header = APIKeyHeader(name="Authorization")


async def get_key_by_user_id_or_ip(request: Request) -> str:
    """
    Tries to get the user ID from the JWT token.
    If it fails (no token, invalid token), it falls back to the client's IP.
    """
    try:
        token = request.headers.get("Authorization")
        scheme, jwt_token = token.split()
        if scheme.lower() != "bearer":
            return request.client.host  # Fallback to IP

        payload = jwt.decode(jwt_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")

        if user_id:
            return str(user_id)
    except (JWTError, ValueError, AttributeError, TypeError):
        # If token is invalid, missing, or malformed, limit by IP
        pass
    return request.client.host


async def get_current_user_id_from_token(
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
        db: Session = Depends(get_db),
        limit: None = Depends(RateLimiter(times=30, minutes=1, identifier=get_key_by_user_id_or_ip))
):
    """
    Create a new booking for the authenticated user.
    """
    if booking.start_date >= booking.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking end date must be after start date."
        )
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

    try:
        # This one call now handles the database transaction atomically
        db_booking = crud.create_booking(db=db, booking=booking, user_id=user_id)
    except Exception as e:
        # Handle potential DB errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the booking: {e}"
        )

    # --- DELETE THE KAFKA CALL ---
    # The try/except block for send_property_update is gone.

    return db_booking


@router.get("/", response_model=List[schemas.BookingRead])
def read_user_bookings(
        user_id: Annotated[int, Depends(get_current_user_id_from_token)],
        db: Session = Depends(get_db),
        skip: int = 0,
        limit: int = 100,
        limit2: None = Depends(RateLimiter(times=5, minutes=1, identifier=get_key_by_user_id_or_ip))
):
    """
    Get all bookings for the authenticated user.
    """
    return crud.get_bookings_by_user(db=db, user_id=user_id, skip=skip, limit=limit)
