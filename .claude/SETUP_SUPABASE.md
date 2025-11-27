# 🚀 Guía de Setup de Supabase - Traductor SCORM

**Story**: STORY-015 - Configuración de Supabase
**Fecha**: 2025-11-27
**Status**: Pendiente de configuración manual

---

## 📋 OVERVIEW

Esta guía te ayudará a configurar Supabase para el proyecto Traductor SCORM. Necesitaremos:
- ✅ Crear proyecto en Supabase
- ✅ Ejecutar migraciones SQL (translation_jobs + translation_cache)
- ✅ Configurar Storage buckets para archivos SCORM
- ✅ Obtener credenciales para conectar el backend/frontend

---

## PASO 1: Crear Proyecto en Supabase

### 1.1 Ir a Supabase Dashboard
1. Ir a https://supabase.com/dashboard
2. Click en "New Project"
3. Seleccionar organización (o crear una nueva)

### 1.2 Configuración del Proyecto
```
Project Name: traductor-scorm-manual
Database Password: [GENERA UNA CONTRASEÑA SEGURA - GUÁRDALA]
Region: South America (São Paulo) - sa-east-1
Pricing Plan: Free (suficiente para MVP)
```

**⏱️ Tiempo estimado**: ~2-3 minutos mientras se crea la database

### 1.3 Guardar Credenciales
Una vez creado el proyecto, ve a **Settings → API** y copia:

```bash
# PROJECT URL
SUPABASE_URL=https://[tu-project-id].supabase.co

# ANON KEY (pública - se puede usar en frontend)
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# SERVICE ROLE KEY (privada - SOLO para backend)
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**⚠️ IMPORTANTE**:
- La `SERVICE_ROLE_KEY` bypasea RLS policies y tiene acceso total a la database
- NUNCA expongas esta key en el frontend
- NUNCA comitees esta key en git

---

## PASO 2: Ejecutar Migraciones SQL

### 2.1 Abrir SQL Editor
1. En Supabase Dashboard, ir a **SQL Editor** (icono de database en sidebar)
2. Click en **"New Query"**

### 2.2 Ejecutar Migración 001 (translation_jobs)

Copiar el contenido completo de:
```
backend/database/migrations/001_create_translation_jobs.sql
```

Pegar en el SQL Editor y hacer click en **"Run"** (o `Ctrl+Enter`)

**✅ Verificar**: Deberías ver el mensaje "Success. No rows returned"

### 2.3 Ejecutar Migración 002 (translation_cache)

Copiar el contenido completo de:
```
backend/database/migrations/002_create_translation_cache.sql
```

Pegar en el SQL Editor y hacer click en **"Run"**

**✅ Verificar**: Deberías ver el mensaje "Success. No rows returned"

### 2.4 Verificar Tablas Creadas

Ir a **Table Editor** (icono de tabla en sidebar) y verificar que existen:
- ✅ `translation_jobs` con columnas: id, user_id, original_filename, scorm_version, source_language, target_languages, status, progress_percentage, created_at, updated_at, completed_at, download_urls, error_message
- ✅ `translation_cache` con columnas: id, source_text, source_language, target_language, translated_text, context_hash, char_count, translation_model, created_at, last_used_at, hit_count

### 2.5 Verificar Índices

En SQL Editor, ejecutar:
```sql
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
    AND tablename IN ('translation_jobs', 'translation_cache')
ORDER BY tablename, indexname;
```

**✅ Verificar**: Deberías ver varios índices como `idx_translation_jobs_user_id`, `idx_translation_cache_lookup`, etc.

### 2.6 Verificar RLS Policies

En SQL Editor, ejecutar:
```sql
SELECT
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;
```

**✅ Verificar**: Deberías ver policies para SELECT, INSERT, UPDATE en ambas tablas

### 2.7 Verificar Funciones y Vistas

En SQL Editor, ejecutar:
```sql
-- Verificar función de limpieza
SELECT proname, prosrc
FROM pg_proc
WHERE proname = 'clean_old_cache_entries';

