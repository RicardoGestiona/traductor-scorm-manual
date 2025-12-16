# API Security Audit Report - Traductor SCORM
**Auditor**: API Security Audit Specialist
**Fecha**: 2025-12-16
**Alcance**: REST API Backend (FastAPI)
**Directorio auditado**: `/backend/app/api/`
**Severidad**: CRITICAL, HIGH, MEDIUM, LOW, INFO

---

## Executive Summary

Se realizó una auditoría de seguridad completa de la API REST del sistema Traductor SCORM. Se identificaron **15 vulnerabilidades** con los siguientes niveles de severidad:

- **CRITICAL**: 3 vulnerabilidades
- **HIGH**: 5 vulnerabilidades
- **MEDIUM**: 4 vulnerabilidades
- **LOW**: 2 vulnerabilidades
- **INFO**: 1 recomendación

**Riesgo General**: HIGH - Se requiere acción inmediata en vulnerabilidades críticas antes de despliegue en producción.

---

## 1. Inventario de Endpoints

### 1.1 Endpoints Públicos (Sin Autenticación)

| Endpoint | Método | Propósito | Riesgo |
|----------|--------|-----------|--------|
| `/` | GET | API info | LOW |
| `/health` | GET | Health check | LOW |
| `/docs` | GET | Swagger UI | MEDIUM - Expone estructura de API |
| `/redoc` | GET | ReDoc UI | MEDIUM - Expone estructura de API |
| `/api/v1/auth/signup` | POST | Registro de usuarios | MEDIUM |
| `/api/v1/auth/login` | POST | Login | MEDIUM |
| `/api/v1/auth/refresh` | POST | Refresh token | MEDIUM |

### 1.2 Endpoints Protegidos (Requieren Autenticación)

| Endpoint | Método | Autenticación | Autorización | Estado RLS |
|----------|--------|---------------|--------------|-----------|
| `/api/v1/auth/me` | GET | Bearer JWT | User | N/A |
| `/api/v1/auth/logout` | POST | Bearer JWT | User | N/A |
| `/api/v1/upload` | POST | Bearer JWT | User | PENDIENTE |
| `/api/v1/jobs` | GET | Bearer JWT | User | MANUAL (No RLS real) |
| `/api/v1/jobs/{job_id}` | GET | Bearer JWT | User + Ownership | MANUAL (No RLS real) |
| `/api/v1/jobs/{job_id}/details` | GET | Bearer JWT | FALTA | CRITICAL - Sin validación |
| `/api/v1/download/{job_id}/{language}` | GET | Bearer JWT | User + Ownership | MANUAL |
| `/api/v1/download/{job_id}/all` | GET | Bearer JWT | FALTA | CRITICAL - Sin validación |

---

## 2. Vulnerabilidades Críticas (CRITICAL)

### CRIT-01: Insecure Direct Object Reference (IDOR) en `/jobs/{job_id}/details`

**Archivo**: `/backend/app/api/v1/jobs.py:239-290`
**Severidad**: CRITICAL
**CVSS Score**: 8.1
**CWE**: CWE-639 - Authorization Bypass Through User-Controlled Key

**Descripción**:
El endpoint `GET /jobs/{job_id}/details` NO valida que el usuario autenticado sea el propietario del job. Cualquier usuario autenticado puede acceder a los detalles completos de cualquier job conociendo el UUID.

**Código vulnerable**:
```python
@router.get("/jobs/{job_id}/details", response_model=TranslationJobResponse)
async def get_job_details(
    job_id: UUID = Path(..., description="Unique identifier of the translation job"),
):
    """Get full details of a translation job."""
    try:
        job = await job_service.get_job(job_id)
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, ...)
        return job  # NO HAY VALIDACIÓN DE OWNERSHIP
```

**Impacto**:
- Acceso no autorizado a información sensible de otros usuarios
- Exposición de nombres de archivos, idiomas traducidos, URLs de descarga
- Posible enumeración de jobs para extraer información del negocio

**Explotación**:
```bash
# Usuario A crea job con ID: 123e4567-e89b-12d3-a456-426614174000
# Usuario B (malicioso) puede acceder:
curl -H "Authorization: Bearer TOKEN_USER_B" \
  http://api.example.com/api/v1/jobs/123e4567-e89b-12d3-a456-426614174000/details
# ¡ACCESO CONCEDIDO sin validación!
```

**Recomendación**:
```python
@router.get("/jobs/{job_id}/details", response_model=TranslationJobResponse)
async def get_job_details(
    job_id: UUID = Path(...),
    user: User = Depends(get_current_user),  # AGREGAR
):
    """Get full details of a translation job."""
    try:
        job = await job_service.get_job(job_id)

        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, ...)

        # VALIDAR OWNERSHIP
        if job.user_id and str(job.user_id) != user.id:
            logger.warning(f"User {user.email} attempted to access job {job_id} owned by {job.user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "Forbidden", "details": "Access denied"}
            )

        return job
```

