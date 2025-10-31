# Imports for testing tools
import pytest
from fastapi.testclient import TestClient # Client to make API requests to your app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock, AsyncMock # For creating mock objects

# Import your actual application code
from app.main import app # The main FastAPI application instance
from app.database import Base, get_db # Base for tables, get_db dependency
from app import models # To create the database tables

# --- Test Database Setup ---
# Define a database URL for a temporary, in-memory SQLite database
# This is much faster than using PostgreSQL for tests and keeps tests isolated
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Create a SQLAlchemy engine for the test database
# connect_args={"check_same_thread": False} is needed only for SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
# Create a session factory specifically for testing, bound to the test engine
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Mocking External Services ---
@pytest.fixture(scope="function", autouse=True)
def mock_kafka_consumer(mocker):
    """Mocks the Kafka consumer startup event."""
    # This fixture runs automatically for every test (`autouse=True`)
    # `mocker` is a fixture provided by pytest-mock
    # `mocker.patch` replaces the real `consume_property_updates` function
    # with an `AsyncMock`. This prevents the real function (which tries
    # to connect to Kafka) from running during tests.
    mocker.patch("app.kafka_consumer.consume_property_updates", new_callable=AsyncMock)

# --- Database Management Fixtures ---
@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Creates and drops the test database tables."""
    # `scope="session"` means this runs once for the entire test session
    # `autouse=True` means it runs automatically without being requested
    # Create all tables defined in your models using the test engine
    Base.metadata.create_all(bind=engine)
    yield # Let the tests run
    # After all tests are done, drop all tables to clean up
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Provides a clean database session for each test."""
    # `scope="function"` means this runs once for each test function
    # Connect to the test engine
    connection = engine.connect()
    # Begin a transaction
    transaction = connection.begin()
    # Create a session bound to this transaction
    session = TestingSessionLocal(bind=connection)
    yield session # Provide the session to the test function
    # After the test finishes:
    session.close() # Close the session
    transaction.rollback() # Rollback any changes made during the test
    connection.close() # Close the connection

# --- API Test Client Fixture ---
@pytest.fixture(scope="function")
def client(db_session):
    """Provides a FastAPI TestClient configured for testing."""
    # This fixture depends on the `db_session` fixture above

    def override_get_db():
        """Dependency override for get_db."""
        # This function replaces the real `get_db` dependency in your app
        try:
            yield db_session # Provides the isolated test session to API endpoints
        finally:
            db_session.close() # Ensure the session is closed

    def override_get_redis_client():
        """Dependency override for get_redis_client."""
        # Replaces the real Redis client with a MagicMock
        # This prevents tests from needing a real Redis server
        return MagicMock()

    # Apply the overrides to the main FastAPI app instance
    app.dependency_overrides[get_db] = override_get_db
    from app.database import get_redis_client # Import here if needed
    app.dependency_overrides[get_redis_client] = override_get_redis_client

    # Create and yield the TestClient
    # `with TestClient(app)` ensures startup/shutdown events run if needed
    with TestClient(app) as c:
        yield c # Provide the client to the test function

    # Clean up the overrides after the test finishes
    app.dependency_overrides.clear()