-- Verificar vista de estadísticas
SELECT * FROM translation_cache_stats LIMIT 1;
```

---

## PASO 3: Configurar Storage Buckets

### 3.1 Crear Bucket para SCORM Originals

1. Ir a **Storage** (icono de carpeta en sidebar)
2. Click en **"New bucket"**
3. Configurar:
   ```
   Name: scorm-originals
   Public: No (privado)
   File size limit: 500 MB
   Allowed MIME types: application/zip, application/x-zip-compressed
   ```
4. Click en **"Create bucket"**

### 3.2 Crear Bucket para SCORM Traducidos

1. Click en **"New bucket"**
2. Configurar:
   ```
   Name: scorm-translated
   Public: No (privado)
   File size limit: 500 MB
   Allowed MIME types: application/zip, application/x-zip-compressed
   ```
3. Click en **"Create bucket"**

### 3.3 Configurar Storage Policies (RLS)

Ir a **Storage → Policies** y crear las siguientes policies:

#### Policy 1: Upload a scorm-originals
```sql
-- Nombre: Users can upload their own SCORM files
-- Bucket: scorm-originals
-- Policy type: INSERT
-- Target roles: authenticated
-- WITH CHECK expression:
bucket_id = 'scorm-originals' AND auth.uid()::text = (storage.foldername(name))[1]
```

#### Policy 2: Download de scorm-originals
```sql
-- Nombre: Users can download their own SCORM files
-- Bucket: scorm-originals
-- Policy type: SELECT
-- Target roles: authenticated
-- USING expression:
bucket_id = 'scorm-originals' AND auth.uid()::text = (storage.foldername(name))[1]
```

#### Policy 3: Download de scorm-translated
```sql
-- Nombre: Users can download their translated SCORM files
-- Bucket: scorm-translated
-- Policy type: SELECT
-- Target roles: authenticated
-- USING expression:
bucket_id = 'scorm-translated' AND auth.uid()::text = (storage.foldername(name))[1]
```

**Nota**: El `service_role` bypasea estas policies y puede escribir en `scorm-translated` desde el backend.

### 3.4 Configurar Lifecycle Policy (Auto-delete después de 7 días)

**⚠️ IMPORTANTE**: Supabase Free tier no soporta lifecycle policies automáticas.

**Workaround para MVP**: Implementar cleanup manual vía Celery cron job que:
1. Busque archivos con `created_at < NOW() - INTERVAL '7 days'` en `translation_jobs`
2. Elimine archivos del Storage usando `supabase.storage.from_('bucket').remove([paths])`
3. Se ejecute daily a las 3 AM

**TODO**: Crear task de Celery `cleanup_old_files.py` (agregar a BACKLOG como task técnico)

---

## PASO 4: Configurar Variables de Entorno

### 4.1 Backend (.env)

Crear archivo `backend/.env` con:

```bash
# Supabase
SUPABASE_URL=https://[tu-project-id].supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Database (para acceso directo si se necesita)
DATABASE_URL=postgresql://postgres:[password]@db.[project-id].supabase.co:5432/postgres

# Claude API (para traducción)
ANTHROPIC_API_KEY=sk-ant-api03-...

# Redis (para Celery)
REDIS_URL=redis://localhost:6379/0

# App Config
ENVIRONMENT=development
MAX_FILE_SIZE_MB=500
```

**Obtener Database URL**:
1. Ir a **Settings → Database**
2. Copiar "Connection string" en modo "URI"
3. Reemplazar `[YOUR-PASSWORD]` con la contraseña que usaste al crear el proyecto

### 4.2 Frontend (.env)

Crear archivo `frontend/.env` con:

```bash
# Solo las keys públicas van en frontend
VITE_SUPABASE_URL=https://[tu-project-id].supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Backend API URL
VITE_API_URL=http://localhost:8000
```

### 4.3 Actualizar .gitignore

Verificar que `.gitignore` incluya:
```
.env
.env.local
.env.*.local
backend/.env
frontend/.env
```

**⚠️ NUNCA comitear archivos .env**

---

## PASO 5: Verificar Conexión

### 5.1 Test de Conexión desde Backend

Crear script temporal `backend/test_supabase.py`:

```python
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

print(f"Conectando a: {url}")
supabase: Client = create_client(url, key)

# Test 1: Listar tablas
print("\n✅ Test 1: Conectividad básica")
response = supabase.table('translation_jobs').select("*").limit(1).execute()
print(f"   Conexión exitosa. Tablas accesibles.")

# Test 2: Insert de prueba
print("\n✅ Test 2: Insert en translation_jobs")
test_job = {
    "original_filename": "test.zip",
    "scorm_version": "1.2",
    "source_language": "en",
    "target_languages": ["es"],
    "status": "uploaded",
    "progress_percentage": 0
}
response = supabase.table('translation_jobs').insert(test_job).execute()
print(f"   Insert exitoso. Job ID: {response.data[0]['id']}")

# Test 3: Delete de prueba
job_id = response.data[0]['id']
print("\n✅ Test 3: Delete de test job")
supabase.table('translation_jobs').delete().eq('id', job_id).execute()
print(f"   Delete exitoso.")

