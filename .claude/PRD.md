# PRD - Product Requirements Document

**Producto**: Traductor SCORM
**Versión**: 1.0 MVP
**Fecha**: 2025-11-25
**Owner**: Ricardo

---

## 📋 EXECUTIVE SUMMARY

Sistema web + API para traducir paquetes SCORM (1.2, 2004, xAPI) a múltiples idiomas usando IA, manteniendo la integridad y funcionalidad del contenido e-learning original.

**Target Users**:
- Diseñadores instruccionales que crean contenido multiidioma
- Empresas de e-learning que distribuyen cursos internacionalmente
- Departamentos de formación de empresas multinacionales

**Core Value Proposition**:
- Reducir de **horas → minutos** el tiempo de localización de SCORM
- Mantener **100% de funcionalidad** del paquete original
- Traducción **contextual** usando IA (no solo palabra por palabra)

---

## 🎯 OBJETIVOS DEL PRODUCTO

### Objetivos de Negocio
1. Lanzar MVP funcional en **8 semanas**
2. Procesar correctamente SCORM 1.2 (versión más común)
3. Soportar al menos **10 idiomas** principales
4. API REST documentada para integraciones B2B

### Objetivos de Usuario
1. Upload de SCORM → traducción → download en **< 5 clicks**
2. **Visibilidad del progreso** en tiempo real
3. **Validación automática** antes y después de traducir
4. **Historial** de traducciones para re-descargas

---

## 👥 USER PERSONAS

### Persona 1: María - Diseñadora Instruccional
- **Rol**: Diseñadora instruccional en empresa de formación
- **Pain points**:
  - Traduce manualmente 20+ cursos SCORM al año
  - Usa traductores externos ($$$) o herramientas básicas que rompen el SCORM
  - No tiene skills técnicos para programar scripts
- **Needs**:
  - Herramienta web simple (sin instalación)
  - Traducción de calidad que respete terminología e-learning
  - Descarga inmediata del SCORM traducido

### Persona 2: Carlos - Desarrollador de Plataforma LMS
- **Rol**: Developer en empresa con LMS propio
- **Pain points**:
  - Necesita automatizar traducción de 100+ cursos
  - Requiere integración con su pipeline de publicación
  - Necesita control de calidad y logging
- **Needs**:
  - API REST bien documentada
  - Webhooks para notificaciones
  - Batch processing de múltiples SCORM

---

## 🔧 FUNCTIONAL REQUIREMENTS

### FR-001: Upload de Paquete SCORM

**Como** usuario
**Quiero** subir un archivo ZIP de SCORM
**Para** poder traducirlo a otros idiomas

**Acceptance Criteria**:
- [ ] Drag & drop de archivo ZIP en interfaz web
- [ ] Alternativa: botón "Select file" para file picker nativo
- [ ] Validación en cliente: solo archivos .zip, max 500MB
- [ ] Feedback visual durante upload (progress bar)
- [ ] Detección automática de versión SCORM (1.2, 2004, xAPI)
- [ ] Error claro si el ZIP no contiene estructura SCORM válida

**Technical Notes**:
- Usar `imsmanifest.xml` para detectar SCORM 1.2/2004
- Usar `tincan.xml` o `activity.json` para xAPI
- Storage temporal en Supabase Storage (TTL: 7 días)

---

### FR-002: Selección de Idiomas

**Como** usuario
**Quiero** seleccionar idioma origen y destino(s)
**Para** especificar qué traducciones necesito

**Acceptance Criteria**:
- [ ] Dropdown de idioma origen con autodetección sugerida
- [ ] Multi-select para idiomas destino (1 a N idiomas)
- [ ] Lista de idiomas soportados:
  - Español (ES)
  - Inglés (EN)
  - Francés (FR)
  - Alemán (DE)
  - Italiano (IT)
  - Portugués (PT)
  - Holandés (NL)
  - Polaco (PL)
  - Chino Simplificado (ZH)
  - Japonés (JA)
- [ ] Indicador de "Popular" en idiomas más usados
- [ ] Opción "Traducir a todos" para casos bulk

**Technical Notes**:
- Autodetección basada en atributo `xml:lang` del manifest
- Códigos ISO 639-1 (2 letras)

---