---

### CRIT-02: Insecure Direct Object Reference (IDOR) en `/download/{job_id}/all`

**Archivo**: `/backend/app/api/v1/download.py:189-342`
**Severidad**: CRITICAL
**CVSS Score**: 9.1
**CWE**: CWE-639 - Authorization Bypass Through User-Controlled Key

**Descripción**:
El endpoint `GET /download/{job_id}/all` NO requiere autenticación ni valida ownership. Permite descargar todos los paquetes SCORM traducidos de cualquier job sin restricciones.

**Código vulnerable**:
```python
@router.get("/download/{job_id}/all", response_class=FileResponse)
async def download_all_translations(job_id: UUID):
    # NO HAY Depends(get_current_user)
    # NO HAY VALIDACIÓN DE OWNERSHIP
    job = await job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, ...)
    # Retorna FileResponse directamente
```

**Impacto**:
- Acceso completamente público a archivos traducidos
- Robo de propiedad intelectual (cursos SCORM completos)
- Violación de confidencialidad de clientes
- Posible uso de recursos del servidor para ataques DDoS (generar ZIPs costosos)

**Explotación**:
```bash
# Cualquiera sin autenticación puede descargar:
curl -O http://api.example.com/api/v1/download/ANY_UUID/all
# ¡DESCARGA EXITOSA sin token!
```

**Recomendación**:
```python
@router.get("/download/{job_id}/all", response_class=FileResponse)
async def download_all_translations(
    job_id: UUID,
    user: User = Depends(get_current_user),  # AGREGAR
):
    """Download all translated SCORM packages."""
    try:
        job = await job_service.get_job(job_id)

        if not job:
            raise HTTPException(status_code=404, ...)

        # VALIDAR OWNERSHIP
        if job.user_id and str(job.user_id) != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "Forbidden"}
            )

        # Continuar con lógica de descarga...
```

---

### CRIT-03: Service Role Key Expuesta y Uso Incorrecto de RLS

**Archivo**: `/backend/app/core/auth.py:149-171`
**Severidad**: CRITICAL
**CVSS Score**: 9.8
**CWE**: CWE-284 - Improper Access Control

**Descripción**:
El sistema NO implementa Row-Level Security (RLS) real de Supabase. Todos los queries usan el service role key que bypasea RLS, y la validación de ownership se hace manualmente en código Python, lo cual es propenso a errores.

**Código problemático**:
```python
def get_supabase_client_for_user(user: User) -> Client:
    """
    Returns a Supabase client scoped to the authenticated user.

    Note: Currently returns service role client. To properly implement RLS,
    we would need to pass the user's access token to create a new client.
    For MVP, we'll filter by user_id manually in queries.
    """
    # TODO: Implement proper user-scoped client with user's access token
    # For now, return service role client and filter manually
    return supabase  # ¡RETORNA SERVICE ROLE CLIENT!
```

**Impacto**:
- Cualquier error en validación manual permite escalación de privilegios
- Service role key comprometida = acceso total a la base de datos
- Violación del principio de defensa en profundidad

**Recomendación**:
```python
def get_supabase_client_for_user(user: User, access_token: str) -> Client:
    """Returns a Supabase client scoped to the authenticated user with RLS."""
    # Crear cliente con token del usuario (respeta RLS)
    user_client = create_client(
        supabase_url=SUPABASE_URL,
        supabase_key=SUPABASE_ANON_KEY,  # Usar anon key
        options={
            'headers': {
                'Authorization': f'Bearer {access_token}'  # Token del usuario
            }
        }
    )
    return user_client

# Actualizar dependency
async def get_user_scoped_supabase(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Client:
    """Dependency que retorna cliente Supabase con RLS."""
    token = credentials.credentials
    user_response = supabase.auth.get_user(token)
    if not user_response or not user_response.user:
        raise HTTPException(status_code=401, detail="Invalid token")

    return get_supabase_client_for_user(user_response.user, token)
```

**Configurar RLS en Supabase**:
```sql
-- Habilitar RLS en translation_jobs
ALTER TABLE translation_jobs ENABLE ROW LEVEL SECURITY;

-- Política: usuarios solo pueden ver sus propios jobs
CREATE POLICY "Users can view own jobs"
  ON translation_jobs
  FOR SELECT
  USING (auth.uid() = user_id);

-- Política: usuarios solo pueden insertar con su propio user_id
CREATE POLICY "Users can insert own jobs"
  ON translation_jobs
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Política: usuarios solo pueden actualizar sus propios jobs
CREATE POLICY "Users can update own jobs"
  ON translation_jobs
  FOR UPDATE
  USING (auth.uid() = user_id);
```

---

## 3. Vulnerabilidades de Alta Severidad (HIGH)

