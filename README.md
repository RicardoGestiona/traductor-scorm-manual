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
✅ **Frontend React completo** con upload, progress tracking y downloads
✅ **Traducción automática con Claude AI** (batch processing, retry logic)
✅ **Autenticación con Supabase Auth** (signup, login, JWT tokens)
✅ **Protección de endpoints** (ownership verification, 401/403 handling)
✅ **Celery + Redis** para procesamiento asíncrono
✅ **Docker Compose** con stack completo (frontend + backend + Celery + DB)
✅ **Progreso en tiempo real** con polling de status
✅ **Storage en Supabase** para SCORM packages y traducciones

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

**Endpoints implementados**:

```http
# Autenticación
POST /api/v1/auth/signup               # Registrar nuevo usuario
POST /api/v1/auth/login                # Iniciar sesión
POST /api/v1/auth/logout               # Cerrar sesión
GET  /api/v1/auth/me                   # Obtener usuario actual
POST /api/v1/auth/refresh              # Renovar access token

# Traducción (requieren autenticación)
POST /api/v1/upload                    # Subir paquete SCORM
GET  /api/v1/jobs/{job_id}            # Status del job (polling)
GET  /api/v1/jobs/{job_id}/details    # Detalles completos del job
GET  /api/v1/download/{job_id}/{lang} # Descargar paquete traducido
GET  /api/v1/download/{job_id}/all    # Descargar todos los idiomas

# Health
GET  /health                           # Health check
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

### ✅ Fase 1: MVP Backend Core (Completada - Sprint 1, 100%)
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
- [x] **Reconstrucción de SCORM traducido** (111 líneas, 10 tests)
  - Aplicación de traducciones a XML (XPath-based)
  - Aplicación de traducciones a HTML (text + attributes)
  - Preservación de estructura de carpetas completa
  - Generación de ZIP del paquete traducido
  - Manejo de traducciones parciales y vacías
- [x] **44 tests unitarios pasando** (100% success rate)
- [x] **Test coverage**: 77.24% overall ✅✅✅ (superado objetivo 70%!)

### ✅ Fase 2: API REST & Database (Completada - Sprint 2, 100%)
- [x] **Endpoint de Upload** (POST /api/v1/upload)
  - Validación de archivos (extensión .zip, max 500MB)
  - Validación de idiomas soportados
  - Upload a Supabase Storage
  - Creación de Translation Jobs en DB
  - Protección con autenticación JWT
  - 10 tests unitarios implementados
- [x] **Endpoint de Status** (GET /api/v1/jobs/{id})
  - Polling optimizado con respuesta ligera
  - Endpoint /details para información completa
  - Descripciones human-readable de estados
  - Manejo de errores (404, 422, 500)
  - Verificación de ownership por usuario
  - 14 tests unitarios implementados
- [x] **Endpoints de Download** (GET /api/v1/download/{id}/{lang})
  - Descarga individual por idioma
  - Descarga de bundle con todos los idiomas
  - URLs firmadas con expiración (7 días)
  - Protección con autenticación y ownership
- [x] **Services Infrastructure**
  - StorageService: Upload/download/signed URLs (Supabase)
  - JobService: CRUD de Translation Jobs
  - Configuración centralizada (Settings)
  - Modelos Pydantic completos
- [x] **Database Setup**
  - Tabla translation_jobs con RLS policies
  - Tabla translation_cache para reducir costos
  - Índices para performance
  - Triggers auto-update timestamps
  - Funciones de limpieza automática
  - Vistas de estadísticas
- [x] **Celery Worker** para procesamiento asíncrono
  - Task de traducción completa
  - Actualización de progreso en tiempo real
  - Retry logic con exponential backoff
  - Error handling robusto
- [x] **Autenticación con Supabase Auth**
  - Endpoints de signup, login, logout, refresh
  - Middleware de verificación JWT
  - Dependencias de FastAPI para autenticación
  - Gestión de sesiones

### ✅ Fase 3: Frontend Completo (Completada - Sprint 3, 100%)
- [x] Estructura base de React funcionando
- [x] Componente de upload con drag & drop
- [x] Selector de idiomas con 12 idiomas soportados
- [x] Progress tracking en tiempo real con polling
- [x] Autenticación completa (signup, login, logout)
- [x] Protección de rutas (ProtectedRoute)
- [x] Botones de descarga por idioma
- [x] Descarga de bundle completo
- [x] Manejo de errores 401/403
- [x] Loading states y feedback visual
- [x] Diseño responsive con Tailwind CSS

### ✅ Fase 4: DevOps & Deployment (Completada - 2025-11-27)
- [x] **Docker Compose** con stack completo
  - Frontend (React + Vite)
  - Backend (FastAPI)
  - Celery Worker
  - PostgreSQL (local para dev)
  - Redis (queue para Celery)
- [x] **Frontend Dockerfile** multi-stage
  - Development stage con hot-reload
  - Build stage optimizado
  - Production stage con nginx
- [x] **Nginx configuration** para SPA
  - Routing para React Router
  - Gzip compression
  - Security headers
  - Static asset caching

### 🔮 Fase 5: Features Avanzadas (Próximo)
- [ ] xAPI/TinCan support completo
- [ ] Edición manual de traducciones pre/post-procesamiento
- [ ] Webhooks para integraciones externas
- [ ] Analytics y reporting de uso
- [ ] Sistema de caché inteligente (implementado pero sin UI)
- [ ] Gestión de glossarios personalizados
- [ ] Soporte para más formatos (H5P, etc.)

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

**Progreso MVP**: 43% completado (9/21 stories)

**Sprint 0**: ✅ 100% completado (Foundation)
**Sprint 1**: ✅ 100% completado (Backend Core - 4/4 stories)
**Sprint 2**: 🔄 50% completado (API REST - 2/4 stories)

**Stories completadas** (9 total):
- ✅ STORY-001: Setup de Documentación
- ✅ STORY-002: Setup de Backend FastAPI
- ✅ STORY-003: Setup de Frontend React
- ✅ STORY-004: Endpoint de Upload de SCORM ⭐ NEW
- ✅ STORY-005: Parser de SCORM 1.2/2004
- ✅ STORY-006: Extracción de Contenido Traducible
- ✅ STORY-007: Integración con Claude API
- ✅ STORY-008: Reconstrucción de SCORM Traducido
- ✅ STORY-009: Endpoint de Status de Job ⭐ NEW

**Próximas Stories**:
1. STORY-010: Celery Task para procesamiento asíncrono (HIGH)
2. STORY-016: Database Schema Setup (ejecutar migration)
3. STORY-011: Frontend Upload Component

**Test Coverage**:
- Sprint 1: 77.24% ✅✅✅ (superado objetivo 70%!)
- Sprint 2: 24 tests adicionales implementados
- **Total**: 68 tests (44 Sprint 1 + 24 Sprint 2)

**Métricas del Proyecto**:
- Líneas de código: ~3,500+ (backend core + API)
- Archivos creados: 30+
- Coverage objetivo: 70%+ (✅ alcanzado)

---

**Estado del proyecto**: 🚧 En desarrollo activo
**Última actualización**: 2025-11-27 12:00 PM
**Versión**: 0.6.0-alpha
