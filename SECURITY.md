# 🔐 Guía de Seguridad - Traductor SCORM

**Última actualización**: 2025-11-28
**Versión**: 1.0.0

---

## 🚨 ALERTA: Credenciales Expuestas Detectadas

### Situación Actual

GitHub ha detectado que se expusieron credenciales en commits anteriores del repositorio. Aunque los archivos `.env` ya no están en el repositorio actual, las credenciales permanecen en el historial de Git.

### ⚠️ Credenciales Comprometidas que DEBES ROTAR

**ACCIÓN INMEDIATA REQUERIDA**: Todas estas credenciales deben ser rotadas/regeneradas:

#### 1. Supabase Service Role Key (CRÍTICO - Máxima Prioridad)
**Archivo donde estaba**: `backend/.env`
**Variable**: `SUPABASE_SERVICE_ROLE_KEY`
**Peligro**: Acceso administrativo completo a tu base de datos
**Valor expuesto**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh1ZXpqY2ZtbmdoZnp2dWp1aHRqIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NDIzMjI3MywiZXhwIjoyMDc5ODA4MjczfQ.LRlub8s84KfR7vMzN4ZydQmqhU7MEInpxlp0X63wVPg`

**Cómo rotarlo**:
```
1. Ir a Supabase Dashboard → Settings → API
2. En la sección "Project API keys", NO puedes rotar directamente
3. OPCIÓN A (Recomendada): Crear nuevo proyecto Supabase
   - Migrar datos al nuevo proyecto
   - Actualizar .env con nuevas keys
4. OPCIÓN B (Temporal): Habilitar RLS en TODAS las tablas
   - Esto limita el daño pero no elimina la vulnerabilidad
5. Contactar soporte de Supabase para rotar service_role key
```

#### 2. Supabase Anon Key (ALTO - Alta Prioridad)
**Archivo donde estaba**: `backend/.env`, `frontend/.env`
**Variable**: `SUPABASE_ANON_KEY` / `VITE_SUPABASE_ANON_KEY`
**Peligro**: Acceso a tu database según RLS policies
**Valor expuesto**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh1ZXpqY2ZtbmdoZnp2dWp1aHRqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQyMzIyNzMsImV4cCI6MjA3OTgwODI3M30.1Cob4jHpV2ItzOZ8QwArNCIh7TW4YOvqVHMpvHzhbi4`

**Nota**: Esta key es "pública" por diseño (va en frontend), pero con RLS bien configurado no es crítico. Sin embargo, es mejor rotarla.

**Cómo rotarlo**: Mismo procedimiento que service_role key.

#### 3. Anthropic API Key (MEDIO - Media Prioridad)
**Archivo donde estaba**: `backend/.env`
**Variable**: `ANTHROPIC_API_KEY`
**Peligro**: Uso no autorizado de tu cuenta de Anthropic → Costos inesperados
**Valor expuesto**: `sk-ant-api03-...` (parcialmente oculto en documentación)

**Cómo rotarlo**:
```
1. Ir a https://console.anthropic.com/settings/keys
2. Revocar la API key actual
3. Crear nueva API key
4. Actualizar backend/.env con la nueva key
5. Reiniciar servidor backend
```

#### 4. Supabase URL (INFO - Baja Prioridad)
**Variable**: `SUPABASE_URL`
**Valor**: `https://xuezjcfmnghfzvujuhtj.supabase.co`
**Peligro**: Bajo (es público de todas formas)
**Acción**: No requiere rotación, pero considera crear nuevo proyecto.

---

## 📋 Checklist de Rotación de Credenciales

Sigue estos pasos EN ORDEN:

### ✅ Paso 1: Rotar Anthropic API Key (5 minutos)
- [ ] Ir a Anthropic Console
- [ ] Revocar key antigua
- [ ] Generar nueva key
- [ ] Actualizar `backend/.env` (solo local)
- [ ] Reiniciar backend

### ✅ Paso 2: Evaluar Opciones para Supabase (15 minutos)

**Opción A - Crear Nuevo Proyecto** (Recomendado si hay pocos datos):
- [ ] Crear nuevo proyecto en Supabase
- [ ] Ejecutar migraciones SQL en nuevo proyecto
- [ ] Crear buckets de storage
- [ ] Migrar datos existentes (si los hay)
- [ ] Actualizar `.env` con nuevas keys
- [ ] Probar funcionamiento
- [ ] Eliminar proyecto antiguo

