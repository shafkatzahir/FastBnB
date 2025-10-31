# Import the functions and models needed for the test
from app import crud, models, schemas
# Import pytest-mock fixture `mocker`
from unittest.mock import MagicMock

# Define a minimal UserCreate schema object for testing
user_data = schemas.UserCreate(username="testadmin", password="password123")

def test_create_user_first_user_is_admin(mocker):
    """Test that the first user created gets the ADMIN role."""
    # --- Setup Mocks ---
    # Create a mock database session object using MagicMock
    mock_db = MagicMock()
    # Configure the mock's query().count() method to return 0,
    # simulating an empty database.
    mock_db.query.return_value.count.return_value = 0
    # Mock the `auth.hash_password` function to avoid real hashing
    mocker.patch("app.auth.hash_password", return_value="hashed_password_abc")

    # --- Action ---
    # Call the function being tested with the mock database
    created_user = crud.create_user(db=mock_db, user=user_data)

    # --- Assertions ---
    # Check that the database's `add` method was called once
    mock_db.add.assert_called_once()
    # Check that the database's `commit` method was called once
    mock_db.commit.assert_called_once()
    # Check that the database's `refresh` method was called once
    mock_db.refresh.assert_called_once()
    # Assert that the returned user object has the ADMIN role
    assert created_user.role == models.UserRole.ADMIN
    # Assert that the username matches
    assert created_user.username == user_data.username

def test_create_user_second_user_is_user(mocker):
    """Test that subsequent users created get the USER role."""
    # --- Setup Mocks ---
    mock_db = MagicMock()
    # Configure the mock's query().count() method to return 1,
    # simulating a database that already has one user.
    mock_db.query.return_value.count.return_value = 1
    # Mock the hashing function
    mocker.patch("app.auth.hash_password", return_value="hashed_password_xyz")

    # --- Action ---
    # Call the function being tested
    created_user = crud.create_user(db=mock_db, user=user_data)

    # --- Assertions ---
    # Check database methods were called
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()
    # Assert that this user has the USER role
    assert created_user.role == models.UserRole.USER
    assert created_user.username == user_data.username