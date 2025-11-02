# Imports for testing tools
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock, AsyncMock # Import AsyncMock

# Import your application code
from app.main import app
from app.database import Base, get_db
from app import models

# --- Test Database Setup ---
# Use a different filename to avoid conflicts if run locally
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_booking.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Database Management Fixtures ---
@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Creates and drops the test database tables for bookings."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Provides a clean database session for each booking test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

# --- Mocking External Services ---
@pytest.fixture(scope="function", autouse=True)
def mock_background_tasks(mocker):
    """
    Mocks the background tasks (poller and scheduler) that run on app lifespan.
    """
    # Patch the functions that are started in main.py
    mocker.patch("app.main.run_outbox_poller", new_callable=AsyncMock)
    mocker.patch("app.main.run_booking_scheduler", new_callable=AsyncMock)

# --- API Test Client Fixture ---
@pytest.fixture(scope="function")
def client(db_session):
    """Provides a TestClient for the booking service."""
    def override_get_db():
        """Overrides the get_db dependency for booking tests."""
        try:
            yield db_session
        finally:
            db_session.close()

    # Apply the database override
    app.dependency_overrides[get_db] = override_get_db

    # Create and yield the TestClient
    with TestClient(app) as c:
        yield c

    # Clean up overrides
    app.dependency_overrides.clear()