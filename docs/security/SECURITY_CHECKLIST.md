# Security Checklist - Traductor SCORM API

Checklist operacional para el equipo de desarrollo. Verificar ANTES de cada despliegue.

---

## Pre-Deployment Security Checklist

### Authentication & Authorization

- [ ] **Todos los endpoints sensibles requieren autenticación**
  - [ ] `/api/v1/upload` tiene `Depends(get_current_user)`
  - [ ] `/api/v1/jobs` tiene `Depends(get_current_user)`
  - [ ] `/api/v1/jobs/{job_id}` tiene `Depends(get_current_user)`
  - [ ] `/api/v1/jobs/{job_id}/details` tiene `Depends(get_current_user)`
  - [ ] `/api/v1/download/{job_id}/{language}` tiene `Depends(get_current_user)`
  - [ ] `/api/v1/download/{job_id}/all` tiene `Depends(get_current_user)`

- [ ] **Validación de ownership implementada**
  - [ ] GET `/jobs/{job_id}` valida `job.user_id == user.id`
  - [ ] GET `/jobs/{job_id}/details` valida `job.user_id == user.id`
  - [ ] GET `/download/{job_id}/*` valida `job.user_id == user.id`

- [ ] **Row-Level Security (RLS) habilitado en Supabase**
  - [ ] Tabla `translation_jobs` tiene RLS enabled
  - [ ] Política "Users can view own jobs" creada
  - [ ] Política "Users can insert own jobs" creada
  - [ ] Política "Users can update own jobs" creada
  - [ ] Queries usan cliente Supabase con token de usuario (no service role)

- [ ] **Contraseñas seguras**
  - [ ] Validación de fortaleza en signup (8+ chars, mayúsculas, minúsculas, números, especiales)
  - [ ] Contraseñas comunes bloqueadas
  - [ ] Hashing con bcrypt (12+ rounds)

---

### Input Validation

- [ ] **Validación de archivos subidos**
  - [ ] Extensión validada (.zip solamente)
  - [ ] Tipo MIME validado con python-magic
  - [ ] Contenido del ZIP validado
  - [ ] Path traversal bloqueado (sin `..` en paths)
  - [ ] Archivos peligrosos rechazados (.exe, .dll, .sh, .bat)
  - [ ] Zip bombs detectados (ratio de compresión < 100x)
  - [ ] Límite de archivos en ZIP (< 10,000 archivos)
  - [ ] Límite de tamaño individual (< 100MB por archivo)

- [ ] **Validación de parámetros**
  - [ ] Query params validados con Pydantic (`limit`, `offset`, `status_filter`)
  - [ ] Path params validados (UUIDs bien formados)
  - [ ] Form data validada (emails, idiomas soportados)

- [ ] **Sanitización de salida**
  - [ ] Mensajes de error no exponen stack traces
  - [ ] Mensajes de error no exponen paths internos
  - [ ] Mensajes de error no exponen versiones de software

---

### Rate Limiting

- [ ] **Rate limiting configurado**
  - [ ] Redis configurado para persistencia
  - [ ] Middleware de slowapi/fastapi-limiter agregado
  - [ ] Límites aplicados por endpoint:
    - [ ] `/auth/login`: 5/minuto
    - [ ] `/auth/signup`: 3/hora
    - [ ] `/upload`: 5/hora
    - [ ] `/download/*`: 30/hora
    - [ ] `/jobs`: 60/minuto

- [ ] **Rate limiting testeado**
  - [ ] Login falla después de 5 intentos
  - [ ] Upload falla después de 5 archivos/hora
  - [ ] Código de error 429 retornado correctamente

---

### Security Headers

- [ ] **SecurityHeadersMiddleware configurado**
  - [ ] `X-Frame-Options: DENY`
  - [ ] `X-Content-Type-Options: nosniff`
  - [ ] `X-XSS-Protection: 1; mode=block`
  - [ ] `Content-Security-Policy` configurado
  - [ ] `Strict-Transport-Security` (solo HTTPS)
  - [ ] `Referrer-Policy: strict-origin-when-cross-origin`
  - [ ] `Permissions-Policy` configurado

- [ ] **CORS restrictivo**
  - [ ] `allow_origins` es lista específica (no `["*"]`)
  - [ ] `allow_methods` es lista específica (no `["*"]`)
  - [ ] `allow_headers` es lista específica (no `["*"]`)

