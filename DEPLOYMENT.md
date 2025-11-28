# 🚀 Guía de Deployment - Traductor SCORM

**Última actualización**: 2025-11-28
**Versión**: 1.0.0 (MVP Completo)

---

## 📋 Pre-requisitos

### Servicios Externos Requeridos

1. **Supabase Project** (Database + Auth + Storage)
   - Database: PostgreSQL con RLS policies
   - Auth: Email/password habilitado
   - Storage: 2 buckets (scorm-originals, scorm-translated)
   - Plan: Free tier suficiente para MVP

2. **Anthropic API Key** (Claude AI)
   - Modelo: Claude 3.5 Sonnet
   - Rate limits: Según tu plan
   - Costo estimado: ~$0.003/request de traducción

3. **Redis** (para Celery)
   - Opcional en MVP (puede usar in-memory)
   - Requerido en producción para procesamiento async

---

## 🏗️ Arquitectura de Deployment

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   Vercel        │      │  Railway/Render  │      │   Supabase      │
│   (Frontend)    │ ───> │  (Backend API)   │ ───> │   (Database)    │
│   React SPA     │      │  FastAPI         │      │   PostgreSQL    │
└─────────────────┘      └──────────────────┘      └─────────────────┘
                                 │
                                 ▼
                         ┌──────────────────┐
                         │  Anthropic API   │
                         │  (Translation)   │
                         └──────────────────┘
```

---

## 🔧 Opción 1: Deployment con Docker Compose (Recomendado para desarrollo)

### 1.1 Setup Inicial

```bash
# Clonar repositorio
git clone https://github.com/RicardoGestiona/traductor-scorm-manual.git
cd traductor-scorm-manual

# Configurar variables de entorno
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

### 1.2 Configurar Backend (.env)

```env
# Supabase (obtener de tu proyecto Supabase)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# AI Translation (obtener de Anthropic Console)
ANTHROPIC_API_KEY=sk-ant-api03-...

# Database (Supabase te da esta URL)
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres

# Redis (para Docker local)
REDIS_URL=redis://redis:6379/0

# Security (generar nuevo secret)
SECRET_KEY=$(openssl rand -hex 32)

# CORS (ajustar según tu dominio frontend)
ALLOWED_ORIGINS=["http://localhost:5173", "https://tu-dominio.vercel.app"]
```

### 1.3 Configurar Frontend (.env)

```env
# Backend API
VITE_API_URL=http://localhost:8000

# Supabase (SOLO claves públicas)
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 1.4 Ejecutar Migraciones de Database

```bash
# 1. Ir a Supabase SQL Editor
# 2. Ejecutar en orden:

# Migration 001: translation_jobs table
-- Ver: backend/database/migrations/001_create_translation_jobs.sql

# Migration 002: translation_cache table
-- Ver: backend/database/migrations/002_create_translation_cache.sql

# 3. Verificar que las tablas existen
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public';
```

### 1.5 Configurar Storage Buckets

```bash
# En Supabase Dashboard → Storage:

# 1. Crear bucket "scorm-originals"
#    - Public: No
#    - File size limit: 500MB
#    - Allowed MIME types: application/zip

# 2. Crear bucket "scorm-translated"
#    - Public: No
#    - File size limit: 500MB
#    - Allowed MIME types: application/zip

# 3. Configurar RLS policies para ambos buckets
-- Ver: .claude/SETUP_SUPABASE.md para scripts SQL
```

### 1.6 Levantar Servicios

```bash
# Build y levantar todos los servicios
docker-compose up --build

# En modo detached (background)
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener servicios
docker-compose down
```

### 1.7 Verificar que Todo Funcione

```bash
# 1. Backend health check
curl http://localhost:8000/health
# Esperado: {"status":"healthy","service":"traductor-scorm-api"}

# 2. Frontend accesible
open http://localhost:5173

# 3. Swagger docs
open http://localhost:8000/docs

