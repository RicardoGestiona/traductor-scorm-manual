"""
Shared fixtures for all tests.

Filepath: backend/tests/conftest.py
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.core.auth import User, get_current_user


# Fixed UUID for consistent testing
TEST_USER_UUID = "550e8400-e29b-41d4-a716-446655440000"
OTHER_USER_UUID = "550e8400-e29b-41d4-a716-446655440001"


# ========================================
# Mock User for authentication
# ========================================

@pytest.fixture
def mock_user():
    """Create a mock authenticated user."""
    return User({
        "id": TEST_USER_UUID,
        "email": "test@example.com",
        "role": "authenticated",
        "user_metadata": {}
    })


@pytest.fixture
def mock_user_2():
    """Create a second mock user for ownership tests."""
    return User({
        "id": OTHER_USER_UUID,
        "email": "other@example.com",
        "role": "authenticated",
        "user_metadata": {}
    })


# ========================================
# Test Client Fixtures
# ========================================

@pytest.fixture
def test_client(mock_user):
    """
    FastAPI test client with mocked authentication.

    This fixture overrides the get_current_user dependency to return
    a mock user, allowing tests to bypass actual Supabase auth.
    """
    def override_get_current_user():
        return mock_user

    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as client:
        yield client

    # Clean up overrides after test
    app.dependency_overrides.clear()


@pytest.fixture
def test_client_no_auth():
    """
    FastAPI test client WITHOUT authentication override.

    Use this to test authentication requirements (401/403 errors).
    """
    # Clear any existing overrides
    app.dependency_overrides.clear()

    with TestClient(app) as client:
        yield client


@pytest.fixture
def client(mock_user):
    """
    Alias for test_client for backward compatibility.
    """
    def override_get_current_user():
        return mock_user

    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


# ========================================
# Supabase Auth Mocks
# ========================================

@pytest.fixture
def mock_supabase_auth():
    """Fixture to mock Supabase Auth client in auth endpoint."""
    with patch('app.api.v1.auth.supabase.auth') as mock_auth:
        yield mock_auth


@pytest.fixture
def mock_core_supabase_auth():
    """Fixture to mock Supabase Auth client in core auth module."""
    with patch('app.core.auth.supabase.auth') as mock_auth:
        yield mock_auth


# ========================================
# Mock Auth Response Classes
# ========================================

class MockAuthUser:
    """Mock of User from Supabase"""
    def __init__(self, id: str, email: str, role: str = "authenticated"):
        self.id = id
        self.email = email
        self.role = role

    def model_dump(self):
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role,
            "user_metadata": {}
        }


class MockAuthSession:
    """Mock of Session from Supabase"""
    def __init__(self, access_token: str, refresh_token: str, expires_at: int):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_at = expires_at


class MockAuthResponse:
    """Mock of AuthResponse from Supabase"""
    def __init__(self, user, session):
        self.user = user
        self.session = session


@pytest.fixture
def valid_auth_user():
    """Valid Supabase auth user for tests."""
    return MockAuthUser(
        id="test-user-uuid-123",
        email="test@example.com",
        role="authenticated"
    )


@pytest.fixture
def valid_auth_session():
    """Valid Supabase auth session for tests."""
    return MockAuthSession(
        access_token="mock-access-token-xyz",
        refresh_token="mock-refresh-token-abc",
        expires_at=1234567890
    )


# ========================================
# Storage and Job Service Mocks
# ========================================

@pytest.fixture
def mock_storage_service():
    """Mock for storage service."""
    with patch('app.services.storage.storage_service') as mock:
        mock.upload_file = AsyncMock(return_value="originals/test-job-id/test.zip")
        mock.get_signed_url = AsyncMock(return_value="https://storage.example.com/signed-url")
        mock.download_file = AsyncMock(return_value=b"fake-zip-content")
        mock.copy_file = AsyncMock(return_value=True)
        mock.get_download_url = AsyncMock(return_value="https://storage.example.com/download-url")
        yield mock


@pytest.fixture
def mock_job_service():
    """Mock for job service."""
    with patch('app.services.job_service.job_service') as mock:
        yield mock
