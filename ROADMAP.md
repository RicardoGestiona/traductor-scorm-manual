# 🗺️ Roadmap - Traductor SCORM

**Versión Actual**: 1.0.0-mvp (MVP Completado)
**Última actualización**: 2025-11-28

---

## ✅ Fase 0-5: MVP COMPLETADO (Nov 2025)

### Lo que YA Funciona

**Core Features**:
- ✅ Upload de paquetes SCORM (1.2, 2004)
- ✅ Traducción automática con Claude AI (12 idiomas)
- ✅ Procesamiento asíncrono con Celery
- ✅ Progress tracking en tiempo real
- ✅ Descarga de paquetes traducidos
- ✅ Sistema completo de autenticación
- ✅ Multi-tenancy con ownership verification

**Technical Stack**:
- ✅ Backend: FastAPI + Python 3.11+
- ✅ Frontend: React 18 + Vite + TypeScript
- ✅ Database: Supabase (PostgreSQL + Auth + Storage)
- ✅ AI: Anthropic Claude 3.5 Sonnet
- ✅ Queue: Celery + Redis
- ✅ Tests: 100 tests automatizados (75% coverage)
- ✅ Docs: OpenAPI/Swagger completo

---

## 🚀 Fase 6: Post-MVP Improvements (Dic 2025)

**Prioridad**: MEDIUM
**Duración estimada**: 2 semanas

### Features Pendientes del Backlog Original

#### STORY-015: Página de Historial de Traducciones
**Estimate**: 6h
**Value**: Permite a usuarios ver y gestionar sus traducciones pasadas

**Features**:
- Tabla con todas las traducciones del usuario
- Filtros: por estado (completed, failed), fecha, idiomas
- Búsqueda por nombre de archivo
- Paginación (10-20 items por página)
- Re-download de archivos antiguos (si aún válidos)
- Acción: Eliminar jobs antiguos

**Technical**:
- Endpoint: `GET /api/v1/jobs?user_id=...&status=...&page=...`
- Frontend: Nueva página `/history`
- Protected route (requiere auth)

#### STORY-018: Validador de SCORM Avanzado
**Estimate**: 8h
**Value**: Detectar problemas en SCORM antes de traducir

**Features**:
- Validación contra XSD schemas de SCORM
- Verificar que recursos referenciados existen
- Validar HTML well-formed
- Detectar JavaScript potencialmente problemático
- Reporte de validación con warnings/errors
- Sugerencias de corrección

**Technical**:
- Librería: `xmlschema` para validar contra XSD
- Endpoint: `POST /api/v1/validate` (antes de upload real)
- Frontend: Vista previa de validación

#### STORY-019: Tests E2E con Playwright
**Estimate**: 10h
**Value**: Testing automático del flujo completo

**Tests E2E**:
1. Signup → Login → Upload → Download (happy path)
2. Login con credenciales incorrectas (error path)
3. Upload de archivo inválido (error path)
4. Traducción fallida por API error (error path)
5. Download antes de completar traducción (error path)

**Technical**:
- Framework: Playwright
- CI: GitHub Actions
- Environments: Staging + Production

---

## 🎯 Fase 7: Production Hardening (Ene 2026)

**Prioridad**: HIGH
**Duración estimada**: 1 semana

### Security & Performance

#### Rate Limiting
**Estimate**: 4h

**Limits**:
- Auth endpoints: 10 intentos/minuto por IP
- Upload endpoint: 5 uploads/hora por usuario
- Download endpoint: 20 descargas/hora por usuario

**Implementation**:
- Librería: `slowapi` (FastAPI rate limiter)
- Storage: Redis (shared counter)
- Error: HTTP 429 (Too Many Requests)

#### Email Verification
**Estimate**: 3h

**Flow**:
1. Signup → Email sent (Supabase)
2. User clicks link → Email verified
3. Solo usuarios verificados pueden traducir

**Configuration**:
- Habilitar en Supabase Dashboard → Auth → Settings
- Template de email personalizado
- Link de verificación válido por 24h

#### Monitoring & Alerting
**Estimate**: 5h

**Tools**:
- **Sentry**: Error tracking (frontend + backend)
- **Vercel Analytics**: Frontend performance
- **Supabase Dashboard**: Database monitoring
- **Anthropic Console**: API usage y costos