### HIGH-01: Falta de Rate Limiting en Endpoints Críticos

**Severidad**: HIGH
**CVSS Score**: 7.5
**CWE**: CWE-770 - Allocation of Resources Without Limits or Throttling

**Descripción**:
No hay rate limiting implementado en ningún endpoint. Esto permite ataques de fuerza bruta, abuso de recursos y DDoS.

**Endpoints afectados**:
- `/api/v1/auth/signup` - Creación masiva de cuentas
- `/api/v1/auth/login` - Fuerza bruta de contraseñas
- `/api/v1/upload` - Agotamiento de storage/procesamiento
- `/api/v1/download/{job_id}/{language}` - Abuso de ancho de banda

**Recomendación**:
```python
# Instalar slowapi
# pip install slowapi

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Aplicar a endpoints
@router.post("/login")
@limiter.limit("5/minute")  # Máximo 5 intentos por minuto
async def login(request: Request, data: LoginRequest):
    # ...

@router.post("/upload")
@limiter.limit("10/hour")  # Máximo 10 uploads por hora
async def upload_scorm(request: Request, file: UploadFile, user: User = Depends(get_current_user)):
    # ...
```

**Alternativa con middleware**:
```python
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis

@app.on_event("startup")
async def startup():
    redis_conn = await redis.from_url("redis://localhost", encoding="utf-8")
    await FastAPILimiter.init(redis_conn)

@router.post("/login", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def login(data: LoginRequest):
    # ...
```

---

### HIGH-02: Validación Insuficiente de Tipos MIME en Upload

**Archivo**: `/backend/app/api/v1/upload.py:32-53`
**Severidad**: HIGH
**CVSS Score**: 7.3
**CWE**: CWE-434 - Unrestricted Upload of File with Dangerous Type

**Descripción**:
La validación de archivos solo verifica la extensión `.zip` pero NO valida el tipo MIME real ni el contenido del archivo. Permite subir archivos maliciosos renombrados.

**Código vulnerable**:
```python
def validate_file_extension(filename: str) -> bool:
    """Validar que el archivo tenga extensión permitida (.zip)."""
    file_ext = Path(filename).suffix.lower()
    return file_ext in settings.ALLOWED_EXTENSIONS  # Solo verifica extensión
```

**Explotación**:
```bash
# Crear archivo malicioso y renombrarlo
echo "<?php system($_GET['cmd']); ?>" > shell.php
mv shell.php malicious.zip
# Subirlo a través del endpoint
curl -F "file=@malicious.zip" -F "target_languages=es,fr" \
  -H "Authorization: Bearer TOKEN" http://api/upload
```

**Recomendación**:
```python
import magic  # pip install python-magic

def validate_file_type(file: UploadFile) -> tuple[bool, str]:
    """
    Validar tipo MIME real del archivo.

    Returns:
        (is_valid, mime_type)
    """
    # Leer primeros bytes para detectar tipo real
    file_header = file.file.read(2048)
    file.file.seek(0)

    # Detectar tipo MIME real
    mime = magic.Magic(mime=True)
    detected_type = mime.from_buffer(file_header)

    # Validar que sea ZIP
    allowed_types = [
        "application/zip",
        "application/x-zip-compressed",
    ]

    is_valid = detected_type in allowed_types
    return is_valid, detected_type

def validate_zip_integrity(file_content: bytes) -> bool:
    """Validar que el ZIP no esté corrupto y no contenga archivos peligrosos."""
    try:
        with zipfile.ZipFile(BytesIO(file_content)) as zf:
            # Verificar integridad
            bad_file = zf.testzip()
            if bad_file is not None:
                return False

            # Verificar que no haya path traversal
            for filename in zf.namelist():
                if filename.startswith('/') or '..' in filename:
                    logger.warning(f"Malicious path detected in ZIP: {filename}")
                    return False

            # Verificar extensiones peligrosas
            dangerous_extensions = ['.exe', '.dll', '.sh', '.bat', '.cmd', '.vbs', '.ps1']
            for filename in zf.namelist():
                if any(filename.lower().endswith(ext) for ext in dangerous_extensions):
                    logger.warning(f"Dangerous file detected in ZIP: {filename}")
                    return False

        return True
    except zipfile.BadZipFile:
        return False

# Aplicar en endpoint de upload
@router.post("/upload")
async def upload_scorm(file: UploadFile, ...):
    # 1. Validar extensión
    if not validate_file_extension(file.filename):
        raise HTTPException(400, detail="Invalid extension")

    # 2. Validar tipo MIME real
    is_valid_type, detected_type = validate_file_type(file)
    if not is_valid_type:
        raise HTTPException(
            400,
            detail=f"Invalid file type. Detected: {detected_type}, expected: application/zip"
        )

    # 3. Leer contenido y validar integridad
    file_content = await file.read()
    if not validate_zip_integrity(file_content):
        raise HTTPException(400, detail="Invalid or malicious ZIP file")

    # Continuar con procesamiento...
```

