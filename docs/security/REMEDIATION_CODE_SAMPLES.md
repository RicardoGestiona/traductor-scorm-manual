# Código de Remediación - Vulnerabilidades API

Este documento contiene código listo para implementar que resuelve las vulnerabilidades identificadas en el API Security Audit Report.

---

## 1. Implementación de RLS (Row-Level Security) Real

### 1.1 SQL: Configuración en Supabase

```sql
-- backend/database/supabase/rls_policies.sql

-- Habilitar RLS en translation_jobs
ALTER TABLE translation_jobs ENABLE ROW LEVEL SECURITY;

-- Política: Usuarios solo pueden ver sus propios jobs
CREATE POLICY "Users can view own translation jobs"
  ON translation_jobs
  FOR SELECT
  USING (
    auth.uid() = user_id OR
    user_id IS NULL  -- Jobs sin usuario (para backward compatibility)
  );

-- Política: Usuarios solo pueden insertar jobs con su propio user_id
CREATE POLICY "Users can insert own translation jobs"
  ON translation_jobs
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Política: Usuarios solo pueden actualizar sus propios jobs
CREATE POLICY "Users can update own translation jobs"
  ON translation_jobs
  FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Política: Usuarios solo pueden eliminar sus propios jobs
CREATE POLICY "Users can delete own translation jobs"
  ON translation_jobs
  FOR DELETE
  USING (auth.uid() = user_id);

-- Opcional: Service role puede hacer todo (para tareas en background)
CREATE POLICY "Service role has full access"
  ON translation_jobs
  FOR ALL
  USING (current_setting('request.jwt.claims', true)::json->>'role' = 'service_role');
```

### 1.2 Python: Cliente Supabase con RLS

```python
# backend/app/core/auth.py

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from app.core.config import settings

security = HTTPBearer()

class User:
    """Authenticated user from Supabase."""

    def __init__(self, user_data: dict):
        self.id: str = user_data.get("id")
        self.email: str = user_data.get("email")
        self.role: str = user_data.get("role", "authenticated")
        self.metadata: dict = user_data.get("user_metadata", {})


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Dependency to get current authenticated user.

    Returns User object with validated JWT token.
    """
    token = credentials.credentials

    try:
        # Crear cliente con service role para validar token
        admin_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY
        )

        # Validar token
        user_response = admin_client.auth.get_user(token)

        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return User(user_response.user.model_dump())

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_user_scoped_supabase(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Client:
    """
    Dependency que retorna un cliente Supabase con el token del usuario.

    Este cliente respeta RLS automáticamente porque usa el token del usuario
    en lugar del service role key.

    Usage:
    ```python
    @router.get("/jobs")
    async def list_jobs(db: Client = Depends(get_user_scoped_supabase)):
        # Este query automáticamente filtra por user_id gracias a RLS
        response = db.table("translation_jobs").select("*").execute()
        return response.data
    ```
    """
    token = credentials.credentials

    try:
        # Crear cliente con ANON KEY (no service role)
        user_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY,  # Usar anon key
        )

        # Configurar token del usuario en el header
        user_client.auth.set_session(token, None)

        return user_client

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not create authenticated session",
        )


def get_service_supabase() -> Client:
    """
    Dependency para cliente Supabase con service role (bypassa RLS).

    USAR SOLO EN:
    - Tareas de background (Celery)
    - Operaciones administrativas explícitas
    - Endpoints internos (no públicos)

    NUNCA USAR EN:
    - Endpoints que retornan datos de usuarios
    - Operaciones donde el user_id viene del request
    """
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_ROLE_KEY
    )
```

### 1.3 Actualizar Endpoints para Usar RLS

