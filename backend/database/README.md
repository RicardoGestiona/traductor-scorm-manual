# Database Migrations & Seed Data

Esta carpeta contiene las migraciones SQL y datos de prueba para Supabase PostgreSQL.

## 📁 Estructura

```
database/
├── migrations/      # Migraciones SQL (esquema, índices, RLS)
│   ├── 001_create_translation_jobs.sql
│   └── 002_create_translation_cache.sql
├── seed/           # Datos de prueba para desarrollo
│   ├── 001_sample_jobs.sql
│   └── 002_sample_cache.sql
└── README.md       # Este archivo
```

## 🚀 Uso

### 1. Ejecutar Migraciones

Las migraciones deben ejecutarse en orden en **Supabase SQL Editor**:

1. Ir a Supabase Dashboard → SQL Editor
2. Crear nuevo query
3. Copiar contenido de `migrations/001_create_translation_jobs.sql`
4. Ejecutar (Run)
5. Repetir para `002_create_translation_cache.sql`

**Orden de ejecución**:
1. ✅ `001_create_translation_jobs.sql` - Tabla principal de jobs
2. ✅ `002_create_translation_cache.sql` - Cache de traducciones

### 2. Ejecutar Seed Data (Desarrollo solamente)

⚠️ **IMPORTANTE**: Los seed data son solo para desarrollo/testing. **NO ejecutar en producción**.

```sql
-- En Supabase SQL Editor (desarrollo)
\i seed/001_sample_jobs.sql
\i seed/002_sample_cache.sql
```

O copiar y pegar el contenido en el SQL Editor.

## 📊 Schema Overview

### Tabla: `translation_jobs`

Almacena los jobs de traducción.

**Campos principales**:
- `id` (UUID): ID único del job
- `original_filename` (TEXT): Nombre del archivo SCORM original
- `storage_path` (TEXT): Path en Supabase Storage
- `scorm_version` (TEXT): "1.2", "2004", "xapi"
- `source_language` (TEXT): Código de idioma origen
- `target_languages` (TEXT[]): Array de códigos de idiomas destino
- `status` (TEXT): Estado del job (uploaded, translating, completed, failed, etc.)
- `progress_percentage` (INTEGER): 0-100
- `download_urls` (JSONB): URLs firmadas por idioma
- `user_id` (UUID): FK a auth.users (para v2)

**Índices**:
- `idx_translation_jobs_status`: Búsqueda por estado
- `idx_translation_jobs_created_at`: Ordenar por fecha
- `idx_translation_jobs_user_id`: Filtrar por usuario

**RLS Policies**:
- ✅ Usuarios solo ven sus propios jobs
- ✅ Usuarios solo crean jobs con su user_id
- ✅ Usuarios solo actualizan sus propios jobs
- ⚠️ user_id IS NULL permite testing sin auth

### Tabla: `translation_cache`

Cache global de traducciones para reducir costos de API.

**Campos principales**:
- `id` (UUID): ID único de entrada
- `source_text` (TEXT): Texto original
- `source_language` (TEXT): Idioma origen
- `target_language` (TEXT): Idioma destino
- `translated_text` (TEXT): Texto traducido
- `context_hash` (TEXT): Hash MD5 del contexto del curso
- `hit_count` (INTEGER): Veces que se ha reutilizado
- `last_used_at` (TIMESTAMPTZ): Última vez usado
- `translation_model` (TEXT): Modelo usado (claude-3-sonnet)

**Índices**:
- `idx_translation_cache_lookup`: Lookup rápido (source_text + languages)
- `idx_translation_cache_context`: Búsqueda por contexto
- `idx_translation_cache_old_entries`: Para limpieza de cache antiguo

**RLS Policies**:
- ✅ Todos pueden leer del cache (compartido)
- ⚠️ Solo service role puede escribir (INSERT/UPDATE)

**Constraint**:
- `unique_translation`: Una combinación única de (source_text, source_language, target_language, context_hash)

### Vista: `translation_cache_stats`

Estadísticas del cache por idioma.

```sql
SELECT * FROM translation_cache_stats;
```

**Campos**:
- `target_language`: Idioma
- `total_entries`: Total de entradas
- `total_hits`: Total de hits acumulados
- `avg_hits_per_entry`: Promedio de hits
- `total_chars_cached`: Total de caracteres cacheados
- `oldest_entry`: Entrada más antigua
- `most_recent_use`: Uso más reciente
- `active_last_week`: Entradas usadas en última semana
- `old_entries_to_clean`: Entradas > 90 días sin uso

## 🧹 Mantenimiento

### Limpiar Cache Antiguo

El cache acumula traducciones. Se recomienda limpiar entradas > 90 días sin uso:

```sql
SELECT clean_old_cache_entries();
-- Retorna número de entradas eliminadas
```

**Automatización**: Se puede configurar un cron job en Supabase:

1. Ir a Database → Cron Jobs
2. Crear nuevo job
3. Schedule: `0 2 * * 0` (cada domingo a las 2 AM)
4. Query: `SELECT clean_old_cache_entries();`

### Verificar Estado del Cache

```sql
-- Ver estadísticas generales
SELECT * FROM translation_cache_stats;

-- Ver entradas más usadas
SELECT
    source_text,
    target_language,
    hit_count,
    last_used_at
FROM translation_cache
ORDER BY hit_count DESC
LIMIT 20;

-- Ver entradas antiguas a limpiar
SELECT COUNT(*)
FROM translation_cache
WHERE last_used_at < NOW() - INTERVAL '90 days';
```

## 🔐 Seguridad (RLS)

### Row Level Security está habilitado en ambas tablas

**translation_jobs**:
- ✅ RLS ENABLED
- Usuarios solo acceden a sus propios jobs via `user_id`
- Para testing sin auth: jobs con `user_id IS NULL` son accesibles

**translation_cache**:
- ✅ RLS ENABLED
- Cache es compartido: todos pueden leer
- Solo service role key puede escribir

### Testing sin Autenticación

Para desarrollo sin Supabase Auth, los jobs con `user_id = NULL` son accesibles por todos.

**Producción**: Todos los jobs deben tener `user_id` asignado.

## 📝 Notas

1. **Migraciones son idempotentes**: Usan `CREATE TABLE IF NOT EXISTS`, seguro ejecutar múltiples veces
2. **Seed data es destructivo**: Comenta `TRUNCATE` para no borrar datos
3. **Cache es global**: Todas las traducciones se comparten entre usuarios
4. **Context hash**: Permite invalidar cache por curso específico
5. **Cleanup automático**: Recomendado configurar cron job semanal

## 🔗 Referencias

- [Supabase SQL Editor](https://app.supabase.com/project/_/sql)
- [Supabase RLS Policies](https://supabase.com/docs/guides/auth/row-level-security)
- [PostgreSQL JSONB](https://www.postgresql.org/docs/current/datatype-json.html)
- [Supabase Cron Jobs](https://supabase.com/docs/guides/database/extensions/pg_cron)