---

### HIGH-03: Exposición de Información Sensible en Mensajes de Error

**Archivo**: Múltiples archivos en `/backend/app/api/v1/`
**Severidad**: HIGH
**CVSS Score**: 6.5
**CWE**: CWE-209 - Information Exposure Through Error Message

**Descripción**:
Los mensajes de error exponen información técnica que puede ayudar a atacantes a mapear la infraestructura y planear ataques.

**Ejemplos vulnerables**:
```python
# auth.py:82
raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail=f"Could not validate credentials: {str(e)}",  # Expone detalles internos
)

# upload.py:239
raise HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail={
        "error": "Failed to process upload",
        "details": str(e),  # Expone stack trace completo
    },
)

# jobs.py:94
detail={
    "error": "Failed to list jobs",
    "details": str(e),  # Expone detalles de DB
}
```

**Información expuesta**:
- Paths internos del servidor
- Versiones de librerías
- Estructura de base de datos
- Stack traces completos
- Nombres de tablas y columnas

**Recomendación**:
```python
import logging

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Centralizar manejo de errores."""

    @staticmethod
    def handle_authentication_error(e: Exception, user_identifier: str = "unknown") -> HTTPException:
        """Manejar errores de autenticación de forma segura."""
        # Log completo para debugging (solo servidor)
        logger.error(f"Authentication failed for {user_identifier}: {str(e)}", exc_info=True)

        # Mensaje genérico para cliente
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",  # Genérico
            headers={"WWW-Authenticate": "Bearer"},
        )

    @staticmethod
    def handle_internal_error(e: Exception, operation: str) -> HTTPException:
        """Manejar errores internos de forma segura."""
        # Log completo para debugging
        logger.error(f"{operation} failed: {str(e)}", exc_info=True)

        # Mensaje genérico para cliente
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{operation} failed. Please try again later.",  # Sin detalles técnicos
        )

# Usar en endpoints
@router.post("/login")
async def login(request: LoginRequest):
    try:
        response = supabase.auth.sign_in_with_password(...)
        # ...
    except Exception as e:
        raise ErrorHandler.handle_authentication_error(e, request.email)

@router.post("/upload")
async def upload_scorm(file: UploadFile, user: User):
    try:
        # Procesamiento...
    except Exception as e:
        raise ErrorHandler.handle_internal_error(e, "File upload")
```

**Configurar logging seguro**:
```python
# main.py
import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
        },
        "detailed": {
            "format": "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": "/var/log/traductor-scorm/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
        },
    },
    "loggers": {
        "app": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
            "propagate": False,
        },
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
```

---

### HIGH-04: Falta de Validación de Password Strength

**Archivo**: `/backend/app/api/v1/auth.py:19-34`
**Severidad**: HIGH
**CVSS Score**: 6.8
**CWE**: CWE-521 - Weak Password Requirements

**Descripción**:
El endpoint de signup NO valida la fortaleza de la contraseña. Permite contraseñas débiles como "12345678" o "password".

**Código vulnerable**:
```python
class SignupRequest(BaseModel):
    email: EmailStr
    password: str  # Sin validación de fortaleza
```

**Recomendación**:
```python
from pydantic import field_validator
import re

class SignupRequest(BaseModel):
    """User signup request with password validation."""

    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Validar fortaleza de contraseña.

        Requisitos:
        - Mínimo 8 caracteres
        - Al menos 1 mayúscula
        - Al menos 1 minúscula
        - Al menos 1 número
        - Al menos 1 carácter especial
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")

        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")

        # Verificar contra lista de contraseñas comunes
        common_passwords = [
            "password", "12345678", "qwerty", "abc123", "password123",
            "admin", "letmein", "welcome", "monkey", "dragon"
        ]
        if v.lower() in common_passwords:
            raise ValueError("Password is too common. Please choose a stronger password")

        return v
```

**Alternativa con librería especializada**:
```python
# pip install password-strength

from password_strength import PasswordPolicy

password_policy = PasswordPolicy.from_names(
    length=8,        # Mínimo 8 caracteres
    uppercase=1,     # Al menos 1 mayúscula
    lowercase=1,     # Al menos 1 minúscula
    numbers=1,       # Al menos 1 número
    special=1,       # Al menos 1 carácter especial
    nonletters=1,    # Al menos 1 no-letra
)

class SignupRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        errors = password_policy.test(v)
        if errors:
            error_messages = [str(error) for error in errors]
            raise ValueError(f"Password requirements not met: {', '.join(error_messages)}")
        return v
```

---

### HIGH-05: Signed URLs con Expiración Excesiva

