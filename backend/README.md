# Backend - Traductor SCORM API

API REST construida con FastAPI para traducir paquetes SCORM a múltiples idiomas usando IA.

## 🚀 Quick Start

### Opción 1: Docker Compose (Recomendado)

```bash
# Desde la raíz del proyecto
cp backend/.env.example backend/.env
# Editar backend/.env con tus API keys

docker-compose up --build
```

API disponible en: `http://localhost:8000`
Docs interactivas: `http://localhost:8000/docs`

### Opción 2: Desarrollo Local

**Requisitos**:
- Python 3.11+
- PostgreSQL 16+
- Redis 7+

**Setup**:

```bash
cd backend

# Crear virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -e ".[dev]"

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# Ejecutar PostgreSQL y Redis localmente
# (o usar servicios cloud)

# Ejecutar servidor de desarrollo
python -m app.main
# o
uvicorn app.main:app --reload
```

API disponible en: `http://localhost:8000`

---

## 📁 Estructura del Proyecto

```
backend/
├── app/
│   ├── api/              # API Endpoints
│   │   └── v1/
│   │       ├── translation.py    # POST /translate, GET /jobs/{id}
│   │       ├── scorm.py          # SCORM validation endpoints
│   │       └── languages.py      # GET /languages
│   ├── core/             # Configuración
│   │   ├── config.py             # Settings con Pydantic
│   │   ├── security.py           # Auth, CORS, etc
│   │   └── celery_app.py         # Configuración de Celery
│   ├── models/           # Pydantic Models
│   │   ├── scorm.py
│   │   ├── translation.py
│   │   └── user.py
│   ├── services/         # Lógica de Negocio
│   │   ├── scorm_parser.py       # Parsear SCORM
│   │   ├── translator.py         # Integración con Claude/OpenAI
│   │   ├── scorm_rebuilder.py    # Reconstruir SCORM traducido
│   │   └── storage.py            # Supabase Storage
│   ├── tasks/            # Celery Tasks
│   │   └── translation_tasks.py
│   └── main.py           # FastAPI app entry point
├── tests/
├── pyproject.toml
├── Dockerfile
├── .env.example
└── README.md
```

---

## 🔧 Configuración

### Variables de Entorno

Copiar `.env.example` a `.env` y configurar:

```bash
# Supabase (obtener de https://supabase.com/dashboard)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-key

# Claude API (obtener de https://console.anthropic.com/)
ANTHROPIC_API_KEY=sk-ant-your-key

# Opcional: OpenAI como fallback
OPENAI_API_KEY=sk-your-openai-key
```

---

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Con coverage
pytest --cov=app --cov-report=html

# Tests específicos
pytest tests/services/test_scorm_parser.py -v
```

---

## 📊 API Endpoints

### Health Check
```http
GET /health
```

### Upload SCORM
```http
POST /api/v1/upload
Content-Type: multipart/form-data

{
  "file": <SCORM.zip>,
  "source_language": "es",
  "target_languages": ["en", "fr"]
}
```

**Response**:
```json
{
  "job_id": "uuid",
  "status": "processing",
  "message": "Translation job started"
}
```

### Get Job Status
```http
GET /api/v1/jobs/{job_id}
```

**Response**:
```json
{
  "id": "uuid",
  "status": "completed",
  "progress_percentage": 100,
  "download_urls": {
    "en": "https://...",
    "fr": "https://..."
  }
}
```

### Get Supported Languages
```http
GET /api/v1/languages
```

Ver documentación completa interactiva en: `http://localhost:8000/docs`

---

## 🛠️ Code Quality

### Linting & Formatting

```bash
# Lint con Ruff
ruff check .

# Auto-fix
ruff check --fix .

# Format
ruff format .
```

### Type Checking

```bash
mypy app/
```

---

## 🐛 Debugging

Con Docker Compose:

```bash
# Ver logs
docker-compose logs -f backend

# Logs de Celery worker
docker-compose logs -f celery_worker

# Entrar al container
docker-compose exec backend bash

# Python shell interactivo
docker-compose exec backend ipython
```

---

## 📚 Referencias

- **FastAPI**: https://fastapi.tiangolo.com/
- **Pydantic**: https://docs.pydantic.dev/
- **Celery**: https://docs.celeryq.dev/
- **Supabase Python**: https://supabase.com/docs/reference/python
- **Anthropic API**: https://docs.anthropic.com/

---

## 🚧 TODO

Ver `.claude/BACKLOG.md` para el backlog completo de features.

**Próximos pasos**:
- [ ] Implementar endpoints de API (STORY-004)
- [ ] SCORM parser (STORY-005)
- [ ] Integración con Claude API (STORY-007)
- [ ] Celery tasks (STORY-010)

---

**Mantenido por**: Ricardo
**Última actualización**: 2025-11-25
