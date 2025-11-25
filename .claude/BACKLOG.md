# BACKLOG - Product Backlog

**Proyecto**: Traductor SCORM
**Última actualización**: 2025-11-25

---

## 📊 ESTRUCTURA DEL BACKLOG

```
EPIC (gran feature)
  └── STORY (funcionalidad user-facing)
       └── TASK (trabajo técnico específico)
```

**Estados**: 📋 Backlog | 🔄 In Progress | ✅ Done | ⏸️ Paused | ❌ Cancelled

---

## 🎯 CURRENT SPRINT: Sprint 0 - Foundation

**Sprint Goal**: Configurar infraestructura básica del proyecto (backend, frontend, database)

**Sprint Dates**: 2025-11-25 → 2025-12-02 (1 semana)

### Stories en Sprint Actual

#### ✅ STORY-001: Setup de Documentación del Proyecto
**Epic**: EPIC-000
**Priority**: High
**Status**: ✅ Done
**Estimate**: 2h

**Tasks**:
- [x] Crear CLAUDE.md con arquitectura completa
- [x] Crear PRD.md con functional requirements
- [x] Crear BACKLOG.md con EPICs y Stories
- [x] Crear STATUSLOG.md inicial

---

#### 🔄 STORY-002: Setup de Backend FastAPI
**Epic**: EPIC-001
**Priority**: High
**Status**: 🔄 In Progress
**Estimate**: 4h

**Acceptance Criteria**:
- Backend estructura de carpetas creada
- pyproject.toml con dependencias configurado
- FastAPI app básica con endpoint de health check
- Docker Compose para desarrollo local
- README con instrucciones de setup

**Tasks**:
- [ ] Crear estructura de carpetas `/backend`
- [ ] Configurar pyproject.toml con Poetry
- [ ] Instalar dependencias base: FastAPI, Pydantic, Uvicorn
- [ ] Crear app/main.py con health check endpoint
- [ ] Configurar Docker Compose (FastAPI + PostgreSQL + Redis)
- [ ] Crear .env.example
- [ ] Crear README.md con setup instructions

---

#### 📋 STORY-003: Setup de Frontend React
**Epic**: EPIC-001
**Priority**: High
**Status**: 📋 Backlog
**Estimate**: 3h

**Acceptance Criteria**:
- Frontend con Vite + React + TypeScript funcionando
- Estructura de carpetas creada
- Layout básico con Navbar
- Configuración de Tailwind CSS

**Tasks**:
- [ ] Crear proyecto Vite con template React-TS
- [ ] Configurar Tailwind CSS
- [ ] Crear estructura de carpetas (components, pages, services)
- [ ] Implementar Layout básico
- [ ] Crear página Home vacía

---

## 🗂️ EPICS

### EPIC-000: Project Foundation ⚙️
**Status**: 🔄 In Progress
**Priority**: Critical
**Description**: Setup inicial del proyecto, infraestructura, documentación

**Stories**: STORY-001 ✅, STORY-002 🔄, STORY-003 📋

---

### EPIC-001: Backend Core API 🔧
**Status**: 📋 Backlog
**Priority**: High
**Description**: Implementar API REST principal para upload, traducción y descarga

**Stories**:

#### STORY-004: Endpoint de Upload de SCORM
**Priority**: High
**Status**: 📋 Backlog
**Estimate**: 8h
**FR Reference**: FR-001

**Acceptance Criteria**:
- Endpoint `POST /api/v1/upload` acepta multipart file
- Validación de tamaño (max 500MB)
- Validación de tipo (solo .zip)
- Almacenamiento temporal en Supabase Storage
- Retorna job_id para tracking

**Tasks**:
- [ ] Crear modelo Pydantic para UploadRequest/Response
- [ ] Implementar endpoint POST /api/v1/upload
- [ ] Integrar con Supabase Storage
- [ ] Validar tamaño y tipo de archivo
- [ ] Crear TranslationJob en database
- [ ] Tests unitarios

---

#### STORY-005: Parser de SCORM 1.2
**Priority**: High
**Status**: 📋 Backlog
**Estimate**: 12h
**FR Reference**: FR-003