**Archivo**: `/backend/app/api/v1/download.py:143-148`
**Severidad**: HIGH
**CVSS Score**: 6.5
**CWE**: CWE-613 - Insufficient Session Expiration

**Descripción**:
Las URLs firmadas para descarga tienen una expiración de 7 días (604,800 segundos), lo cual es excesivo y permite compartir enlaces de forma no autorizada.

**Código vulnerable**:
```python
signed_url = await storage_service.get_signed_url(
    file_path=download_url,
    expires_in=7 * 24 * 3600,  # 7 días - DEMASIADO TIEMPO
)
```

**Impacto**:
- Usuario puede compartir URL de descarga con terceros
- URLs permanecen válidas incluso después de revocar acceso del usuario
- Dificultad para auditar quién descargó qué archivo

**Recomendación**:
```python
# Reducir expiración a 1 hora (3600 segundos)
signed_url = await storage_service.get_signed_url(
    file_path=download_url,
    expires_in=3600,  # 1 hora - Más seguro
)

# Alternativamente, implementar descarga directa con validación:
@router.get("/download/{job_id}/{language}")
async def download_translated_scorm(
    job_id: UUID,
    language: str,
    user: User = Depends(get_current_user),
):
    """Download con validación en tiempo real (sin signed URL)."""
    # Validar ownership
    job = await job_service.get_job(job_id)
    if job.user_id != user.id:
        raise HTTPException(403, detail="Forbidden")

    # Descargar archivo desde storage
    file_content = await storage_service.download_file(job.download_urls[language])

    # Retornar como StreamingResponse
    return StreamingResponse(
        BytesIO(file_content),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{job.original_filename}"'
        }
    )
```

---

## 4. Vulnerabilidades de Severidad Media (MEDIUM)

### MED-01: CORS Demasiado Permisivo

**Archivo**: `/backend/app/main.py:24-31`
**Severidad**: MEDIUM
**CVSS Score**: 5.3
**CWE**: CWE-942 - Overly Permissive Cross-domain Whitelist

**Descripción**:
La configuración CORS permite todos los métodos y todos los headers sin restricciones.

**Código vulnerable**:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos
    allow_headers=["*"],  # Permite todos los headers
)
```

**Recomendación**:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # Ya está OK (lista específica)
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Lista específica
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "User-Agent",
        "DNT",
        "Cache-Control",
        "X-Requested-With",
    ],  # Lista específica
    max_age=600,  # Cache preflight por 10 minutos
)
```

---

### MED-02: Documentación de API Expuesta en Producción

**Archivo**: `/backend/app/main.py:16-22`
**Severidad**: MEDIUM
**CVSS Score**: 5.0
**CWE**: CWE-200 - Exposure of Sensitive Information

**Descripción**:
Swagger UI (`/docs`) y ReDoc (`/redoc`) están habilitados sin restricciones, exponiendo la estructura completa de la API.

**Código vulnerable**:
```python
app = FastAPI(
    title="Traductor SCORM API",
    description="API REST para traducir paquetes SCORM a múltiples idiomas usando IA",
    version="0.1.0",
    docs_url="/docs",  # Accesible por cualquiera
    redoc_url="/redoc",  # Accesible por cualquiera
)
```

**Recomendación**:
```python
from app.core.config import settings

# Deshabilitar en producción
docs_url = "/docs" if settings.ENVIRONMENT == "development" else None
redoc_url = "/redoc" if settings.ENVIRONMENT == "development" else None

app = FastAPI(
    title="Traductor SCORM API",
    description="API REST para traducir paquetes SCORM a múltiples idiomas usando IA",
    version="0.1.0",
    docs_url=docs_url,
    redoc_url=redoc_url,
)

# Alternativamente, proteger con autenticación
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi

# Deshabilitar docs automáticos
app = FastAPI(docs_url=None, redoc_url=None)

@app.get("/docs", include_in_schema=False)
async def get_documentation(user: User = Depends(get_current_user)):
    """Docs protegidos con autenticación."""
    return get_swagger_ui_html(openapi_url="/openapi.json", title="Docs")

@app.get("/openapi.json", include_in_schema=False)
async def get_openapi_endpoint(user: User = Depends(get_current_user)):
    """OpenAPI schema protegido."""
    return get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
```

---

### MED-03: Falta de Content Security Policy y Security Headers

**Archivo**: `/backend/app/main.py`
**Severidad**: MEDIUM
**CVSS Score**: 4.7
**CWE**: CWE-1021 - Improper Restriction of Rendered UI Layers

**Descripción**:
No hay headers de seguridad configurados (CSP, X-Frame-Options, X-Content-Type-Options, etc.).