### FR-003: Procesamiento y Traducción

**Como** sistema
**Debo** traducir el contenido SCORM preservando estructura
**Para** generar paquetes funcionales en idiomas destino

**Acceptance Criteria**:
- [ ] Parsear `imsmanifest.xml` y extraer textos traducibles
- [ ] Identificar archivos HTML en recursos
- [ ] Extraer textos de HTML preservando estructura:
  - [ ] Contenido de tags: `<p>`, `<h1-6>`, `<span>`, `<li>`, `<div>`
  - [ ] Atributos: `alt`, `title`, `placeholder`, `aria-label`
  - [ ] NO traducir: JavaScript inline, CSS, URLs, IDs, clases
- [ ] Enviar textos a API de traducción (Claude) con contexto del curso
- [ ] Aplicar traducciones manteniendo formato HTML exacto
- [ ] Reconstruir archivo ZIP con estructura SCORM idéntica
- [ ] Generar un ZIP por cada idioma destino

**Technical Notes**:
- Usar BeautifulSoup para parsing HTML
- Usar lxml para XML del manifest
- Batch de traducciones (max 50 textos por llamada a API)
- Implementar retry logic para API calls (3 intentos)

---

### FR-004: Progreso en Tiempo Real

**Como** usuario
**Quiero** ver el progreso de la traducción
**Para** saber cuánto falta y si hay errores

**Acceptance Criteria**:
- [ ] Progress bar con porcentaje (0-100%)
- [ ] Estados visibles:
  - "Validando SCORM..." (5%)
  - "Extrayendo contenido..." (15%)
  - "Traduciendo a [idioma]..." (20-80%)
  - "Reconstruyendo paquete..." (85%)
  - "Listo para descargar" (100%)
- [ ] Indicador de tiempo estimado restante
- [ ] Notificación si el proceso tarda > 2 minutos
- [ ] Error detallado si falla algún paso

**Technical Notes**:
- WebSocket o Server-Sent Events (SSE) para updates en tiempo real
- Fallback a polling cada 2s si WebSocket no disponible
- Store progress en Redis para persistencia

---

### FR-005: Descarga de SCORM Traducido

**Como** usuario
**Quiero** descargar los paquetes SCORM traducidos
**Para** subirlos a mi LMS

**Acceptance Criteria**:
- [ ] Botón de descarga por cada idioma traducido
- [ ] Nombre de archivo descriptivo: `{original_name}_ES.zip`
- [ ] Link de descarga válido por 7 días
- [ ] Opción "Descargar todos" (ZIP con todos los idiomas)
- [ ] Opción "Re-descargar" desde historial

**Technical Notes**:
- Generar signed URLs de Supabase Storage (TTL: 7 días)
- Auto-delete archivos después de 7 días (lifecycle policy)

---

### FR-006: Validación de SCORM

**Como** sistema
**Debo** validar que el SCORM traducido funciona correctamente
**Para** evitar entregar paquetes rotos al usuario

**Acceptance Criteria**:
- [ ] Validar XML del manifest contra XSD de SCORM
- [ ] Verificar que todos los recursos referenciados existen
- [ ] Verificar que estructura de carpetas es idéntica
- [ ] Validar que HTML es well-formed después de traducción
- [ ] Test básico de tracking (si es posible simular LMS)
- [ ] Reporte de validación descargable

**Technical Notes**:
- Usar librerías de validación XML
- Implementar SCORM player simple para test básico (opcional v2)

---

### FR-007: Historial de Traducciones

**Como** usuario
**Quiero** ver mis traducciones anteriores
**Para** re-descargar o consultar detalles

**Acceptance Criteria**:
- [ ] Tabla con historial de traducciones:
  - Nombre archivo original
  - Idiomas traducidos
  - Fecha
  - Estado (completado/fallido)
  - Acciones (descargar, eliminar)
- [ ] Filtro por estado y fecha
- [ ] Búsqueda por nombre de archivo
- [ ] Paginación (20 items por página)

---

### FR-008: API REST

**Como** desarrollador externo
**Quiero** usar una API REST documentada
**Para** integrar la traducción en mi sistema

**Acceptance Criteria**:
- [ ] Endpoint `POST /api/v1/translate`:
  - Input: file (multipart/form-data), source_lang, target_langs[]
  - Output: job_id, status