---

### API Documentation

- [ ] **Swagger UI protegido en producción**
  - [ ] `/docs` deshabilitado si `ENVIRONMENT=production`
  - [ ] `/redoc` deshabilitado si `ENVIRONMENT=production`
  - [ ] Alternativa: Docs requieren autenticación

---

### Logging & Monitoring

- [ ] **Logging de seguridad implementado**
  - [ ] Login exitoso loggeado
  - [ ] Login fallido loggeado
  - [ ] Acceso no autorizado loggeado
  - [ ] Upload de archivos loggeado
  - [ ] Actividad sospechosa loggeada

- [ ] **Logs configurados correctamente**
  - [ ] Logs NO contienen contraseñas
  - [ ] Logs NO contienen tokens completos
  - [ ] Logs NO contienen PII sin encriptar
  - [ ] Logs rotan automáticamente (max 10 archivos de 10MB)

---

### Error Handling

- [ ] **ErrorHandler centralizado**
  - [ ] Errores de autenticación usan mensajes genéricos
  - [ ] Errores de autorización usan mensajes genéricos
  - [ ] Errores internos no exponen stack traces
  - [ ] Todos los endpoints tienen manejo de excepciones

---

### Dependencies & Configuration

- [ ] **Variables de entorno**
  - [ ] `.env` NO está en Git
  - [ ] `.env.example` tiene placeholders (no valores reales)
  - [ ] `SECRET_KEY` es random y único
  - [ ] `SUPABASE_SERVICE_ROLE_KEY` es válida y rotada
  - [ ] `ANTHROPIC_API_KEY` es válida

- [ ] **Dependencias actualizadas**
  - [ ] `pip install safety && safety check` sin vulnerabilidades críticas
  - [ ] `bandit -r app/` sin vulnerabilidades críticas
  - [ ] Dependencias pinned o con upper bound

---

### File Storage

- [ ] **Supabase Storage configurado**
  - [ ] Buckets `scorm-originals` y `scorm-translated` creados
  - [ ] Políticas de storage configuradas (usuarios solo acceden a sus archivos)
  - [ ] Lifecycle policy configurado (auto-delete después de 30 días)

- [ ] **Signed URLs**
  - [ ] Expiración <= 1 hora (no 7 días)
  - [ ] URLs firmadas solo generadas después de validar ownership

---

### Testing

- [ ] **Tests de seguridad pasando**
  - [ ] Test IDOR: Usuario B no puede acceder a jobs de Usuario A
  - [ ] Test rate limiting: Endpoint retorna 429 después de límite
  - [ ] Test upload malicioso: Archivo .exe renombrado a .zip rechazado
  - [ ] Test contraseña débil: "12345678" rechazado en signup

- [ ] **Pentesting básico realizado**
  - [ ] OWASP ZAP scan ejecutado
  - [ ] Vulnerabilidades críticas resueltas
  - [ ] Falsos positivos documentados

---

## Environment-Specific Checks

### Development

- [ ] `DEBUG=True` está OK
- [ ] Swagger UI habilitado está OK
- [ ] Logs verbosos están OK

### Staging

- [ ] `DEBUG=False`
- [ ] Swagger UI protegido o deshabilitado
- [ ] Variables de entorno de staging (no producción)
- [ ] Testing de smoke después de deploy

### Production

- [ ] `DEBUG=False`
- [ ] Swagger UI deshabilitado
- [ ] HTTPS forzado
- [ ] `Strict-Transport-Security` habilitado
- [ ] Rate limiting agresivo
- [ ] Logs solo errores y warnings (no debug)
- [ ] Monitoreo activo (Sentry, Datadog)
- [ ] Backups automáticos configurados

---

## Post-Deployment Verification

### Inmediato (Primeras 24 horas)

- [ ] Health check retorna 200
- [ ] Login funciona correctamente
- [ ] Upload de SCORM funciona
- [ ] Download de SCORM funciona
- [ ] Logs no muestran errores 500
- [ ] Métricas de performance normales

### Primera Semana

- [ ] Revisar logs de seguridad diariamente
- [ ] Monitorear intentos de acceso no autorizado
- [ ] Verificar tasa de errores < 1%
- [ ] Verificar que rate limiting está funcionando

### Primer Mes

- [ ] Auditoría de logs de acceso
- [ ] Revisar usuarios con actividad anómala
- [ ] Verificar que no hay credenciales expuestas
- [ ] Rotar service role key si hubo incidente