# 4. Verificar Celery worker
docker-compose logs celery-worker | grep "ready"
```

---

## 🌐 Opción 2: Deployment en Producción (Vercel + Railway)

### 2.1 Frontend en Vercel

```bash
# 1. Instalar Vercel CLI
npm install -g vercel

# 2. Login
vercel login

# 3. Deploy desde carpeta frontend
cd frontend
vercel

# 4. Configurar variables de entorno en Vercel Dashboard:
# - VITE_API_URL=https://tu-backend.railway.app
# - VITE_SUPABASE_URL=https://xxx.supabase.co
# - VITE_SUPABASE_ANON_KEY=eyJhbG...

# 5. Deploy a producción
vercel --prod
```

**Configuración de Build en Vercel**:
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "installCommand": "npm install",
  "framework": "vite"
}
```

### 2.2 Backend en Railway

```bash
# 1. Crear cuenta en Railway.app

# 2. Crear nuevo proyecto
# - Conectar repositorio GitHub
# - Seleccionar carpeta: backend/

# 3. Configurar variables de entorno en Railway:
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJhbG...
SUPABASE_SERVICE_ROLE_KEY=eyJhbG...
ANTHROPIC_API_KEY=sk-ant-api03-...
DATABASE_URL=${{Postgres.DATABASE_URL}}  # Auto-generado por Railway
REDIS_URL=${{Redis.REDIS_URL}}          # Auto-generado por Railway
SECRET_KEY=<generar-nuevo>
ALLOWED_ORIGINS=["https://tu-frontend.vercel.app"]

# 4. Agregar servicios adicionales:
# - PostgreSQL (si no usas Supabase como DB principal)
# - Redis (para Celery)

# 5. Deploy automático en cada push a main
```

**railway.json** (crear en backend/):
```json
{
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -e ."
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### 2.3 Celery Worker en Railway (Servicio Adicional)

```bash
# Crear otro servicio en Railway para Celery worker

# Dockerfile.celery (crear en backend/):
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install -e .

CMD ["celery", "-A", "app.core.celery_app", "worker", "--loglevel=info"]

# Variables de entorno: Las mismas que el backend
# Comando de start: Configurado en Dockerfile
```

---

## 🔐 Checklist de Seguridad para Producción

### Backend

- [ ] `SECRET_KEY` generado con `openssl rand -hex 32` (único por ambiente)
- [ ] `SUPABASE_SERVICE_ROLE_KEY` NUNCA expuesto en frontend
- [ ] `ANTHROPIC_API_KEY` guardado en variables de entorno (no en código)
- [ ] CORS configurado solo para dominios permitidos
- [ ] HTTPS habilitado (Railway/Render lo hacen automáticamente)
- [ ] Database URL con credentials seguros
- [ ] Rate limiting habilitado en endpoints críticos (TODO)

### Frontend

- [ ] SOLO usar `SUPABASE_ANON_KEY` (nunca service role key)
- [ ] Variables de entorno prefijadas con `VITE_`
- [ ] Build de producción minimizado (`npm run build`)
- [ ] HTTPS habilitado (Vercel lo hace automáticamente)
- [ ] CSP headers configurados (TODO)

### Supabase

- [ ] RLS policies habilitadas en todas las tablas
- [ ] Storage buckets con policies de acceso apropiadas
- [ ] Email confirmation habilitado en Auth settings (recomendado)
- [ ] Password strength requirements configurados
- [ ] Backups automáticos habilitados

---

## 📊 Monitoreo y Logs

### Backend Logs (Railway)

```bash
# Ver logs en tiempo real
railway logs

# Filtrar por servicio
railway logs --service=backend