```python
# backend/app/api/v1/jobs.py

from supabase import Client
from app.core.auth import get_current_user, get_user_scoped_supabase, User

@router.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status_filter: Optional[str] = Query(default=None),
    user: User = Depends(get_current_user),
    db: Client = Depends(get_user_scoped_supabase),  # RLS automático
):
    """
    List translation jobs for authenticated user.

    Con RLS habilitado, el query automáticamente filtra por user_id.
    NO ES NECESARIO agregar .eq("user_id", user.id) manualmente.
    """
    try:
        query = db.table("translation_jobs").select("*")

        # Aplicar filtro de status si se proporciona
        if status_filter:
            query = query.eq("status", status_filter)

        # Ordenar y paginar
        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

        response = query.execute()

        # RLS garantiza que solo se retornan jobs del usuario actual
        jobs = [
            TranslationJobResponse(
                id=UUID(job["id"]),
                user_id=UUID(job["user_id"]) if job.get("user_id") else None,
                original_filename=job["original_filename"],
                source_language=job["source_language"],
                target_languages=job["target_languages"],
                status=TranslationStatus(job["status"]),
                progress_percentage=job.get("progress_percentage", 0),
                created_at=datetime.fromisoformat(job["created_at"]),
                completed_at=(
                    datetime.fromisoformat(job["completed_at"])
                    if job.get("completed_at")
                    else None
                ),
                download_urls=job.get("download_urls", {}),
                error_message=job.get("error_message"),
            )
            for job in response.data
        ]

        # Contar total (también respeta RLS)
        count_response = db.table("translation_jobs").select("id", count="exact").execute()
        total = count_response.count or 0

        return JobListResponse(
            jobs=jobs,
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + len(jobs)) < total,
        )

    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to list jobs"
        )


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: UUID = Path(...),
    user: User = Depends(get_current_user),
    db: Client = Depends(get_user_scoped_supabase),
):
    """
    Get job status with automatic RLS validation.

    Si el job no pertenece al usuario, Supabase retorna 404 automáticamente.
    """
    try:
        response = (
            db.table("translation_jobs")
            .select("*")
            .eq("id", str(job_id))
            .single()
            .execute()
        )

        if not response.data:
            # RLS bloqueó el acceso o el job no existe
            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )

        job_data = response.data

        return JobStatusResponse(
            job_id=UUID(job_data["id"]),
            status=TranslationStatus(job_data["status"]),
            progress_percentage=job_data.get("progress_percentage", 0),
            current_step=_get_current_step_description(job_data),
            download_urls=job_data.get("download_urls", {}),
            error_message=job_data.get("error_message"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {e}")
        raise HTTPException(500, detail="Failed to get job status")
```

---

## 2. Rate Limiting Completo

```python
# backend/app/core/rate_limiter.py

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import FastAPI, Request, Response
from typing import Callable
import logging

logger = logging.getLogger(__name__)

# Crear limiter global
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],  # Límite global por defecto
    storage_uri="redis://localhost:6379/1",  # Usar Redis para persistencia
)


def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler para rate limit exceeded.

    Retorna respuesta JSON en lugar de texto plano.
    """
    logger.warning(
        f"Rate limit exceeded | IP: {request.client.host} | "
        f"Path: {request.url.path} | Limit: {exc.detail}"
    )

    return Response(
        content={
            "error": "Rate limit exceeded",
            "detail": f"Too many requests. {exc.detail}",
            "retry_after": "60 seconds"
        },
        status_code=429,
        headers={
            "Retry-After": "60",
            "X-RateLimit-Limit": str(exc.detail),
        }
    )


def setup_rate_limiting(app: FastAPI) -> None:
    """
    Configurar rate limiting en la aplicación.

    Args:
        app: FastAPI application instance
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)
    app.add_middleware(SlowAPIMiddleware)


# Decoradores personalizados por tipo de endpoint
class RateLimits:
    """Límites de rate predefinidos para diferentes tipos de endpoints."""

    # Autenticación (más estricto)
    AUTH_LOGIN = "5/minute"        # 5 intentos de login por minuto
    AUTH_SIGNUP = "3/hour"         # 3 registros por hora
    AUTH_REFRESH = "10/minute"     # 10 refresh de token por minuto

    # Upload (costoso en recursos)
    UPLOAD_FILE = "5/hour"         # 5 uploads por hora
    UPLOAD_FILE_PREMIUM = "20/hour"  # 20 uploads para usuarios premium

    # Downloads (ancho de banda)
    DOWNLOAD_SINGLE = "30/hour"    # 30 descargas individuales por hora
    DOWNLOAD_ALL = "10/hour"       # 10 descargas de paquetes completos por hora

    # Consultas (menos estricto)
    QUERY_LIST = "60/minute"       # 60 consultas de listas por minuto
    QUERY_DETAIL = "120/minute"    # 120 consultas de detalles por minuto

    # Healthcheck (muy permisivo)
    HEALTHCHECK = "300/minute"     # 300 healthchecks por minuto
```