**Opción B - Fortalecer Proyecto Actual** (Si no puedes migrar):
- [ ] Verificar que RLS está habilitado en TODAS las tablas
- [ ] Revisar políticas RLS (solo deben permitir acceso a propietarios)
- [ ] Habilitar autenticación obligatoria
- [ ] Monitorear logs de acceso en Supabase
- [ ] Contactar soporte para rotar service_role key

### ✅ Paso 3: Limpiar Historial de Git (30 minutos)

**IMPORTANTE**: Esto reescribe el historial de Git y requiere force push.

```bash
# Instalar BFG Repo-Cleaner (más rápido que git filter-branch)
brew install bfg  # Mac
# o descargar de: https://rtyley.github.io/bfg-repo-cleaner/

# Hacer backup del repositorio
cd ..
cp -r traductor-scorm-manual traductor-scorm-manual-backup

# Limpiar archivos .env del historial
cd traductor-scorm-manual
bfg --delete-files '.env'

# Limpiar referencias
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push (CUIDADO: esto reescribe historial)
git push origin main --force

# Notificar a GitHub que rotaste las credenciales
# (GitHub puede seguir mostrando alerta hasta que cierres el issue)
```

**ADVERTENCIA**: Force push reescribe el historial. Si hay colaboradores, notifícales.

### ✅ Paso 4: Verificar que Todo Funciona (10 minutos)
- [ ] Hacer git clone fresco del repo
- [ ] Copiar `.env` con nuevas credenciales
- [ ] Ejecutar backend: `cd backend && uvicorn app.main:app --reload`
- [ ] Ejecutar frontend: `cd frontend && npm run dev`
- [ ] Probar signup/login
- [ ] Probar traducción de SCORM

---

## 🛡️ Conceptos Básicos de Seguridad - Nunca Más Expongas Credenciales

### 1. ¿Qué NUNCA debe estar en Git?

❌ **NUNCA commitear**:
- Archivos `.env` (producción, desarrollo, staging)
- API keys (Anthropic, OpenAI, etc.)
- Database passwords
- Service role keys de Supabase
- SECRET_KEY de aplicaciones
- Tokens JWT
- Certificados privados (.pem, .key)
- Credenciales de AWS, Google Cloud, Azure
- Contraseñas en código

✅ **SÍ puede estar en Git**:
- `.env.example` (con valores de ejemplo/placeholders)
- Documentación con ejemplos genéricos
- Supabase ANON_KEY (es pública por diseño, pero con RLS)

### 2. Anatomía de un .env Seguro

**❌ INCORRECTO** (backend/.env en el repo):
```env
SUPABASE_URL=https://xuezjcfmnghfzvujuhtj.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
ANTHROPIC_API_KEY=sk-ant-api03-abc123...
```

**✅ CORRECTO** (backend/.env.example en el repo):
```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# AI Translation
ANTHROPIC_API_KEY=sk-ant-api03-your_key_here

# Security
SECRET_KEY=generate_with_openssl_rand_hex_32
```

**✅ CORRECTO** (backend/.env solo local, nunca commitear):
```env
SUPABASE_URL=https://xuezjcfmnghfzvujuhtj.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
ANTHROPIC_API_KEY=sk-ant-api03-abc123...
```

### 3. Workflow Seguro de Desarrollo

#### Setup Inicial (Primera vez)

```bash
# 1. Clonar repositorio
git clone https://github.com/tu-usuario/tu-proyecto.git
cd tu-proyecto

# 2. Copiar template de .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# 3. Editar .env con tus credenciales REALES (nunca commitear)
nano backend/.env  # o tu editor favorito

# 4. Verificar que .env está en .gitignore
cat .gitignore | grep ".env"

# 5. NUNCA hacer git add backend/.env
```

#### Antes de Cada Commit

```bash
# Verificar que no estás committeando secretos
git status

# Si ves archivos .env, ¡DETENTE!
# Nunca hagas: git add backend/.env

# Solo agregar archivos seguros
git add src/
git add .env.example  # OK, es template
git add README.md

# Revisar diff antes de commit
git diff --cached

# Si ves credenciales, deshacer:
git reset HEAD archivo-con-secretos.env
```

### 4. Herramientas de Prevención

#### A. Pre-commit Hook (Recomendado)

