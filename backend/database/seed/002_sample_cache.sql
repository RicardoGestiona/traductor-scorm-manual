-- Seed Data: Sample translation cache entries for testing
-- Filepath: backend/database/seed/002_sample_cache.sql
-- Feature alignment: STORY-016 - Database Schema Setup
-- Purpose: Cache de traducciones comunes para testing de performance

-- IMPORTANTE: Este seed data es solo para desarrollo/testing
-- NO ejecutar en producción (el cache se llenará automáticamente)

-- Limpiar cache existente (solo para desarrollo)
-- TRUNCATE TABLE translation_cache CASCADE;

-- Traducciones comunes EN → ES
INSERT INTO translation_cache (
    source_text,
    source_language,
    target_language,
    translated_text,
    context_hash,
    char_count,
    translation_model,
    created_at,
    last_used_at,
    hit_count
) VALUES
    -- Frases comunes en SCORM
    (
        'Welcome to the course',
        'en',
        'es',
        'Bienvenido al curso',
        'common',
        21,
        'claude-3-sonnet',
        NOW() - INTERVAL '10 days',
        NOW() - INTERVAL '1 day',
        15
    ),
    (
        'Click Next to continue',
        'en',
        'es',
        'Haz clic en Siguiente para continuar',
        'common',
        21,
        'claude-3-sonnet',
        NOW() - INTERVAL '10 days',
        NOW() - INTERVAL '2 hours',
        25
    ),
    (
        'Course completed successfully',
        'en',
        'es',
        'Curso completado exitosamente',
        'common',
        28,
        'claude-3-sonnet',
        NOW() - INTERVAL '8 days',
        NOW() - INTERVAL '5 hours',
        18
    ),
    (
        'Assessment',
        'en',
        'es',
        'Evaluación',
        'common',
        10,
        'claude-3-sonnet',
        NOW() - INTERVAL '7 days',
        NOW() - INTERVAL '3 hours',
        30
    ),
    (
        'Progress',
        'en',
        'es',
        'Progreso',
        'common',
        8,
        'claude-3-sonnet',
        NOW() - INTERVAL '7 days',
        NOW() - INTERVAL '1 hour',
        22
    );

-- Traducciones comunes EN → FR
INSERT INTO translation_cache (
    source_text,
    source_language,
    target_language,
    translated_text,
    context_hash,
    char_count,
    translation_model,
    created_at,
    last_used_at,
    hit_count
) VALUES
    (
        'Welcome to the course',
        'en',
        'fr',
        'Bienvenue au cours',
        'common',
        21,
        'claude-3-sonnet',
        NOW() - INTERVAL '10 days',
        NOW() - INTERVAL '2 days',
        12
    ),
    (
        'Click Next to continue',
        'en',
        'fr',
        'Cliquez sur Suivant pour continuer',
        'common',
        21,
        'claude-3-sonnet',
        NOW() - INTERVAL '10 days',
        NOW() - INTERVAL '3 hours',
        20
    ),
    (
        'Course completed successfully',
        'en',
        'fr',
        'Cours terminé avec succès',
        'common',
        28,
        'claude-3-sonnet',
        NOW() - INTERVAL '8 days',
        NOW() - INTERVAL '6 hours',
        14
    );

-- Traducciones comunes ES → EN
INSERT INTO translation_cache (
    source_text,
    source_language,
    target_language,
    translated_text,
    context_hash,
    char_count,
    translation_model,
    created_at,
    last_used_at,
    hit_count
) VALUES
    (
        'Bienvenido al curso',
        'es',
        'en',
        'Welcome to the course',
        'common',
        19,
        'claude-3-sonnet',
        NOW() - INTERVAL '9 days',
        NOW() - INTERVAL '4 hours',
        10
    ),
    (
        'Siguiente',
        'es',
        'en',
        'Next',
        'common',
        9,
        'claude-3-sonnet',
        NOW() - INTERVAL '9 days',
        NOW() - INTERVAL '2 hours',
        28
    ),
    (
        'Atrás',
        'es',
        'en',
        'Back',
        'common',
        5,
        'claude-3-sonnet',
        NOW() - INTERVAL '9 days',
        NOW() - INTERVAL '1 hour',
        25
    );

-- Bloque de texto largo (simulando párrafo de SCORM)
INSERT INTO translation_cache (
    source_text,
    source_language,
    target_language,
    translated_text,
    context_hash,
    char_count,
    translation_model,
    created_at,
    last_used_at,
    hit_count
) VALUES
    (
        'This course will teach you the fundamentals of cybersecurity. You will learn about common threats, security best practices, and how to protect your organization from cyber attacks.',
        'en',
        'es',
        'Este curso te enseñará los fundamentos de la ciberseguridad. Aprenderás sobre amenazas comunes, mejores prácticas de seguridad y cómo proteger a tu organización de ataques cibernéticos.',
        'cybersecurity_101',
        173,
        'claude-3-sonnet',
        NOW() - INTERVAL '5 days',
        NOW() - INTERVAL '12 hours',
        5
    ),
    (
        'This course will teach you the fundamentals of cybersecurity. You will learn about common threats, security best practices, and how to protect your organization from cyber attacks.',
        'en',
        'fr',
        'Ce cours vous enseignera les fondamentaux de la cybersécurité. Vous apprendrez les menaces courantes, les meilleures pratiques de sécurité et comment protéger votre organisation contre les cyberattaques.',
        'cybersecurity_101',
        173,
        'claude-3-sonnet',
        NOW() - INTERVAL '5 days',
        NOW() - INTERVAL '10 hours',
        3
    );

-- Entradas de cache antiguas (para testing de cleanup)
INSERT INTO translation_cache (
    source_text,
    source_language,
    target_language,
    translated_text,
    context_hash,
    char_count,
    translation_model,
    created_at,
    last_used_at,
    hit_count
) VALUES
    (
        'Old content that should be cleaned',
        'en',
        'es',
        'Contenido antiguo que debería ser limpiado',
        'old_course',
        33,
        'claude-3-sonnet',
        NOW() - INTERVAL '120 days',
        NOW() - INTERVAL '95 days',
        1
    ),
    (
        'Another old translation',
        'en',
        'fr',
        'Une autre vieille traduction',
        'deprecated',
        23,
        'claude-3-sonnet',
        NOW() - INTERVAL '150 days',
        NOW() - INTERVAL '100 days',
        0
    );

-- Comentario sobre el seed data
COMMENT ON TABLE translation_cache IS 'Sample cache includes: 13 common translations, 2 old entries for cleanup testing';

-- Verificar estadísticas del cache después del seed
-- SELECT * FROM translation_cache_stats;
