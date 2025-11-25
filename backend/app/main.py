"""
Main FastAPI application entry point.

This module initializes the FastAPI app, configures middleware,
and registers API routers.

Filepath: backend/app/main.py
Feature alignment: STORY-002 - Setup de Backend FastAPI
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# TODO-FASE-1: Import routers when implemented
# from app.api.v1 import translation, scorm, languages

app = FastAPI(
    title="Traductor SCORM API",
    description="API REST para traducir paquetes SCORM a múltiples idiomas usando IA",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware - Configure for production later
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO-FASE-1: Restrict to frontend domain in production
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


# TODO-FASE-1: Register API routers
# app.include_router(translation.router, prefix="/api/v1", tags=["translation"])
# app.include_router(scorm.router, prefix="/api/v1", tags=["scorm"])
# app.include_router(languages.router, prefix="/api/v1", tags=["languages"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes (dev only)
    )
