"""
Celery tasks package.

Filepath: backend/app/tasks/__init__.py
"""

from app.tasks.translation_tasks import translate_scorm_task

__all__ = ["translate_scorm_task"]
