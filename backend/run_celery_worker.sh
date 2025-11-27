#!/bin/bash
# Script para iniciar Celery worker
#
# Uso:
#   chmod +x run_celery_worker.sh
#   ./run_celery_worker.sh

echo "🚀 Starting Celery worker..."

# Activar virtual environment si existe
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Iniciar worker con configuración optimizada
celery -A app.core.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --max-tasks-per-child=50 \
    --task-events \
    --without-gossip \
    --without-mingle \
    --without-heartbeat