```python
# backend/app/main.py

from app.core.rate_limiter import setup_rate_limiting, limiter

app = FastAPI(...)

# Configurar rate limiting
setup_rate_limiting(app)

@app.get("/health")
@limiter.limit("300/minute")
async def health_check(request: Request):
    return {"status": "healthy"}
```

```python
# backend/app/api/v1/auth.py

from app.core.rate_limiter import limiter, RateLimits
from fastapi import Request

@router.post("/login")
@limiter.limit(RateLimits.AUTH_LOGIN)
async def login(request: Request, data: LoginRequest):
    """Login con rate limiting de 5 intentos por minuto."""
    # ...

@router.post("/signup")
@limiter.limit(RateLimits.AUTH_SIGNUP)
async def signup(request: Request, data: SignupRequest):
    """Signup con rate limiting de 3 registros por hora."""
    # ...
```

```python
# backend/app/api/v1/upload.py

from app.core.rate_limiter import limiter, RateLimits

@router.post("/upload")
@limiter.limit(RateLimits.UPLOAD_FILE)
async def upload_scorm(
    request: Request,
    file: UploadFile,
    user: User = Depends(get_current_user)
):
    """Upload con rate limiting de 5 archivos por hora."""
    # ...
```

---

## 3. Validación Avanzada de Archivos

