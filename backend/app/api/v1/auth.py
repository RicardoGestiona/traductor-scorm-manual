"""
Authentication endpoints for Supabase Auth.

Handles user registration, login, logout, and session management.

Filepath: backend/app/api/v1/auth.py
Feature alignment: STORY-017 - Autenticación con Supabase
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from app.core.auth import get_supabase_client, get_current_user, User

router = APIRouter()
supabase = get_supabase_client()


# Request/Response Models
class SignupRequest(BaseModel):
    """User signup request."""

    email: EmailStr
    password: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "user@example.com",
                    "password": "securePassword123",
                }
            ]
        }
    }


class LoginRequest(BaseModel):
    """User login request."""

    email: EmailStr
    password: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "user@example.com",
                    "password": "securePassword123",
                }
            ]
        }
    }


class AuthResponse(BaseModel):
    """Authentication response with session info."""

    access_token: str
    refresh_token: str
    user: dict
    expires_at: int

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "refresh_token_here",
                    "user": {
                        "id": "uuid-here",
                        "email": "user@example.com",
                        "role": "authenticated",
                    },
                    "expires_at": 1234567890,
                }
            ]
        }
    }


class UserResponse(BaseModel):
    """Current user information."""

    id: str
    email: str
    role: str
    metadata: dict

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "uuid-here",
                    "email": "user@example.com",
                    "role": "authenticated",
                    "metadata": {},
                }
            ]
        }
    }


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest):
    """
    Register a new user with email and password.

    Creates a new user account in Supabase Auth and returns access tokens.

    **Note**: Supabase may send a confirmation email depending on your settings.
    Check your Supabase Auth settings to enable/disable email confirmation.

    Args:
        request: Signup credentials (email, password)

    Returns:
        AuthResponse: Access token, refresh token, and user info

    Raises:
        HTTPException: 400 if user already exists or validation fails
        HTTPException: 500 if signup fails
    """
    try:
        response = supabase.auth.sign_up(
            {
                "email": request.email,
                "password": request.password,
            }
        )

        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user. Email may already be registered.",
            )

        return AuthResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            user={
                "id": response.user.id,
                "email": response.user.email,
                "role": response.user.role,
            },
            expires_at=response.session.expires_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signup failed: {str(e)}",
        )


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """
    Authenticate user with email and password.

    Args:
        request: Login credentials (email, password)

    Returns:
        AuthResponse: Access token, refresh token, and user info

    Raises:
        HTTPException: 401 if credentials are invalid
        HTTPException: 500 if login fails
    """
    try:
        response = supabase.auth.sign_in_with_password(
            {"email": request.email, "password": request.password}
        )

        if not response.user or not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        return AuthResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            user={
                "id": response.user.id,
                "email": response.user.email,
                "role": response.user.role,
            },
            expires_at=response.session.expires_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}",
        )


@router.post("/logout")
async def logout(user: User = Depends(get_current_user)):
    """
    Logout current user (invalidate session).

    Requires authentication.

    Args:
        user: Current authenticated user (from dependency)

    Returns:
        dict: Success message

    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 500 if logout fails
    """
    try:
        # Supabase logout
        supabase.auth.sign_out()

        return {"message": "Successfully logged out"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}",
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.

    Requires authentication via Bearer token in Authorization header.

    Args:
        user: Current authenticated user (from dependency)

    Returns:
        UserResponse: Current user information

    Raises:
        HTTPException: 401 if not authenticated or token invalid
    """
    return UserResponse(
        id=user.id,
        email=user.email,
        role=user.role,
        metadata=user.metadata,
    )


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(refresh_token: str):
    """
    Refresh access token using refresh token.

    Use this endpoint when access token expires to get a new one
    without requiring user to login again.

    Args:
        refresh_token: Refresh token from previous login/signup

    Returns:
        AuthResponse: New access token and user info

    Raises:
        HTTPException: 401 if refresh token is invalid or expired
        HTTPException: 500 if refresh fails
    """
    try:
        response = supabase.auth.refresh_session(refresh_token)

        if not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        return AuthResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            user={
                "id": response.user.id,
                "email": response.user.email,
                "role": response.user.role,
            },
            expires_at=response.session.expires_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}",
        )