**Alerts**:
- Errores críticos (500) → Email inmediato
- API usage > 80% del budget → Email warning
- Database storage > 90% → Email warning

#### Backup & Disaster Recovery
**Estimate**: 3h

**Strategy**:
- Database: Backups diarios automáticos (Supabase)
- Code: GitHub (ya versionado)
- Secrets: 1Password/Vault (backup de .env)
- Recovery plan documentado

---

## 💡 Fase 8: UX Enhancements (Feb 2026)

**Prioridad**: MEDIUM
**Duración estimada**: 2 semanas

### User Experience Improvements

#### Edición de Traducciones Pre/Post
**Estimate**: 12h
**Value**: Usuarios pueden corregir traducciones antes de descargar

**Features**:
- Vista de preview de traducciones
- Editor inline para correcciones
- Comparación lado a lado (original vs traducido)
- Re-traducir segmentos específicos
- Guardar cambios y regenerar SCORM

**Technical**:
- Endpoint: `PATCH /api/v1/jobs/{id}/segments/{segment_id}`
- Frontend: Editor modal con syntax highlighting
- Database: Tabla `translation_edits` (audit trail)

#### Glossary Management
**Estimate**: 10h
**Value**: Consistencia en términos técnicos

**Features**:
- Crear glossario personalizado (usuario o global)
- Importar/Exportar glossary (CSV, XLSX)
- Aplicar glossary durante traducción
- Sugerencias de glossary (términos frecuentes)

**Technical**:
- Database: Tabla `glossaries`, `glossary_terms`
- AI: Prompt incluye glossary terms
- Frontend: CRUD interface para glossary

#### Analytics Dashboard
**Estimate**: 8h
**Value**: Insights de uso y costos

**Metrics**:
- Traducciones por mes (gráfico de líneas)
- Idiomas más traducidos (pie chart)
- Costos de API acumulados
- Tiempo promedio de traducción
- Tasa de éxito vs errores

**Technical**:
- Endpoint: `GET /api/v1/analytics`
- Frontend: Dashboard con charts (Chart.js o Recharts)
- Data: Agregación de translation_jobs

---

## 🌐 Fase 9: Internationalization (Mar 2026)

**Prioridad**: LOW-MEDIUM
**Duración estimada**: 1 semana

### Features

#### UI Multiidioma
**Estimate**: 8h

**Languages**:
- Español (default)
- English
- Français
- Deutsch

**Implementation**:
- Librería: `react-i18next`
- Files: `locales/es.json`, `locales/en.json`
- Language switcher en navbar

#### Soporte para Más Idiomas de Traducción
**Estimate**: 4h

**Add**:
- 🇨🇳 Chino (simplificado + tradicional)
- 🇯🇵 Japonés
- 🇰🇷 Coreano
- 🇮🇹 Italiano
- 🇵🇹 Portugués (BR + PT)

**Total**: 20+ idiomas soportados

---

## 🔧 Fase 10: Advanced Features (Abr-May 2026)

**Prioridad**: LOW
**Duración estimada**: 1 mes

### Features Avanzadas

#### xAPI/TinCan Support Completo
**Estimate**: 16h

**Additions**:
- Parser para `tincan.xml` y `activity.json`
- Traducción de statements JSON
- Preservar formato xAPI completo
- Validación contra xAPI spec

#### Webhooks para Integraciones
**Estimate**: 8h

**Events**:
- `translation.started`
- `translation.completed`
- `translation.failed`

**Payload**:
```json
{
  "event": "translation.completed",
  "job_id": "uuid",
  "user_id": "uuid",
  "status": "completed",
  "languages": ["en", "fr"],
  "timestamp": "2026-04-15T10:30:00Z"
}
```

**Use Cases**:
- Integración con LMS
- Notificaciones a Slack
- Trigger de workflows externos

#### Batch Upload
**Estimate**: 12h

**Feature**:
- Upload múltiples SCORM de una vez
- Progress tracking por archivo
- Descarga batch cuando todos completen

**UI**:
- Drag & drop múltiple
- Lista de archivos en cola
- Progress individual por archivo

#### API Webhooks + Zapier Integration
**Estimate**: 10h

**Zapier**:
- Trigger: "New Translation Completed"
- Action: "Translate SCORM"

**Use Cases**:
- Auto-traducir cuando se sube a Google Drive
- Notificar equipo en Slack cuando completa