**Acceptance Criteria**:
- Descomprimir ZIP de SCORM
- Parsear imsmanifest.xml correctamente
- Extraer metadata (title, description, version)
- Identificar archivos HTML de recursos
- Detectar idioma origen automáticamente

**Tasks**:
- [ ] Crear ScormParser service
- [ ] Implementar descompresión de ZIP
- [ ] Parsear imsmanifest.xml con lxml
- [ ] Extraer estructura de organizaciones
- [ ] Extraer recursos y archivos
- [ ] Detectar idioma desde xml:lang
- [ ] Tests con SCORM de ejemplo

---

#### STORY-006: Extracción de Contenido Traducible
**Priority**: High
**Status**: 📋 Backlog
**Estimate**: 10h
**FR Reference**: FR-003

**Acceptance Criteria**:
- Extraer textos de imsmanifest.xml (titles, descriptions)
- Extraer textos de archivos HTML
- Preservar estructura HTML exacta
- NO extraer código JavaScript, CSS, URLs
- Generar estructura intermedia TranslatableContent

**Tasks**:
- [ ] Crear ContentExtractor service
- [ ] Implementar extracción de XML (manifest)
- [ ] Implementar extracción de HTML con BeautifulSoup
- [ ] Filtrar elementos no traducibles
- [ ] Extraer atributos (alt, title, placeholder)
- [ ] Generar TranslatableContent objects
- [ ] Tests con HTML complejo

---

#### STORY-007: Integración con API de Traducción (Claude)
**Priority**: High
**Status**: 📋 Backlog
**Estimate**: 8h
**FR Reference**: FR-003

**Acceptance Criteria**:
- Enviar textos a Claude API con contexto
- Batch de traducciones (max 50 por request)
- Retry logic para fallos de API
- Cache de traducciones en database
- Tracking de costos de API

**Tasks**:
- [ ] Crear TranslationService con cliente de Claude
- [ ] Implementar prompt de traducción con contexto
- [ ] Batch processing de textos
- [ ] Retry logic con exponential backoff
- [ ] Cache lookup en translation_cache table
- [ ] Store traducciones en cache
- [ ] Tests con mock de API

---

#### STORY-008: Reconstrucción de SCORM Traducido
**Priority**: High
**Status**: 📋 Backlog
**Estimate**: 10h
**FR Reference**: FR-003

**Acceptance Criteria**:
- Aplicar traducciones a manifest XML
- Aplicar traducciones a archivos HTML preservando estructura
- Reconstruir estructura de carpetas idéntica
- Generar ZIP del SCORM traducido
- Subir a Supabase Storage

**Tasks**:
- [ ] Crear ScormRebuilder service
- [ ] Aplicar traducciones a XML (manifest)
- [ ] Aplicar traducciones a HTML manteniendo tags
- [ ] Reconstruir árbol de carpetas
- [ ] Generar ZIP con compresión
- [ ] Upload a Supabase Storage
- [ ] Tests de integridad del SCORM

---

#### STORY-009: Endpoint de Status de Job
**Priority**: High
**Status**: 📋 Backlog
**Estimate**: 4h
**FR Reference**: FR-004, FR-008

**Acceptance Criteria**:
- Endpoint `GET /api/v1/jobs/{job_id}` retorna estado
- Incluye progress_percentage (0-100)
- Incluye status actual (uploading, translating, etc)
- Incluye download_urls cuando completed

**Tasks**:
- [ ] Crear endpoint GET /api/v1/jobs/{job_id}
- [ ] Query a translation_jobs table
- [ ] Retornar JobStatus model
- [ ] Tests unitarios

---

#### STORY-010: Celery Task para Traducción Asíncrona
**Priority**: High
**Status**: 📋 Backlog
**Estimate**: 6h
**FR Reference**: FR-003, FR-004

**Acceptance Criteria**:
- Celery worker procesando traducciones en background
- Updates de progreso a database cada 10%
- Manejo de errores con logging
- Retry automático de tareas fallidas

**Tasks**:
- [ ] Configurar Celery + Redis
- [ ] Crear translate_scorm_task
- [ ] Orquestar: parse → extract → translate → rebuild
- [ ] Update progress en database
- [ ] Error handling y logging
- [ ] Tests de integración