# Test 4: Storage
print("\n✅ Test 4: Listar buckets")
buckets = supabase.storage.list_buckets()
print(f"   Buckets disponibles: {[b.name for b in buckets]}")

print("\n🎉 Todos los tests pasaron. Supabase está correctamente configurado.")
```

Ejecutar:
```bash
cd backend
python test_supabase.py
```

**✅ Verificar**: Deberías ver todos los tests pasando sin errores.

**Limpiar**: Eliminar `test_supabase.py` después de verificar.

### 5.2 Test de Conexión desde Frontend

En `frontend/src/App.tsx`, agregar temporalmente:

```typescript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
)

// Test en useEffect
useEffect(() => {
  const testConnection = async () => {
    const { data, error } = await supabase
      .from('translation_jobs')
      .select('*')
      .limit(1)

    if (error) {
      console.error('❌ Error conectando a Supabase:', error)
    } else {
      console.log('✅ Conexión exitosa a Supabase')
    }
  }

  testConnection()
}, [])
```

Ejecutar:
```bash
cd frontend
npm run dev
```

Abrir DevTools → Console

**✅ Verificar**: Deberías ver "✅ Conexión exitosa a Supabase" en consola

**Limpiar**: Eliminar el código de test del `useEffect`

---

## PASO 6: (Opcional) Seed Data para Testing

Si quieres datos de prueba en desarrollo:

### 6.1 Ejecutar Seed de Jobs

En SQL Editor, copiar y ejecutar:
```
backend/database/seed/001_sample_jobs.sql
```

### 6.2 Ejecutar Seed de Cache

En SQL Editor, copiar y ejecutar:
```
backend/database/seed/002_sample_cache.sql
```

**⚠️ SOLO DESARROLLO**: NO ejecutar en producción.

**Verificar**:
```sql
SELECT COUNT(*) FROM translation_jobs;  -- Debería retornar 6
SELECT COUNT(*) FROM translation_cache; -- Debería retornar 15
```

---

## ✅ CHECKLIST DE COMPLETITUD

### Setup Básico
- [ ] Proyecto Supabase creado
- [ ] Contraseña de database guardada en lugar seguro
- [ ] Credenciales copiadas (URL, ANON_KEY, SERVICE_ROLE_KEY)

### Database
- [ ] Migración 001 (translation_jobs) ejecutada
- [ ] Migración 002 (translation_cache) ejecutada
- [ ] Tablas verificadas en Table Editor
- [ ] Índices creados correctamente
- [ ] RLS policies activas
- [ ] Función `clean_old_cache_entries()` creada
- [ ] Vista `translation_cache_stats` creada

### Storage
- [ ] Bucket `scorm-originals` creado
- [ ] Bucket `scorm-translated` creado
- [ ] Storage policies configuradas
- [ ] Límite de 500MB establecido

### Configuración Local
- [ ] `backend/.env` creado con todas las variables
- [ ] `frontend/.env` creado con variables públicas
- [ ] `.gitignore` actualizado
- [ ] Test de conexión backend pasando
- [ ] Test de conexión frontend pasando

### Opcional (Desarrollo)
- [ ] Seed data ejecutado
- [ ] 6 jobs de ejemplo visibles en Table Editor
- [ ] 15 cache entries de ejemplo visibles

---

## 🚨 TROUBLESHOOTING

### Error: "relation does not exist"
**Causa**: La migración no se ejecutó correctamente
**Solución**: Re-ejecutar la migración SQL en SQL Editor

### Error: "new row violates row-level security policy"
**Causa**: RLS policies mal configuradas
**Solución**: Usar `service_role_key` en backend (bypasea RLS)

### Error: "The resource you requested could not be found"
**Causa**: Bucket de Storage no existe o nombre incorrecto
**Solución**: Verificar nombre exacto del bucket en Storage panel

### Error: "Invalid API key"
**Causa**: Key incorrecta o mal copiada
**Solución**: Re-copiar las keys desde Settings → API (cuidado con espacios extra)

### Error: "timeout"
**Causa**: Region muy lejos o problemas de red
**Solución**: Esperar unos minutos, Supabase a veces tarda en provisionar

---

## 📚 PRÓXIMOS PASOS

Una vez completado este setup:

1. ✅ Actualizar STATUSLOG.md documentando el setup de Supabase
2. ✅ Comitear cambios:
   - `.env.example` (sin valores reales)
   - `SETUP_SUPABASE.md` (esta guía)
3. ✅ Continuar con STORY-017: Implementar autenticación con Supabase Auth
4. ✅ O continuar con stories de backend/frontend que necesiten Supabase

---

**Creado por**: Claude Code
**Fecha**: 2025-11-27
**Story Reference**: STORY-015