---

## 🚀 Fase 11: Scaling & Enterprise (Jun 2026+)

**Prioridad**: FUTURE
**Duración estimada**: 2-3 meses

### Enterprise Features

#### Multi-Tenant SaaS
**Estimate**: 40h

**Features**:
- Organizations (múltiples usuarios por org)
- Roles: Admin, Translator, Viewer
- Billing por organización
- Usage limits por plan (Free, Pro, Enterprise)

**Plans**:
- **Free**: 5 traducciones/mes, 2 idiomas, 100MB max
- **Pro**: 50 traducciones/mes, todos los idiomas, 500MB max
- **Enterprise**: Unlimited, custom integration, SLA

#### White-Label
**Estimate**: 20h

**Customization**:
- Logo personalizado
- Colores de marca
- Dominio custom (traductor.tu-empresa.com)
- Email branding

#### SSO (Single Sign-On)
**Estimate**: 16h

**Providers**:
- SAML 2.0
- Google Workspace
- Microsoft Azure AD
- Okta

#### Compliance
**Estimate**: 30h

**Certifications**:
- **GDPR**: Privacy policy, data export, right to deletion
- **SOC 2**: Security audit, controls documentation
- **ISO 27001**: Information security management

---

## 🔬 R&D & Experimental (2027+)

### Ideas para Explorar

#### AI Quality Improvements
- Fine-tuning de Claude específico para e-learning
- Context injection con terminología del curso completo
- Post-editing automático (detección de errores)

#### Voice & Video Translation
- Transcripción automática de audio en SCORM
- Traducción de subtitles
- Voice-over automático (text-to-speech)

#### Real-Time Collaboration
- Múltiples usuarios editando traducciones simultáneamente
- Comments y suggestions (Google Docs style)
- Revision history

#### Offline Mode
- Progressive Web App (PWA)
- Download de traducciones para trabajo offline
- Sync cuando vuelve conexión

---

## 📊 Success Metrics por Fase

| Fase | Métrica Clave | Target |
|------|---------------|--------|
| **Fase 6** (Post-MVP) | Users activos/mes | 50+ |
| **Fase 7** (Hardening) | Uptime | 99.5%+ |
| **Fase 8** (UX) | User satisfaction | 8/10+ |
| **Fase 9** (i18n) | International users | 30%+ |
| **Fase 10** (Advanced) | xAPI support | 100 cursos |
| **Fase 11** (Enterprise) | Paying orgs | 5+ |

---

## 🤝 Community & Open Source

### Contribuciones Bienvenidas

**Areas**:
- Traducción de UI a más idiomas
- Tests adicionales (E2E, unit)
- Documentación mejorada
- Bug fixes
- Nuevos idiomas de traducción

**Guidelines**:
- Ver [CONTRIBUTING.md](CONTRIBUTING.md) (TODO)
- Código de conducta
- Pull request template

---

## 📅 Timeline Visual

```
2025 Nov ████████████ MVP Completado (Fase 0-5)
2025 Dic ██████        Post-MVP (Fase 6)
2026 Ene ████          Hardening (Fase 7)
2026 Feb ████████      UX Enhancements (Fase 8)
2026 Mar ████          Internationalization (Fase 9)
2026 Abr-May ████████  Advanced Features (Fase 10)
2026 Jun+ ████████████ Enterprise (Fase 11)
```

---

## 🎯 Priorización de Próximos Pasos

### Inmediato (1-2 semanas)

1. **Email Verification** → Seguridad básica
2. **Rate Limiting** → Prevenir abuso
3. **Sentry Integration** → Monitoreo de errores

### Corto Plazo (1 mes)

1. **History Page** → Feature más solicitada
2. **SCORM Validator** → Reduce errores
3. **E2E Tests** → Confianza en releases

### Medio Plazo (3 meses)

1. **Glossary Management** → Calidad de traducciones
2. **Analytics Dashboard** → Insights de uso
3. **UI Multiidioma** → Alcance internacional

### Largo Plazo (6+ meses)

1. **xAPI Support** → Expansión de mercado
2. **Webhooks** → Integración con LMS
3. **Enterprise Features** → Monetización

---

**Estado**: 🚀 MVP LISTO - Ready for Phase 6

**Próximo Milestone**: Email Verification + Rate Limiting (Fase 7)

**Última actualización**: 2025-11-28