**Recomendación**:
```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware para agregar headers de seguridad."""

    async def dispatch(self, request, call_next):
        response = await call_next(request)

        # Prevenir clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Prevenir MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Habilitar XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https://xuezjcfmnghfzvujuhtj.supabase.co; "
            "frame-ancestors 'none';"
        )

        # HSTS (solo en HTTPS)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions policy
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        return response

# Aplicar middleware
app.add_middleware(SecurityHeadersMiddleware)

# Trusted hosts (prevenir Host header attacks)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "yourdomain.com", "*.yourdomain.com"]
)
```

---

### MED-04: Logging Insuficiente de Eventos de Seguridad

**Archivo**: Múltiples archivos
**Severidad**: MEDIUM
**CVSS Score**: 4.3
**CWE**: CWE-778 - Insufficient Logging

**Descripción**:
No hay logging consistente de eventos de seguridad críticos (intentos de login fallidos, accesos no autorizados, etc.).

**Recomendación**:
```python
import logging
from datetime import datetime

# Configurar logger de seguridad
security_logger = logging.getLogger("security")
security_logger.setLevel(logging.INFO)

# Handler para archivo de logs de seguridad
security_handler = logging.FileHandler("/var/log/traductor-scorm/security.log")
security_handler.setFormatter(
    logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
)
security_logger.addHandler(security_handler)

# Eventos a loggear
class SecurityEvent:
    @staticmethod
    def log_failed_login(email: str, ip: str, reason: str):
        security_logger.warning(
            f"Failed login attempt | Email: {email} | IP: {ip} | Reason: {reason}"
        )

    @staticmethod
    def log_successful_login(user_id: str, email: str, ip: str):
        security_logger.info(
            f"Successful login | User: {user_id} | Email: {email} | IP: {ip}"
        )

    @staticmethod
    def log_unauthorized_access(user_id: str, resource: str, ip: str):
        security_logger.warning(
            f"Unauthorized access attempt | User: {user_id} | Resource: {resource} | IP: {ip}"
        )

    @staticmethod
    def log_file_upload(user_id: str, filename: str, size_mb: float):
        security_logger.info(
            f"File upload | User: {user_id} | File: {filename} | Size: {size_mb}MB"
        )

# Usar en endpoints
@router.post("/login")
async def login(request: Request, data: LoginRequest):
    try:
        response = supabase.auth.sign_in_with_password(...)
        SecurityEvent.log_successful_login(
            response.user.id,
            response.user.email,
            request.client.host
        )
        return AuthResponse(...)
    except Exception as e:
        SecurityEvent.log_failed_login(
            data.email,
            request.client.host,
            str(e)
        )
        raise HTTPException(401, detail="Invalid credentials")
```

---

## 5. Vulnerabilidades de Baja Severidad (LOW)

### LOW-01: Falta de Input Sanitization en Query Parameters

**Archivo**: `/backend/app/api/v1/jobs.py:35-40`
**Severidad**: LOW
**CVSS Score**: 3.1

**Descripción**:
Los parámetros de query no tienen validación de rangos ni sanitización.

**Recomendación**:
```python
from fastapi import Query

@router.get("/jobs")
async def list_jobs(
    limit: int = Query(default=20, ge=1, le=100),  # Entre 1 y 100
    offset: int = Query(default=0, ge=0),  # >= 0
    status_filter: Optional[str] = Query(default=None, regex="^(uploaded|translating|completed|failed)$"),
    user: User = Depends(get_current_user),
):
    # ...
```

---

### LOW-02: Falta de Versionado Explícito en Dependencias

**Archivo**: `/backend/pyproject.toml:16-49`
**Severidad**: LOW
**CVSS Score**: 2.8

**Descripción**:
Algunas dependencias usan versiones con `>=` lo cual puede introducir breaking changes.

**Recomendación**:
```toml
# Usar versiones pinned o con límite superior
dependencies = [
    "fastapi>=0.104.0,<0.105.0",  # Prevenir breaking changes
    "uvicorn[standard]>=0.24.0,<0.25.0",
    "pydantic>=2.5.0,<3.0.0",
    # ...
]
```

---

## 6. Recomendaciones Informativas (INFO)

### INFO-01: Implementar Health Check Detallado

**Recomendación**:
```python
@app.get("/health")
async def health_check():
    """Health check con verificación de dependencias."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "traductor-scorm-api",
        "version": "0.1.0",
        "checks": {}
    }

    # Check database
    try:
        supabase.table("translation_jobs").select("id").limit(1).execute()
        health_status["checks"]["database"] = "ok"
    except Exception as e:
        health_status["checks"]["database"] = "error"
        health_status["status"] = "degraded"

    # Check storage
    try:
        supabase.storage.list_buckets()
        health_status["checks"]["storage"] = "ok"
    except Exception as e:
        health_status["checks"]["storage"] = "error"
        health_status["status"] = "degraded"

    # Check Redis (si está configurado)
    try:
        redis_client.ping()
        health_status["checks"]["redis"] = "ok"
    except:
        health_status["checks"]["redis"] = "not configured"

    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)
```