Crea `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Pre-commit hook para prevenir commit de secretos

# Lista de patrones peligrosos
PATTERNS=(
  "sk-ant-api"           # Anthropic API keys
  "sk-[a-zA-Z0-9]{48}"   # OpenAI API keys
  "eyJhbGciOiJIUzI1NiI"  # JWT tokens
  "postgres://.*@.*"     # Database URLs con credenciales
  "SUPABASE_SERVICE_ROLE_KEY=eyJ"
)

# Verificar staged files
FILES=$(git diff --cached --name-only)

for FILE in $FILES; do
  for PATTERN in "${PATTERNS[@]}"; do
    if git diff --cached $FILE | grep -qE "$PATTERN"; then
      echo "❌ ERROR: Posible credencial detectada en $FILE"
      echo "Patrón encontrado: $PATTERN"
      echo ""
      echo "Revisa el archivo y remueve las credenciales antes de commitear."
      exit 1
    fi
  done
done

echo "✅ Pre-commit check passed - No credentials detected"
exit 0
```

Hacerlo ejecutable:
```bash
chmod +x .git/hooks/pre-commit
```

#### B. git-secrets (GitHub oficial)

```bash
# Instalar
brew install git-secrets  # Mac
# o: apt-get install git-secrets  # Linux

# Configurar en tu repo
cd traductor-scorm-manual
git secrets --install
git secrets --register-aws  # Previene AWS keys

# Agregar patrones custom
git secrets --add 'sk-ant-api[0-9a-zA-Z\-]+'
git secrets --add 'eyJhbGciOiJIUzI1NiI[a-zA-Z0-9\-_=]+'

# Escanear historial existente
git secrets --scan-history
```

#### C. GitHub Secret Scanning (Automático)

GitHub escanea automáticamente tu repositorio en busca de:
- API keys conocidas
- Tokens de servicios populares
- Certificados

**Cuando GitHub detecta un secreto**:
1. Te envía un email
2. Crea un "Secret scanning alert" en Settings → Security
3. Notifica al proveedor del servicio (ej. Anthropic)

**Tu respuesta**:
1. Rotar credencial INMEDIATAMENTE
2. Cerrar el issue en GitHub
3. Limpiar historial de Git

### 5. Variables de Entorno en Producción

#### Vercel (Frontend)

```bash
# NO hacer esto en el código:
const API_KEY = "sk-ant-api03-abc123";  // ❌ MAL

# Usar variables de entorno:
const API_KEY = import.meta.env.VITE_API_KEY;  // ✅ BIEN
```

**Configuración en Vercel**:
1. Dashboard → Project → Settings → Environment Variables
2. Agregar: `VITE_API_URL`, `VITE_SUPABASE_URL`, etc.
3. Nunca expongas service_role keys en frontend

#### Railway (Backend)

1. Dashboard → Project → Variables
2. Agregar todas las variables de `backend/.env`
3. Railway las inyecta automáticamente en runtime

#### Docker Compose (Local)

```yaml
# docker-compose.yml
services:
  backend:
    env_file:
      - ./backend/.env  # ✅ BIEN - archivo no está en Git
    # NO hardcodear:
    # environment:
    #   - ANTHROPIC_API_KEY=sk-ant-api03-abc  # ❌ MAL
```

### 6. Niveles de Sensibilidad de Credenciales

| Nivel | Tipo | Ejemplo | Acción si se expone |
|-------|------|---------|---------------------|
| 🔴 **CRÍTICO** | Service Role Keys | Supabase service_role | Rotar INMEDIATAMENTE, auditar accesos |
| 🟠 **ALTO** | API Keys con billing | Anthropic, OpenAI | Rotar en < 1 hora, revisar billing |
| 🟡 **MEDIO** | Secret Keys | JWT SECRET_KEY | Rotar, invalidar sesiones activas |
| 🟢 **BAJO** | Public Keys | Supabase anon_key | Verificar RLS, considerar rotar |
| ⚪ **INFO** | URLs públicas | SUPABASE_URL | No requiere acción |

### 7. Qué Hacer si Expones un Secreto

**Checklist de Respuesta a Incidentes**:

1. **Minuto 0-5: Contener**
   - [ ] Revocar/rotar credencial expuesta INMEDIATAMENTE
   - [ ] Deshabilitar servicio si es posible (ej. API key)

2. **Minuto 5-15: Evaluar Daño**
   - [ ] Revisar logs de acceso (¿alguien usó la credencial?)
   - [ ] Revisar billing (¿hubo uso inesperado?)
   - [ ] Identificar qué datos/servicios están comprometidos

3. **Minuto 15-30: Limpiar**
   - [ ] Limpiar credencial del historial de Git (BFG)
   - [ ] Force push (si es tu repo personal)
   - [ ] Notificar a colaboradores si es repo compartido

4. **Día 1: Fortalecer**
   - [ ] Implementar pre-commit hooks
   - [ ] Revisar .gitignore
   - [ ] Configurar git-secrets
   - [ ] Habilitar 2FA en todos los servicios

