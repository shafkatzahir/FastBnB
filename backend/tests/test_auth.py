# Import the specific functions you want to test
from app import auth
# Import specific exceptions if needed
from passlib.exc import UnknownHashError
import pytest # Import pytest for features like raising exceptions

def test_hash_password():
    """Verify that hash_password returns a non-empty string different from the original."""
    password = "password123"
    # Call the function being tested
    hashed = auth.hash_password(password)
    # Assert that the result is a string
    assert isinstance(hashed, str)
    # Assert that the hash is not empty
    assert len(hashed) > 0
    # Assert that the hash is different from the original password
    assert hashed != password

def test_verify_password_correct():
    """Verify that verify_password works with a correctly hashed password."""
    password = "password123"
    # First, hash the password using the function we tested above
    hashed = auth.hash_password(password)
    # Call the function being tested with the correct plain password and hash
    is_valid = auth.verify_password(password, hashed)
    # Assert that the verification returns True
    assert is_valid is True

def test_verify_password_incorrect():
    """Verify that verify_password returns False for an incorrect password."""
    password = "password123"
    incorrect_password = "wrongpassword"
    # Hash the original password
    hashed = auth.hash_password(password)
    # Call the function with the INCORRECT plain password
    is_valid = auth.verify_password(incorrect_password, hashed)
    # Assert that the verification returns False
    assert is_valid is False

def test_verify_password_invalid_hash():
    """Verify that verify_password handles non-bcrypt hashes gracefully."""
    password = "password123"
    invalid_hash = "not_a_real_hash"
    # Call the function with an invalid hash format
    # Assert that the function (after our fix) returns False, not raises an error
    assert auth.verify_password(password, invalid_hash) is False