---

### EPIC-002: Frontend Web Interface 🎨
**Status**: 📋 Backlog
**Priority**: High
**Description**: Interfaz web para usuarios finales (upload, progreso, descarga)

**Stories**:

#### STORY-011: Componente de Upload de SCORM
**Priority**: High
**Status**: 📋 Backlog
**Estimate**: 6h
**FR Reference**: FR-001

**Acceptance Criteria**:
- Drag & drop zone funcional
- Alternativa con file picker
- Progress bar de upload
- Validación client-side (tipo, tamaño)
- Feedback visual de éxito/error

**Tasks**:
- [ ] Crear UploadZone component
- [ ] Implementar drag & drop con react-dropzone
- [ ] Progress bar durante upload
- [ ] Validación de archivo
- [ ] Llamada a API /upload
- [ ] Error handling

---

#### STORY-012: Selector de Idiomas
**Priority**: High
**Status**: 📋 Backlog
**Estimate**: 4h
**FR Reference**: FR-002

**Acceptance Criteria**:
- Dropdown de idioma origen
- Multi-select de idiomas destino
- Lista de 10 idiomas principales
- UI clara y accesible

**Tasks**:
- [ ] Crear LanguageSelector component
- [ ] Implementar dropdown con react-select
- [ ] Multi-select para target languages
- [ ] Fetch de /api/v1/languages
- [ ] Styling con Tailwind

---

#### STORY-013: Progress Tracker en Tiempo Real
**Priority**: High
**Status**: 📋 Backlog
**Estimate**: 8h
**FR Reference**: FR-004

**Acceptance Criteria**:
- Progress bar con porcentaje
- Estados textuales descriptivos
- Polling a /api/v1/jobs/{id} cada 2s
- Notificación cuando completa

**Tasks**:
- [ ] Crear TranslationProgress component
- [ ] Implementar polling con useEffect
- [ ] Progress bar animado
- [ ] Estados descriptivos
- [ ] Notificación de completado
- [ ] Error states

---

#### STORY-014: Descarga de SCORM Traducido
**Priority**: High
**Status**: 📋 Backlog
**Estimate**: 3h
**FR Reference**: FR-005

**Acceptance Criteria**:
- Botones de descarga por idioma
- Download de signed URLs de Supabase
- Nombres de archivo descriptivos

**Tasks**:
- [ ] Crear DownloadButton component
- [ ] Trigger download de signed URLs
- [ ] Nombres de archivo: {original}_ES.zip
- [ ] Loading states

---

#### STORY-015: Página de Historial
**Priority**: Medium
**Status**: 📋 Backlog
**Estimate**: 6h
**FR Reference**: FR-007

**Acceptance Criteria**:
- Tabla con traducciones anteriores
- Filtros por estado y fecha
- Re-descarga de archivos
- Paginación

**Tasks**:
- [ ] Crear History page
- [ ] Tabla con datos de translation_jobs
- [ ] Filtros y búsqueda
- [ ] Paginación
- [ ] Re-download functionality

---

### EPIC-003: Database & Auth 🗄️
**Status**: 📋 Backlog
**Priority**: High
**Description**: Schema de Supabase, autenticación, RLS policies

**Stories**:

#### STORY-016: Database Schema Setup
**Priority**: High
**Status**: 📋 Backlog
**Estimate**: 4h

**Acceptance Criteria**:
- Tablas creadas en Supabase: translation_jobs, translation_cache
- Indexes para performance
- RLS policies configuradas

**Tasks**:
- [ ] Crear migration SQL para translation_jobs
- [ ] Crear migration SQL para translation_cache
- [ ] Crear indexes (job lookup, cache lookup)
- [ ] RLS policy: users solo ven sus jobs
- [ ] Seed data para testing

---

#### STORY-017: Autenticación con Supabase
**Priority**: High
**Status**: 📋 Backlog
**Estimate**: 5h

**Acceptance Criteria**:
- Login/Signup con email/password
- Sesión persistente
- Protección de rutas en frontend
- RLS aplicado en backend

**Tasks**:
- [ ] Configurar Supabase Auth
- [ ] Crear Login/Signup pages
- [ ] Auth context en React
- [ ] Protected routes
- [ ] Middleware de auth en FastAPI

