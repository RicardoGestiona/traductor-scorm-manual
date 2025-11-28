# ⚡ Guía de Inicio Rápido - Traductor SCORM

**Tiempo estimado**: 10 minutos para estar traduciendo tu primer SCORM

---

## 🎯 Objetivo

Al final de esta guía tendrás:
- ✅ Backend y Frontend corriendo localmente
- ✅ Cuenta de usuario creada
- ✅ Tu primer SCORM traducido a múltiples idiomas

---

## 📋 Pre-requisitos

Antes de empezar, asegúrate de tener:

- **Node.js 18+**: `node --version`
- **Python 3.11+**: `python3 --version`
- **Git**: `git --version`
- **Cuenta de Supabase** (gratis): https://supabase.com
- **API Key de Anthropic** (opcional para demo): https://console.anthropic.com

---

## 🚀 Paso 1: Clonar el Repositorio (1 min)

```bash
# Clonar proyecto
git clone https://github.com/RicardoGestiona/traductor-scorm-manual.git
cd traductor-scorm-manual

# Verificar estructura
ls -la
# Deberías ver: backend/ frontend/ .claude/ README.md
```

---

## 🔧 Paso 2: Configurar Supabase (3 min)

### 2.1 Crear Proyecto en Supabase

1. Ir a https://supabase.com/dashboard
2. Click en **"New Project"**
3. Configurar:
   - **Name**: traductor-scorm
   - **Database Password**: (guárdalo bien)
   - **Region**: Elige la más cercana
   - Click **"Create new project"** (tarda ~2 min)

### 2.2 Obtener Credenciales

Una vez creado el proyecto:

1. Ir a **Settings** → **API**
2. Copiar:
   - **Project URL**: `https://xxx.supabase.co`
   - **anon/public key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
   - **service_role key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

### 2.3 Ejecutar Migraciones

1. Ir a **SQL Editor** en Supabase Dashboard
2. Click **"New Query"**
3. Copiar y ejecutar el contenido de:
   - `backend/database/migrations/001_create_translation_jobs.sql`
   - Click **"Run"** (verde abajo a la derecha)
4. Repetir con:
   - `backend/database/migrations/002_create_translation_cache.sql`

### 2.4 Crear Storage Buckets

1. Ir a **Storage** en Supabase Dashboard
2. Click **"Create a new bucket"**
   - **Name**: `scorm-originals`
   - **Public**: No (desmarcado)
   - Click **"Create bucket"**
3. Repetir para bucket:
   - **Name**: `scorm-translated`

---

## 🔑 Paso 3: Configurar Variables de Entorno (2 min)

### 3.1 Backend

```bash
cd backend

# Copiar template
cp .env.example .env

# Editar con tus credenciales
nano .env  # o usa tu editor favorito
```

**Archivo `.env`** (rellenar con tus valores):

```env
# Supabase (obtener de Step 2.2)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# AI Translation (obtener de Anthropic Console)
# Para DEMO puedes dejarlo vacío y usar mock
ANTHROPIC_API_KEY=sk-ant-api03-...

# Database (obtener de Supabase Settings → Database)
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres

# Redis (para desarrollo local, dejar así)
REDIS_URL=redis://localhost:6379/0

# Security (generar nuevo)
SECRET_KEY=$(openssl rand -hex 32)

# CORS (para desarrollo local, dejar así)
ALLOWED_ORIGINS=["http://localhost:5173"]
```

**Tip**: Para generar `SECRET_KEY` en Mac/Linux:
```bash
openssl rand -hex 32
```

### 3.2 Frontend

```bash
cd ../frontend

# Copiar template
cp .env.example .env

# Editar
nano .env
```

**Archivo `.env`**:

```env
# Backend API (para desarrollo local)
VITE_API_URL=http://127.0.0.1:8000

# Supabase (SOLO anon key, NO service role)
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 🏃 Paso 4: Instalar Dependencias y Ejecutar (3 min)

### 4.1 Backend

```bash
cd backend

# Crear virtual environment
python3 -m venv venv

# Activar
source venv/bin/activate  # Mac/Linux
# o en Windows: venv\Scripts\activate

# Instalar dependencias
pip install -e ".[dev]"

# Ejecutar servidor
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Deberías ver:
# INFO:     Uvicorn running on http://127.0.0.1:8000
# INFO:     Application startup complete.
```

**Verificar**: Abre http://127.0.0.1:8000/docs en tu navegador

### 4.2 Frontend (en otra terminal)

```bash
cd frontend

# Instalar dependencias
npm install

# Ejecutar servidor de desarrollo
npm run dev

# Deberías ver:
# VITE v5.0.0  ready in 500 ms
# ➜  Local:   http://localhost:5173/
```

**Verificar**: Abre http://localhost:5173 en tu navegador

---

## 🎉 Paso 5: Probar el Sistema (1 min)

### 5.1 Crear tu Primera Cuenta

1. Ir a http://localhost:5173
2. Deberías ver la página de **Login**
3. Click en **"Regístrate aquí"**
4. Completar formulario:
   - **Email**: tu@email.com
   - **Password**: mínimo 6 caracteres
   - **Confirmar Password**: repetir
5. Click **"Crear Cuenta"**
6. Serás redirigido a **Login**
7. Ingresar credenciales
8. ¡Ya estás dentro! 🎉

### 5.2 Traducir tu Primer SCORM (Demo)

**Nota**: Para esta demo, puedes usar un SCORM de ejemplo o crear uno simple.

#### Crear SCORM Simple de Prueba:

```bash
# Crear estructura mínima
mkdir -p sample_scorm
cd sample_scorm

