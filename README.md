# 🌍 Traductor SCORM

Sistema web + API para traducir paquetes SCORM (1.2, 2004, xAPI) a múltiples idiomas usando IA, manteniendo la integridad y funcionalidad del contenido e-learning original.

## 🎯 ¿Qué hace?

- **Upload** un paquete SCORM (.zip)
- **Selecciona** idiomas destino (ES, EN, FR, DE, IT, PT, NL, PL, ZH, JA)
- **Traduce** automáticamente usando Claude AI
- **Descarga** paquetes SCORM traducidos listos para tu LMS

**Tiempo**: De horas de trabajo manual → **5 minutos automáticos**

---

## ✨ Features

✅ **Parser completo de SCORM 1.2 y 2004** (11 tests pasando)
✅ **Detección automática de versión** SCORM (1.2, 2004, xAPI)
✅ **Parsing de sequencing rules** y objectives (SCORM 2004)
✅ **Validación de estructura** de paquetes SCORM
✅ **Backend API funcionando** (FastAPI + health check)
✅ **Frontend React** conectado con backend
🔄 Traducción automática con IA contextual (en desarrollo)
🔄 Interfaz web de upload (en desarrollo)
⏳ API REST completa para integraciones
⏳ Progreso en tiempo real

---

## 🏗️ Arquitectura

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend  │ ───> │  FastAPI API │ ───> │  Celery     │
│  (React)    │      │  (Python)    │      │  Worker     │
└─────────────┘      └──────────────┘      └─────────────┘
                            │                      │
                            ▼                      ▼
                     ┌─────────────┐        ┌─────────────┐
                     │  Supabase   │        │  Claude API │
                     │  (DB + Auth)│        │  (Translate)│
                     └─────────────┘        └─────────────┘
```

**Stack**:
- **Backend**: FastAPI + Python 3.14 + Pydantic
- **Frontend**: React 18 + Vite + TypeScript + Tailwind CSS v3
- **Database**: Supabase (PostgreSQL)
- **Queue**: Celery + Redis (pendiente)
- **AI**: Anthropic Claude API (pendiente integración)
- **Storage**: Supabase Storage (pendiente)
- **Parsing**: lxml + BeautifulSoup4

---

## 🚀 Quick Start

### Con Docker Compose (Recomendado)

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/traductor-scorm.git
cd traductor-scorm

# Configurar variables de entorno
cp backend/.env.example backend/.env
# Editar backend/.env con tus API keys (Supabase, Anthropic)

# Levantar todos los servicios
docker-compose up --build
```

**Servicios disponibles**:
- API: `http://localhost:8000` (Docs: `/docs`)
- Frontend: `http://localhost:5173` (TODO: Fase 1)
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

### Desarrollo Local (sin Docker)

**Requisitos**:
- Python 3.11+
- Node.js 18+
- npm

**Setup inicial**:

```bash
# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# Editar .env con tus API keys

# Frontend (en otra terminal)
cd frontend
npm install
cp .env.example .env
```

**Iniciar servidores**:

```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2 - Frontend
cd frontend
npm run dev
```

**URLs**:
- Frontend: http://localhost:5173
- Backend API: http://127.0.0.1:8000
- API Docs: http://127.0.0.1:8000/docs

Ver instrucciones detalladas en:
- Backend: [`backend/README.md`](backend/README.md)
- Frontend: [`frontend/README.md`](frontend/README.md)

---

## 📖 Documentación

### Para Desarrolladores

- **[CLAUDE.md](.claude/CLAUDE.md)**: Arquitectura completa, stack, convenciones
- **[PRD.md](.claude/PRD.md)**: Product Requirements, acceptance criteria
- **[BACKLOG.md](.claude/BACKLOG.md)**: EPICs, Stories, Tasks
- **[STATUSLOG.md](.claude/STATUSLOG.md)**: Estado actual, decisiones, ADRs

### API Reference

Documentación interactiva: `http://localhost:8000/docs`

**Endpoints principales**:

```http
POST /api/v1/upload
GET  /api/v1/jobs/{job_id}
GET  /api/v1/languages
```