---

## 7. Checklist OWASP API Security Top 10 (2023)

| ID | Vulnerabilidad | Estado | Severidad Detectada | Acción Requerida |
|----|----------------|--------|---------------------|------------------|
| API1:2023 | Broken Object Level Authorization (BOLA/IDOR) | VULNERABLE | CRITICAL | Implementar validación de ownership en todos los endpoints |
| API2:2023 | Broken Authentication | VULNERABLE | HIGH | Fortalecer validación de contraseñas, implementar rate limiting |
| API3:2023 | Broken Object Property Level Authorization | PARCIAL | MEDIUM | Validar que usuarios no puedan modificar campos no autorizados |
| API4:2023 | Unrestricted Resource Consumption | VULNERABLE | HIGH | Implementar rate limiting, limitar tamaño de archivos |
| API5:2023 | Broken Function Level Authorization | VULNERABLE | CRITICAL | Implementar RLS real, validar roles en endpoints |
| API6:2023 | Unrestricted Access to Sensitive Business Flows | VULNERABLE | MEDIUM | Implementar rate limiting en flujos críticos (upload, download) |
| API7:2023 | Server Side Request Forgery (SSRF) | NO APLICA | N/A | No hay endpoints que hagan requests externos basados en input |
| API8:2023 | Security Misconfiguration | VULNERABLE | MEDIUM | Deshabilitar docs en prod, configurar headers de seguridad |
| API9:2023 | Improper Inventory Management | PARCIAL | LOW | Documentar todos los endpoints, deshabilitar endpoints deprecados |
| API10:2023 | Unsafe Consumption of APIs | NO APLICA | N/A | No se consumen APIs externas en endpoints públicos |

**Score OWASP**: 6/10 vulnerables - Requiere atención inmediata

---

## 8. Plan de Remediación Priorizado

### Fase 1: Críticas (Semana 1)

1. **CRIT-01**: Agregar validación de ownership en `/jobs/{job_id}/details`
2. **CRIT-02**: Agregar autenticación y validación en `/download/{job_id}/all`
3. **CRIT-03**: Implementar RLS real en Supabase

**Esfuerzo estimado**: 3 días
**Responsable**: Backend Team Lead

### Fase 2: Altas (Semana 2)

4. **HIGH-01**: Implementar rate limiting global
5. **HIGH-02**: Mejorar validación de archivos (MIME + contenido)
6. **HIGH-03**: Implementar manejo de errores seguro
7. **HIGH-04**: Agregar validación de password strength
8. **HIGH-05**: Reducir expiración de signed URLs

**Esfuerzo estimado**: 4 días
**Responsable**: Backend Team

### Fase 3: Medias (Semana 3)

9. **MED-01**: Configurar CORS restrictivo
10. **MED-02**: Proteger/deshabilitar docs en producción
11. **MED-03**: Implementar security headers middleware
12. **MED-04**: Configurar logging de seguridad

**Esfuerzo estimado**: 2 días
**Responsable**: DevOps + Backend

### Fase 4: Bajas e Informativas (Semana 4)

13. **LOW-01**: Validar query parameters
14. **LOW-02**: Pinear versiones de dependencias
15. **INFO-01**: Health check detallado

**Esfuerzo estimado**: 1 día
**Responsable**: Backend Team

---

## 9. Código de Ejemplo: API Endpoint Seguro

Ejemplo de endpoint completamente seguro implementando todas las recomendaciones:

```python
"""
Endpoint seguro para obtener detalles de job.
Implementa todas las mejores prácticas de seguridad.
"""

from fastapi import APIRouter, HTTPException, status, Path, Depends, Request
from fastapi_limiter.depends import RateLimiter
from uuid import UUID
import logging

from app.core.auth import get_current_user, User
from app.models.translation import TranslationJobResponse, ErrorResponse
from app.services.job_service import job_service
from app.utils.error_handler import ErrorHandler
from app.utils.security_logger import SecurityEvent

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/jobs/{job_id}",
    response_model=TranslationJobResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Job not found"},
        429: {"model": ErrorResponse, "description": "Too many requests"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    dependencies=[Depends(RateLimiter(times=60, seconds=60))],  # 60 req/min
)
async def get_job_details(
    request: Request,
    job_id: UUID = Path(
        ...,
        description="Unique identifier of the translation job",
        example="123e4567-e89b-12d3-a456-426614174000"
    ),
    user: User = Depends(get_current_user),
):
    """
    Get full details of a translation job.

    Security measures:
    - Requires authentication (Bearer token)
    - Validates job ownership
    - Rate limited to 60 requests per minute
    - Logs security events
    - Returns generic error messages
    """
    try:
        # Log access attempt
        logger.info(
            f"Job details request | User: {user.id} | Job: {job_id} | IP: {request.client.host}"
        )

        # Fetch job from database
        job = await job_service.get_job(job_id)

        # Validate job exists
        if not job:
            logger.warning(f"Job not found | Job: {job_id} | User: {user.id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"  # Generic message
            )

        # CRITICAL: Validate ownership
        if job.user_id and str(job.user_id) != user.id:
            # Log unauthorized access attempt
            SecurityEvent.log_unauthorized_access(
                user_id=user.id,
                resource=f"job:{job_id}",
                ip=request.client.host,
                actual_owner=str(job.user_id)
            )

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"  # Generic message, no details
            )

        # Log successful access
        SecurityEvent.log_resource_access(
            user_id=user.id,
            resource=f"job:{job_id}",
            action="read",
            ip=request.client.host
        )

        return job

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except Exception as e:
        # Handle unexpected errors securely
        logger.error(
            f"Unexpected error fetching job | Job: {job_id} | User: {user.id} | Error: {str(e)}",
            exc_info=True  # Full stack trace in logs only
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching job details"  # Generic
        )
```