---

### EPIC-004: Validación & Quality Assurance ✅
**Status**: 📋 Backlog
**Priority**: Medium
**Description**: Validación de SCORM, tests, CI/CD

**Stories**:

#### STORY-018: Validador de SCORM
**Priority**: Medium
**Status**: 📋 Backlog
**Estimate**: 8h
**FR Reference**: FR-006

**Acceptance Criteria**:
- Validar XML contra XSD de SCORM
- Verificar recursos referenciados existen
- Validar HTML well-formed
- Reporte de validación

**Tasks**:
- [ ] Crear ScormValidator service
- [ ] Validar XML con xmlschema
- [ ] Verificar integridad de recursos
- [ ] Validar HTML
- [ ] Generar reporte de validación

---

#### STORY-019: Tests Unitarios Backend
**Priority**: Medium
**Status**: 📋 Backlog
**Estimate**: 10h

**Acceptance Criteria**:
- Coverage > 70% en services críticos
- Tests de ScormParser, ContentExtractor, TranslationService
- Tests de endpoints API

**Tasks**:
- [ ] Setup pytest + fixtures
- [ ] Tests de ScormParser
- [ ] Tests de ContentExtractor
- [ ] Tests de TranslationService
- [ ] Tests de API endpoints

---

#### STORY-020: Tests E2E
**Priority**: Low
**Status**: 📋 Backlog
**Estimate**: 8h

**Acceptance Criteria**:
- Test de flujo completo: upload → translate → download
- Test con SCORM 1.2 real

**Tasks**:
- [ ] Setup Playwright
- [ ] Test de upload
- [ ] Test de traducción completa
- [ ] Test de descarga

---

### EPIC-005: API Documentation & Developer Experience 📚
**Status**: 📋 Backlog
**Priority**: Medium
**Description**: Documentación de API, ejemplos, SDKs

**Stories**:

#### STORY-021: OpenAPI/Swagger Documentation
**Priority**: Medium
**Status**: 📋 Backlog
**Estimate**: 3h
**FR Reference**: FR-008

**Acceptance Criteria**:
- Swagger UI accesible en /docs
- Ejemplos de requests/responses
- Autenticación documentada

**Tasks**:
- [ ] Configurar FastAPI OpenAPI
- [ ] Añadir docstrings descriptivos
- [ ] Ejemplos en modelos Pydantic
- [ ] Documentar autenticación

---

## 📊 BACKLOG PRIORITIZADO

### High Priority (Sprint 1-2)
1. ✅ STORY-001: Setup de Documentación
2. 🔄 STORY-002: Setup Backend FastAPI
3. STORY-003: Setup Frontend React
4. STORY-004: Endpoint Upload
5. STORY-005: Parser SCORM 1.2
6. STORY-006: Extracción de Contenido
7. STORY-007: Integración Claude API
8. STORY-008: Reconstrucción SCORM
9. STORY-009: Endpoint Status
10. STORY-010: Celery Task

### Medium Priority (Sprint 3-4)
11. STORY-011: Upload Component
12. STORY-012: Language Selector
13. STORY-013: Progress Tracker
14. STORY-014: Download Component
15. STORY-016: Database Schema
16. STORY-017: Autenticación
17. STORY-018: Validador SCORM

### Low Priority (Sprint 5+)
18. STORY-015: Historial
19. STORY-019: Tests Unitarios
20. STORY-020: Tests E2E
21. STORY-021: OpenAPI Docs

---

## 🎯 DEFINITION OF DONE

**Para STORY**:
- [ ] Código implementado y funcionando
- [ ] Acceptance criteria cumplidos
- [ ] Tests unitarios pasando (cuando aplique)
- [ ] Documentación inline actualizada
- [ ] STATUSLOG.md actualizado
- [ ] Code review (autocrítica) realizada

**Para EPIC**:
- [ ] Todas las stories completadas
- [ ] Integración entre stories validada
- [ ] Tests de integración pasando
- [ ] Documentación de epic actualizada

---

**Última actualización**: 2025-11-25
**Próxima revisión**: Al completar Sprint 0