Ver ejemplos completos en [backend/README.md](backend/README.md#-api-endpoints)

---

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest --cov=app

# Frontend tests (TODO: Fase 1)
cd frontend
npm test
```

---

## 📊 Roadmap

### ✅ Fase 0: Foundation (Completada - 2025-11-25)
- [x] Documentación completa (CLAUDE.md, PRD.md, BACKLOG.md)
- [x] Estructura de proyecto
- [x] Docker Compose setup
- [x] Health check endpoint
- [x] Setup de Backend FastAPI funcionando
- [x] Setup de Frontend React + Vite + TypeScript + Tailwind
- [x] Conexión frontend-backend verificada
- [x] Repositorio GitHub configurado

### 🔄 Fase 1: MVP Backend (En Progreso - Sprint 1, 75% completado)
- [x] **SCORM 1.2 parser completo** (252 líneas, 11 tests)
- [x] **SCORM 2004 parser completo** (sequencing, objectives, completion threshold)
- [x] **Extracción de contenido traducible** (manifest + HTML, 9 tests)
  - Filtrado inteligente de elementos no traducibles (script, style, code)
  - Extracción de atributos (alt, title, placeholder, aria-*)
  - Contexto detallado para cada segmento
  - Contador de caracteres para estimación de costos
- [x] **Integración con Claude API** (91 líneas, 14 tests)
  - Modelo: Claude 3.5 Sonnet (temperatura 0.3)
  - Batch processing (max 50 segmentos/batch)
  - Retry logic con exponential backoff (3 intentos)
  - Prompts contextuales para e-learning
  - Tracking de tokens y estimación de costos
  - Soporte para 12 idiomas
- [x] **34 tests unitarios pasando** (100% success rate)
- [x] **Test coverage**: 74.07% overall ✅✅ (superado ampliamente objetivo 70%!)
- [ ] Endpoints de upload/translate/download
- [ ] Celery worker para procesamiento async

### ⏳ Fase 2: Frontend Completo (Próximo)
- [x] Estructura base de React funcionando
- [ ] Componente de upload con drag & drop
- [ ] Selector de idiomas
- [ ] Progress tracking en tiempo real
- [ ] Autenticación con Supabase

### 🔮 Fase 3: Features Avanzadas
- [ ] xAPI/TinCan support
- [ ] Edición manual de traducciones
- [ ] Webhooks para integraciones
- [ ] Analytics y reporting

Ver backlog completo en [BACKLOG.md](.claude/BACKLOG.md)

---

## 🤝 Contribución

Este es un proyecto personal en desarrollo activo. Sugerencias y feedback son bienvenidos!

**Para desarrollar**:
1. Fork el repositorio
2. Crear rama: `git checkout -b feature/mi-feature`
3. Commit: `git commit -m "feat: descripción"`
4. Push: `git push origin feature/mi-feature`
5. Abrir Pull Request

---

## 📝 Licencia

MIT License - Ver [LICENSE](LICENSE)

---

## 👤 Autor

**Ricardo**

---

## 🙏 Agradecimientos

- [FastAPI](https://fastapi.tiangolo.com/) - Framework web moderno
- [Anthropic](https://www.anthropic.com/) - Claude AI para traducción
- [Supabase](https://supabase.com/) - Backend as a Service
- [Celery](https://docs.celeryq.dev/) - Task queue distribuida

---

## 📈 Estado Actual

**Progreso MVP**: 29% completado (6/21 stories)
**Sprint actual**: Sprint 1 - Backend Core (75% completado)
**Stories completadas**:
- ✅ STORY-001: Setup de Documentación
- ✅ STORY-002: Setup de Backend FastAPI
- ✅ STORY-003: Setup de Frontend React
- ✅ STORY-005: Parser de SCORM 1.2/2004
- ✅ STORY-006: Extracción de Contenido Traducible
- ✅ STORY-007: Integración con Claude API

**Próxima Story**: STORY-008 - Reconstrucción de SCORM Traducido

**Test Coverage**: 74.07% ✅✅ (superado ampliamente objetivo 70%!)
**Tests**: 34/34 passing (100%)

---

**Estado del proyecto**: 🚧 En desarrollo activo
**Última actualización**: 2025-11-26 04:45 AM
**Versión**: 0.4.0-alpha