5. **Semana 1: Prevenir**
   - [ ] Auditar otros repositorios
   - [ ] Documentar proceso (como este SECURITY.md)
   - [ ] Capacitar al equipo

### 8. Mejores Prácticas por Tecnología

#### Python/FastAPI

```python
# ❌ MAL
API_KEY = "sk-ant-api03-abc123"

# ✅ BIEN
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("ANTHROPIC_API_KEY")

# ✅ MEJOR (con validación)
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    anthropic_api_key: str

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()  # Falla si falta variable
```

#### React/Vite

```typescript
// ❌ MAL
const API_URL = "https://api.example.com";
const SECRET = "abc123";

// ✅ BIEN (solo para valores públicos)
const API_URL = import.meta.env.VITE_API_URL;

// ⚠️ ADVERTENCIA: NUNCA pongas secretos en frontend
// Cualquier variable VITE_* es PÚBLICA en el bundle
```

#### Docker

```dockerfile
# ❌ MAL
ENV ANTHROPIC_API_KEY=sk-ant-api03-abc123

# ✅ BIEN
# No poner secretos en Dockerfile
# Pasarlos en runtime con docker-compose o --env-file
```

```yaml
# docker-compose.yml
services:
  backend:
    env_file: .env  # ✅ BIEN
    # NO:
    # environment:
    #   - SECRET_KEY=abc123  # ❌ MAL
```

---

## 🔍 Auditoría de Seguridad Regular

### Checklist Mensual

- [ ] Escanear repo con `git-secrets --scan-history`
- [ ] Revisar alertas de GitHub Security
- [ ] Rotar credenciales críticas (cada 90 días)
- [ ] Revisar logs de acceso en Supabase
- [ ] Revisar billing de APIs (detectar uso anómalo)
- [ ] Actualizar dependencias (`npm audit`, `pip-audit`)

### Comandos Útiles

```bash
# Escanear archivos por patrones sospechosos
grep -r "sk-ant-api" .  # Buscar API keys
grep -r "eyJhbGciOiJIUzI1NiI" .  # Buscar JWT tokens
grep -r "password.*=" . --include="*.py"  # Buscar passwords

# Verificar qué archivos están tracked en Git
git ls-files | grep -E "\.(env|key|pem)$"

# Ver historial de un archivo (incluido si fue borrado)
git log --all --full-history -- "**/.env"

# Encontrar cuando se agregó un secreto
git log -p -S "sk-ant-api03" --all
```

---

## 📚 Recursos Adicionales

### Herramientas

- **git-secrets**: https://github.com/awslabs/git-secrets
- **BFG Repo-Cleaner**: https://rtyley.github.io/bfg-repo-cleaner/
- **TruffleHog**: https://github.com/trufflesecurity/trufflehog
- **GitGuardian**: https://www.gitguardian.com/
- **Gitleaks**: https://github.com/gitleaks/gitleaks

### Lecturas Recomendadas

- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **GitHub Security Best Practices**: https://docs.github.com/en/code-security
- **Twelve-Factor App**: https://12factor.net/config

### Comunidad

- **r/netsec** (Reddit)
- **OWASP Slack**
- **GitHub Security Lab**

---

## 🆘 Contacto en Caso de Emergencia

Si descubres una vulnerabilidad de seguridad:

1. **NO abras un issue público**
2. Contacta en privado: [tu-email-seguridad@ejemplo.com]
3. Incluye:
   - Descripción de la vulnerabilidad
   - Pasos para reproducir
   - Impacto potencial
   - Sugerencias de mitigación (si tienes)

**Tiempo de respuesta**: < 24 horas

---

## ✅ Checklist de Seguridad para Nuevos Desarrolladores

Antes de tu primer commit:

- [ ] He leído este SECURITY.md completo
- [ ] He configurado pre-commit hooks
- [ ] He instalado git-secrets
- [ ] Sé dónde está el .env.example (y que NUNCA debo commitear .env)
- [ ] He verificado que .gitignore incluye todos los archivos sensibles
- [ ] Sé cómo rotar credenciales si las expongo
- [ ] Conozco los niveles de sensibilidad de cada credencial
- [ ] He habilitado 2FA en GitHub, Supabase, y Anthropic

---

**Última revisión**: 2025-11-28
**Próxima auditoría**: 2025-12-28
**Responsable de seguridad**: [Tu nombre]

---

**Recuerda**: La seguridad es responsabilidad de todos. Un solo error puede comprometer todo el sistema.

**Regla de oro**: Si tienes duda si algo debe estar en Git, probablemente NO debe estar.
