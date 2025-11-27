"""
Configuración de Celery para procesamiento asíncrono.

Filepath: backend/app/core/celery_app.py
Feature alignment: STORY-010 - Celery Task para Traducción Asíncrona
"""

from celery import Celery
from app.core.config import settings

# Crear instancia de Celery
celery_app = Celery(
    "traductor_scorm",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.translation_tasks"],
)

# Configuración de Celery
celery_app.conf.update(
    # Serialización
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Retry
    task_acks_late=True,  # Acknowledge task solo después de completar
    task_reject_on_worker_lost=True,  # Rechazar si worker se cae
    # Timeouts
    task_soft_time_limit=3600,  # 1 hora soft limit (lanza excepción)
    task_time_limit=3900,  # 1h 5min hard limit (mata el proceso)
    # Resultados
    result_expires=86400,  # Resultados expiran en 24 horas
    # Performance
    worker_prefetch_multiplier=1,  # Solo tomar 1 tarea a la vez (para tareas largas)
    worker_max_tasks_per_child=50,  # Restart worker después de 50 tareas (evitar memory leaks)
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.tasks"])
