# Import testing tools
import pytest
from fastapi.testclient import TestClient
from datetime import date, timedelta
from unittest.mock import AsyncMock # For checking async function calls

# Import JWT library and settings to create test tokens
from jose import jwt
from app.config import settings as booking_settings # Use settings from booking service

# --- Helper function to create test JWT ---
def create_test_token(user_id: int = 1) -> str:
    """Creates a simple JWT for testing."""
    # The payload only needs the 'sub' (subject) claim for this API
    payload = {"sub": str(user_id)}
    # Encode the token using the secret key and algorithm from config
    token = jwt.encode(payload, booking_settings.SECRET_KEY, algorithm=booking_settings.ALGORITHM)
    # Return the token prefixed with "Bearer " as expected by the API
    return f"Bearer {token}"

# --- Fixture to provide auth headers ---
@pytest.fixture
def auth_headers():
    """Provides authorization headers with a default test token (user_id=1)."""
    return {"Authorization": create_test_token()}

# --- Test Cases ---

# This test requires the `client`, `auth_headers`, and `mock_kafka_producer` fixtures
def test_create_booking_success(client: TestClient, auth_headers, mock_kafka_producer):
    """Test successfully creating a booking."""
    # Define the data for the new booking request
    booking_data = {
        "property_id": 101,
        "start_date": str(date.today()), # Use today's date
        "end_date": str(date.today() + timedelta(days=5)), # 5 days from today
    }
    # Make a POST request using the TestClient
    response = client.post("/bookings/", json=booking_data, headers=auth_headers)

    # Assert the HTTP status code is 201 Created
    assert response.status_code == 201
    # Parse the response JSON
    data = response.json()
    # Assert the data in the response matches the request and expectations
    assert data["property_id"] == 101
    assert data["user_id"] == 1 # User ID comes from the test token
    assert data["start_date"] == str(date.today())
    assert "id" in data # Check that the booking got an ID
    assert "created_at" in data # Check that a timestamp was added

    # Assert that our mock Kafka producer function was called exactly once
    # with the correct arguments.
    mock_kafka_producer.assert_called_once_with(property_id=101, status="UNAVAILABLE")

def test_create_booking_invalid_dates(client: TestClient, auth_headers):
    """Test creating a booking where end_date is not after start_date."""
    booking_data = {
        "property_id": 102,
        "start_date": str(date.today()),
        "end_date": str(date.today()), # End date is the same as start date
    }
    response = client.post("/bookings/", json=booking_data, headers=auth_headers)
    # Assert the status code is 400 Bad Request
    assert response.status_code == 400
    # Assert the specific error message is returned
    assert "end date must be after start date" in response.json()["detail"]

def test_create_booking_conflict(client: TestClient, auth_headers, db_session):
    """Test creating a booking that conflicts with an existing one."""
    # This test needs the `db_session` fixture to manually add data
    from app import models # Import models to create a booking object

    # 1. Manually create an existing booking directly in the test database
    existing_start = date.today() + timedelta(days=2)
    existing_end = date.today() + timedelta(days=7)
    existing_booking = models.Booking(
        property_id=103,
        user_id=99, # Belongs to a different user
        start_date=existing_start,
        end_date=existing_end
    )
    db_session.add(existing_booking)
    db_session.commit() # Save it to the test DB

    # 2. Attempt to create a new booking that overlaps the existing one
    booking_data = {
        "property_id": 103, # Same property
        "start_date": str(date.today()), # Starts before existing
        "end_date": str(existing_start + timedelta(days=1)), # Ends *after* existing starts
    }
    response = client.post("/bookings/", json=booking_data, headers=auth_headers)

    # Assert the status code is 409 Conflict
    assert response.status_code == 409
    # Assert the specific conflict error message
    assert "already booked for these dates" in response.json()["detail"]

def test_create_booking_no_auth(client: TestClient):
    """Test creating a booking without providing an auth token."""
    booking_data = {
        "property_id": 104,
        "start_date": str(date.today()),
        "end_date": str(date.today() + timedelta(days=5)),
    }
    # Make the POST request *without* the `headers` argument
    response = client.post("/bookings/", json=booking_data)
    # Assert the status code is 403 Forbidden (FastAPI returns this for missing APIKeyHeader)
    assert response.status_code == 403
    # Assert the specific detail message
    assert response.json() == {"detail": "Not authenticated"}

def test_read_user_bookings(client: TestClient, auth_headers, db_session):
    """Test retrieving bookings only for the authenticated user."""
    # Needs `db_session` to add test data
    from app import models

    # 1. Add bookings for user 1 (the user in our default test token)
    db_session.add(models.Booking(property_id=201, user_id=1, start_date=date(2025,1,1), end_date=date(2025,1,5)))
    db_session.add(models.Booking(property_id=202, user_id=1, start_date=date(2025,2,1), end_date=date(2025,2,5)))
    # 2. Add a booking for a different user (user 2)
    db_session.add(models.Booking(property_id=203, user_id=2, start_date=date(2025,3,1), end_date=date(2025,3,5)))
    db_session.commit() # Save all bookings

    # 3. Make a GET request to retrieve bookings, using auth headers for user 1
    response = client.get("/bookings/", headers=auth_headers)

    # Assert the status code is 200 OK
    assert response.status_code == 200
    # Parse the response JSON
    data = response.json()
    # Assert the response is a list
    assert isinstance(data, list)
    # Assert that only the 2 bookings belonging to user 1 are returned
    assert len(data) == 2
    # Check the property IDs to be sure
    assert data[0]["property_id"] == 201
    assert data[1]["property_id"] == 202