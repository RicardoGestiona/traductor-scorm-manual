# Changelog

Todos los cambios notables en este proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

---

## [1.1.0] - 2025-12-17

### Seguridad

Esta versión incluye una auditoría de seguridad completa con 12 vulnerabilidades corregidas.

#### Críticas (CRITICAL)
- **CRIT-001**: Eliminada inyección dinámica de CSS en `TranslationProgress.tsx`
  - La animación `@keyframes shine` ahora está definida estáticamente en `index.css`
  - Previene ataques de inyección CSS

- **CRIT-002**: Implementada protección CSRF
  - Añadido middleware `CSRFProtectionMiddleware` en el backend
  - Todas las peticiones POST/PUT/DELETE requieren header `X-Requested-With: XMLHttpRequest`
  - El frontend envía automáticamente este header en todas las peticiones

#### Altas (HIGH)
- **HIGH-001**: Añadidos security headers en `index.html`
  - Content-Security-Policy (CSP)
  - X-Content-Type-Options: nosniff
  - X-Frame-Options: DENY
  - Referrer-Policy: strict-origin-when-cross-origin
  - Permissions-Policy (deshabilita geolocation, microphone, camera)

- **HIGH-002**: Fortalecida validación de contraseñas en `Signup.tsx`
  - Mínimo 8 caracteres
  - Al menos una mayúscula
  - Al menos una minúscula
  - Al menos un número
  - Al menos un carácter especial

- **HIGH-003**: Implementado refresh proactivo de tokens en `AuthContext.tsx`
  - Los tokens se refrescan automáticamente 5 minutos antes de expirar
  - Previene errores 401 durante sesiones largas

- **HIGH-004**: Completada implementación de logout en `AuthContext.tsx`
  - Limpia sesión de Supabase
  - Limpia localStorage y sessionStorage
  - Redirige a página de login

- **HIGH-005**: Añadida validación de magic bytes en `UploadZone.tsx`
  - Valida firma ZIP (PK..) además de la extensión
  - Previene uploads de archivos maliciosos disfrazados

- **HIGH-006**: Sanitizados mensajes de error en `api.ts`
  - Los errores técnicos solo se muestran en desarrollo
  - En producción se muestran mensajes genéricos y seguros

#### Medias (MEDIUM)
- **MED-002**: Logging condicional por entorno
  - `console.log/error` solo activos en modo desarrollo
  - Añadido wrapper `secureLog` para logging seguro

- **MED-003**: Añadido Error Boundary en `App.tsx`
  - Nuevo componente `ErrorBoundary.tsx`
  - Captura errores de React y muestra UI amigable
  - Los stack traces solo se muestran en desarrollo

- **MED-004**: Añadido límite de reintentos en polling
  - Máximo 180 reintentos (6 minutos a 2s/intento)
  - Previene loops infinitos de polling

#### Bajas (LOW)
- **LOW-002**: Deshabilitados source maps en producción
  - Configurado `sourcemap: false` en `vite.config.ts`
  - Previene exposición del código fuente

### Añadido
- Nuevo componente `ErrorBoundary.tsx` para manejo global de errores
- Documentación de seguridad en `docs/security/`
- Auditoría de seguridad del frontend en `docs/security/FRONTEND_SECURITY_AUDIT.md`

### Modificado
- `backend/app/main.py`: Añadido CSRFProtectionMiddleware
- `frontend/index.html`: Añadidos meta tags de seguridad
- `frontend/src/services/api.ts`: Headers CSRF y errores sanitizados
- `frontend/src/contexts/AuthContext.tsx`: Token refresh y logout completo
- `frontend/src/components/UploadZone.tsx`: Validación magic bytes
- `frontend/src/components/TranslationProgress.tsx`: Límite de reintentos
- `frontend/src/index.css`: Animaciones movidas desde JS
- `frontend/vite.config.ts`: Source maps deshabilitados

---

## [1.0.0] - 2025-11-28

### Añadido
- **MVP Completo** del Traductor SCORM
- Parser completo de SCORM 1.2 y 2004
- Integración con Claude AI para traducciones
- Frontend React con TypeScript y Tailwind CSS
- Backend FastAPI con autenticación Supabase
- Procesamiento asíncrono con Celery + Redis
- Docker Compose para desarrollo
- 100 tests automatizados
- Soporte para 12 idiomas

### Características principales
- Upload de paquetes SCORM (.zip)
- Selección múltiple de idiomas destino
- Traducción automática con IA
- Progress tracking en tiempo real
- Descarga de paquetes traducidos
- Autenticación de usuarios (signup, login, logout)
- Historial de traducciones por usuario

---

## [0.1.0] - 2025-11-25

### Añadido
- Estructura inicial del proyecto
- Documentación base (CLAUDE.md, PRD.md, BACKLOG.md)
- Setup de FastAPI
- Setup de React + Vite
- Docker Compose básico
- Health check endpoint