# Buscar errores
railway logs | grep ERROR
```

### Frontend Errors (Vercel)

- Vercel Dashboard → Logs
- Integrar Sentry para error tracking (opcional)

### Database Monitoring (Supabase)

- Supabase Dashboard → Database → Query Performance
- Monitorear slow queries
- Revisar uso de conexiones

### API Usage Monitoring (Anthropic)

- Anthropic Console → Usage
- Monitorear costos y rate limits
- Alertas si se excede budget

---

## 🧪 Testing Post-Deployment

### 1. Test de Health Checks

```bash
# Backend
curl https://tu-backend.railway.app/health

# Expected: {"status":"healthy","service":"traductor-scorm-api"}
```

### 2. Test de Autenticación

```bash
# Signup
curl -X POST https://tu-backend.railway.app/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# Login
curl -X POST https://tu-backend.railway.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

### 3. Test de Upload (requiere auth)

```bash
# Obtener token de login primero
TOKEN="<access_token_from_login>"

# Upload SCORM
curl -X POST https://tu-backend.railway.app/api/v1/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@sample_scorm.zip" \
  -F "source_language=es" \
  -F "target_languages=en,fr"
```

### 4. Test E2E Manual

1. Ir a `https://tu-frontend.vercel.app`
2. Crear cuenta nueva (signup)
3. Login con credenciales
4. Subir archivo SCORM de prueba
5. Verificar progreso en tiempo real
6. Descargar archivos traducidos
7. Verificar que archivos sean válidos

---

## 🔄 CI/CD con GitHub Actions

### .github/workflows/deploy.yml

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run backend tests
        run: |
          cd backend
          pip install -e ".[dev]"
          pytest --cov=app

  deploy-backend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Railway
        run: |
          railway up --service backend
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}

  deploy-frontend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Vercel
        run: |
          cd frontend
          vercel --prod --token=${{ secrets.VERCEL_TOKEN }}
```

---

## 🐛 Troubleshooting

### Error: "CORS policy blocked"

**Solución**: Agregar dominio frontend a `ALLOWED_ORIGINS` en backend

```python
# backend/app/core/config.py
ALLOWED_ORIGINS = [
    "https://tu-frontend.vercel.app",
    "http://localhost:5173"  # Para desarrollo
]
```

### Error: "Supabase connection timeout"

**Solución**: Verificar que DATABASE_URL tenga formato correcto y que IP esté en allowlist

```bash
# Formato correcto
postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
```

### Error: "Translation job stuck in 'translating' state"

**Solución**: Verificar que Celery worker esté corriendo y tenga acceso a Redis

```bash
# Verificar Celery worker
docker-compose logs celery-worker

# Verificar conexión a Redis
redis-cli ping
```

### Error: "File upload fails (413 Entity Too Large)"

**Solución**: Aumentar límite de tamaño en nginx/proxy

```nginx
# Para Railway/Render (configurado automáticamente)
client_max_body_size 500M;
```

---

## 📈 Escalabilidad y Optimizaciones

### Para Producción Alta Demanda

1. **Horizontal Scaling**:
   - Railway: Auto-scaling habilitado
   - Múltiples Celery workers
   - Connection pooling en PostgreSQL

2. **Caching**:
   - Redis para cache de traducciones
   - CDN para assets estáticos (Vercel incluye)

3. **Database Optimization**:
   - Índices en columnas frecuentemente consultadas
   - Partitioning de tabla translation_jobs por fecha
   - Read replicas para queries pesadas

4. **Cost Optimization**:
   - Batch processing de traducciones (ya implementado)
   - Cache agresivo de traducciones comunes
   - Monitoring de costos de Anthropic API

---

## 📞 Soporte

**Documentación**:
- [README.md](README.md) - Guía general
- [CLAUDE.md](.claude/CLAUDE.md) - Arquitectura técnica
- [STATUSLOG.md](.claude/STATUSLOG.md) - Historial de desarrollo

**Issues**:
- GitHub Issues: https://github.com/RicardoGestiona/traductor-scorm-manual/issues

---

**Última actualización**: 2025-11-28
**Versión del MVP**: 1.0.0 (Production Ready)
