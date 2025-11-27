"""
Authentication middleware and utilities for Supabase Auth.

This module provides:
- JWT token verification from Supabase
- User dependency for FastAPI routes
- Optional authentication decorator
"""

import os
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Supabase client configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError(
        "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment"
    )

# Create Supabase client (singleton)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# HTTP Bearer token scheme
security = HTTPBearer()


class User:
    """Represents an authenticated user from Supabase."""

    def __init__(self, user_data: dict):
        self.id: str = user_data.get("id")
        self.email: str = user_data.get("email")
        self.role: str = user_data.get("role", "authenticated")
        self.metadata: dict = user_data.get("user_metadata", {})

    def __repr__(self):
        return f"User(id={self.id}, email={self.email}, role={self.role})"


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.

    Usage in FastAPI routes:
    ```python
    @app.get("/protected")
    async def protected_route(user: User = Depends(get_current_user)):
        return {"user_id": user.id, "email": user.email}
    ```

    Raises:
        HTTPException: 401 if token is invalid or expired
    """
    token = credentials.credentials

    try:
        # Verify JWT token with Supabase
        user_response = supabase.auth.get_user(token)

        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return User(user_response.user.model_dump())

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    )
) -> Optional[User]:
    """
    Dependency to optionally get the current user.

    Returns None if no credentials provided (allows anonymous access).
    Raises 401 if credentials provided but invalid.

    Usage:
    ```python
    @app.get("/optional-auth")
    async def route(user: Optional[User] = Depends(get_current_user_optional)):
        if user:
            return {"message": f"Hello {user.email}"}
        return {"message": "Hello anonymous"}
    ```
    """
    if not credentials:
        return None

    try:
        user_response = supabase.auth.get_user(credentials.credentials)

        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return User(user_response.user.model_dump())

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_supabase_client() -> Client:
    """
    Returns the Supabase client with service role permissions.

    Use this for server-side operations that need to bypass RLS.

    Usage:
    ```python
    from app.core.auth import get_supabase_client

    supabase = get_supabase_client()
    response = supabase.table('translation_jobs').select("*").execute()
    ```
    """
    return supabase


def get_supabase_client_for_user(user: User) -> Client:
    """
    Returns a Supabase client scoped to the authenticated user.

    This respects RLS policies based on the user's JWT token.

    Usage:
    ```python
    @app.get("/my-jobs")
    async def get_my_jobs(user: User = Depends(get_current_user)):
        client = get_supabase_client_for_user(user)
        # This query will only return jobs for this specific user (RLS applied)
        response = client.table('translation_jobs').select("*").execute()
        return response.data
    ```

    Note: Currently returns service role client. To properly implement RLS,
    we would need to pass the user's access token to create a new client.
    For MVP, we'll filter by user_id manually in queries.
    """
    # TODO: Implement proper user-scoped client with user's access token
    # For now, return service role client and filter manually
    return supabase
