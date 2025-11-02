# Import testing tools
import pytest
from fastapi.testclient import TestClient
from datetime import date, timedelta
import json  # Import json to parse the payload
from sqlalchemy.orm import Session  # Import Session for db_session typing

# Import models to query the OutboxEvent
from app import models

# Import JWT library and settings to create test tokens
from jose import jwt
from app.config import settings as booking_settings  # Use settings from booking service


# --- Helper function to create test JWT ---
def create_test_token(user_id: int = 1) -> str:
    """Creates a simple JWT for testing."""
    payload = {"sub": str(user_id)}
    token = jwt.encode(payload, booking_settings.SECRET_KEY, algorithm=booking_settings.ALGORITHM)
    return f"Bearer {token}"


# --- Fixture to provide auth headers ---
@pytest.fixture
def auth_headers():
    """Provides authorization headers with a default test token (user_id=1)."""
    return {"Authorization": create_test_token()}


# --- Test Cases ---

# This test now requires the `db_session` fixture
def test_create_booking_success(client: TestClient, auth_headers, db_session: Session):
    """Test successfully creating a booking."""
    booking_data = {
        "property_id": 101,
        "start_date": str(date.today()),
        "end_date": str(date.today() + timedelta(days=5)),
    }
    response = client.post("/bookings/", json=booking_data, headers=auth_headers)

    # --- Assertions for the API Response ---
    assert response.status_code == 201
    data = response.json()
    assert data["property_id"] == 101
    assert data["user_id"] == 1  # User ID from the test token
    assert "id" in data

    # --- NEW: Assertions for the Outbox Event ---

    # 1. Query the database to find the outbox event
    outbox_event = db_session.query(models.OutboxEvent).first()

    # 2. Check that it exists and has the correct properties
    assert outbox_event is not None
    assert outbox_event.status == "PENDING"
    assert outbox_event.topic == booking_settings.KAFKA_PROPERTY_TOPIC

    # 3. Check the payload is correct
    payload = json.loads(outbox_event.payload)
    assert payload["property_id"] == 101
    assert payload["status"] == "UNAVAILABLE"


def test_create_booking_invalid_dates(client: TestClient, auth_headers):
    """Test creating a booking where end_date is not after start_date."""
    # (This test remains unchanged)
    booking_data = {
        "property_id": 102,
        "start_date": str(date.today()),
        "end_date": str(date.today()),
    }
    response = client.post("/bookings/", json=booking_data, headers=auth_headers)
    assert response.status_code == 400
    assert "end date must be after start date" in response.json()["detail"]


def test_create_booking_conflict(client: TestClient, auth_headers, db_session: Session):
    """Test creating a booking that conflicts with an existing one."""
    # (This test remains unchanged)
    existing_start = date.today() + timedelta(days=2)
    existing_end = date.today() + timedelta(days=7)
    existing_booking = models.Booking(
        property_id=103,
        user_id=99,
        start_date=existing_start,
        end_date=existing_end
    )
    db_session.add(existing_booking)
    db_session.commit()

    booking_data = {
        "property_id": 103,
        "start_date": str(date.today()),
        "end_date": str(existing_start + timedelta(days=1)),
    }
    response = client.post("/bookings/", json=booking_data, headers=auth_headers)

    assert response.status_code == 409
    assert "already booked for these dates" in response.json()["detail"]


def test_create_booking_no_auth(client: TestClient):
    """Test creating a booking without providing an auth token."""
    # (This test remains unchanged)
    booking_data = {
        "property_id": 104,
        "start_date": str(date.today()),
        "end_date": str(date.today() + timedelta(days=5)),
    }
    response = client.post("/bookings/", json=booking_data)
    assert response.status_code == 403
    assert response.json() == {"detail": "Not authenticated"}


def test_read_user_bookings(client: TestClient, auth_headers, db_session: Session):
    """Test retrieving bookings only for the authenticated user."""
    # (This test remains unchanged)

    # 1. Add bookings for user 1 (the user in our default test token)
    db_session.add(models.Booking(property_id=201, user_id=1, start_date=date(2025, 1, 1), end_date=date(2025, 1, 5)))
    db_session.add(models.Booking(property_id=202, user_id=1, start_date=date(2025, 2, 1), end_date=date(2025, 2, 5)))
    # 2. Add a booking for a different user (user 2)
    db_session.add(models.Booking(property_id=203, user_id=2, start_date=date(2025, 3, 1), end_date=date(2025, 3, 5)))
    db_session.commit()

    # 3. Make a GET request
    response = client.get("/bookings/", headers=auth_headers)

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["property_id"] == 201
    assert data[1]["property_id"] == 202