"""
Main FastAPI application entry point.

This module initializes the FastAPI app, configures middleware,
and registers API routers.

Filepath: backend/app/main.py
Feature alignment: STORY-002 - Setup de Backend FastAPI
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import upload, jobs, download
from app.core.config import settings

app = FastAPI(
    title="Traductor SCORM API",
    description="API REST para traducir paquetes SCORM a múltiples idiomas usando IA",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
