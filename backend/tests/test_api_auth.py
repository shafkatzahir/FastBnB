# Import the TestClient type hint
from fastapi.testclient import TestClient
# Import models if needed for assertions
from app import models

# Note: The `client` fixture is automatically injected by pytest from conftest.py

def test_register_user(client: TestClient):
    """Test user registration endpoint."""
    # Make a POST request to the /auth/register endpoint
    response = client.post(
        "/auth/register",
        # Send the user data as JSON in the request body
        json={"username": "testuser", "password": "password123"}
    )
    # Assert that the HTTP status code is 201 Created
    assert response.status_code == 201
    # Parse the JSON response body
    data = response.json()
    # Assert that the username in the response matches
    assert data["username"] == "testuser"
    # Assert that the role is ADMIN (because it's the first user in the test DB)
    assert data["role"] == models.UserRole.ADMIN.value # Use .value for the string representation
    # Assert that the response includes an 'id'
    assert "id" in data

def test_register_user_duplicate(client: TestClient):
    """Test registering a user with an already existing username."""
    # First, register a user (this uses the same isolated DB as the previous test ended)
    client.post("/auth/register", json={"username": "testuser1", "password": "password123"})
    # Now, attempt to register ANOTHER user with the SAME username
    response = client.post("/auth/register", json={"username": "testuser1", "password": "anotherpassword"})
    # Assert that the status code is 400 Bad Request
    assert response.status_code == 400
    # Assert that the detail message indicates the username is taken
    assert "Username already registered" in response.json()["detail"]

def test_login_for_access_token_success(client: TestClient):
    """Test successful login and receiving tokens."""
    # 1. Register a user first
    client.post("/auth/register", json={"username": "loginuser", "password": "password123"})

    # 2. Make a POST request to the /auth/login endpoint
    # Note: Login expects form data (x-www-form-urlencoded), not JSON
    response = client.post(
        "/auth/login",
        data={"username": "loginuser", "password": "password123"}
    )
    # Assert the status code is 200 OK
    assert response.status_code == 200
    # Parse the JSON response
    data = response.json()
    # Assert that an 'access_token' is present
    assert "access_token" in data
    # Assert that the 'token_type' is 'bearer'
    assert data["token_type"] == "bearer"
    # Check if the refresh token cookie was set (optional but good)
    assert "refresh_token" in response.cookies

def test_login_for_access_token_invalid_password(client: TestClient):
    """Test login attempt with an incorrect password."""
    # 1. Register a user
    client.post("/auth/register", json={"username": "loginuser2", "password": "password123"})

    # 2. Attempt to login with the WRONG password
    response = client.post(
        "/auth/login",
        data={"username": "loginuser2", "password": "wrongpassword"}
    )
    # Assert the status code is 401 Unauthorized
    assert response.status_code == 401
    # Assert the detail message indicates incorrect credentials
    assert "Incorrect username or password" in response.json()["detail"]

def test_login_for_access_token_user_not_found(client: TestClient):
    """Test login attempt for a user that does not exist."""
    # Attempt to login with a username that hasn't been registered
    response = client.post(
        "/auth/login",
        data={"username": "nonexistentuser", "password": "password123"}
    )
    # Assert the status code is 401 Unauthorized
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]