```python
# backend/app/utils/file_validator.py

import magic
import zipfile
from io import BytesIO
from typing import Tuple, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class FileValidator:
    """Validador de seguridad para archivos subidos."""

    # Tipos MIME permitidos
    ALLOWED_MIME_TYPES = [
        "application/zip",
        "application/x-zip-compressed",
        "application/x-zip",
    ]

    # Extensiones peligrosas que no deben estar en el ZIP
    DANGEROUS_EXTENSIONS = [
        ".exe", ".dll", ".so", ".dylib",  # Ejecutables
        ".sh", ".bat", ".cmd", ".ps1",    # Scripts
        ".vbs", ".js", ".jar",            # Scripts/ejecutables
        ".app", ".deb", ".rpm",           # Paquetes
        ".scr", ".pif", ".com",           # Ejecutables Windows
    ]

    # Máximo tamaño de archivo individual dentro del ZIP (100MB)
    MAX_INDIVIDUAL_FILE_SIZE = 100 * 1024 * 1024

    # Máximo número de archivos en el ZIP (prevenir zip bombs)
    MAX_FILES_IN_ZIP = 10000

    # Máximo ratio de compresión (prevenir zip bombs)
    MAX_COMPRESSION_RATIO = 100

    @staticmethod
    def validate_mime_type(file_content: bytes) -> Tuple[bool, str]:
        """
        Validar tipo MIME real del archivo.

        Args:
            file_content: Contenido del archivo en bytes

        Returns:
            (is_valid, detected_mime_type)
        """
        try:
            mime = magic.Magic(mime=True)
            detected_type = mime.from_buffer(file_content[:2048])

            is_valid = detected_type in FileValidator.ALLOWED_MIME_TYPES

            if not is_valid:
                logger.warning(f"Invalid MIME type detected: {detected_type}")

            return is_valid, detected_type

        except Exception as e:
            logger.error(f"MIME type detection failed: {e}")
            return False, "unknown"

    @staticmethod
    def validate_zip_integrity(file_content: bytes) -> Tuple[bool, List[str]]:
        """
        Validar integridad y seguridad del archivo ZIP.

        Checks:
        - No está corrupto
        - No contiene path traversal
        - No contiene archivos peligrosos
        - No es un zip bomb

        Args:
            file_content: Contenido del archivo ZIP

        Returns:
            (is_valid, list_of_errors)
        """
        errors = []

        try:
            with zipfile.ZipFile(BytesIO(file_content)) as zf:
                # 1. Verificar integridad
                bad_file = zf.testzip()
                if bad_file is not None:
                    errors.append(f"Corrupted file in ZIP: {bad_file}")
                    return False, errors

                # 2. Verificar cantidad de archivos (zip bomb detection)
                file_count = len(zf.namelist())
                if file_count > FileValidator.MAX_FILES_IN_ZIP:
                    errors.append(
                        f"Too many files in ZIP: {file_count} > {FileValidator.MAX_FILES_IN_ZIP}"
                    )
                    return False, errors

                # 3. Verificar cada archivo
                total_compressed_size = 0
                total_uncompressed_size = 0

                for file_info in zf.infolist():
                    filename = file_info.filename

                    # Check path traversal
                    if filename.startswith('/') or '..' in filename:
                        errors.append(f"Path traversal detected: {filename}")
                        return False, errors

                    # Check extensiones peligrosas
                    file_ext = Path(filename).suffix.lower()
                    if file_ext in FileValidator.DANGEROUS_EXTENSIONS:
                        errors.append(f"Dangerous file detected: {filename}")
                        return False, errors

                    # Check tamaño individual
                    if file_info.file_size > FileValidator.MAX_INDIVIDUAL_FILE_SIZE:
                        errors.append(
                            f"File too large: {filename} "
                            f"({file_info.file_size / 1024 / 1024:.2f}MB)"
                        )
                        return False, errors

                    # Acumular tamaños para detectar zip bombs
                    total_compressed_size += file_info.compress_size
                    total_uncompressed_size += file_info.file_size

                # 4. Detectar zip bombs por ratio de compresión
                if total_compressed_size > 0:
                    compression_ratio = total_uncompressed_size / total_compressed_size
                    if compression_ratio > FileValidator.MAX_COMPRESSION_RATIO:
                        errors.append(
                            f"Suspicious compression ratio: {compression_ratio:.2f}x "
                            f"(max allowed: {FileValidator.MAX_COMPRESSION_RATIO}x)"
                        )
                        return False, errors

                return True, []

        except zipfile.BadZipFile:
            errors.append("Invalid ZIP file format")
            return False, errors

        except Exception as e:
            logger.error(f"ZIP validation error: {e}")
            errors.append(f"Validation error: {str(e)}")
            return False, errors

    @classmethod
    def validate_upload(cls, file_content: bytes, filename: str) -> Tuple[bool, List[str]]:
        """
        Validación completa de archivo subido.

        Args:
            file_content: Contenido del archivo
            filename: Nombre del archivo

        Returns:
            (is_valid, list_of_errors)
        """
        all_errors = []

        # 1. Validar extensión
        file_ext = Path(filename).suffix.lower()
        if file_ext != ".zip":
            all_errors.append(f"Invalid extension: {file_ext}. Only .zip allowed")
            return False, all_errors

        # 2. Validar tipo MIME
        is_valid_mime, detected_mime = cls.validate_mime_type(file_content)
        if not is_valid_mime:
            all_errors.append(
                f"Invalid file type. Detected: {detected_mime}, expected: application/zip"
            )
            return False, all_errors

        # 3. Validar contenido del ZIP
        is_valid_zip, zip_errors = cls.validate_zip_integrity(file_content)
        if not is_valid_zip:
            all_errors.extend(zip_errors)
            return False, all_errors

        return True, []
```

