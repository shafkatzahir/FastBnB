# Import necessary modules
from datetime import date, timedelta
from sqlalchemy.orm import Session
from unittest.mock import MagicMock

# Import the function to test and the model
from app import crud, models

# --- Helper function to create a mock Booking object ---
def create_mock_booking(start_offset: int, end_offset: int, property_id: int = 1):
    """Creates a mock Booking object with dates relative to today."""
    return models.Booking(
        id=1, # Add an ID for completeness if needed by filter logic
        property_id=property_id,
        user_id=1,
        start_date=date.today() + timedelta(days=start_offset),
        end_date=date.today() + timedelta(days=end_offset),
    )

# --- Test Cases for check_booking_conflict ---

def test_check_booking_conflict_no_conflict():
    """Test case where there are no existing bookings."""
    mock_db = MagicMock(spec=Session)
    # Configure the mock query to return None (no conflicting booking found)
    mock_db.query.return_value.filter.return_value.first.return_value = None

    # Dates for the new booking attempt
    new_start = date.today()
    new_end = date.today() + timedelta(days=5)

    # Call the function
    conflict = crud.check_booking_conflict(mock_db, 1, new_start, new_end)
    # Assert that no conflict is found (should return False)
    assert conflict is False
    # Verify the database query was called
    mock_db.query.return_value.filter.return_value.first.assert_called_once()

def test_check_booking_conflict_full_overlap():
    """Test case where the new booking is fully inside an existing booking."""
    mock_db = MagicMock(spec=Session)
    # Existing booking: today+2 days to today+10 days
    existing_booking = create_mock_booking(start_offset=2, end_offset=10)
    # Configure mock query to return the existing booking
    mock_db.query.return_value.filter.return_value.first.return_value = existing_booking

    # New booking attempt: today+3 days to today+7 days (inside existing)
    new_start = date.today() + timedelta(days=3)
    new_end = date.today() + timedelta(days=7)

    # Call the function
    conflict = crud.check_booking_conflict(mock_db, 1, new_start, new_end)
    # Assert that a conflict IS found (should return True)
    assert conflict is True

def test_check_booking_conflict_partial_overlap_start():
    """Test case where the new booking starts before and overlaps the start."""
    mock_db = MagicMock(spec=Session)
    # Existing booking: today+5 days to today+10 days
    existing_booking = create_mock_booking(start_offset=5, end_offset=10)
    mock_db.query.return_value.filter.return_value.first.return_value = existing_booking

    # New booking attempt: today+3 days to today+7 days (overlaps start of existing)
    new_start = date.today() + timedelta(days=3)
    new_end = date.today() + timedelta(days=7)

    # Call the function
    conflict = crud.check_booking_conflict(mock_db, 1, new_start, new_end)
    # Assert that a conflict IS found
    assert conflict is True

def test_check_booking_conflict_partial_overlap_end():
    """Test case where the new booking starts inside and overlaps the end."""
    mock_db = MagicMock(spec=Session)
    # Existing booking: today+2 days to today+8 days
    existing_booking = create_mock_booking(start_offset=2, end_offset=8)
    mock_db.query.return_value.filter.return_value.first.return_value = existing_booking

    # New booking attempt: today+6 days to today+10 days (overlaps end of existing)
    new_start = date.today() + timedelta(days=6)
    new_end = date.today() + timedelta(days=10)

    # Call the function
    conflict = crud.check_booking_conflict(mock_db, 1, new_start, new_end)
    # Assert that a conflict IS found
    assert conflict is True

def test_check_booking_conflict_wraps_existing():
    """Test case where the new booking completely contains an existing booking."""
    mock_db = MagicMock(spec=Session)
    # Existing booking: today+3 days to today+5 days
    existing_booking = create_mock_booking(start_offset=3, end_offset=5)
    mock_db.query.return_value.filter.return_value.first.return_value = existing_booking

    # New booking attempt: today+1 days to today+10 days (wraps existing)
    new_start = date.today() + timedelta(days=1)
    new_end = date.today() + timedelta(days=10)

    # Call the function
    conflict = crud.check_booking_conflict(mock_db, 1, new_start, new_end)
    # Assert that a conflict IS found
    assert conflict is True

def test_check_booking_conflict_touching_end_start():
    """Test case where new booking starts exactly when existing ends (NO conflict)."""
    mock_db = MagicMock(spec=Session)
    # Existing booking: today+2 days to today+5 days
    existing_booking = create_mock_booking(start_offset=2, end_offset=5)
    # Configure mock query to return NO booking, because the filter shouldn't match
    # The filter is `existing_end > new_start`. If existing_end == new_start, it's false.
    mock_db.query.return_value.filter.return_value.first.return_value = None # Simulate no overlap found

    # New booking attempt: today+5 days to today+10 days
    new_start = date.today() + timedelta(days=5)
    new_end = date.today() + timedelta(days=10)

    # Call the function
    conflict = crud.check_booking_conflict(mock_db, 1, new_start, new_end)
    # Assert that NO conflict is found
    assert conflict is False

def test_check_booking_conflict_touching_start_end():
    """Test case where new booking ends exactly when existing starts (NO conflict)."""
    mock_db = MagicMock(spec=Session)
    # Existing booking: today+5 days to today+10 days
    existing_booking = create_mock_booking(start_offset=5, end_offset=10)
    # Configure mock query to return NO booking
    # The filter is `existing_start < new_end`. If existing_start == new_end, it's false.
    mock_db.query.return_value.filter.return_value.first.return_value = None # Simulate no overlap found

    # New booking attempt: today+2 days to today+5 days
    new_start = date.today() + timedelta(days=2)
    new_end = date.today() + timedelta(days=5)

    # Call the function
    conflict = crud.check_booking_conflict(mock_db, 1, new_start, new_end)
    # Assert that NO conflict is found
    assert conflict is False

def test_check_booking_conflict_different_property():
    """Test case where an existing booking is for a different property (NO conflict)."""
    mock_db = MagicMock(spec=Session)
    # Existing booking: today+2 days to today+10 days for property 99
    existing_booking = create_mock_booking(start_offset=2, end_offset=10, property_id=99)
    # Configure mock query to return None because the property_id filter won't match
    mock_db.query.return_value.filter.return_value.first.return_value = None

    # New booking attempt: today+3 days to today+7 days for property 1
    new_start = date.today() + timedelta(days=3)
    new_end = date.today() + timedelta(days=7)

    # Call the function for property 1
    conflict = crud.check_booking_conflict(mock_db, 1, new_start, new_end)
    # Assert that NO conflict is found
    assert conflict is False