# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Traductor SCORM - Sistema web + API para traducir paquetes SCORM (1.2, 2004, xAPI) a múltiples idiomas usando IA (Claude), manteniendo la integridad del contenido e-learning.

## Build & Development Commands

### Con Docker Compose (Recomendado)
```bash
cp backend/.env.example backend/.env  # Configurar API keys
docker-compose up --build
```

### Desarrollo Local
```bash
# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Frontend
cd frontend
npm install
npm run dev

# Tests
cd backend && pytest --cov=app
```

## Tech Stack

### Backend
- FastAPI + Python 3.14 + Pydantic
- Celery + Redis (procesamiento asíncrono)
- Supabase (PostgreSQL + Storage + Auth)
- Anthropic Claude API (traducción)
- lxml + BeautifulSoup4 (parsing)

### Frontend
- React 18 + Vite + TypeScript
- Tailwind CSS v3
- Supabase Auth

## Architecture

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

## API Endpoints

### Autenticación
- `POST /api/v1/auth/signup` - Registro
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/logout` - Logout
- `POST /api/v1/auth/refresh` - Renovar token

### Traducción
- `POST /api/v1/upload` - Subir paquete SCORM
- `GET /api/v1/jobs/{job_id}` - Status del job
- `GET /api/v1/download/{job_id}/{lang}` - Descargar traducción

## Services

- API: `http://localhost:8000` (Docs: `/docs`)
- Frontend: `http://localhost:5173`

## CLI Tool

Herramienta de línea de comandos en `traductor-scorm-cli/`:
```bash
cd traductor-scorm-cli
pip install -r requirements.txt
python traductor.py
```