- [ ] Endpoint `GET /api/v1/jobs/{job_id}`:
  - Output: status, progress, download_urls
- [ ] Endpoint `GET /api/v1/languages`:
  - Output: lista de idiomas soportados
- [ ] Autenticación con API Key
- [ ] Rate limiting: 100 req/hora
- [ ] Documentación auto-generada (Swagger/OpenAPI)

**Technical Notes**:
- FastAPI genera OpenAPI automáticamente
- API Keys en header: `X-API-Key: xxx`
- Store API keys en Supabase con hash

---

## 🎨 NON-FUNCTIONAL REQUIREMENTS

### NFR-001: Performance
- Traducción de SCORM típico (50 páginas HTML) debe completarse en **< 5 minutos**
- Upload de 100MB debe completarse en **< 30 segundos** (conexión normal)
- API debe responder en **< 500ms** para endpoints síncronos

### NFR-002: Reliability
- **99% uptime** (objetivo)
- Sistema debe recuperarse automáticamente de fallos de API de traducción
- Retry automático de traducciones fallidas (max 3 intentos)

### NFR-003: Scalability
- Soportar **10 traducciones simultáneas** (MVP)
- Escalable a 100+ con más workers de Celery

### NFR-004: Security
- Archivos SCORM escaneados para malware antes de procesar
- Autenticación obligatoria (Supabase Auth)
- HTTPS obligatorio en producción
- Logs de auditoría de todas las operaciones

### NFR-005: Usability
- Interfaz en español e inglés
- Compatible con Chrome, Firefox, Safari, Edge (últimas 2 versiones)
- Mobile responsive (básico)
- WCAG 2.1 Level A (accesibilidad básica)

---

## 🚫 OUT OF SCOPE (v1)

Las siguientes features NO están en el MVP:

- ❌ Edición manual de traducciones en interfaz
- ❌ Traducción de audio/video
- ❌ Traducción de imágenes con texto
- ❌ Soporte offline
- ❌ Integración directa con LMS (Moodle, etc)
- ❌ Traducción de código JavaScript (solo strings en v2)
- ❌ Webhooks (v2)
- ❌ Batch upload de múltiples SCORM
- ❌ Roles y permisos (admin, editor) - solo un rol "usuario"

---

## 📊 SUCCESS METRICS

### Métricas de Adopción
- **10 usuarios activos** en primer mes post-launch
- **50 traducciones** completadas exitosamente

### Métricas de Calidad
- **< 5% tasa de error** en traducciones (SCORM rotos)
- **80%+ satisfacción** de usuarios (NPS)
- **95%+ precisión** de traducción (evaluación manual de muestras)

### Métricas de Performance
- **< 5 minutos** tiempo promedio de traducción
- **< 2 segundos** tiempo de carga de interfaz

---

## 🗺️ ROADMAP

### Fase 1: MVP (8 semanas) - **CURRENT**
- ✅ Setup proyecto
- Backend API básico (upload, translate, download)
- Frontend web (upload, progress, download)
- Soporte SCORM 1.2
- 10 idiomas

### Fase 2: Mejoras (4 semanas)
- Soporte SCORM 2004 completo
- xAPI/TinCan básico
- Edición manual de traducciones
- Cache inteligente de traducciones

### Fase 3: Enterprise (6 semanas)
- Webhooks
- Batch processing
- Roles y permisos
- Integración con LMS populares
- Plan de pricing

---

## 📚 ASSUMPTIONS & DEPENDENCIES

**Assumptions**:
- Usuarios tienen conocimiento básico de SCORM
- Paquetes SCORM son well-formed (no corruptos)
- API de Claude/OpenAI está disponible y funcional

**Dependencies**:
- Cuenta de Supabase (gratis tier OK para MVP)
- API Key de Anthropic (Claude) o OpenAI
- Redis para Celery (puede ser Redis Cloud gratis)

**Risks**:
- Costo de API de traducción puede ser alto con muchos usuarios
- SCORM mal formados pueden romper el parser
- Archivos muy grandes (> 500MB) pueden timeout

---

**Última actualización**: 2025-11-25
**Próxima revisión**: Al completar MVP