```python
# backend/app/api/v1/upload.py

from app.utils.file_validator import FileValidator

@router.post("/upload")
async def upload_scorm(
    request: Request,
    file: UploadFile = File(...),
    source_language: str = Form("auto"),
    target_languages: str = Form(...),
    user: User = Depends(get_current_user),
):
    """Upload SCORM con validación de seguridad avanzada."""

    # Leer contenido del archivo
    file_content = await file.read()

    # VALIDACIÓN COMPLETA DE SEGURIDAD
    is_valid, validation_errors = FileValidator.validate_upload(
        file_content,
        file.filename
    )

    if not is_valid:
        logger.warning(
            f"File validation failed | User: {user.email} | "
            f"File: {file.filename} | Errors: {validation_errors}"
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "File validation failed",
                "validation_errors": validation_errors
            }
        )

    # Continuar con procesamiento si la validación pasa...
```

---

## 4. Manejo de Errores Seguro

```python
# backend/app/utils/error_handler.py

from fastapi import HTTPException, status, Request
from typing import Optional, Any
import logging
import traceback

logger = logging.getLogger(__name__)
security_logger = logging.getLogger("security")


class SecureErrorHandler:
    """Manejador centralizado de errores con seguridad."""

    @staticmethod
    def handle_authentication_error(
        request: Request,
        exception: Exception,
        user_identifier: Optional[str] = None
    ) -> HTTPException:
        """
        Manejar errores de autenticación de forma segura.

        - Loggea detalles completos en servidor
        - Retorna mensaje genérico al cliente
        - Registra intento en log de seguridad
        """
        # Log detallado (solo servidor)
        logger.error(
            f"Authentication failed | "
            f"User: {user_identifier or 'unknown'} | "
            f"IP: {request.client.host} | "
            f"Error: {str(exception)}",
            exc_info=True
        )

        # Log de seguridad
        security_logger.warning(
            f"Failed auth | User: {user_identifier} | IP: {request.client.host}"
        )

        # Mensaje genérico al cliente (sin detalles)
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    @staticmethod
    def handle_authorization_error(
        request: Request,
        user_id: str,
        resource: str,
        action: str
    ) -> HTTPException:
        """Manejar errores de autorización."""
        security_logger.warning(
            f"Unauthorized access | "
            f"User: {user_id} | "
            f"Resource: {resource} | "
            f"Action: {action} | "
            f"IP: {request.client.host}"
        )

        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"  # Genérico
        )

    @staticmethod
    def handle_not_found_error(
        resource_type: str,
        resource_id: Optional[str] = None
    ) -> HTTPException:
        """Manejar errores 404."""
        logger.info(f"Resource not found | Type: {resource_type} | ID: {resource_id}")

        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource_type.capitalize()} not found"
        )

    @staticmethod
    def handle_validation_error(
        validation_errors: list,
        operation: str
    ) -> HTTPException:
        """Manejar errores de validación."""
        logger.warning(f"Validation failed | Operation: {operation} | Errors: {validation_errors}")

        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Validation failed",
                "validation_errors": validation_errors
            }
        )

    @staticmethod
    def handle_internal_error(
        request: Request,
        exception: Exception,
        operation: str,
        context: Optional[dict] = None
    ) -> HTTPException:
        """
        Manejar errores internos 500.

        - Loggea stack trace completo
        - Retorna mensaje genérico
        - Incluye request ID para correlación
        """
        # Generate request ID si no existe
        request_id = getattr(request.state, "request_id", "unknown")

        # Log completo con stack trace
        logger.error(
            f"Internal error | "
            f"Operation: {operation} | "
            f"Request ID: {request_id} | "
            f"Context: {context} | "
            f"Error: {str(exception)}",
            exc_info=True
        )

        # Retornar error genérico
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": f"{operation} failed",
                "message": "An internal error occurred. Please try again later.",
                "request_id": request_id  # Para soporte técnico
            }
        )
```

---

## 5. Security Headers Middleware

