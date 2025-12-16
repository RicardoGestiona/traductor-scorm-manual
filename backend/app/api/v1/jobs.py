"""
Endpoint de gestión de Translation Jobs.

Filepath: backend/app/api/v1/jobs.py
Feature alignment: STORY-009 - Endpoint de Status de Job
"""

import logging
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Path, Depends
from typing import Optional

from app.core.auth import get_current_user, User
from app.models.translation import (
    TranslationJobResponse,
    JobStatusResponse,
    JobListResponse,
    ErrorResponse,
)
from app.services.job_service import job_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/jobs",
    response_model=JobListResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def list_jobs(
    limit: int = 20,
    offset: int = 0,
    status_filter: Optional[str] = None,
    user: User = Depends(get_current_user),
):
    """
    List translation jobs for the authenticated user (history).

    **Authentication:** Required (Bearer token)

    **Query Parameters:**
    - limit: Maximum number of results (default: 20, max: 100)
    - offset: Offset for pagination (default: 0)
    - status_filter: Filter by status (optional): uploaded, translating, completed, failed

    **Returns:**
    - jobs: List of translation jobs
    - total: Total number of jobs for this user
    - limit/offset: Pagination info
    - has_more: Whether there are more results

    **Example:**
    ```bash
    curl -X GET "http://localhost:8000/api/v1/jobs?limit=10&offset=0" \\
      -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
    ```
    """
    try:
        # Validar límite
        limit = min(limit, 100)

        logger.info(f"Listing jobs for user {user.email} (limit={limit}, offset={offset})")

        # Obtener jobs del usuario
        jobs = await job_service.list_jobs_by_user(
            user_id=user.id,
            limit=limit,
            offset=offset,
            status_filter=status_filter,
        )

        # Obtener total
        total = await job_service.count_jobs_by_user(user.id)

        return JobListResponse(
            jobs=jobs,
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + len(jobs)) < total,
        )

    except Exception as e:
        # SECURITY: ERROR-001 fix - Log full error, return generic message
        logger.error(f"Failed to list jobs for user {user.email}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to list jobs",
                "message": "An error occurred while retrieving your jobs. Please try again.",
            },
        )


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - Job belongs to another user"},
        404: {"model": ErrorResponse, "description": "Job not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_job_status(
    job_id: UUID = Path(..., description="Unique identifier of the translation job"),
    user: User = Depends(get_current_user),
):
    """
    Get the status of a translation job.

    This endpoint allows clients to poll the status of a translation job
    to track its progress and retrieve download URLs when completed.

    **Returns:**
    - job_id: UUID of the job
    - status: Current status (uploaded, validating, parsing, translating, rebuilding, completed, failed)
    - progress_percentage: Progress from 0 to 100
    - current_step: Human-readable description of current step
    - download_urls: Dict of language code -> signed URL (when completed)
    - error_message: Error details if status is 'failed'
    - estimated_completion: Estimated timestamp for completion (if available)

    **Typical polling pattern:**
    ```javascript
    const pollStatus = async (jobId) => {
      const interval = setInterval(async () => {
        const response = await fetch(`/api/v1/jobs/${jobId}`);
        const data = await response.json();

        if (data.status === 'completed' || data.status === 'failed') {
          clearInterval(interval);
          // Handle completion or error
        }

        // Update UI with progress
        updateProgressBar(data.progress_percentage);
      }, 2000); // Poll every 2 seconds
    };
    ```

    **Example response (in progress):**
    ```json
    {
      "job_id": "123e4567-e89b-12d3-a456-426614174000",
      "status": "translating",
      "progress_percentage": 45,
      "current_step": "Translating content to Spanish (45% complete)",
      "download_urls": {},
      "error_message": null
    }
    ```

    **Example response (completed):**
    ```json
    {
      "job_id": "123e4567-e89b-12d3-a456-426614174000",
      "status": "completed",
      "progress_percentage": 100,
      "current_step": "Translation completed successfully",
      "download_urls": {
        "es": "https://storage.supabase.co/...",
        "fr": "https://storage.supabase.co/..."
      },
      "error_message": null
    }
    ```
    """
    try:
        logger.info(f"Fetching status for job {job_id} (user: {user.email})")

        # Obtener job desde la base de datos
        job = await job_service.get_job(job_id)

        if not job:
            logger.warning(f"Job {job_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Job not found",
                    "details": f"No translation job found with ID: {job_id}",
                },
            )

        # Verificar que el job pertenece al usuario autenticado
        if job.user_id and str(job.user_id) != user.id:
            logger.warning(f"User {user.email} attempted to access job {job_id} owned by {job.user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Forbidden",
                    "details": "You don't have permission to access this translation job",
                },
            )

        # Generar descripción del paso actual basado en el estado
        current_step = _get_current_step_description(job)

        # Construir respuesta
        response = JobStatusResponse(
            job_id=job.id,
            status=job.status,
            progress_percentage=job.progress_percentage,
            current_step=current_step,
            download_urls=job.download_urls,
            error_message=job.error_message,
            estimated_completion=job.completed_at,  # Si ya completó, usar esa fecha
        )

        logger.info(f"Job {job_id} status: {job.status} ({job.progress_percentage}%)")
        return response

    except HTTPException:
        # Re-raise HTTP exceptions (como 404)
        raise

    except Exception as e:
        # SECURITY: ERROR-001 fix - Log full error, return generic message
        logger.error(f"Failed to fetch job status for {job_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to fetch job status",
                "message": "An error occurred while retrieving job status. Please try again.",
            },
        )