---

## Incident Response

### Si detectas una vulnerabilidad

1. [ ] **NO la ignores**
2. [ ] Documenta la vulnerabilidad (descripción, impacto, PoC)
3. [ ] Notifica a security@traductor-scorm.com INMEDIATAMENTE
4. [ ] Si es CRITICAL, escala a CTO
5. [ ] NO publiques la vulnerabilidad públicamente

### Si detectas un breach

1. [ ] **Aislar el sistema** (take down si es necesario)
2. [ ] Notificar a todo el equipo de liderazgo
3. [ ] Preservar logs y evidencia
4. [ ] Investigar alcance (qué datos fueron accedidos)
5. [ ] Rotar TODAS las credenciales
6. [ ] Notificar a usuarios afectados (GDPR compliance)
7. [ ] Post-mortem y remediación

---

## Compliance Checks

### GDPR

- [ ] Usuario puede exportar sus datos
- [ ] Usuario puede eliminar su cuenta
- [ ] Datos encriptados en tránsito (HTTPS)
- [ ] Datos encriptados en reposo (Supabase encryption)
- [ ] Logs no contienen PII sin justificación
- [ ] Privacy policy actualizada

### OWASP API Top 10

- [ ] API1 (BOLA/IDOR): Validación de ownership en todos los endpoints
- [ ] API2 (Broken Auth): Rate limiting + password strength
- [ ] API4 (Resource Consumption): Límites de tamaño y rate limiting
- [ ] API5 (Function Level Auth): RLS + validación de roles
- [ ] API8 (Misconfiguration): Headers de seguridad + docs protegidos

---

## Developer Checklist (Before Each Commit)

- [ ] Código no contiene credenciales hardcodeadas
- [ ] Código no tiene `TODO: Security` sin resolver
- [ ] Tests de seguridad pasando
- [ ] Linter pasando (`ruff check .`)
- [ ] Type checker pasando (`mypy app/`)
- [ ] No hay warnings de Bandit críticos

---

## Code Review Checklist

### Para el Reviewer

- [ ] Endpoint nuevo tiene autenticación si es necesario
- [ ] Endpoint nuevo valida ownership si accede a recursos de usuario
- [ ] Inputs están validados con Pydantic
- [ ] Errores usan ErrorHandler (no exposición de detalles)
- [ ] Queries usan cliente con RLS (no service role si no es necesario)
- [ ] No hay credenciales en código
- [ ] Logs no exponen información sensible

---

## Automation

### Pre-commit Hooks

```bash
# Instalar pre-commit
pip install pre-commit

# Configurar .pre-commit-config.yaml
cat > .pre-commit-config.yaml <<EOF
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: check-added-large-files
      - id: check-json
      - id: check-yaml
      - id: detect-private-key

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ['-r', 'app/', '-ll']  # Solo high/medium

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.8
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
EOF

# Instalar hooks
pre-commit install
```

### CI/CD Pipeline

```yaml
# .github/workflows/security.yml
name: Security Checks

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install safety bandit

      - name: Check for known vulnerabilities
        run: safety check

      - name: Run Bandit
        run: bandit -r app/ -f json -o bandit-report.json

      - name: Upload Bandit report
        uses: actions/upload-artifact@v3
        with:
          name: bandit-report
          path: bandit-report.json
```

---

## Quick Reference

### Comandos Útiles

```bash
# Escanear dependencias
pip install safety
safety check

# Escanear código
pip install bandit
bandit -r app/ -ll

# Verificar tipos
mypy app/

# Linter
ruff check app/

# Tests de seguridad
pytest tests/security/ -v

# Verificar que .env no está en Git
git ls-files | grep ".env$"  # Debe estar vacío

# Generar SECRET_KEY segura
openssl rand -hex 32
```

### Contactos de Emergencia

| Tipo | Contacto | SLA |
|------|----------|-----|
| Vulnerabilidad CRITICAL | security@traductor-scorm.com | < 4h |
| Vulnerabilidad HIGH | devops@traductor-scorm.com | < 24h |
| Consulta de seguridad | #security Slack | < 48h |
| Breach activo | CTO directo + security@ | Inmediato |

---

**Última actualización**: 2025-12-16
**Próxima revisión**: Cada sprint (2 semanas)
**Responsable**: Security Champion del equipo
