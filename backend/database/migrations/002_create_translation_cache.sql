-- Migration: Create translation_cache table
-- Filepath: backend/database/migrations/002_create_translation_cache.sql
-- Feature alignment: STORY-016 - Database Schema Setup
-- Purpose: Cache de traducciones para reducir costos de API y mejorar performance

-- Crear tabla de cache de traducciones
CREATE TABLE IF NOT EXISTS translation_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Original text
    source_text TEXT NOT NULL,
    source_language TEXT NOT NULL,

    -- Translated text
    target_language TEXT NOT NULL,
    translated_text TEXT NOT NULL,

    -- Context for cache invalidation
    context_hash TEXT,  -- MD5 hash del contexto del curso para invalidación selectiva

    -- Metadata
    char_count INTEGER,  -- Número de caracteres del texto original
    translation_model TEXT DEFAULT 'claude-3-sonnet',  -- Modelo usado para traducir

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ DEFAULT NOW(),

    -- Stats
    hit_count INTEGER DEFAULT 0,  -- Veces que se ha usado este cache

    -- Constraint: Una combinación única de source_text + languages + context
    CONSTRAINT unique_translation UNIQUE (source_text, source_language, target_language, context_hash)
);

-- Índices para lookups rápidos
CREATE INDEX IF NOT EXISTS idx_translation_cache_lookup
    ON translation_cache(source_text, source_language, target_language);

CREATE INDEX IF NOT EXISTS idx_translation_cache_context
    ON translation_cache(context_hash);

CREATE INDEX IF NOT EXISTS idx_translation_cache_created_at
    ON translation_cache(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_translation_cache_last_used
    ON translation_cache(last_used_at DESC);

-- Índice para limpiar cache antiguo
CREATE INDEX IF NOT EXISTS idx_translation_cache_old_entries
    ON translation_cache(last_used_at)
    WHERE last_used_at < NOW() - INTERVAL '90 days';

-- Trigger para actualizar last_used_at cuando se usa una traducción del cache
CREATE OR REPLACE FUNCTION update_cache_last_used()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_used_at = NOW();
    NEW.hit_count = OLD.hit_count + 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Función para limpiar cache antiguo (> 90 días sin uso)
CREATE OR REPLACE FUNCTION clean_old_cache_entries()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM translation_cache
    WHERE last_used_at < NOW() - INTERVAL '90 days';

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- RLS Policies (cache es compartido entre todos los usuarios)
ALTER TABLE translation_cache ENABLE ROW LEVEL SECURITY;

-- Policy: Todos pueden leer del cache (compartido)
CREATE POLICY "Anyone can read from cache"
    ON translation_cache
    FOR SELECT
    USING (true);

-- Policy: Solo el sistema puede escribir en el cache (service role)
CREATE POLICY "Only system can write cache"
    ON translation_cache
    FOR INSERT
    WITH CHECK (false);  -- Solo service role key puede insertar

-- Policy: Solo el sistema puede actualizar el cache
CREATE POLICY "Only system can update cache"
    ON translation_cache
    FOR UPDATE
    USING (false);  -- Solo service role key puede actualizar

-- Comentarios de documentación
COMMENT ON TABLE translation_cache IS 'Cache global de traducciones para reducir llamadas a API y costos';
COMMENT ON COLUMN translation_cache.source_text IS 'Texto original a traducir (max 10,000 chars recomendado)';
COMMENT ON COLUMN translation_cache.context_hash IS 'MD5 hash del contexto del curso - permite invalidar cache por curso';
COMMENT ON COLUMN translation_cache.hit_count IS 'Contador de veces que se ha reutilizado esta traducción';
COMMENT ON COLUMN translation_cache.last_used_at IS 'Última vez que se usó - para limpieza de cache antiguo';

-- Vista para estadísticas de cache
CREATE OR REPLACE VIEW translation_cache_stats AS
SELECT
    target_language,
    COUNT(*) as total_entries,
    SUM(hit_count) as total_hits,
    AVG(hit_count) as avg_hits_per_entry,
    SUM(char_count) as total_chars_cached,
    MIN(created_at) as oldest_entry,
    MAX(last_used_at) as most_recent_use,
    COUNT(*) FILTER (WHERE last_used_at > NOW() - INTERVAL '7 days') as active_last_week,
    COUNT(*) FILTER (WHERE last_used_at < NOW() - INTERVAL '90 days') as old_entries_to_clean
FROM translation_cache
GROUP BY target_language
ORDER BY total_entries DESC;

COMMENT ON VIEW translation_cache_stats IS 'Estadísticas del cache de traducciones por idioma';