# Crear imsmanifest.xml
cat > imsmanifest.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="SCORM_001" version="1.2">
  <metadata>
    <schema>ADL SCORM</schema>
    <schemaversion>1.2</schemaversion>
  </metadata>
  <organizations default="ORG-001">
    <organization identifier="ORG-001">
      <title>Curso de Prueba</title>
      <item identifier="ITEM-001" identifierref="RES-001">
        <title>Lección 1: Introducción</title>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="RES-001" type="webcontent" href="index.html">
      <file href="index.html"/>
    </resource>
  </resources>
</manifest>
EOF

# Crear index.html
cat > index.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Lección 1</title>
</head>
<body>
  <h1>Bienvenido al Curso</h1>
  <p>Este es un curso de ejemplo para probar el traductor SCORM.</p>
  <p>Aquí aprenderás conceptos básicos de e-learning.</p>
</body>
</html>
EOF

# Comprimir en ZIP
zip -r ../sample_scorm.zip .
cd ..
```

#### Subir y Traducir:

1. En http://localhost:5173, verás la pantalla de **Upload**
2. **Paso 1**: Arrastra `sample_scorm.zip` a la zona de drop
   - O click para seleccionar archivo
3. **Paso 2**: Seleccionar idiomas
   - **Origen**: Español (o "auto-detect")
   - **Destino**: Marcar English, Français
4. Click **"Iniciar Traducción"**
5. **Paso 3**: Ver progreso en tiempo real
   - Verás barra de progreso
   - Estados: Validating → Parsing → Translating → Rebuilding
6. **Paso 4**: Descargar archivos traducidos
   - Botón por cada idioma: **Descargar EN**, **Descargar FR**
   - O **"Descargar Todos"** para bundle ZIP

¡Listo! Ya tienes tu SCORM traducido 🎊

---

## 🐛 Solución de Problemas Comunes

### Backend no inicia

**Error**: `ModuleNotFoundError: No module named 'fastapi'`

**Solución**:
```bash
cd backend
source venv/bin/activate
pip install -e ".[dev]"
```

### Frontend muestra error de CORS

**Error**: `Access to fetch at 'http://127.0.0.1:8000' has been blocked by CORS`

**Solución**: Verificar que `ALLOWED_ORIGINS` en `backend/.env` incluya:
```env
ALLOWED_ORIGINS=["http://localhost:5173"]
```

### Error de autenticación en Supabase

**Error**: `Invalid API key`

**Solución**:
1. Verificar que copiaste las keys correctamente
2. En Supabase Dashboard → Settings → API, copiar de nuevo
3. Asegurarte que en frontend usas `SUPABASE_ANON_KEY` (NO service role)

### Traducción no funciona

**Error**: `Translation failed: API key not found`

**Solución**: Agregar tu `ANTHROPIC_API_KEY` en `backend/.env`

O para testing sin API key:
1. Comentar llamada a Claude en `backend/app/services/translation_service.py`
2. Retornar mock translation (para desarrollo)

---

## 📚 Próximos Pasos

Ya tienes el sistema funcionando. ¿Qué sigue?

### Explorar Funcionalidades

- **API Docs**: http://127.0.0.1:8000/docs
  - Probar endpoints manualmente
  - Ver modelos de datos

- **Traducir SCORM Real**:
  - Subir un paquete SCORM real (hasta 500MB)
  - Probar con múltiples idiomas (hasta 12 disponibles)

### Desarrollo

- **Leer Arquitectura**: [CLAUDE.md](.claude/CLAUDE.md)
- **Ver Roadmap**: [BACKLOG.md](.claude/BACKLOG.md)
- **Revisar Decisiones**: [STATUSLOG.md](.claude/STATUSLOG.md)

### Deployment

- **Production Deploy**: [DEPLOYMENT.md](DEPLOYMENT.md)
  - Deploy en Vercel (frontend)
  - Deploy en Railway (backend)
  - Configuración de CI/CD

### Contribuir

- **Issues**: https://github.com/RicardoGestiona/traductor-scorm-manual/issues
- **Pull Requests**: Siempre bienvenidas

---

## 🆘 Ayuda

¿Algo no funciona? ¿Tienes preguntas?

1. **Revisar Logs**:
   ```bash
   # Backend logs (en terminal donde corre uvicorn)
   # Frontend logs (en consola del navegador - F12)
   ```

2. **Consultar Documentación**:
   - [README.md](README.md) - Documentación general
   - [DEPLOYMENT.md](DEPLOYMENT.md) - Troubleshooting detallado

3. **Abrir Issue**:
   - https://github.com/RicardoGestiona/traductor-scorm-manual/issues

---

**¡Felicitaciones!** 🎉 Ya tienes tu propio traductor SCORM funcionando

**Tiempo total**: ~10 minutos
**Siguiente paso**: Traducir tu primer SCORM real