---

## 10. Testing de Seguridad

### Casos de Prueba Recomendados

```python
# tests/security/test_api_security.py

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

class TestSecurityVulnerabilities:
    """Test cases for security vulnerabilities."""

    def test_idor_job_details_unauthorized(self, client: TestClient, test_users):
        """Test IDOR vulnerability in job details endpoint."""
        # User A creates a job
        user_a_token = test_users["user_a"]["token"]
        job_response = client.post(
            "/api/v1/upload",
            headers={"Authorization": f"Bearer {user_a_token}"},
            files={"file": ("test.zip", b"fake zip content")},
            data={"target_languages": "es,fr"}
        )
        job_id = job_response.json()["job_id"]

        # User B tries to access User A's job
        user_b_token = test_users["user_b"]["token"]
        response = client.get(
            f"/api/v1/jobs/{job_id}/details",
            headers={"Authorization": f"Bearer {user_b_token}"}
        )

        # Should return 403 Forbidden
        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]

    def test_rate_limiting_login(self, client: TestClient):
        """Test rate limiting on login endpoint."""
        # Attempt 10 logins in rapid succession
        for _ in range(10):
            response = client.post(
                "/api/v1/auth/login",
                json={"email": "test@example.com", "password": "wrongpassword"}
            )

        # After rate limit, should return 429
        assert response.status_code == 429

    def test_weak_password_rejected(self, client: TestClient):
        """Test that weak passwords are rejected."""
        response = client.post(
            "/api/v1/auth/signup",
            json={"email": "test@example.com", "password": "12345678"}
        )

        assert response.status_code == 400
        assert "password" in response.json()["detail"].lower()

    def test_malicious_file_upload_rejected(self, client: TestClient, auth_token):
        """Test that malicious files are rejected."""
        # Create fake ZIP with PHP shell
        malicious_content = b"<?php system($_GET['cmd']); ?>"

        response = client.post(
            "/api/v1/upload",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={"file": ("malicious.zip", malicious_content)},
            data={"target_languages": "es"}
        )

        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()
```

---

## 11. Herramientas de Seguridad Recomendadas

### Análisis Estático
- **Bandit**: Escaneo de vulnerabilidades en código Python
  ```bash
  pip install bandit
  bandit -r app/ -f json -o security-report.json
  ```

- **Safety**: Verificación de dependencias vulnerables
  ```bash
  pip install safety
  safety check --json
  ```

### Análisis Dinámico
- **OWASP ZAP**: Proxy de interceptación y escaneo de vulnerabilidades
- **Burp Suite**: Testing manual de API
- **Postman**: Testing de endpoints con colecciones de seguridad

### Monitoreo Continuo
- **Sentry**: Monitoreo de errores y excepciones
- **Datadog**: Monitoreo de métricas de seguridad
- **ELK Stack**: Agregación y análisis de logs

---

## 12. Contacto y Escalación

**Para vulnerabilidades críticas**:
- Email: security@traductor-scorm.com
- Tiempo de respuesta: < 4 horas

**Para consultas de seguridad**:
- Email: devops@traductor-scorm.com
- Tiempo de respuesta: < 24 horas

---

## Anexos

### Anexo A: Referencias

- OWASP API Security Top 10: https://owasp.org/www-project-api-security/
- FastAPI Security: https://fastapi.tiangolo.com/tutorial/security/
- Supabase RLS: https://supabase.com/docs/guides/auth/row-level-security
- CWE Top 25: https://cwe.mitre.org/top25/

### Anexo B: Changelog

| Fecha | Versión | Cambios |
|-------|---------|---------|
| 2025-12-16 | 1.0 | Auditoría inicial completa |

---

**Firma Digital**: API Security Audit Specialist
**Fecha de Emisión**: 2025-12-16
**Próxima Auditoría**: 2025-03-16 (3 meses)
