"""
Main FastAPI application entry point.

This module initializes the FastAPI app, configures middleware,
and registers API routers.

Filepath: backend/app/main.py
Feature alignment: STORY-002 - Setup de Backend FastAPI
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.api.v1 import upload, jobs, download, auth
from app.core.config import settings


# SECURITY: HEADER-001 fix - Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Enable XSS filter (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions policy (restrict browser features)
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # HSTS - only in production with HTTPS
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        return response


app = FastAPI(
    title="Traductor SCORM API",
    description="API REST para traducir paquetes SCORM a múltiples idiomas usando IA",
    version="0.1.0",
    # SECURITY: Swagger UI available only in development
    docs_url="/docs" if settings.DEBUG or settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.DEBUG or settings.ENVIRONMENT == "development" else None,
)

# SECURITY: HEADER-001 fix - Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# SECURITY: CORS-001 fix - Restrictive CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    # Restrict to specific methods instead of "*"
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    # Restrict to specific headers instead of "*"
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
)


@app.get("/")
async def root():
    """Root endpoint - API info."""
    return {
        "name": "Traductor SCORM API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Used by Docker, Kubernetes, load balancers, etc. to verify service is running.

    Returns:
        dict: Status information
    """
    return {
        "status": "healthy",
        "service": "traductor-scorm-api",
    }


# Register API routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(upload.router, prefix="/api/v1", tags=["upload"])
app.include_router(jobs.router, prefix="/api/v1", tags=["jobs"])
app.include_router(download.router, prefix="/api/v1", tags=["download"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes (dev only)
    )
