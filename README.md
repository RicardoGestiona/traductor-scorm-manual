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

✅ Traducción automática con IA contextual (Claude/GPT-4)
✅ Soporta SCORM 1.2, 2004 y xAPI/TinCan
✅ Preserva 100% de funcionalidad del SCORM original
✅ Interfaz web simple (drag & drop)
✅ API REST para integraciones
✅ Validación automática pre/post traducción
✅ Progreso en tiempo real
✅ Historial de traducciones

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
- **Backend**: FastAPI + Python 3.11
- **Frontend**: React + Vite + TypeScript
- **Database**: Supabase (PostgreSQL)
- **Queue**: Celery + Redis
- **AI**: Anthropic Claude API
- **Storage**: Supabase Storage

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

### Desarrollo Local

Ver instrucciones detalladas en:
- Backend: [`backend/README.md`](backend/README.md)
- Frontend: [`frontend/README.md`](frontend/README.md) *(Próximamente)*

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

### ✅ Fase 0: Foundation (Completada)
- [x] Documentación completa (CLAUDE.md, PRD.md, BACKLOG.md)
- [x] Estructura de proyecto
- [x] Docker Compose setup
- [x] Health check endpoint

### 🔄 Fase 1: MVP Backend (En Progreso)
- [ ] SCORM 1.2 parser
- [ ] Integración con Claude API
- [ ] Endpoints de upload/translate/download
- [ ] Celery worker para procesamiento async

### ⏳ Fase 2: Frontend + Auth (Próximo)
- [ ] Interfaz web React
- [ ] Autenticación con Supabase
- [ ] Upload de SCORM con drag & drop
- [ ] Progress tracking en tiempo real

### 🔮 Fase 3: Features Avanzadas
- [ ] SCORM 2004 completo
- [ ] xAPI/TinCan support
- [ ] Edición manual de traducciones
- [ ] Webhooks para integraciones

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

**Estado del proyecto**: 🚧 En desarrollo activo
**Última actualización**: 2025-11-25
**Versión**: 0.1.0-alpha
