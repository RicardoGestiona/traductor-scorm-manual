-- Migration: Create translation_jobs table
-- Filepath: backend/database/migrations/001_create_translation_jobs.sql
-- Feature alignment: STORY-004 - Upload, STORY-009 - Status de Job

-- Crear tabla de translation_jobs
CREATE TABLE IF NOT EXISTS translation_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- File info
    original_filename TEXT NOT NULL,
    storage_path TEXT,  -- Path en Supabase Storage
    scorm_version TEXT,  -- "1.2", "2004", "xapi" (detectado durante parsing)

    -- Languages
    source_language TEXT NOT NULL DEFAULT 'auto',
    target_languages TEXT[] NOT NULL,

    -- Status tracking
    status TEXT NOT NULL DEFAULT 'uploaded',
    progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,

    -- Downloads
    download_urls JSONB DEFAULT '{}',  -- {"es": "url", "fr": "url"}

    -- Error handling
    error_message TEXT,

    -- User (for v2 with auth)
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_translation_jobs_status ON translation_jobs(status);
CREATE INDEX IF NOT EXISTS idx_translation_jobs_created_at ON translation_jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_translation_jobs_user_id ON translation_jobs(user_id);

-- Trigger para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_translation_jobs_updated_at
    BEFORE UPDATE ON translation_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- RLS Policies (para cuando se implemente auth en v2)
ALTER TABLE translation_jobs ENABLE ROW LEVEL SECURITY;

-- Policy: Usuarios solo ven sus propios jobs
CREATE POLICY "Users can view their own jobs"
    ON translation_jobs
    FOR SELECT
    USING (auth.uid() = user_id OR user_id IS NULL);

-- Policy: Usuarios solo crean jobs con su user_id
CREATE POLICY "Users can create their own jobs"
    ON translation_jobs
    FOR INSERT
    WITH CHECK (auth.uid() = user_id OR user_id IS NULL);

-- Policy: Usuarios solo actualizan sus propios jobs
CREATE POLICY "Users can update their own jobs"
    ON translation_jobs
    FOR UPDATE
    USING (auth.uid() = user_id OR user_id IS NULL);

-- Comentarios de documentación
COMMENT ON TABLE translation_jobs IS 'Jobs de traducción de paquetes SCORM';
COMMENT ON COLUMN translation_jobs.status IS 'Estados: uploaded, validating, parsing, translating, rebuilding, completed, failed';
COMMENT ON COLUMN translation_jobs.progress_percentage IS 'Progreso de 0 a 100';
COMMENT ON COLUMN translation_jobs.download_urls IS 'URLs firmadas para descarga por idioma';