```python
# backend/app/middleware/security_headers.py

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware que agrega headers de seguridad a todas las respuestas."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # X-Frame-Options: Prevenir clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # X-Content-Type-Options: Prevenir MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-XSS-Protection: Habilitar filtro XSS del navegador
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Content-Security-Policy
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # Ajustar según necesidad
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            f"connect-src 'self' {settings.SUPABASE_URL}",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # Strict-Transport-Security (HSTS) - solo en HTTPS
        if request.url.scheme == "https" or settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Referrer-Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy (antes Feature-Policy)
        permissions_directives = [
            "geolocation=()",
            "microphone=()",
            "camera=()",
            "payment=()",
            "usb=()",
            "magnetometer=()",
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions_directives)

        # X-Permitted-Cross-Domain-Policies
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

        return response
```

```python
# backend/app/main.py

from app.middleware.security_headers import SecurityHeadersMiddleware

app = FastAPI(...)

# Agregar middleware de seguridad
app.add_middleware(SecurityHeadersMiddleware)
```

---

## 6. Logging de Seguridad

```python
# backend/app/utils/security_logger.py

import logging
from datetime import datetime
from typing import Optional
import json

# Logger dedicado para eventos de seguridad
security_logger = logging.getLogger("security")


class SecurityEvent:
    """Utilidad para loggear eventos de seguridad."""

    @staticmethod
    def log_failed_login(email: str, ip: str, reason: str):
        """Loggear intento de login fallido."""
        security_logger.warning(
            f"FAILED_LOGIN | "
            f"Email: {email} | "
            f"IP: {ip} | "
            f"Reason: {reason} | "
            f"Timestamp: {datetime.utcnow().isoformat()}"
        )

    @staticmethod
    def log_successful_login(user_id: str, email: str, ip: str):
        """Loggear login exitoso."""
        security_logger.info(
            f"SUCCESSFUL_LOGIN | "
            f"UserID: {user_id} | "
            f"Email: {email} | "
            f"IP: {ip} | "
            f"Timestamp: {datetime.utcnow().isoformat()}"
        )

    @staticmethod
    def log_unauthorized_access(
        user_id: str,
        resource: str,
        ip: str,
        actual_owner: Optional[str] = None
    ):
        """Loggear intento de acceso no autorizado."""
        security_logger.warning(
            f"UNAUTHORIZED_ACCESS | "
            f"UserID: {user_id} | "
            f"Resource: {resource} | "
            f"ActualOwner: {actual_owner} | "
            f"IP: {ip} | "
            f"Timestamp: {datetime.utcnow().isoformat()}"
        )

    @staticmethod
    def log_file_upload(
        user_id: str,
        filename: str,
        size_mb: float,
        ip: str,
        validation_result: str = "success"
    ):
        """Loggear upload de archivo."""
        security_logger.info(
            f"FILE_UPLOAD | "
            f"UserID: {user_id} | "
            f"Filename: {filename} | "
            f"Size: {size_mb:.2f}MB | "
            f"ValidationResult: {validation_result} | "
            f"IP: {ip} | "
            f"Timestamp: {datetime.utcnow().isoformat()}"
        )

    @staticmethod
    def log_suspicious_activity(
        event_type: str,
        user_id: Optional[str],
        ip: str,
        details: dict
    ):
        """Loggear actividad sospechosa."""
        security_logger.critical(
            f"SUSPICIOUS_ACTIVITY | "
            f"EventType: {event_type} | "
            f"UserID: {user_id or 'anonymous'} | "
            f"IP: {ip} | "
            f"Details: {json.dumps(details)} | "
            f"Timestamp: {datetime.utcnow().isoformat()}"
        )

    @staticmethod
    def log_resource_access(
        user_id: str,
        resource: str,
        action: str,
        ip: str,
        result: str = "success"
    ):
        """Loggear acceso a recursos."""
        security_logger.info(
            f"RESOURCE_ACCESS | "
            f"UserID: {user_id} | "
            f"Resource: {resource} | "
            f"Action: {action} | "
            f"Result: {result} | "
            f"IP: {ip} | "
            f"Timestamp: {datetime.utcnow().isoformat()}"
        )
```

---

Este código está listo para implementar y resuelve las vulnerabilidades críticas identificadas en la auditoría.
