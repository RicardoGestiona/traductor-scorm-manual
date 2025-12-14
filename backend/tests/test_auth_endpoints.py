"""
Tests para endpoints de autenticación.

Filepath: backend/tests/test_auth_endpoints.py
Feature alignment: STORY-017 - Autenticación con Supabase
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.auth import get_current_user


# ========================================
# Test Client sin auth (para tests de auth endpoints)
# ========================================

@pytest.fixture
def auth_client():
    """Cliente sin override de autenticación para probar auth endpoints."""
    app.dependency_overrides.clear()
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


# ========================================
# Mock Classes
# ========================================

class MockAuthUser:
    """Mock de User de Supabase"""
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
    """Mock de Session de Supabase"""
    def __init__(self, access_token: str, refresh_token: str, expires_at: int):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_at = expires_at


class MockAuthResponse:
    """Mock de AuthResponse de Supabase"""
    def __init__(self, user, session):
        self.user = user
        self.session = session


# ========================================
# Fixtures
# ========================================

@pytest.fixture
def mock_supabase_auth():
    """Fixture para mockear Supabase Auth client"""
    with patch('app.api.v1.auth.supabase.auth') as mock_auth:
        yield mock_auth


@pytest.fixture
def valid_user():
    """Usuario válido para tests"""
    return MockAuthUser(
        id="test-user-uuid-123",
        email="test@example.com",
        role="authenticated"
    )


@pytest.fixture
def valid_session():
    """Sesión válida para tests"""
    return MockAuthSession(
        access_token="mock-access-token-xyz",
        refresh_token="mock-refresh-token-abc",
        expires_at=1234567890
    )


# ========================================
# Tests de POST /api/v1/auth/signup
# ========================================

def test_signup_success(mock_supabase_auth, valid_user, valid_session, auth_client):
    """Test signup exitoso con email y password válidos"""
    mock_response = MockAuthResponse(user=valid_user, session=valid_session)
    mock_supabase_auth.sign_up.return_value = mock_response

    response = auth_client.post(
        "/api/v1/auth/signup",
        json={
            "email": "newuser@example.com",
            "password": "securePassword123"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "user" in data
    assert data["user"]["email"] == valid_user.email
    assert data["user"]["id"] == valid_user.id


def test_signup_user_already_exists(mock_supabase_auth, auth_client):
    """Test signup con email que ya existe"""
    mock_response = MockAuthResponse(user=None, session=None)
    mock_supabase_auth.sign_up.return_value = mock_response

    response = auth_client.post(
        "/api/v1/auth/signup",
        json={
            "email": "existing@example.com",
            "password": "password123"
        }
    )

    assert response.status_code == 400
    assert "already be registered" in response.json()["detail"]


def test_signup_invalid_email(auth_client):
    """Test signup con email inválido"""
    response = auth_client.post(
        "/api/v1/auth/signup",
        json={
            "email": "not-an-email",
            "password": "password123"
        }
    )

    assert response.status_code == 422  # Validation error


def test_signup_missing_password(auth_client):
    """Test signup sin contraseña"""
    response = auth_client.post(
        "/api/v1/auth/signup",
        json={
            "email": "test@example.com"
        }
    )

    assert response.status_code == 422


def test_signup_supabase_error(mock_supabase_auth, auth_client):
    """Test signup con error de Supabase"""
    mock_supabase_auth.sign_up.side_effect = Exception("Supabase connection error")

    response = auth_client.post(
        "/api/v1/auth/signup",
        json={
            "email": "test@example.com",
            "password": "password123"
        }
    )

    assert response.status_code == 500
    assert "Signup failed" in response.json()["detail"]


# ========================================
# Tests de POST /api/v1/auth/login
# ========================================

def test_login_success(mock_supabase_auth, valid_user, valid_session, auth_client):
    """Test login exitoso con credenciales válidas"""
    mock_response = MockAuthResponse(user=valid_user, session=valid_session)
    mock_supabase_auth.sign_in_with_password.return_value = mock_response

    response = auth_client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["access_token"] == valid_session.access_token
    assert "refresh_token" in data
    assert "user" in data
    assert data["user"]["email"] == valid_user.email


def test_login_invalid_credentials(mock_supabase_auth, auth_client):
    """Test login con credenciales incorrectas"""
    mock_response = MockAuthResponse(user=None, session=None)
    mock_supabase_auth.sign_in_with_password.return_value = mock_response

    response = auth_client.post(
        "/api/v1/auth/login",
        json={
            "email": "wrong@example.com",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_login_missing_email(auth_client):
    """Test login sin email"""
    response = auth_client.post(
        "/api/v1/auth/login",
        json={
            "password": "password123"
        }
    )

    assert response.status_code == 422


def test_login_supabase_error(mock_supabase_auth, auth_client):
    """Test login con error de Supabase"""
    mock_supabase_auth.sign_in_with_password.side_effect = Exception("Network error")

    response = auth_client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123"
        }
    )

    assert response.status_code == 500
    assert "Login failed" in response.json()["detail"]


# ========================================
# Tests de POST /api/v1/auth/logout
# ========================================

@patch('app.core.auth.supabase.auth')
def test_logout_success(mock_core_auth, mock_supabase_auth, valid_user, auth_client):
    """Test logout exitoso con usuario autenticado"""
    # Mock del get_current_user - verificar token y retornar usuario
    mock_user_response = MagicMock()
    mock_user_response.user = valid_user
    mock_core_auth.get_user.return_value = mock_user_response

    response = auth_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": "Bearer mock-token"}
    )

    assert response.status_code == 200
    assert "Successfully logged out" in response.json()["message"]


def test_logout_without_auth(auth_client):
    """Test logout sin token de autenticación"""
    response = auth_client.post("/api/v1/auth/logout")

    assert response.status_code == 403  # No credentials provided


# ========================================
# Tests de GET /api/v1/auth/me
# ========================================

@patch('app.core.auth.supabase.auth')
def test_get_current_user_success(mock_auth, valid_user, auth_client):
    """Test obtener usuario actual con token válido"""
    mock_user_response = MagicMock()
    mock_user_response.user = valid_user
    mock_auth.get_user.return_value = mock_user_response

    response = auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer valid-token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == valid_user.email
    assert data["id"] == valid_user.id
    assert data["role"] == valid_user.role


def test_get_current_user_without_auth(auth_client):
    """Test obtener usuario sin autenticación"""
    response = auth_client.get("/api/v1/auth/me")

    assert response.status_code == 403


@patch('app.core.auth.supabase.auth')
def test_get_current_user_invalid_token(mock_auth, auth_client):
    """Test obtener usuario con token inválido"""
    mock_auth.get_user.side_effect = Exception("Invalid token")

    response = auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid-token"}
    )

    assert response.status_code == 401


# ========================================
# Tests de POST /api/v1/auth/refresh
# ========================================

def test_refresh_token_success(mock_supabase_auth, valid_user, valid_session, auth_client):
    """Test refresh token exitoso"""
    mock_response = MockAuthResponse(user=valid_user, session=valid_session)
    mock_supabase_auth.refresh_session.return_value = mock_response

    response = auth_client.post(
        "/api/v1/auth/refresh",
        params={"refresh_token": "valid-refresh-token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_refresh_token_invalid(mock_supabase_auth, auth_client):
    """Test refresh con token inválido o expirado"""
    mock_response = MockAuthResponse(user=None, session=None)
    mock_supabase_auth.refresh_session.return_value = mock_response

    response = auth_client.post(
        "/api/v1/auth/refresh",
        params={"refresh_token": "invalid-refresh-token"}
    )

    assert response.status_code == 401
    assert "Invalid or expired refresh token" in response.json()["detail"]


def test_refresh_token_supabase_error(mock_supabase_auth, auth_client):
    """Test refresh con error de Supabase"""
    mock_supabase_auth.refresh_session.side_effect = Exception("Token refresh failed")

    response = auth_client.post(
        "/api/v1/auth/refresh",
        params={"refresh_token": "some-token"}
    )

    assert response.status_code == 500
    assert "Token refresh failed" in response.json()["detail"]


# ========================================
# Tests de integración
# ========================================

@patch('app.core.auth.supabase.auth')
def test_auth_flow_integration(mock_core_auth, mock_supabase_auth, valid_user, valid_session, auth_client):
    """Test flujo completo: signup → login → get user info → logout"""
    # 1. Signup
    mock_response = MockAuthResponse(user=valid_user, session=valid_session)
    mock_supabase_auth.sign_up.return_value = mock_response

    signup_response = auth_client.post(
        "/api/v1/auth/signup",
        json={"email": "flow@test.com", "password": "test123"}
    )
    assert signup_response.status_code == 201

    # 2. Login
    mock_supabase_auth.sign_in_with_password.return_value = mock_response
    login_response = auth_client.post(
        "/api/v1/auth/login",
        json={"email": "flow@test.com", "password": "test123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # 3. Get user info (mock core auth)
    mock_user_response = MagicMock()
    mock_user_response.user = valid_user
    mock_core_auth.get_user.return_value = mock_user_response

    user_response = auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert user_response.status_code == 200

    # 4. Logout
    logout_response = auth_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert logout_response.status_code == 200