@router.get(
    "/jobs/{job_id}/details",
    response_model=TranslationJobResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - Job belongs to another user"},
        404: {"model": ErrorResponse, "description": "Job not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_job_details(
    job_id: UUID = Path(..., description="Unique identifier of the translation job"),
    user: User = Depends(get_current_user),
):
    """
    Get full details of a translation job.

    This endpoint returns all available information about a translation job,
    including metadata, timestamps, and file information.

    **Returns:**
    - Complete TranslationJobResponse with all fields
    - Includes: filename, SCORM version, languages, timestamps, etc.

    **Use this endpoint when:**
    - You need complete job information (not just status)
    - Building a job history/details page
    - Debugging or auditing purposes

    **For simple status polling, use GET /jobs/{job_id} instead**
    (lighter response, optimized for frequent polling)
    """
    try:
        logger.info(f"Fetching full details for job {job_id} (user: {user.email})")

        job = await job_service.get_job(job_id)

        if not job:
            logger.warning(f"Job {job_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Job not found",
                    "details": f"No translation job found with ID: {job_id}",
                },
            )

        # SECURITY: IDOR-001 fix - Verificar que el job pertenece al usuario autenticado
        if job.user_id and str(job.user_id) != user.id:
            logger.warning(f"User {user.email} attempted to access job details {job_id} owned by {job.user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Forbidden",
                    "details": "You don't have permission to access this translation job",
                },
            )

        logger.info(f"Returning full details for job {job_id}")
        return job

    except HTTPException:
        raise

    except Exception as e:
        # SECURITY: ERROR-001 fix - Log full error, return generic message
        logger.error(f"Failed to fetch job details for {job_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to fetch job details",
                "message": "An error occurred while retrieving job details. Please try again.",
            },
        )


def _get_current_step_description(job: TranslationJobResponse) -> str:
    """
    Generar descripción human-readable del paso actual.

    Args:
        job: Job con status y progress

    Returns:
        String descriptivo del paso actual
    """
    status_descriptions = {
        "uploaded": "File uploaded successfully. Waiting to start processing.",
        "validating": f"Validating SCORM package structure... ({job.progress_percentage}%)",
        "parsing": f"Extracting translatable content... ({job.progress_percentage}%)",
        "translating": f"Translating content to {len(job.target_languages)} language(s)... ({job.progress_percentage}%)",
        "rebuilding": f"Rebuilding translated SCORM package(s)... ({job.progress_percentage}%)",
        "completed": f"Translation completed successfully! {len(job.download_urls)} package(s) ready for download.",
        "failed": f"Translation failed: {job.error_message or 'Unknown error'}",
    }

    return status_descriptions.get(
        job.status.value, f"Processing... ({job.progress_percentage}%)"
    )
