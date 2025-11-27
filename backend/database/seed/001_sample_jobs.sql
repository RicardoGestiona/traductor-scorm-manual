-- Seed Data: Sample translation jobs for testing
-- Filepath: backend/database/seed/001_sample_jobs.sql
-- Feature alignment: STORY-016 - Database Schema Setup
-- Purpose: Datos de prueba para desarrollo y testing

-- IMPORTANTE: Este seed data es solo para desarrollo/testing
-- NO ejecutar en producción

-- Limpiar datos existentes (solo para desarrollo)
-- TRUNCATE TABLE translation_jobs CASCADE;

-- Job 1: Completado exitosamente (ES → EN, FR)
INSERT INTO translation_jobs (
    id,
    original_filename,
    storage_path,
    scorm_version,
    source_language,
    target_languages,
    status,
    progress_percentage,
    created_at,
    updated_at,
    completed_at,
    download_urls,
    user_id
) VALUES (
    'a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d',
    'curso_basico_seguridad.zip',
    'originals/a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d/curso_basico_seguridad.zip',
    '1.2',
    'es',
    ARRAY['en', 'fr'],
    'completed',
    100,
    NOW() - INTERVAL '2 days',
    NOW() - INTERVAL '2 days',
    NOW() - INTERVAL '2 days',
    '{"en": "https://storage.example.com/translated/curso_EN.zip", "fr": "https://storage.example.com/translated/curso_FR.zip"}'::jsonb,
    NULL  -- Sin user_id para testing sin auth
);

-- Job 2: En progreso - Traduciendo (EN → ES, DE, IT)
INSERT INTO translation_jobs (
    id,
    original_filename,
    storage_path,
    scorm_version,
    source_language,
    target_languages,
    status,
    progress_percentage,
    created_at,
    updated_at,
    user_id
) VALUES (
    'b2c3d4e5-f6a7-4b5c-9d0e-1f2a3b4c5d6e',
    'cybersecurity_fundamentals.zip',
    'originals/b2c3d4e5-f6a7-4b5c-9d0e-1f2a3b4c5d6e/cybersecurity_fundamentals.zip',
    '2004',
    'en',
    ARRAY['es', 'de', 'it'],
    'translating',
    45,
    NOW() - INTERVAL '30 minutes',
    NOW() - INTERVAL '5 minutes',
    NULL
);

-- Job 3: Fallido - Error durante parsing
INSERT INTO translation_jobs (
    id,
    original_filename,
    storage_path,
    scorm_version,
    source_language,
    target_languages,
    status,
    progress_percentage,
    created_at,
    updated_at,
    error_message,
    user_id
) VALUES (
    'c3d4e5f6-a7b8-4c5d-0e1f-2a3b4c5d6e7f',
    'corrupted_package.zip',
    'originals/c3d4e5f6-a7b8-4c5d-0e1f-2a3b4c5d6e7f/corrupted_package.zip',
    NULL,
    'auto',
    ARRAY['en', 'fr', 'de'],
    'failed',
    15,
    NOW() - INTERVAL '1 day',
    NOW() - INTERVAL '1 day',
    'Invalid SCORM structure: imsmanifest.xml not found',
    NULL
);

-- Job 4: Recién subido - En validación
INSERT INTO translation_jobs (
    id,
    original_filename,
    storage_path,
    scorm_version,
    source_language,
    target_languages,
    status,
    progress_percentage,
    created_at,
    updated_at,
    user_id
) VALUES (
    'd4e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f8a',
    'employee_onboarding.zip',
    'originals/d4e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f8a/employee_onboarding.zip',
    NULL,
    'en',
    ARRAY['es', 'pt', 'zh'],
    'validating',
    5,
    NOW() - INTERVAL '2 minutes',
    NOW() - INTERVAL '1 minute',
    NULL
);

-- Job 5: Completado - Múltiples idiomas (FR → ES, EN, DE, IT, PT)
INSERT INTO translation_jobs (
    id,
    original_filename,
    storage_path,
    scorm_version,
    source_language,
    target_languages,
    status,
    progress_percentage,
    created_at,
    updated_at,
    completed_at,
    download_urls,
    user_id
) VALUES (
    'e5f6a7b8-c9d0-4e1f-2a3b-4c5d6e7f8a9b',
    'formation_professionnelle.zip',
    'originals/e5f6a7b8-c9d0-4e1f-2a3b-4c5d6e7f8a9b/formation_professionnelle.zip',
    '1.2',
    'fr',
    ARRAY['es', 'en', 'de', 'it', 'pt'],
    'completed',
    100,
    NOW() - INTERVAL '5 days',
    NOW() - INTERVAL '5 days',
    NOW() - INTERVAL '5 days',
    '{
        "es": "https://storage.example.com/translated/formation_ES.zip",
        "en": "https://storage.example.com/translated/formation_EN.zip",
        "de": "https://storage.example.com/translated/formation_DE.zip",
        "it": "https://storage.example.com/translated/formation_IT.zip",
        "pt": "https://storage.example.com/translated/formation_PT.zip"
    }'::jsonb,
    NULL
);

-- Job 6: En rebuilding - Casi completo
INSERT INTO translation_jobs (
    id,
    original_filename,
    storage_path,
    scorm_version,
    source_language,
    target_languages,
    status,
    progress_percentage,
    created_at,
    updated_at,
    user_id
) VALUES (
    'f6a7b8c9-d0e1-4f2a-3b4c-5d6e7f8a9b0c',
    'sales_training_advanced.zip',
    'originals/f6a7b8c9-d0e1-4f2a-3b4c-5d6e7f8a9b0c/sales_training_advanced.zip',
    '2004',
    'en',
    ARRAY['es', 'fr'],
    'rebuilding',
    85,
    NOW() - INTERVAL '15 minutes',
    NOW() - INTERVAL '1 minute',
    NULL
);

-- Comentario sobre el seed data
COMMENT ON TABLE translation_jobs IS 'Sample jobs include: completed (2), in-progress (2), failed (1), validating (1)';
