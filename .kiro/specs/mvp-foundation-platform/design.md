# Diseño del MVP - Plataforma de Coaching AI Multi-Canal

## Visión General

Este documento presenta el diseño técnico detallado para el MVP de la plataforma de coaching AI multi-canal. El diseño se basa en una arquitectura de microservicios escalable que soporta multi-tenancy desde el día uno, utilizando tecnologías modernas como FastAPI, PostgreSQL, ChromaDB, y Ollama para crear una base sólida que pueda evolucionar hacia una plataforma completa multi-canal.

La arquitectura está diseñada para ser agnóstica al canal, facilitando futuras integraciones con WhatsApp, Telegram y aplicaciones móviles sin reestructuración mayor del sistema core.

## Arquitectura

### Arquitectura de Alto Nivel

```mermaid
graph TB
    subgraph "Frontend Layer"
        WW[Web Widget]
        CH[Creator Hub]
    end
    
    subgraph "API Gateway Layer"
        AG[API Gateway<br/>Kong/Nginx]
    end
    
    subgraph "Application Layer"
        AS[Auth Service<br/>FastAPI]
        CHS[Creator Hub Service<br/>FastAPI]
        AIS[AI Engine Service<br/>FastAPI]
        CS[Channel Service<br/>FastAPI]
    end
    
    subgraph "AI/ML Layer"
        OL[Ollama<br/>LLM Server]
        CD[ChromaDB<br/>Vector Store]
    end
    
    subgraph "Data Layer"
        PG[(PostgreSQL<br/>Primary DB)]
        RD[(Redis<br/>Cache & Sessions)]
        FS[File Storage<br/>S3/MinIO]
    end
    
    subgraph "Infrastructure Layer"
        MQ[Message Queue<br/>Redis Streams]
        LOG[Logging<br/>ELK Stack]
        MON[Monitoring<br/>Prometheus]
    end
    
    WW --> AG
    CH --> AG
    AG --> AS
    AG --> CHS
    AG --> AIS
    AG --> CS
    
    AS --> PG
    AS --> RD
    CHS --> PG
    CHS --> FS
    AIS --> OL
    AIS --> CD
    AIS --> PG
    CS --> MQ
    CS --> RD
    
    AIS --> MQ
    CHS --> MQ
```

### Principios de Diseño

1. **Multi-Tenancy First**: Aislamiento completo de datos por creador desde el nivel de base de datos
2. **Escalabilidad Horizontal**: Todos los servicios diseñados para escalar independientemente
3. **Agnóstico al Canal**: Abstracción de mensajería que soporta múltiples canales
4. **Observabilidad**: Logging, métricas y trazabilidad integrados desde el inicio
5. **Seguridad por Diseño**: Autenticación, autorización y encriptación en todas las capas

## Organización de Modelos Compartidos

### Estructura del Paquete Shared

Para mejorar la reutilización de código y mantener consistencia entre servicios, se organizan los modelos Pydantic en un paquete compartido:

```
shared/
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── auth.py          # CreatorCreate, CreatorResponse, TokenResponse, UserSession
│   ├── documents.py     # ProcessingResult, DocumentChunk, ProcessingStatus
│   ├── widgets.py       # WidgetConfig, WidgetTheme, WidgetBehavior
│   ├── conversations.py # Message, Conversation, ConversationContext
│   └── base.py          # BaseModel extensions, common validators
├── exceptions/
│   ├── __init__.py
│   ├── base.py          # BaseException classes
│   ├── auth.py          # AuthenticationError, AuthorizationError
│   ├── documents.py     # DocumentProcessingError, ValidationError
│   └── widgets.py       # WidgetConfigError
├── validators/
│   ├── __init__.py
│   ├── common.py        # Email, URL, domain validators
│   └── business.py      # Business logic validators
└── utils/
    ├── __init__.py
    ├── serializers.py   # Custom JSON encoders/decoders
    └── helpers.py       # Common utility functions
```

### Instalación del Paquete Shared

```python
# pyproject.toml para cada servicio
[tool.poetry.dependencies]
shared-models = {path = "../shared", develop = true}

# O usando pip en desarrollo
pip install -e ../shared
```

### Ejemplo de Uso en Servicios

```python
# En cualquier servicio
from shared.models.documents import ProcessingResult, DocumentChunk
from shared.models.widgets import WidgetConfig, WidgetTheme
from shared.exceptions.documents import DocumentProcessingError
from shared.validators.common import validate_domain

# Uso directo de los modelos tipados
async def process_document(file_path: str) -> ProcessingResult:
    # Implementación con tipos explícitos
    pass
```

## Documentación de API con OpenAPI

### Configuración OpenAPI por Servicio

Cada servicio FastAPI incluye documentación OpenAPI completa con:

```python
# Configuración base para cada servicio
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="Creator Hub Service API",
    description="API para gestión de creadores y configuración de widgets",
    version="1.0.0",
    openapi_tags=[
        {
            "name": "creators",
            "description": "Operaciones de gestión de creadores"
        },
        {
            "name": "widgets",
            "description": "Configuración y gestión de widgets"
        },
        {
            "name": "documents",
            "description": "Gestión de documentos y knowledge base"
        }
    ]
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Agregar esquemas de seguridad
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    
    # Agregar ejemplos de respuesta
    openapi_schema["components"]["examples"] = {
        "ProcessingResultExample": {
            "summary": "Resultado de procesamiento exitoso",
            "value": {
                "document_id": "abc123def456",
                "creator_id": "creator_789",
                "status": "completed",
                "chunks": [
                    {
                        "id": "chunk_001",
                        "content": "Contenido del primer chunk...",
                        "metadata": {"page": 1, "section": "introduction"},
                        "chunk_index": 0,
                        "token_count": 150
                    }
                ],
                "total_chunks": 5,
                "processing_time_seconds": 2.34,
                "metadata": {
                    "file_path": "/uploads/document.pdf",
                    "chunk_size": 1000,
                    "original_text_length": 5000
                }
            }
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

### Documentación de Endpoints con Ejemplos

```python
from fastapi import APIRouter, Depends, HTTPException, status
from shared.models.documents import ProcessingResult
from shared.models.widgets import WidgetConfig

router = APIRouter(prefix="/api/v1/creators", tags=["creators"])

@router.post(
    "/knowledge/upload",
    response_model=ProcessingResult,
    status_code=status.HTTP_201_CREATED,
    summary="Procesar y subir documento",
    description="Procesa un documento cargado y lo prepara para búsqueda semántica",
    responses={
        201: {
            "description": "Documento procesado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "document_id": "abc123def456",
                        "creator_id": "creator_789",
                        "status": "completed",
                        "total_chunks": 5,
                        "processing_time_seconds": 2.34
                    }
                }
            }
        },
        400: {
            "description": "Error de validación",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Formato de archivo no soportado: .xlsx"
                    }
                }
            }
        },
        422: {
            "description": "Error de procesamiento",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "No se pudo extraer texto del documento"
                    }
                }
            }
        }
    }
)
async def upload_document(
    file: UploadFile,
    creator_id: str = Depends(get_current_creator_id)
) -> ProcessingResult:
    """
    Procesa un documento cargado y retorna información detallada del procesamiento.
    
    - **file**: Archivo a procesar (PDF, TXT, DOCX, MD)
    - **creator_id**: ID del creador (obtenido del token JWT)
    
    El procesamiento incluye:
    1. Validación del formato
    2. Extracción de texto
    3. División en chunks optimizados
    4. Generación de embeddings
    5. Almacenamiento en vector store
    """
    # Implementación
    pass

@router.put(
    "/widget/config",
    response_model=WidgetConfig,
    summary="Actualizar configuración del widget",
    description="Actualiza la configuración del widget y regenera el código embed",
    responses={
        200: {
            "description": "Configuración actualizada exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "creator_id": "creator_789",
                        "widget_id": "widget_abc123",
                        "is_active": True,
                        "theme": {
                            "primary_color": "#007bff",
                            "secondary_color": "#6c757d"
                        },
                        "embed_code": "<script>/* Código generado */</script>"
                    }
                }
            }
        }
    }
)
async def update_widget_config(
    config: WidgetConfig,
    creator_id: str = Depends(get_current_creator_id)
) -> WidgetConfig:
    """
    Actualiza la configuración del widget del creador.
    
    Regenera automáticamente el código embed si hay cambios en:
    - Tema visual (colores, bordes)
    - Comportamiento (mensajes, delays)
    - Dominios permitidos
    - Límites de rate limiting
    """
    # Implementación
    pass
```

### Generación de Documentación Consolidada

```bash
# Script para generar documentación consolidada
#!/bin/bash

# Generar OpenAPI specs para cada servicio
curl http://localhost:8001/openapi.json > docs/openapi/auth-service.json
curl http://localhost:8002/openapi.json > docs/openapi/creator-hub-service.json
curl http://localhost:8003/openapi.json > docs/openapi/ai-engine-service.json
curl http://localhost:8004/openapi.json > docs/openapi/channel-service.json

# Generar documentación HTML usando Redoc
redoc-cli build docs/openapi/auth-service.json --output docs/html/auth-service.html
redoc-cli build docs/openapi/creator-hub-service.json --output docs/html/creator-hub-service.html
redoc-cli build docs/openapi/ai-engine-service.json --output docs/html/ai-engine-service.html
redoc-cli build docs/openapi/channel-service.json --output docs/html/channel-service.html

echo "Documentación API generada en docs/html/"
```

## Componentes y Interfaces

### 1. API Gateway

**Tecnología**: Kong o Nginx con módulos de autenticación
**Puerto**: 80/443 (HTTP/HTTPS)

**Responsabilidades**:
- Routing de requests a servicios apropiados
- Terminación SSL/TLS
- Rate limiting por tenant
- Autenticación JWT
- CORS handling
- Request/Response logging

**Configuración**:
```yaml
# Kong Configuration Example
services:
  - name: auth-service
    url: http://auth-service:8001
    routes:
      - name: auth-routes
        paths: ["/api/v1/auth"]
  
  - name: creator-hub-service
    url: http://creator-hub-service:8002
    routes:
      - name: creator-routes
        paths: ["/api/v1/creators"]
        
  - name: ai-engine-service
    url: http://ai-engine-service:8003
    routes:
      - name: ai-routes
        paths: ["/api/v1/ai"]

plugins:
  - name: jwt
    config:
      secret_is_base64: false
  - name: rate-limiting
    config:
      minute: 100
      hour: 1000
```

### 2. Auth Service

**Tecnología**: FastAPI + JWT + bcrypt
**Puerto**: 8001

**Endpoints**:
```python
# API Specification
POST /api/v1/auth/register/creator
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
GET  /api/v1/auth/me
POST /api/v1/auth/verify-token
```

**Modelos de Datos**:
```python
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

class CreatorCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    company_name: Optional[str] = None

class CreatorResponse(BaseModel):
    id: str
    email: str
    full_name: str
    company_name: Optional[str]
    is_active: bool
    created_at: datetime
    subscription_tier: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class UserSession(BaseModel):
    session_id: str
    creator_id: str
    channel: str
    created_at: datetime
    last_activity: datetime
    metadata: Dict[str, Any]

# Document Processing Models
class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class DocumentChunk(BaseModel):
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding_vector: Optional[List[float]] = None
    chunk_index: int
    token_count: int

class ProcessingResult(BaseModel):
    document_id: str
    creator_id: str
    status: ProcessingStatus
    chunks: List[DocumentChunk]
    total_chunks: int
    processing_time_seconds: float
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Widget Configuration Models
class WidgetTheme(BaseModel):
    primary_color: str = Field(default="#007bff", description="Primary brand color")
    secondary_color: str = Field(default="#6c757d", description="Secondary color")
    background_color: str = Field(default="#ffffff", description="Widget background")
    text_color: str = Field(default="#212529", description="Text color")
    border_radius: int = Field(default=8, ge=0, le=50, description="Border radius in pixels")

class WidgetBehavior(BaseModel):
    auto_open: bool = Field(default=False, description="Auto-open widget on page load")
    greeting_message: str = Field(default="¡Hola! ¿En qué puedo ayudarte?", description="Initial greeting")
    placeholder_text: str = Field(default="Escribe tu mensaje...", description="Input placeholder")
    show_typing_indicator: bool = Field(default=True, description="Show typing indicator")
    response_delay_ms: int = Field(default=1000, ge=0, le=5000, description="Simulated response delay")

class WidgetConfig(BaseModel):
    creator_id: str
    widget_id: str
    is_active: bool = Field(default=True)
    theme: WidgetTheme = Field(default_factory=WidgetTheme)
    behavior: WidgetBehavior = Field(default_factory=WidgetBehavior)
    allowed_domains: List[str] = Field(default_factory=list, description="Allowed domains for widget")
    rate_limit_per_minute: int = Field(default=10, ge=1, le=100, description="Messages per minute limit")
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    embed_code: Optional[str] = None
```

### 3. Creator Hub Service

**Tecnología**: FastAPI + SQLAlchemy + Alembic
**Puerto**: 8002

**Endpoints**:
```python
# Creator Management
GET    /api/v1/creators/profile
PUT    /api/v1/creators/profile
GET    /api/v1/creators/dashboard/metrics

# Knowledge Base Management
POST   /api/v1/creators/knowledge/upload
GET    /api/v1/creators/knowledge/documents
DELETE /api/v1/creators/knowledge/documents/{doc_id}
GET    /api/v1/creators/knowledge/documents/{doc_id}/status

# Widget Configuration
GET    /api/v1/creators/widget/config
PUT    /api/v1/creators/widget/config
GET    /api/v1/creators/widget/embed-code

# Conversations Management
GET    /api/v1/creators/conversations
GET    /api/v1/creators/conversations/{conversation_id}
```

**Servicios Internos**:
```python
from typing import List, Optional
from pathlib import Path
import asyncio
import hashlib
import logging
import os
from datetime import datetime

from shared.models import ProcessingResult, ProcessingStatus, DocumentChunk, WidgetConfig
from shared.exceptions import DocumentProcessingError, ValidationError

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Procesa documentos cargados y los prepara para ChromaDB"""
    
    # Default security constants (configurable via constructor)
    DEFAULT_MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50MB limit
    DEFAULT_UPLOADS_DIR = Path("/app/uploads")  # Default upload directory
    DEFAULT_SUPPORTED_FORMATS = {'.pdf', '.txt', '.docx', '.md'}
    
    def __init__(self, ai_engine_client, vector_store_client, uploads_dir: str = None, 
                 create_uploads_dir: bool = True, max_upload_bytes: int = None,
                 supported_formats: set = None, config_provider = None):
        self.ai_engine = ai_engine_client
        self.vector_store = vector_store_client
        
        # Configure limits from parameters, environment, or config provider
        self.max_upload_bytes = self._resolve_config_value(
            'MAX_UPLOAD_BYTES', max_upload_bytes, self.DEFAULT_MAX_UPLOAD_BYTES, int
        )
        self.supported_formats = self._resolve_config_value(
            'SUPPORTED_FORMATS', supported_formats, self.DEFAULT_SUPPORTED_FORMATS, set
        )
        
        # Legacy property for backward compatibility
        self.MAX_UPLOAD_BYTES = self.max_upload_bytes
        # Semaphore to limit concurrent file reads (prevent resource exhaustion)
        self._file_read_semaphore = asyncio.Semaphore(4)
        
        # Configure and validate uploads directory
        if uploads_dir:
            self.uploads_dir = Path(uploads_dir).resolve()
        else:
            uploads_dir_config = self._resolve_config_value(
                'UPLOADS_DIR', None, str(self.DEFAULT_UPLOADS_DIR), str
            )
            self.uploads_dir = Path(uploads_dir_config).resolve()
        
        # Validate and setup uploads directory
        self._setup_uploads_directory(create_uploads_dir)
    
    def _resolve_config_value(self, env_key: str, param_value, default_value, value_type):
        """
        Resolves configuration values from multiple sources in priority order:
        1. Constructor parameter (highest priority)
        2. Environment variable
        3. Config provider (if available)
        4. Default value (lowest priority)
        """
        if param_value is not None:
            return param_value
        
        # Try environment variable
        env_value = os.getenv(env_key)
        if env_value is not None:
            try:
                if value_type == int:
                    return int(env_value)
                elif value_type == set:
                    # Parse comma-separated string to set
                    return set(ext.strip() for ext in env_value.split(','))
                else:
                    return value_type(env_value)
            except (ValueError, TypeError) as e:
                logger.warning(
                    f"Invalid environment variable value - "
                    f"key: {env_key}, value: {env_value}, expected_type: {value_type.__name__}, "
                    f"error: {str(e)}, using_default: {default_value}"
                )
        
        # Try config provider if available
        if hasattr(self, 'config_provider') and self.config_provider:
            try:
                config_value = self.config_provider.get(env_key.lower())
                if config_value is not None:
                    return value_type(config_value)
            except Exception as e:
                logger.warning(
                    f"Config provider error - "
                    f"key: {env_key}, error: {str(e)}, using_default: {default_value}"
                )
        
        return default_value
    
    def _setup_uploads_directory(self, create_if_missing: bool = True):
        """
        Validates and sets up the uploads directory with proper security checks
        
        Args:
            create_if_missing: Whether to create the directory if it doesn't exist
            
        Raises:
            ValidationError: If directory setup fails or security checks fail
        """
        try:
            # 1. Security check: Prevent access to restricted system paths
            restricted_paths = {
                Path("/etc").resolve(),
                Path("/sys").resolve(), 
                Path("/proc").resolve(),
                Path("/dev").resolve(),
                Path("/boot").resolve(),
                Path("/root").resolve(),
                Path("/var/log").resolve(),
                Path("/usr/bin").resolve(),
                Path("/usr/sbin").resolve(),
            }
            
            # Add Windows system paths
            if os.name == 'nt':
                restricted_paths.update({
                    Path("C:/Windows").resolve(),
                    Path("C:/Program Files").resolve(),
                    Path("C:/Program Files (x86)").resolve(),
                    Path("C:/System Volume Information").resolve(),
                })
            
            # Check if uploads directory is in a restricted path
            for restricted_path in restricted_paths:
                try:
                    if str(self.uploads_dir).startswith(str(restricted_path)):
                        logger.error(
                            f"Security violation: uploads directory in restricted path - "
                            f"requested_path: {self.uploads_dir}, "
                            f"restricted_parent: {restricted_path}"
                        )
                        raise ValidationError(
                            f"Uploads directory cannot be in restricted system path: {restricted_path}"
                        )
                except (OSError, ValueError):
                    # Skip comparison if path resolution fails (path might not exist)
                    continue
            
            # 2. Check if directory exists
            if not self.uploads_dir.exists():
                if create_if_missing:
                    logger.info(
                        f"Creating uploads directory - "
                        f"path: {self.uploads_dir}"
                    )
                    try:
                        # Create directory with secure permissions (755)
                        self.uploads_dir.mkdir(parents=True, exist_ok=True, mode=0o755)
                        logger.info(
                            f"Uploads directory created successfully - "
                            f"path: {self.uploads_dir}"
                        )
                    except OSError as e:
                        logger.exception(
                            f"Failed to create uploads directory - "
                            f"path: {self.uploads_dir}, "
                            f"error: {str(e)}"
                        )
                        raise ValidationError(
                            "No se pudo crear el directorio de archivos. Contacte al administrador."
                        ) from e
                else:
                    logger.error(
                        f"Uploads directory does not exist - "
                        f"path: {self.uploads_dir}, "
                        f"create_if_missing: false"
                    )
                    raise ValidationError(
                        f"Uploads directory does not exist: {self.uploads_dir}"
                    )
            
            # 3. Verify it's actually a directory
            if not self.uploads_dir.is_dir():
                logger.error(
                    f"Uploads path is not a directory - "
                    f"path: {self.uploads_dir}, "
                    f"is_file: {self.uploads_dir.is_file()}"
                )
                raise ValidationError(
                    f"Uploads path is not a directory: {self.uploads_dir}"
                )
            
            # 4. Check write permissions
            test_file = self.uploads_dir / ".write_test"
            try:
                # Try to create and delete a test file
                test_file.touch()
                test_file.unlink()
                logger.info(
                    f"Uploads directory write permissions verified - "
                    f"path: {self.uploads_dir}"
                )
            except (OSError, PermissionError) as e:
                logger.exception(
                    f"No write permissions to uploads directory - "
                    f"path: {self.uploads_dir}, "
                    f"error: {str(e)}"
                )
                raise ValidationError(
                    "Error de permisos en el directorio de archivos. Contacte al administrador."
                ) from e
            
            # 5. Check read permissions
            try:
                list(self.uploads_dir.iterdir())
                logger.info(
                    f"Uploads directory read permissions verified - "
                    f"path: {self.uploads_dir}"
                )
            except (OSError, PermissionError) as e:
                logger.exception(
                    f"No read permissions to uploads directory - "
                    f"path: {self.uploads_dir}, "
                    f"error: {str(e)}"
                )
                raise ValidationError(
                    f"No read permissions to uploads directory: {str(e)}"
                ) from e
            
            # 6. Log successful setup
            logger.info(
                f"Uploads directory setup completed successfully - "
                f"path: {self.uploads_dir}, "
                f"exists: true, "
                f"writable: true, "
                f"readable: true"
            )
            
        except ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.exception(
                f"Unexpected error during uploads directory setup - "
                f"path: {self.uploads_dir}, "
                f"error_type: {type(e).__name__}"
            )
            raise ValidationError(
                f"Failed to setup uploads directory: {str(e)}"
            ) from e
    
    async def process_document(
        self, 
        file_path: str, 
        creator_id: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> ProcessingResult:
        """
        Procesa un documento y retorna el resultado estructurado
        
        Args:
            file_path: Ruta al archivo a procesar
            creator_id: ID del creador propietario
            chunk_size: Tamaño máximo de cada chunk en tokens
            chunk_overlap: Solapamiento entre chunks
            
        Returns:
            ProcessingResult con chunks procesados y metadatos
            
        Raises:
            DocumentProcessingError: Si falla el procesamiento
            ValidationError: Si el archivo no es válido
        """
        start_time = datetime.utcnow()
        document_id = await self._generate_document_id(file_path, creator_id)
        
        try:
            # 1. Validar formato de archivo
            await self._validate_file_format(file_path)
            
            # 2. Extraer texto usando bibliotecas apropiadas
            raw_text = await self._extract_text(file_path)
            
            # 3. Dividir en chunks optimizados
            chunks = await self._create_chunks(
                raw_text, chunk_size, chunk_overlap, document_id
            )
            
            # 4. Generar embeddings para cada chunk
            processed_chunks = await self._generate_embeddings(chunks)
            
            # 5. Calcular tiempo de procesamiento
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return ProcessingResult(
                document_id=document_id,
                creator_id=creator_id,
                status=ProcessingStatus.COMPLETED,
                chunks=processed_chunks,
                total_chunks=len(processed_chunks),
                processing_time_seconds=processing_time,
                metadata={
                    "file_path": file_path,
                    "chunk_size": chunk_size,
                    "chunk_overlap": chunk_overlap,
                    "original_text_length": len(raw_text)
                }
            )
            
        except ValidationError as e:
            # Re-raise validation errors with original message
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.warning(
                f"Document validation failed - creator_id: {creator_id}, "
                f"document_id: {document_id}, processing_time: {processing_time:.2f}s, "
                f"error: {str(e)}"
            )
            return ProcessingResult(
                document_id=document_id,
                creator_id=creator_id,
                status=ProcessingStatus.FAILED,
                chunks=[],
                total_chunks=0,
                processing_time_seconds=processing_time,
                error_message=f"Validation error: {str(e)}"
            )
        except DocumentProcessingError as e:
            # Re-raise document processing errors with original message
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            return ProcessingResult(
                document_id=document_id,
                creator_id=creator_id,
                status=ProcessingStatus.FAILED,
                chunks=[],
                total_chunks=0,
                processing_time_seconds=processing_time,
                error_message=f"Processing error: {str(e)}"
            )
        except (FileNotFoundError, PermissionError, OSError) as e:
            # Handle file system related errors
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.exception(
                f"File system error during document processing - "
                f"filename: {Path(file_path).name}, "
                f"creator_id: {creator_id}, "
                f"document_id: {document_id}, "
                f"processing_time: {processing_time:.2f}s, "
                f"error_type: {type(e).__name__}"
            )
            return ProcessingResult(
                document_id=document_id,
                creator_id=creator_id,
                status=ProcessingStatus.FAILED,
                chunks=[],
                total_chunks=0,
                processing_time_seconds=processing_time,
                error_message="File access error occurred during processing"
            )
        except MemoryError as e:
            # Handle memory exhaustion
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.exception(
                f"Memory exhaustion during document processing - "
                f"filename: {Path(file_path).name}, "
                f"creator_id: {creator_id}, "
                f"document_id: {document_id}, "
                f"processing_time: {processing_time:.2f}s, "
                f"error_type: MemoryError"
            )
            return ProcessingResult(
                document_id=document_id,
                creator_id=creator_id,
                status=ProcessingStatus.FAILED,
                chunks=[],
                total_chunks=0,
                processing_time_seconds=processing_time,
                error_message="Document too large to process"
            )
        except Exception as e:
            # Handle unexpected errors without exposing sensitive information
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.exception(f"Unexpected error processing document for creator {creator_id}: {type(e).__name__}")
            return ProcessingResult(
                document_id=document_id,
                creator_id=creator_id,
                status=ProcessingStatus.FAILED,
                chunks=[],
                total_chunks=0,
                processing_time_seconds=processing_time,
                error_message="An unexpected error occurred during processing"
            )
    
    async def _generate_document_id(self, file_path: str, creator_id: str) -> str:
        """
        Genera un ID único y determinístico para el documento basado en su contenido
        
        Args:
            file_path: Ruta al archivo
            creator_id: ID del creador (para namespacing)
            
        Returns:
            ID único del documento (SHA-256 hash de contenido + creator_id)
            
        Note:
            Zero-length files are explicitly supported and will produce a deterministic
            hash based solely on the creator_id. This ensures consistent behavior
            for empty files while maintaining the deterministic property of the ID
            generation algorithm.
            
        Raises:
            DocumentProcessingError: If file is too large to process in memory
        """
        try:
            # Leer el contenido del archivo de forma async-safe usando chunked reading
            def _compute_file_hash(path: str, creator_id: str) -> str:
                """Compute SHA-256 hash of file content in chunks to prevent memory issues"""
                hash_obj = hashlib.sha256()
                
                with open(path, 'rb') as file:
                    # Read file in 8KB chunks to prevent memory exhaustion
                    # Update hash incrementally to avoid memory allocation for concatenation
                    while True:
                        chunk = file.read(8192)
                        if not chunk:
                            break
                        hash_obj.update(chunk)
                
                # Update hash with creator_id bytes incrementally (no concatenation)
                hash_obj.update(creator_id.encode('utf-8'))
                return hash_obj.hexdigest()
            
            # Use semaphore to limit concurrent file reads
            async with self._file_read_semaphore:
                content_hash = await asyncio.to_thread(_compute_file_hash, file_path, creator_id)
            
            # Use 24 characters for better collision resistance (16^24 = ~2.8 x 10^28 combinations)
            # This provides sufficient uniqueness for large-scale systems
            base_id = f"doc_{content_hash[:24]}"
            
            # Check for collision and add entropy if needed
            final_id = await self._ensure_unique_document_id(base_id, creator_id)
            return final_id
            
        except FileNotFoundError as e:
            # File doesn't exist - use UUID fallback
            import uuid
            fallback_id = str(uuid.uuid4()).replace('-', '')[:24]
            logger.warning(
                f"File not found during ID generation - "
                f"filename: {Path(file_path).name}, "
                f"operation: generate_document_id, "
                f"using_uuid_fallback: true, "
                f"error_type: FileNotFoundError"
            )
            return f"doc_{fallback_id}"
        except PermissionError as e:
            # Permission denied - use UUID fallback
            import uuid
            fallback_id = str(uuid.uuid4()).replace('-', '')[:24]
            logger.warning(
                f"Permission denied during ID generation - "
                f"filename: {Path(file_path).name}, "
                f"operation: generate_document_id, "
                f"using_uuid_fallback: true, "
                f"error_type: PermissionError"
            )
            return f"doc_{fallback_id}"
        except OSError as e:
            # Other OS-level errors (disk full, network issues, etc.)
            import uuid
            fallback_id = str(uuid.uuid4()).replace('-', '')[:24]
            logger.warning(
                f"OS error during ID generation - "
                f"filename: {Path(file_path).name}, "
                f"operation: generate_document_id, "
                f"using_uuid_fallback: true, "
                f"error_type: {type(e).__name__}"
            )
            return f"doc_{fallback_id}"
        except MemoryError as e:
            # File too large to read into memory
            raise DocumentProcessingError(f"File too large to process: {file_path}")
        except Exception as e:
            # Unexpected error - log without exposing sensitive file paths
            import uuid
            fallback_id = str(uuid.uuid4()).replace('-', '')[:16]
            logger.exception(f"Unexpected error generating document ID: {type(e).__name__}")
            return f"doc_{fallback_id}"
    
    async def _ensure_unique_document_id(self, base_id: str, creator_id: str) -> str:
        """
        Ensures document ID uniqueness by checking for collisions and adding entropy
        
        Args:
            base_id: Base document ID to check
            creator_id: Creator ID for scoped uniqueness check
            
        Returns:
            Unique document ID with entropy added if collision detected
        """
        try:
            # Check if ID already exists for this creator
            if await self._document_id_exists(base_id, creator_id):
                logger.warning(
                    f"Document ID collision detected - "
                    f"base_id: {base_id}, creator_id: {creator_id}, "
                    f"adding_entropy: true"
                )
                
                # Add entropy using timestamp and random component
                import time
                import secrets
                entropy = f"{int(time.time() * 1000000) % 1000000:06d}{secrets.token_hex(2)}"
                unique_id = f"{base_id}_{entropy}"
                
                # Verify the new ID is unique (recursive check with limit)
                collision_count = 1
                while await self._document_id_exists(unique_id, creator_id) and collision_count < 5:
                    entropy = f"{int(time.time() * 1000000) % 1000000:06d}{secrets.token_hex(2)}"
                    unique_id = f"{base_id}_{entropy}"
                    collision_count += 1
                
                if collision_count >= 5:
                    # Fallback to UUID if multiple collisions
                    import uuid
                    unique_id = f"doc_{str(uuid.uuid4()).replace('-', '')[:24]}"
                    logger.error(
                        f"Multiple ID collisions detected - "
                        f"base_id: {base_id}, creator_id: {creator_id}, "
                        f"using_uuid_fallback: true, final_id: {unique_id}"
                    )
                
                return unique_id
            
            return base_id
            
        except Exception as e:
            logger.exception(
                f"Error checking document ID uniqueness - "
                f"base_id: {base_id}, creator_id: {creator_id}, "
                f"error_type: {type(e).__name__}"
            )
            # Return base_id if uniqueness check fails (graceful degradation)
            return base_id
    
    async def _document_id_exists(self, document_id: str, creator_id: str) -> bool:
        """
        Check if document ID already exists for the given creator
        
        Args:
            document_id: Document ID to check
            creator_id: Creator ID for scoped check
            
        Returns:
            True if document ID exists, False otherwise
        """
        try:
            # This would typically query the database
            # Implementation depends on your database layer
            # Example with SQLAlchemy:
            # result = await self.db.execute(
            #     select(KnowledgeDocument).where(
            #         and_(
            #             KnowledgeDocument.document_id == document_id,
            #             KnowledgeDocument.creator_id == creator_id
            #         )
            #     )
            # )
            # return result.first() is not None
            
            # Placeholder implementation - replace with actual database query
            logger.debug(
                f"Checking document ID existence - "
                f"document_id: {document_id}, creator_id: {creator_id}"
            )
            return False  # Placeholder - implement actual database check
            
        except Exception as e:
            logger.exception(
                f"Error checking document ID existence - "
                f"document_id: {document_id}, creator_id: {creator_id}, "
                f"error_type: {type(e).__name__}"
            )
            # Return False on error (assume ID doesn't exist for graceful degradation)
            return False
    
    async def _validate_file_format(self, file_path: str) -> None:
        """
        Valida que el archivo sea seguro y soportado
        
        Includes:
        - File size validation (DoS prevention)
        - Path traversal protection
        - Format validation
        """
        try:
            # 1. Path sanitization and traversal protection
            file_path_obj = Path(file_path).resolve()
            
            # Verify file is within allowed uploads directory
            if not str(file_path_obj).startswith(str(self.uploads_dir)):
                logger.warning(
                    f"Path traversal attempt detected - "
                    f"requested_path: {Path(file_path).name}, "  # Only log filename for security
                    f"resolved_outside_uploads_dir: true"
                )
                raise ValidationError("Acceso a archivo no autorizado")
            
            # 2. File existence check
            if not file_path_obj.exists():
                logger.warning(
                    f"File not found - "
                    f"filename: {file_path_obj.name}, "
                    f"operation: validation"
                )
                raise ValidationError("Archivo no encontrado")
            
            # 3. File size validation (DoS prevention)
            file_size = file_path_obj.stat().st_size
            if file_size > self.max_upload_bytes:
                logger.warning(
                    f"File size exceeds limit - "
                    f"filename: {file_path_obj.name}, "
                    f"size_bytes: {file_size}, "
                    f"max_allowed_bytes: {self.max_upload_bytes}, "
                    f"operation: validation"
                )
                raise ValidationError(
                    f"Archivo demasiado grande. Máximo permitido: "
                    f"{self.max_upload_bytes // (1024*1024)}MB"
                )
            
            # 4. Format validation
            file_extension = file_path_obj.suffix.lower()
            if file_extension not in self.supported_formats:
                logger.warning(
                    f"Unsupported file format - "
                    f"filename: {file_path_obj.name}, "
                    f"extension: {file_extension}, "
                    f"supported_formats: {list(self.supported_formats)}"
                )
                raise ValidationError(f"Formato no soportado: {file_extension}")
            
            # 5. Log successful validation (for audit trail)
            logger.info(
                f"File validation successful - "
                f"filename: {file_path_obj.name}, "
                f"size_bytes: {file_size}, "
                f"extension: {file_extension}"
            )
            
        except (OSError, PermissionError) as e:
            logger.exception(
                f"File system error during validation - "
                f"filename: {Path(file_path).name}, "
                f"error_type: {type(e).__name__}"
            )
            raise ValidationError("Error accediendo al archivo") from e
    
    async def _extract_text(self, file_path: str) -> str:
        """Extrae texto del archivo según su formato"""
        # Implementación específica por formato
        pass
    
    async def _create_chunks(
        self, 
        text: str, 
        chunk_size: int, 
        overlap: int, 
        document_id: str
    ) -> List[DocumentChunk]:
        """Divide el texto en chunks optimizados"""
        # Implementación de chunking inteligente
        pass
    
    async def _generate_embeddings(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Genera embeddings para cada chunk usando el AI Engine"""
        # Implementación de generación de embeddings
        pass

class WidgetConfigManager:
    """Gestiona configuración del widget por creador"""
    
    def __init__(self, database_client, template_engine):
        self.db = database_client
        self.templates = template_engine
        self.widget_template_path = "templates/widget_embed.js"
    
    async def generate_embed_code(self, creator_id: str) -> str:
        """
        Genera código JavaScript personalizado para el widget
        
        Args:
            creator_id: ID del creador
            
        Returns:
            Código JavaScript listo para embeber
            
        Raises:
            ValidationError: Si el creador no existe o no tiene configuración
        """
        config = await self.get_widget_config(creator_id)
        if not config:
            raise ValidationError(f"No se encontró configuración para creador: {creator_id}")
        
        # Generar código JavaScript personalizado
        embed_code = await self._render_widget_template(config)
        
        # Actualizar el embed_code en la configuración
        config.embed_code = embed_code
        await self.update_widget_config(creator_id, config)
        
        return embed_code
    
    async def update_widget_config(
        self, 
        creator_id: str, 
        config: WidgetConfig
    ) -> WidgetConfig:
        """
        Actualiza configuración del widget y regenera código
        
        Args:
            creator_id: ID del creador
            config: Nueva configuración del widget
            
        Returns:
            Configuración actualizada con nuevo embed_code
        """
        # Validar configuración
        await self._validate_widget_config(config)
        
        # Actualizar timestamp
        config.updated_at = datetime.utcnow()
        
        # Regenerar código embed si es necesario
        if not config.embed_code or await self._config_changed(creator_id, config):
            config.embed_code = await self._render_widget_template(config)
        
        # Guardar en base de datos
        await self.db.update_widget_config(creator_id, config)
        
        return config
    
    async def get_widget_config(self, creator_id: str) -> Optional[WidgetConfig]:
        """Obtiene la configuración actual del widget"""
        return await self.db.get_widget_config(creator_id)
    
    async def _validate_widget_config(self, config: WidgetConfig) -> None:
        """Valida la configuración del widget"""
        # Validar dominios permitidos
        for domain in config.allowed_domains:
            if not self._is_valid_domain(domain):
                raise ValidationError(f"Dominio inválido: {domain}")
        
        # Validar colores hexadecimales
        color_fields = [
            config.theme.primary_color,
            config.theme.secondary_color,
            config.theme.background_color,
            config.theme.text_color
        ]
        
        for color in color_fields:
            if not self._is_valid_hex_color(color):
                raise ValidationError(f"Color hexadecimal inválido: {color}")
    
    async def _render_widget_template(self, config: WidgetConfig) -> str:
        """Renderiza el template del widget con la configuración"""
        template_vars = {
            "widget_id": config.widget_id,
            "creator_id": config.creator_id,
            "theme": config.theme.dict(),
            "behavior": config.behavior.dict(),
            "rate_limit": config.rate_limit_per_minute,
            "allowed_domains": config.allowed_domains
        }
        
        return await self.templates.render(self.widget_template_path, template_vars)
    
    async def _config_changed(self, creator_id: str, new_config: WidgetConfig) -> bool:
        """Verifica si la configuración ha cambiado"""
        try:
            # Obtener configuración actual de la base de datos
            current_config = await self.get_widget_config(creator_id)
            
            if not current_config:
                return True  # No hay configuración previa, es un cambio
            
            # Comparar campos clave que afectan el código embed
            key_fields_changed = (
                current_config.theme != new_config.theme or
                current_config.behavior != new_config.behavior or
                current_config.allowed_domains != new_config.allowed_domains or
                current_config.rate_limit_per_minute != new_config.rate_limit_per_minute or
                current_config.is_active != new_config.is_active
            )
            
            return key_fields_changed
            
        except ValidationError as e:
            # Database validation error - assume changes to regenerate
            logger.warning(
                f"Widget config validation failed - creator_id: {creator_id}, "
                f"operation: config_comparison, assuming_changes: true, "
                f"error: {str(e)}"
            )
            return True
        except (RedisConnectionError, RedisTimeoutError, RedisResponseError) as e:
            # Redis connection issues - assume changes to be safe
            logger.exception(
                f"Redis connection error during widget config comparison - "
                f"creator_id: {creator_id}, operation: config_comparison, "
                f"assuming_changes: true, error_type: {type(e).__name__}, "
                f"error: {str(e)}"
            )
            return True
        except Exception as e:
            # Unexpected error - assume changes to regenerate, log without sensitive data
            logger.exception(f"Unexpected error comparing widget config for creator {creator_id}: {type(e).__name__}")
            return True
    
    def _is_valid_domain(self, domain: str) -> bool:
        """Valida formato de dominio"""
        import re
        pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        return bool(re.match(pattern, domain))
    
    def _is_valid_hex_color(self, color: str) -> bool:
        """Valida formato de color hexadecimal"""
        import re
        pattern = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
        return bool(re.match(pattern, color))
```

### 4. AI Engine Service

**Tecnología**: FastAPI + LangChain + Ollama + ChromaDB
**Puerto**: 8003

**Endpoints**:
```python
# Conversation Processing
POST /api/v1/ai/chat
POST /api/v1/ai/process-document
GET  /api/v1/ai/conversation/{conversation_id}/context

# Knowledge Management
POST /api/v1/ai/knowledge/embed
GET  /api/v1/ai/knowledge/search
POST /api/v1/ai/knowledge/update-embeddings

# Health and Status
GET  /api/v1/ai/health
GET  /api/v1/ai/models/status
```

**Arquitectura RAG**:
```python
class RAGPipeline:
    """Pipeline principal de Retrieval-Augmented Generation"""
    
    def __init__(self):
        self.ollama_client = OllamaClient()
        self.chroma_client = ChromaClient()
        self.conversation_manager = ConversationManager()
    
    async def process_query(self, query: str, creator_id: str, 
                          conversation_id: str) -> AIResponse:
        # 1. Recuperar contexto de conversación
        context = await self.conversation_manager.get_context(conversation_id)
        
        # 2. Búsqueda de conocimiento relevante
        relevant_docs = await self.retrieve_knowledge(query, creator_id)
        
        # 3. Construir prompt con contexto
        prompt = self.build_prompt(query, context, relevant_docs)
        
        # 4. Generar respuesta con Ollama
        response = await self.ollama_client.generate(prompt)
        
        # 5. Actualizar contexto de conversación
        await self.conversation_manager.update_context(
            conversation_id, query, response
        )
        
        return AIResponse(
            response=response,
            sources=relevant_docs,
            confidence=self.calculate_confidence(relevant_docs)
        )

class ChromaManager:
    """Gestiona colecciones de ChromaDB por creador"""
    
    def __init__(self):
        self.client = chromadb.HttpClient(host="chromadb", port=8000)
    
    async def get_or_create_collection(self, creator_id: str):
        collection_name = f"creator_{creator_id}_knowledge"
        return self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.get_embedding_function()
        )
    
    async def add_documents(self, creator_id: str, documents: List[Document]):
        collection = await self.get_or_create_collection(creator_id)
        
        # Procesar documentos en chunks
        chunks = []
        metadatas = []
        ids = []
        
        for doc in documents:
            doc_chunks = self.chunk_document(doc)
            for i, chunk in enumerate(doc_chunks):
                chunks.append(chunk.content)
                metadatas.append({
                    "document_id": doc.id,
                    "chunk_index": i,
                    "creator_id": creator_id,
                    "source": doc.source,
                    "created_at": doc.created_at.isoformat()
                })
                ids.append(f"{doc.id}_chunk_{i}")
        
        collection.add(
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
```

### 5. Channel Service

**Tecnología**: FastAPI + WebSockets + Redis Streams
**Puerto**: 8004

**Endpoints**:
```python
# WebSocket Connections
WS   /api/v1/channels/widget/{creator_id}/connect

# Message Processing
POST /api/v1/channels/message/send
POST /api/v1/channels/message/receive
GET  /api/v1/channels/conversations/{conversation_id}/messages

# Channel Management
GET  /api/v1/channels/status
POST /api/v1/channels/widget/deploy
```

**WebSocket Manager**:
```python
import json
import logging
from datetime import datetime
from typing import Dict, List
from fastapi import WebSocket
import redis.asyncio as redis
from redis.exceptions import (
    ConnectionError as RedisConnectionError,
    TimeoutError as RedisTimeoutError,
    ResponseError as RedisResponseError,
    BusyLoadingError as RedisBusyLoadingError,
    AuthenticationError as RedisAuthenticationError
)

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Gestiona conexiones WebSocket del widget"""
    
    def __init__(self, redis_url: str = "redis://redis:6379"):
        self.active_connections: Dict[str, WebSocket] = {}
        self.redis_client = None
        self.redis_url = redis_url
        self._connections_lock = asyncio.Lock()  # Thread safety for active_connections
    
    async def _get_redis_client(self):
        """Lazy initialization of async Redis client"""
        if self.redis_client is None:
            try:
                self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
                # Test connection
                await self.redis_client.ping()
                logger.info(f"Redis client initialized successfully - url: {self.redis_url}")
            except (RedisConnectionError, RedisAuthenticationError, RedisTimeoutError) as e:
                logger.exception(
                    f"Failed to initialize Redis client - "
                    f"url: {self.redis_url}, error_type: {type(e).__name__}, "
                    f"error: {str(e)}"
                )
                raise
        return self.redis_client
    
    async def connect(self, websocket: WebSocket, creator_id: str, 
                     session_id: str):
        await websocket.accept()
        connection_id = f"{creator_id}_{session_id}"
        
        # Thread-safe access to active_connections
        async with self._connections_lock:
            self.active_connections[connection_id] = websocket
        
        # Registrar conexión en Redis para escalabilidad
        try:
            redis_client = await self._get_redis_client()
            await redis_client.hset(
                "active_connections", 
                connection_id, 
                json.dumps({
                    "creator_id": creator_id,
                    "session_id": session_id,
                    "connected_at": datetime.utcnow().isoformat()
                })
            )
            logger.info(
                f"WebSocket connection established - "
                f"creator_id: {creator_id}, session_id: {session_id}, "
                f"connection_id: {connection_id}, operation: connect"
            )
        except (RedisConnectionError, RedisTimeoutError, RedisResponseError) as e:
            logger.exception(
                f"Failed to register connection in Redis - "
                f"creator_id: {creator_id}, session_id: {session_id}, "
                f"connection_id: {connection_id}, error_type: {type(e).__name__}, "
                f"error: {str(e)}"
            )
            # Continue with connection even if Redis registration fails
            # The connection will still work locally
    
    async def send_message(self, connection_id: str, message: dict):
        """Envía mensaje a una conexión específica con manejo de errores"""
        # Thread-safe access to active_connections
        async with self._connections_lock:
            websocket = self.active_connections.get(connection_id)
        
        if websocket:
            try:
                await websocket.send_json(message)
            except Exception as e:
                # Conexión cerrada o error de envío
                logger.exception(f"Failed to send message to {connection_id}: {e}")
                await self._remove_connection(connection_id)
    
    async def get_creator_connections(self, creator_id: str) -> List[str]:
        """Obtiene todas las conexiones activas de un creador"""
        try:
            redis_client = await self._get_redis_client()
            all_connections = await redis_client.hgetall("active_connections")
            
            creator_connections = []
            for connection_id, connection_data in all_connections.items():
                try:
                    data = json.loads(connection_data)
                    if data.get("creator_id") == creator_id:
                        # Verificar que la conexión aún esté activa localmente
                        # connection_id ya está decodificado gracias a decode_responses=True
                        async with self._connections_lock:
                            is_active = connection_id in self.active_connections
                        
                        if is_active:
                            creator_connections.append(connection_id)
                        else:
                            # Limpiar conexión stale de Redis
                            await redis_client.hdel("active_connections", connection_id)
                except (json.JSONDecodeError, KeyError) as e:
                    logger.exception(f"Invalid connection data for {connection_id}: {e}")
                    await redis_client.hdel("active_connections", connection_id)
            
            return creator_connections
            
        except (RedisConnectionError, RedisTimeoutError, RedisResponseError, RedisBusyLoadingError) as e:
            # Redis connection issues
            logger.exception(
                f"Redis error retrieving creator connections - "
                f"creator_id: {creator_id}, operation: get_connections, "
                f"error_type: {type(e).__name__}, returning_empty_list: true, "
                f"error: {str(e)}"
            )
            return []
        except json.JSONDecodeError as e:
            # Corrupted data in Redis
            logger.exception(f"JSON decode error in creator connections for {creator_id}: {e}")
            return []
        except Exception as e:
            # Unexpected error - log without exposing sensitive data
            logger.exception(f"Unexpected error getting creator connections for {creator_id}: {type(e).__name__}")
            return []
    
    async def _remove_connection(self, connection_id: str):
        """Remueve una conexión de los registros locales y Redis"""
        try:
            # Remover de conexiones locales con thread safety
            async with self._connections_lock:
                if connection_id in self.active_connections:
                    del self.active_connections[connection_id]
            
            # Remover de Redis
            redis_client = await self._get_redis_client()
            await redis_client.hdel("active_connections", connection_id)
            
            logger.info(f"Removed stale connection: {connection_id}")
            
        except (RedisConnectionError, RedisTimeoutError, RedisResponseError, RedisBusyLoadingError) as e:
            # Redis connection issues - connection may still exist in Redis
            logger.exception(
                f"Redis error during connection removal - "
                f"connection_id: {connection_id}, operation: remove_connection, "
                f"error_type: {type(e).__name__}, connection_may_persist_in_redis: true, "
                f"error: {str(e)}"
            )
        except KeyError as e:
            # Connection already removed - this is expected in some cases
            logger.info(
                f"Connection already removed from local registry - "
                f"connection_id: {connection_id}, operation: remove_connection, "
                f"status: already_removed"
            )
        except Exception as e:
            # Unexpected error - log without exposing sensitive connection data
            logger.exception(
                f"Unexpected error during connection removal - "
                f"connection_id: {connection_id}, operation: remove_connection, "
                f"error_type: {type(e).__name__}"
            )
    
    async def disconnect(self, connection_id: str):
        """Desconecta una conexión WebSocket específica"""
        # Thread-safe access to active_connections
        async with self._connections_lock:
            websocket = self.active_connections.get(connection_id)
        
        if websocket:
            try:
                await websocket.close()
            except Exception as e:
                logger.exception(f"Error closing websocket {connection_id}: {e}")
            finally:
                await self._remove_connection(connection_id)
    
    async def broadcast_to_creator(self, creator_id: str, message: dict):
        """Envía mensaje a todas las conexiones de un creador"""
        connections = await self.get_creator_connections(creator_id)
        
        # Usar asyncio.gather para envío paralelo
        import asyncio
        tasks = [self.send_message(connection_id, message) for connection_id in connections]
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def shutdown(self):
        """
        Graceful shutdown of WebSocketManager
        
        Closes all active WebSocket connections and Redis client properly
        to prevent resource leaks during application shutdown.
        """
        logger.info("Starting WebSocketManager shutdown...")
        
        try:
            # Get all active connections before starting shutdown
            async with self._connections_lock:
                active_connection_ids = list(self.active_connections.keys())
                connection_count = len(active_connection_ids)
            
            logger.info(f"Closing {connection_count} active WebSocket connections...")
            
            # Close all WebSocket connections concurrently
            if active_connection_ids:
                close_tasks = []
                for connection_id in active_connection_ids:
                    async with self._connections_lock:
                        websocket = self.active_connections.get(connection_id)
                    
                    if websocket:
                        close_tasks.append(self._close_websocket_safely(websocket, connection_id))
                
                # Wait for all connections to close with timeout
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*close_tasks, return_exceptions=True),
                        timeout=30.0  # 30 second timeout for graceful shutdown
                    )
                except asyncio.TimeoutError:
                    logger.warning("Timeout waiting for WebSocket connections to close")
            
            # Clear the active connections registry
            async with self._connections_lock:
                self.active_connections.clear()
            
            # Close Redis client if it exists
            if self.redis_client:
                logger.info("Closing Redis client connection...")
                try:
                    await self.redis_client.close()
                    logger.info("Redis client closed successfully")
                except Exception as e:
                    logger.exception(f"Error closing Redis client: {e}")
            
            logger.info("WebSocketManager shutdown completed successfully")
            
        except Exception as e:
            logger.exception(f"Error during WebSocketManager shutdown: {e}")
            raise
    
    async def _close_websocket_safely(self, websocket: WebSocket, connection_id: str):
        """
        Safely close a WebSocket connection with proper error handling
        
        Args:
            websocket: WebSocket connection to close
            connection_id: ID of the connection for logging
        """
        try:
            # Send close frame if connection is still open
            if not websocket.client_state.DISCONNECTED:
                await websocket.close(code=1001, reason="Server shutdown")
            
            # Remove from local registry
            async with self._connections_lock:
                if connection_id in self.active_connections:
                    del self.active_connections[connection_id]
            
            # Remove from Redis (best effort - don't fail shutdown if Redis is down)
            try:
                if self.redis_client:
                    await self.redis_client.hdel("active_connections", connection_id)
            except Exception as e:
                logger.warning(f"Failed to remove connection {connection_id} from Redis during shutdown: {e}")
            
            logger.debug(f"Successfully closed connection: {connection_id}")
            
        except Exception as e:
            logger.exception(f"Error closing WebSocket connection {connection_id}: {e}")
            # Continue with shutdown even if individual connection fails to close

### Application Shutdown Integration

```python
# services/channel/main.py - FastAPI application with proper shutdown handling

import signal
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from shared.services.websocket_manager import WebSocketManager

# Global WebSocket manager instance
websocket_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown"""
    global websocket_manager
    
    # Startup
    logger.info("Starting Channel Service...")
    websocket_manager = WebSocketManager()
    
    # Register shutdown handlers for graceful termination
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        asyncio.create_task(shutdown_handler())
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    yield
    
    # Shutdown
    await shutdown_handler()

async def shutdown_handler():
    """Handle graceful shutdown of all resources"""
    global websocket_manager
    
    logger.info("Initiating graceful shutdown...")
    
    try:
        if websocket_manager:
            await websocket_manager.shutdown()
        
        # Close other resources (database connections, etc.)
        # await database.disconnect()
        # await other_cleanup()
        
        logger.info("Graceful shutdown completed")
        
    except Exception as e:
        logger.exception(f"Error during shutdown: {e}")
        raise

# Create FastAPI app with lifespan management
app = FastAPI(
    title="Channel Service",
    lifespan=lifespan
)

@app.websocket("/ws/{creator_id}")
async def websocket_endpoint(websocket: WebSocket, creator_id: str):
    """WebSocket endpoint for widget connections"""
    global websocket_manager
    
    session_id = str(uuid.uuid4())
    
    try:
        await websocket_manager.connect(websocket, creator_id, session_id)
        
        # Handle WebSocket communication
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Process message and send response
                response = await process_message(message, creator_id)
                await websocket_manager.send_message(f"{creator_id}_{session_id}", response)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected: {creator_id}_{session_id}")
                break
            except Exception as e:
                logger.exception(f"Error in WebSocket communication: {e}")
                break
    
    finally:
        # Cleanup connection
        await websocket_manager.disconnect(f"{creator_id}_{session_id}")

# Alternative shutdown handling for non-FastAPI applications
class GracefulShutdownHandler:
    """Standalone graceful shutdown handler"""
    
    def __init__(self, websocket_manager: WebSocketManager):
        self.websocket_manager = websocket_manager
        self.shutdown_event = asyncio.Event()
        
        # Register signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, setting shutdown event...")
        self.shutdown_event.set()
    
    async def wait_for_shutdown(self):
        """Wait for shutdown signal and perform cleanup"""
        await self.shutdown_event.wait()
        logger.info("Shutdown signal received, cleaning up...")
        
        try:
            await self.websocket_manager.shutdown()
            logger.info("Cleanup completed successfully")
        except Exception as e:
            logger.exception(f"Error during cleanup: {e}")
            raise

# Usage example for standalone applications
async def main():
    """Main application entry point"""
    websocket_manager = WebSocketManager()
    shutdown_handler = GracefulShutdownHandler(websocket_manager)
    
    try:
        # Start your application logic here
        # await start_server()
        
        # Wait for shutdown signal
        await shutdown_handler.wait_for_shutdown()
        
    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt, shutting down...")
    except Exception as e:
        logger.exception(f"Unexpected error in main: {e}")
        raise
    finally:
        logger.info("Application shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())
```

class MessageProcessor:
    """Procesa mensajes entre usuarios y AI"""
    
    async def process_user_message(self, message: UserMessage) -> AIResponse:
        # 1. Validar y sanitizar mensaje
        # 2. Crear o recuperar conversación
        # 3. Enviar a AI Engine para procesamiento
        # 4. Almacenar mensaje y respuesta
        # 5. Enviar respuesta via WebSocket
        pass
```

## Modelos de Datos

### Esquema de Base de Datos PostgreSQL

```sql
-- Tabla de creadores (tenants)
CREATE TABLE creators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    company_name VARCHAR(255),
    subscription_tier VARCHAR(50) DEFAULT 'free',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    settings JSONB DEFAULT '{}'::jsonb
);

-- Tabla de sesiones de usuarios finales
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID NOT NULL REFERENCES creators(id) ON DELETE CASCADE,
    session_id VARCHAR(255) NOT NULL,
    channel VARCHAR(50) NOT NULL DEFAULT 'widget',
    user_profile JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    UNIQUE(creator_id, session_id)
);

-- Tabla de conversaciones
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID NOT NULL REFERENCES creators(id) ON DELETE CASCADE,
    user_session_id UUID NOT NULL REFERENCES user_sessions(id) ON DELETE CASCADE,
    channel VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    context JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de mensajes
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_type VARCHAR(20) NOT NULL CHECK (sender_type IN ('user', 'ai')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de documentos de conocimiento
CREATE TABLE knowledge_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID NOT NULL REFERENCES creators(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    processing_status VARCHAR(50) DEFAULT 'pending',
    processed_at TIMESTAMP WITH TIME ZONE,
    chunk_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de configuración de widgets
CREATE TABLE widget_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID NOT NULL REFERENCES creators(id) ON DELETE CASCADE,
    primary_color VARCHAR(7) DEFAULT '#007bff',
    secondary_color VARCHAR(7) DEFAULT '#6c757d',
    logo_url VARCHAR(500),
    welcome_message TEXT DEFAULT 'Hello! How can I help you today?',
    placeholder_text VARCHAR(255) DEFAULT 'Type your message...',
    position VARCHAR(20) DEFAULT 'bottom-right',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(creator_id)
);

-- Índices para optimización
CREATE INDEX idx_creators_email ON creators(email);
CREATE INDEX idx_user_sessions_creator_id ON user_sessions(creator_id);
CREATE INDEX idx_user_sessions_session_id ON user_sessions(session_id);
CREATE INDEX idx_conversations_creator_id ON conversations(creator_id);
CREATE INDEX idx_conversations_user_session_id ON conversations(user_session_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_knowledge_documents_creator_id ON knowledge_documents(creator_id);
CREATE INDEX idx_knowledge_documents_status ON knowledge_documents(processing_status);
```

### Modelos ChromaDB

```python
# Estructura de colecciones por creador
collection_name_pattern = "creator_{creator_id}_knowledge"

# Metadatos estándar para documentos
document_metadata = {
    "creator_id": str,
    "document_id": str,
    "chunk_index": int,
    "source": str,  # filename o URL
    "document_type": str,  # pdf, txt, docx, etc.
    "created_at": str,  # ISO format
    "processed_at": str,  # ISO format
    "chunk_size": int,
    "language": str,  # detectado automáticamente
    "section": str,  # si aplica (header, paragraph, etc.)
}

# Configuración de embedding
embedding_config = {
    "model": "nomic-embed-text",  # Modelo de Ollama
    "dimensions": 768,
    "distance_metric": "cosine"
}
```

## Manejo de Errores

### Estrategia de Manejo de Errores

```python
from enum import Enum
from typing import Optional, Dict, Any

class ErrorCode(Enum):
    # Authentication Errors
    INVALID_CREDENTIALS = "AUTH_001"
    TOKEN_EXPIRED = "AUTH_002"
    INSUFFICIENT_PERMISSIONS = "AUTH_003"
    
    # Validation Errors
    INVALID_INPUT = "VAL_001"
    MISSING_REQUIRED_FIELD = "VAL_002"
    INVALID_FILE_FORMAT = "VAL_003"
    
    # AI Engine Errors
    AI_SERVICE_UNAVAILABLE = "AI_001"
    KNOWLEDGE_BASE_EMPTY = "AI_002"
    CONTEXT_TOO_LONG = "AI_003"
    
    # Rate Limiting
    RATE_LIMIT_EXCEEDED = "RATE_001"
    
    # System Errors
    DATABASE_ERROR = "SYS_001"
    EXTERNAL_SERVICE_ERROR = "SYS_002"

class APIError(Exception):
    def __init__(self, 
                 error_code: ErrorCode, 
                 message: str, 
                 details: Optional[Dict[str, Any]] = None,
                 status_code: int = 400):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        super().__init__(message)

# Error Handler Middleware
@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code.value,
                "message": exc.message,
                "details": exc.details,
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request.headers.get("X-Request-ID")
            }
        }
    )

# Circuit Breaker para servicios externos
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise APIError(
                    ErrorCode.EXTERNAL_SERVICE_ERROR,
                    "Service temporarily unavailable"
                )
        
        try:
            result = await func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            
            raise APIError(
                ErrorCode.EXTERNAL_SERVICE_ERROR,
                f"External service error: {str(e)}"
            )
```

## Estrategia de Testing

### Pirámide de Testing

```python
# 1. Unit Tests (70%)
import pytest
from unittest.mock import Mock, patch

class TestRAGPipeline:
    @pytest.fixture
    def rag_pipeline(self):
        return RAGPipeline()
    
    @patch('ai_engine.ollama_client.OllamaClient.generate')
    @patch('ai_engine.chroma_manager.ChromaManager.retrieve_knowledge')
    async def test_process_query_success(self, mock_retrieve, mock_generate, rag_pipeline):
        # Arrange
        mock_retrieve.return_value = [{"content": "test doc", "score": 0.9}]
        mock_generate.return_value = "AI response"
        
        # Act
        result = await rag_pipeline.process_query(
            "test query", "creator_123", "conv_456"
        )
        
        # Assert
        assert result.response == "AI response"
        assert len(result.sources) == 1
        mock_retrieve.assert_called_once()
        mock_generate.assert_called_once()

# 2. Integration Tests (20%)
class TestAPIIntegration:
    @pytest.mark.asyncio
    async def test_full_conversation_flow(self, test_client, test_creator):
        # Test complete flow from widget message to AI response
        
        # 1. Create user session
        session_response = await test_client.post(
            "/api/v1/channels/widget/session",
            json={"creator_id": test_creator.id}
        )
        session_id = session_response.json()["session_id"]
        
        # 2. Send message via WebSocket
        async with test_client.websocket_connect(
            f"/api/v1/channels/widget/{test_creator.id}/connect?session_id={session_id}"
        ) as websocket:
            await websocket.send_json({
                "type": "user_message",
                "content": "Hello, I need help"
            })
            
            response = await websocket.receive_json()
            assert response["type"] == "ai_response"
            assert "content" in response

# 3. End-to-End Tests (10%)
class TestE2EScenarios:
    def test_creator_onboarding_to_first_conversation(self):
        # Test complete user journey
        pass
```

### Testing de Accesibilidad

```python
# Automated Accessibility Testing
import pytest
from axe_selenium_python import Axe

class TestAccessibility:
    def test_creator_hub_accessibility(self, selenium_driver):
        selenium_driver.get("http://localhost:3000/creator-hub")
        axe = Axe(selenium_driver)
        
        # Run accessibility scan
        results = axe.run()
        
        # Assert no violations
        assert len(results["violations"]) == 0, f"Accessibility violations found: {results['violations']}"
    
    def test_widget_accessibility(self, selenium_driver):
        selenium_driver.get("http://localhost:3000/widget-demo")
        axe = Axe(selenium_driver)
        
        results = axe.run()
        assert len(results["violations"]) == 0
    
    def test_keyboard_navigation(self, selenium_driver):
        # Test tab navigation through all interactive elements
        selenium_driver.get("http://localhost:3000/creator-hub")
        
        # Find all focusable elements
        focusable_elements = selenium_driver.find_elements(
            By.CSS_SELECTOR, 
            "button, input, select, textarea, a[href], [tabindex]:not([tabindex='-1'])"
        )
        
        # Test tab navigation
        for element in focusable_elements:
            element.send_keys(Keys.TAB)
            # Verify focus indicator is visible
            assert element.value_of_css_property("outline") != "none"
```

## Configuración de Despliegue

### Docker Compose para Desarrollo

```yaml
version: '3.8'

services:
  # API Gateway
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - auth-service
      - creator-hub-service
      - ai-engine-service
      - channel-service

  # Core Services
  auth-service:
    build: ./services/auth
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/coaching_platform
      - REDIS_URL=redis://redis:6379
      - JWT_SECRET=${JWT_SECRET}
      - ELASTICSEARCH_URL=http://elasticsearch:9200
      - LOG_LEVEL=INFO
      - SERVICE_NAME=auth-service
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        labels: "service=auth-service"
    depends_on:
      - postgres
      - redis
      - elasticsearch

  creator-hub-service:
    build: ./services/creator-hub
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/coaching_platform
      - REDIS_URL=redis://redis:6379
      - FILE_STORAGE_URL=http://minio:9000
      - ELASTICSEARCH_URL=http://elasticsearch:9200
      - LOG_LEVEL=INFO
      - SERVICE_NAME=creator-hub-service
    volumes:
      - ./uploads:/app/uploads
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        labels: "service=creator-hub-service"
    depends_on:
      - postgres
      - redis
      - minio
      - elasticsearch

  ai-engine-service:
    build: ./services/ai-engine
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/coaching_platform
      - CHROMADB_URL=http://chromadb:8000
      - OLLAMA_URL=http://ollama:11434
      - ELASTICSEARCH_URL=http://elasticsearch:9200
      - LOG_LEVEL=INFO
      - SERVICE_NAME=ai-engine-service
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        labels: "service=ai-engine-service"
    depends_on:
      - postgres
      - chromadb
      - ollama
      - elasticsearch

  channel-service:
    build: ./services/channel
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/coaching_platform
      - REDIS_URL=redis://redis:6379
      - ELASTICSEARCH_URL=http://elasticsearch:9200
      - LOG_LEVEL=INFO
      - SERVICE_NAME=channel-service
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        labels: "service=channel-service"
    depends_on:
      - postgres
      - redis
      - elasticsearch

  # AI/ML Services
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_MODELS=nomic-embed-text,llama2:7b-chat

  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8000:8000"
    volumes:
      - chromadb_data:/chroma/chroma
    environment:
      - IS_PERSISTENT=TRUE
      - ALLOW_RESET=True

  # Data Services
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=coaching_platform
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  minio:
    image: minio/minio:latest
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"

  # Monitoring & Logging
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana

  # ELK Stack for Centralized Logging
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: elasticsearch
    environment:
      - node.name=elasticsearch
      - cluster.name=coaching-platform-logs
      - discovery.type=single-node
      - bootstrap.memory_lock=true
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
      - xpack.security.enabled=false
      - xpack.security.enrollment.enabled=false
    ulimits:
      memlock:
        soft: -1
        hard: -1
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"
      - "9300:9300"
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9200/_cluster/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    container_name: logstash
    volumes:
      - ./logstash/config/logstash.yml:/usr/share/logstash/config/logstash.yml:ro
      - ./logstash/pipeline:/usr/share/logstash/pipeline:ro
    ports:
      - "5044:5044"
      - "5000:5000/tcp"
      - "5000:5000/udp"
      - "9600:9600"
    environment:
      LS_JAVA_OPTS: "-Xmx512m -Xms512m"
    depends_on:
      elasticsearch:
        condition: service_healthy

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    container_name: kibana
    ports:
      - "5601:5601"
    environment:
      ELASTICSEARCH_URL: http://elasticsearch:9200
      ELASTICSEARCH_HOSTS: '["http://elasticsearch:9200"]'
      SERVER_NAME: kibana
      SERVER_HOST: "0.0.0.0"
    volumes:
      - kibana_data:/usr/share/kibana/data
    depends_on:
      elasticsearch:
        condition: service_healthy

  # Filebeat for log shipping
  filebeat:
    image: docker.elastic.co/beats/filebeat:8.11.0
    container_name: filebeat
    user: root
    volumes:
      - ./filebeat/filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - filebeat_data:/usr/share/filebeat/data
    environment:
      - ELASTICSEARCH_HOST=elasticsearch:9200
      - KIBANA_HOST=kibana:5601
    depends_on:
      elasticsearch:
        condition: service_healthy
    command: ["--strict.perms=false"]

volumes:
  postgres_data:
  redis_data:
  chromadb_data:
  ollama_data:
  minio_data:
  prometheus_data:
  grafana_data:
  elasticsearch_data:
  logstash_data:
  kibana_data:
  filebeat_data:
```

### Configuración de ELK Stack y Observabilidad

#### Configuración de Logstash Pipeline

```yaml
# logstash/pipeline/logstash.conf
input {
  beats {
    port => 5044
  }
  
  tcp {
    port => 5000
    codec => json_lines
  }
}

filter {
  # Parse JSON logs from services (already decoded by Filebeat)
  if [fields][service] {
    mutate {
      add_field => { "service_name" => "%{[fields][service]}" }
    }
  }
  
  # Handle JSON logs that may come as message field
  if [message] and [message] != "" {
    # Try to parse as JSON if it looks like JSON
    if [message] =~ /^\s*\{/ {
      json {
        source => "message"
        target => "parsed_log"
        skip_on_invalid_json => true
      }
      
      # If JSON parsing succeeded, promote fields
      if [parsed_log] {
        # Extract common structured fields
        if [parsed_log][timestamp] {
          mutate { add_field => { "log_timestamp" => "%{[parsed_log][timestamp]}" } }
        }
        if [parsed_log][level] {
          mutate { add_field => { "log_level" => "%{[parsed_log][level]}" } }
        }
        if [parsed_log][service] {
          mutate { add_field => { "service_name" => "%{[parsed_log][service]}" } }
        }
        if [parsed_log][request_id] {
          mutate { add_field => { "request_id" => "%{[parsed_log][request_id]}" } }
        }
        if [parsed_log][creator_id] {
          mutate { add_field => { "creator_id" => "%{[parsed_log][creator_id]}" } }
        }
        if [parsed_log][endpoint] {
          mutate { add_field => { "endpoint" => "%{[parsed_log][endpoint]}" } }
        }
        if [parsed_log][response_time] {
          mutate { add_field => { "response_time" => "%{[parsed_log][response_time]}" } }
        }
        if [parsed_log][status_code] {
          mutate { add_field => { "status_code" => "%{[parsed_log][status_code]}" } }
        }
        
        # Replace message with the actual log message
        if [parsed_log][message] {
          mutate { replace => { "message" => "%{[parsed_log][message]}" } }
        }
        
        # Remove the temporary parsed_log field
        mutate { remove_field => [ "parsed_log" ] }
      }
    }
  }
  
  # Extract X-Request-ID from structured fields (preferred) or headers
  if [request_id] {
    # Already extracted from JSON, nothing to do
  } else if [http][request][headers][x-request-id] {
    mutate { add_field => { "request_id" => "%{[http][request][headers][x-request-id]}" } }
  } else if [http][request][headers][X-Request-ID] {
    mutate { add_field => { "request_id" => "%{[http][request][headers][X-Request-ID]}" } }
  }
  
  # Parse timestamp from structured logs
  if [log_timestamp] {
    date {
      match => [ "log_timestamp", "ISO8601", "yyyy-MM-dd'T'HH:mm:ss.SSSSSS", "yyyy-MM-dd'T'HH:mm:ss" ]
      target => "@timestamp"
    }
  } else if [timestamp] {
    date {
      match => [ "timestamp", "ISO8601", "yyyy-MM-dd'T'HH:mm:ss.SSSSSS", "yyyy-MM-dd'T'HH:mm:ss" ]
      target => "@timestamp"
    }
  }
  
  # Normalize log level
  if [log_level] {
    mutate { uppercase => [ "log_level" ] }
  }
  
  # Convert numeric fields
  if [response_time] {
    mutate { convert => { "response_time" => "float" } }
  }
  if [status_code] {
    mutate { convert => { "status_code" => "integer" } }
  }
  
  # Enrich with service metadata
  mutate {
    add_field => { "environment" => "development" }
    add_field => { "platform" => "coaching-ai-mvp" }
  }
  
  # Clean up temporary fields
  mutate {
    remove_field => [ "log_timestamp" ]
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "coaching-platform-logs-%{+YYYY.MM.dd}"
    template_name => "coaching-platform"
    template_pattern => "coaching-platform-*"
    template => {
      "index_patterns" => ["coaching-platform-*"],
      "settings" => {
        "number_of_shards" => 1,
        "number_of_replicas" => 0
      },
      "mappings" => {
        "properties" => {
          "@timestamp" => { "type" => "date" },
          "service_name" => { "type" => "keyword" },
          "request_id" => { "type" => "keyword" },
          "level" => { "type" => "keyword" },
          "message" => { "type" => "text" },
          "creator_id" => { "type" => "keyword" },
          "user_id" => { "type" => "keyword" },
          "endpoint" => { "type" => "keyword" },
          "response_time" => { "type" => "float" },
          "status_code" => { "type" => "integer" }
        }
      }
    }
  }
  
  stdout { codec => rubydebug }
}
```

#### Configuración de Filebeat

```yaml
# filebeat/filebeat.yml
filebeat.inputs:
- type: container
  paths:
    - '/var/lib/docker/containers/*/*.log'
  processors:
    - add_docker_metadata:
        host: "unix:///var/run/docker.sock"
    - decode_json_fields:
        fields: ["message"]
        target: ""
        overwrite_keys: true

output.logstash:
  hosts: ["logstash:5044"]

processors:
  - add_host_metadata:
      when.not.contains.tags: forwarded
  - add_docker_metadata: ~
  - add_kubernetes_metadata: ~

logging.level: info
logging.to_files: true
logging.files:
  path: /var/log/filebeat
  name: filebeat
  keepfiles: 7
  permissions: 0644
```

#### Implementación de X-Request-ID en FastAPI

```python
# shared/middleware/request_id.py
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

logger = logging.getLogger(__name__)

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware para generar y propagar X-Request-ID across services"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        # Obtener o generar X-Request-ID
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Agregar al contexto de la request
        request.state.request_id = request_id
        
        # Configurar logging context
        logger = logging.getLogger()
        old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.request_id = request_id
            return record
        
        logging.setLogRecordFactory(record_factory)
        
        try:
            response = await call_next(request)
            
            # Agregar X-Request-ID al response header
            response.headers["X-Request-ID"] = request_id
            
            return response
        finally:
            # Restaurar logging factory
            logging.setLogRecordFactory(old_factory)

# shared/clients/http_client.py
import httpx
from fastapi import Request
import logging

logger = logging.getLogger(__name__)

class ServiceClient:
    """Cliente HTTP que propaga X-Request-ID entre servicios"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url)
    
    async def request(
        self, 
        method: str, 
        endpoint: str, 
        request: Request = None,
        **kwargs
    ):
        """Realizar request propagando X-Request-ID"""
        headers = kwargs.get("headers", {})
        
        # Propagar X-Request-ID si está disponible
        if request and hasattr(request.state, 'request_id'):
            headers["X-Request-ID"] = request.state.request_id
        
        kwargs["headers"] = headers
        
        logger.info(
            f"Making {method} request to {endpoint}",
            extra={
                "endpoint": endpoint,
                "method": method,
                "service": "http_client"
            }
        )
        
        response = await self.client.request(method, endpoint, **kwargs)
        
        logger.info(
            f"Received response from {endpoint}",
            extra={
                "endpoint": endpoint,
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            }
        )
        
        return response

# Ejemplo de uso en cada servicio
# services/auth/main.py
from fastapi import FastAPI
from shared.middleware.request_id import RequestIDMiddleware
import logging
import json

# Configurar logging estructurado
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "service": "auth-service", "request_id": "%(request_id)s", "message": "%(message)s", "module": "%(name)s"}',
    datefmt='%Y-%m-%dT%H:%M:%S'
)

app = FastAPI(title="Auth Service")

# Agregar middleware de Request ID
app.add_middleware(RequestIDMiddleware)

@app.get("/health")
async def health_check(request: Request):
    logger.info("Health check requested")
    return {
        "status": "healthy",
        "service": "auth-service",
        "request_id": request.state.request_id
    }
```

#### Configuración de Prometheus con OpenTelemetry

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'coaching-platform-services'
    static_configs:
      - targets: 
          - 'auth-service:8001'
          - 'creator-hub-service:8002'
          - 'ai-engine-service:8003'
          - 'channel-service:8004'
    metrics_path: '/metrics'
    scrape_interval: 10s
    
  - job_name: 'elasticsearch'
    static_configs:
      - targets: ['elasticsearch:9200']
    metrics_path: '/_prometheus/metrics'
    
  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
      
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### Configuración de Kubernetes para Producción

```yaml
# Namespace
apiVersion: v1
kind: Namespace
metadata:
  name: coaching-platform

---
# ConfigMap para configuración compartida
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: coaching-platform
data:
  DATABASE_HOST: "postgres-service"
  REDIS_HOST: "redis-service"
  CHROMADB_HOST: "chromadb-service"
  OLLAMA_HOST: "ollama-service"

---
# Secret para credenciales
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: coaching-platform
type: Opaque
data:
  DATABASE_PASSWORD: <base64-encoded-password>
  JWT_SECRET: <base64-encoded-jwt-secret>
  REDIS_PASSWORD: <base64-encoded-redis-password>

---
# Deployment para AI Engine Service
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-engine-service
  namespace: coaching-platform
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-engine-service
  template:
    metadata:
      labels:
        app: ai-engine-service
    spec:
      containers:
      - name: ai-engine
        image: coaching-platform/ai-engine:latest
        ports:
        - containerPort: 8003
        env:
        - name: DATABASE_URL
          value: "postgresql://user:$(DATABASE_PASSWORD)@$(DATABASE_HOST):5432/coaching_platform"
        - name: CHROMADB_URL
          value: "http://$(CHROMADB_HOST):8000"
        - name: OLLAMA_URL
          value: "http://$(OLLAMA_HOST):11434"
        envFrom:
        - configMapRef:
            name: app-config
        - secretRef:
            name: app-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8003
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8003
          initialDelaySeconds: 5
          periodSeconds: 5

---
# Service para AI Engine
apiVersion: v1
kind: Service
metadata:
  name: ai-engine-service
  namespace: coaching-platform
spec:
  selector:
    app: ai-engine-service
  ports:
  - port: 8003
    targetPort: 8003
  type: ClusterIP

---
# HorizontalPodAutoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ai-engine-hpa
  namespace: coaching-platform
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ai-engine-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Consideraciones de Seguridad

### Implementación de Seguridad Multi-Capa

```python
# 1. Validación de Input
from pydantic import BaseModel, validator
import re

class MessageInput(BaseModel):
    content: str
    
    @validator('content')
    def validate_content(cls, v):
        # Sanitizar contenido
        if len(v.strip()) == 0:
            raise ValueError('Message content cannot be empty')
        
        if len(v) > 4000:
            raise ValueError('Message too long')
        
        # Detectar y bloquear contenido malicioso
        malicious_patterns = [
            r'<script.*?>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
        ]
        
        for pattern in malicious_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError('Potentially malicious content detected')
        
        return v.strip()

# 2. Rate Limiting por Tenant
class TenantRateLimiter:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def check_rate_limit(self, creator_id: str, endpoint: str) -> bool:
        key = f"rate_limit:{creator_id}:{endpoint}"
        current = await self.redis.get(key)
        
        if current is None:
            await self.redis.setex(key, 60, 1)  # 1 request per minute initially
            return True
        
        if int(current) >= self.get_limit_for_endpoint(endpoint):
            return False
        
        await self.redis.incr(key)
        return True
    
    def get_limit_for_endpoint(self, endpoint: str) -> int:
        limits = {
            "chat": 100,  # 100 messages per minute
            "upload": 10,  # 10 uploads per minute
            "embed": 50,   # 50 embedding requests per minute
        }
        return limits.get(endpoint, 30)

# 3. Encriptación de Datos Sensibles
from cryptography.fernet import Fernet
import os

class DataEncryption:
    def __init__(self):
        self.key = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key())
        self.cipher = Fernet(self.key)
    
    def encrypt_sensitive_data(self, data: str) -> str:
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        return self.cipher.decrypt(encrypted_data.encode()).decode()

# 4. Audit Logging
class AuditLogger:
    def __init__(self, db_session):
        self.db = db_session
    
    async def log_action(self, creator_id: str, action: str, 
                        resource: str, details: dict = None):
        audit_log = AuditLog(
            creator_id=creator_id,
            action=action,
            resource=resource,
            details=details or {},
            ip_address=self.get_client_ip(),
            user_agent=self.get_user_agent(),
            timestamp=datetime.utcnow()
        )
        
        self.db.add(audit_log)
        await self.db.commit()
```

Este diseño proporciona una base sólida y escalable para el MVP, con todas las consideraciones necesarias para soportar el crecimiento futuro hacia una plataforma multi-canal completa.

## Unit Tests

### Tests para DocumentProcessor._generate_document_id

```python
import pytest
import asyncio
import tempfile
import os
import hashlib
from unittest.mock import patch, mock_open
from shared.services.document_processor import DocumentProcessor

class TestDocumentProcessor:
    
    @pytest.fixture
    def document_processor(self):
        """Fixture para crear instancia de DocumentProcessor"""
        return DocumentProcessor(
            ai_engine_client=None,
            vector_store_client=None
        )
    
    @pytest.mark.asyncio
    async def test_generate_document_id_consistent_for_same_file(self, document_processor):
        """Test que verifica que el mismo archivo genera el mismo ID"""
        # Crear archivo temporal con contenido conocido
        test_content = b"This is test content for document ID generation"
        creator_id = "test_creator_123"
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name
        
        try:
            # Generar ID dos veces para el mismo archivo
            id1 = await document_processor._generate_document_id(temp_file_path, creator_id)
            id2 = await document_processor._generate_document_id(temp_file_path, creator_id)
            
            # Verificar que los IDs son idénticos
            assert id1 == id2
            assert id1.startswith("doc_")
            assert len(id1) == 28  # "doc_" + 24 caracteres de hash
            
        finally:
            os.unlink(temp_file_path)
    
    @pytest.mark.asyncio
    async def test_generate_document_id_different_for_different_creators(self, document_processor):
        """Test que verifica que diferentes creadores generan IDs diferentes para el mismo archivo"""
        test_content = b"Same content, different creators"
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name
        
        try:
            id1 = await document_processor._generate_document_id(temp_file_path, "creator_1")
            id2 = await document_processor._generate_document_id(temp_file_path, "creator_2")
            
            # Verificar que los IDs son diferentes
            assert id1 != id2
            assert id1.startswith("doc_")
            assert id2.startswith("doc_")
            
        finally:
            os.unlink(temp_file_path)
    
    @pytest.mark.asyncio
    async def test_generate_document_id_different_for_different_content(self, document_processor):
        """Test que verifica que diferentes contenidos generan IDs diferentes"""
        creator_id = "test_creator"
        
        # Crear dos archivos con contenido diferente
        with tempfile.NamedTemporaryFile(delete=False) as temp_file1:
            temp_file1.write(b"Content for file 1")
            temp_file1_path = temp_file1.name
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file2:
            temp_file2.write(b"Content for file 2")
            temp_file2_path = temp_file2.name
        
        try:
            id1 = await document_processor._generate_document_id(temp_file1_path, creator_id)
            id2 = await document_processor._generate_document_id(temp_file2_path, creator_id)
            
            # Verificar que los IDs son diferentes
            assert id1 != id2
            
        finally:
            os.unlink(temp_file1_path)
            os.unlink(temp_file2_path)
    
    @pytest.mark.asyncio
    async def test_generate_document_id_fallback_to_uuid_on_error(self, document_processor):
        """Test que verifica el fallback a UUID cuando no se puede leer el archivo"""
        non_existent_file = "/path/that/does/not/exist.txt"
        creator_id = "test_creator"
        
        # Mock UUID para tener un resultado predecible
        with patch('uuid.uuid4') as mock_uuid:
            mock_uuid.return_value.hex = "abcdef123456789012345678901234567890abcd"
            
            id_result = await document_processor._generate_document_id(non_existent_file, creator_id)
            
            # Verificar que se usa el fallback UUID
            assert id_result.startswith("doc_")
            assert "abcdef123456789012345678901234567890abcd"[:16] in id_result
            mock_uuid.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_document_id_expected_hash_format(self, document_processor):
        """Test que verifica el formato esperado del hash generado"""
        test_content = b"Known content for hash verification"
        creator_id = "known_creator"
        
        # Calcular hash esperado manualmente usando el mismo método chunked
        hash_obj = hashlib.sha256()
        hash_obj.update(test_content)
        hash_obj.update(creator_id.encode('utf-8'))
        expected_hash = hash_obj.hexdigest()[:16]
        expected_id = f"doc_{expected_hash}"
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name
        
        try:
            actual_id = await document_processor._generate_document_id(temp_file_path, creator_id)
            
            # Verificar que el ID generado coincide con el esperado
            assert actual_id == expected_id
            
        finally:
            os.unlink(temp_file_path)
    
    @pytest.mark.asyncio
    async def test_generate_document_id_uses_asyncio_to_thread(self, document_processor):
        """Test que verifica que se usa asyncio.to_thread para operaciones de archivo"""
        test_content = b"Test content"
        creator_id = "test_creator"
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name
        
        try:
            # Mock asyncio.to_thread para verificar que se llama
            with patch('asyncio.to_thread') as mock_to_thread:
                # Create a completed future with the expected hash
                hash_obj = hashlib.sha256()
                hash_obj.update(test_content)
                hash_obj.update(creator_id.encode('utf-8'))
                expected_hash = hash_obj.hexdigest()
                
                future = asyncio.Future()
                future.set_result(expected_hash)
                mock_to_thread.return_value = future
                
                await document_processor._generate_document_id(temp_file_path, creator_id)
                
                # Verificar que asyncio.to_thread fue llamado
                mock_to_thread.assert_called_once()
                
        finally:
            os.unlink(temp_file_path)
    
    @pytest.mark.asyncio
    async def test_generate_document_id_zero_length_file(self, document_processor):
        """Test que verifica el manejo correcto de archivos de longitud cero"""
        creator_id = "test_creator"
        
        # Crear archivo vacío
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # No escribir contenido - archivo vacío
            temp_file_path = temp_file.name
        
        try:
            # Generar ID para archivo vacío
            id_result = await document_processor._generate_document_id(temp_file_path, creator_id)
            
            # Verificar que se genera un ID válido
            assert id_result.startswith("doc_")
            assert len(id_result) == 20  # "doc_" + 16 caracteres
            
            # Verificar que es determinístico - mismo ID para mismo creador y archivo vacío
            id_result2 = await document_processor._generate_document_id(temp_file_path, creator_id)
            assert id_result == id_result2
            
            # Verificar que diferentes creadores generan IDs diferentes para archivo vacío
            id_different_creator = await document_processor._generate_document_id(temp_file_path, "different_creator")
            assert id_result != id_different_creator
            
        finally:
            os.unlink(temp_file_path)
    
    @pytest.mark.asyncio
    async def test_generate_document_id_specific_exceptions(self, document_processor):
        """Test que verifica el manejo específico de diferentes tipos de excepciones"""
        creator_id = "test_creator"
        
        # Test FileNotFoundError
        non_existent_file = "/path/that/does/not/exist.txt"
        with patch('uuid.uuid4') as mock_uuid:
            mock_uuid.return_value.hex = "filenotfound123456789012345678901234567890abcdef"
            
            id_result = await document_processor._generate_document_id(non_existent_file, creator_id)
            assert id_result.startswith("doc_")
            assert len(id_result) == 28  # "doc_" + 24 characters
            mock_uuid.assert_called_once()
        
        # Test PermissionError
        with patch('asyncio.to_thread') as mock_to_thread:
            mock_to_thread.side_effect = PermissionError("Permission denied")
            with patch('uuid.uuid4') as mock_uuid:
                mock_uuid.return_value.hex = "permission123456789012345678901234567890abcdef"
                
                id_result = await document_processor._generate_document_id("/some/file.txt", creator_id)
                assert id_result.startswith("doc_")
                assert len(id_result) == 28  # "doc_" + 24 characters
                mock_uuid.assert_called_once()
        
        # Test MemoryError should raise DocumentProcessingError
        with patch('asyncio.to_thread') as mock_to_thread:
            mock_to_thread.side_effect = MemoryError("File too large")
            
            with pytest.raises(DocumentProcessingError, match="File too large to process"):
                await document_processor._generate_document_id("/large/file.txt", creator_id)
    
    @pytest.mark.asyncio
    async def test_generate_document_id_semaphore_limits_concurrency(self, document_processor):
        """Test que verifica que el semáforo limita la concurrencia de lectura de archivos"""
        creator_id = "test_creator"
        
        # Crear múltiples archivos temporales
        temp_files = []
        for i in range(10):
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_file.write(f"Content for file {i}".encode())
            temp_file.close()
            temp_files.append(temp_file.name)
        
        try:
            # Mock asyncio.to_thread para simular operaciones lentas
            call_count = 0
            original_semaphore_value = document_processor._file_read_semaphore._value
            
            async def slow_hash_computation(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                # Simular operación lenta
                await asyncio.sleep(0.1)
                return f"hash_{call_count}"
            
            with patch('asyncio.to_thread', side_effect=slow_hash_computation):
                # Ejecutar múltiples operaciones concurrentes
                tasks = [
                    document_processor._generate_document_id(file_path, creator_id)
                    for file_path in temp_files
                ]
                
                # Verificar que el semáforo limita la concurrencia
                start_time = asyncio.get_event_loop().time()
                results = await asyncio.gather(*tasks)
                end_time = asyncio.get_event_loop().time()
                
                # Con semáforo de 4, 10 operaciones deberían tomar al menos 3 batches
                # (4 + 4 + 2 operaciones) * 0.1s = al menos 0.3s
                assert end_time - start_time >= 0.25  # Margen para timing
                
                # Verificar que todas las operaciones completaron
                assert len(results) == 10
                assert all(result.startswith("doc_hash_") for result in results)
                
                # Verificar que el semáforo se restauró
                assert document_processor._file_read_semaphore._value == original_semaphore_value
                
        finally:
            # Limpiar archivos temporales
            for file_path in temp_files:
                try:
                    os.unlink(file_path)
                except FileNotFoundError:
                    pass
    
    @pytest.mark.asyncio
    async def test_generate_document_id_chunked_reading_large_file(self, document_processor):
        """Test que verifica la lectura chunked para archivos grandes"""
        creator_id = "test_creator"
        
        # Crear archivo grande (simulado con contenido repetitivo)
        large_content = b"A" * 50000  # 50KB de contenido
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(large_content)
            temp_file_path = temp_file.name
        
        try:
            # Verificar que el método funciona con archivos grandes
            id_result = await document_processor._generate_document_id(temp_file_path, creator_id)
            
            # Verificar formato del ID
            assert id_result.startswith("doc_")
            assert len(id_result) == 20
            
            # Verificar que es determinístico
            id_result2 = await document_processor._generate_document_id(temp_file_path, creator_id)
            assert id_result == id_result2
            
        finally:
            os.unlink(temp_file_path)
    
    @pytest.mark.asyncio
    async def test_file_size_validation(self, document_processor):
        """Test que verifica la validación de tamaño de archivo"""
        # Mock max_upload_bytes para testing
        original_max_size = document_processor.max_upload_bytes
        document_processor.max_upload_bytes = 1024  # 1KB limit for testing
        document_processor.MAX_UPLOAD_BYTES = 1024  # Update legacy property too
        
        try:
            # Crear archivo que excede el límite
            large_content = b"A" * 2048  # 2KB content
            
            with tempfile.NamedTemporaryFile(delete=False, dir=document_processor.uploads_dir) as temp_file:
                temp_file.write(large_content)
                temp_file_path = temp_file.name
            
            try:
                # Debería lanzar ValidationError por tamaño excesivo
                with pytest.raises(ValidationError, match="Archivo demasiado grande"):
                    await document_processor._validate_file_format(temp_file_path)
                    
            finally:
                os.unlink(temp_file_path)
                
        finally:
            # Restaurar límite original
            document_processor.max_upload_bytes = original_max_size
            document_processor.MAX_UPLOAD_BYTES = original_max_size
    
    @pytest.mark.asyncio
    async def test_path_traversal_protection(self, document_processor):
        """Test que verifica la protección contra path traversal"""
        # Intentar acceder a archivo fuera del directorio permitido
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow",
            "C:\\Windows\\System32\\config\\SAM"
        ]
        
        for malicious_path in malicious_paths:
            with pytest.raises(ValidationError, match="Acceso a archivo no autorizado"):
                await document_processor._validate_file_format(malicious_path)
    
    @pytest.mark.asyncio
    async def test_document_id_collision_detection(self, document_processor):
        """Test que verifica la detección y resolución de colisiones de ID"""
        creator_id = "test_creator"
        base_id = "doc_abcdef123456789012345678"
        
        # Mock _document_id_exists para simular colisión
        with patch.object(document_processor, '_document_id_exists') as mock_exists:
            # Primera llamada: colisión detectada, segunda llamada: ID único
            mock_exists.side_effect = [True, False]
            
            # Mock time y secrets para entropy predecible
            with patch('time.time', return_value=1234567890.123456):
                with patch('secrets.token_hex', return_value='abcd'):
                    unique_id = await document_processor._ensure_unique_document_id(base_id, creator_id)
                    
                    # Verificar que se agregó entropy
                    assert unique_id != base_id
                    assert unique_id.startswith(base_id)
                    assert "_123456abcd" in unique_id
                    
                    # Verificar que se llamó _document_id_exists dos veces
                    assert mock_exists.call_count == 2
    
    @pytest.mark.asyncio
    async def test_secure_logging_no_sensitive_data(self, document_processor, caplog):
        """Test que verifica que el logging no expone datos sensibles"""
        # Crear archivo temporal con path que podría ser sensible
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt', 
                                       dir=document_processor.uploads_dir) as temp_file:
            temp_file.write(b"test content")
            temp_file_path = temp_file.name
        
        try:
            # Ejecutar validación exitosa
            await document_processor._validate_file_format(temp_file_path)
            
            # Verificar que los logs no contienen paths completos
            log_messages = [record.message for record in caplog.records]
            for message in log_messages:
                # No debería contener paths completos
                assert temp_file_path not in message
                assert "/tmp" not in message or "filename:" in message
                # Debería contener solo el nombre del archivo
                assert Path(temp_file_path).name in message or "validation" in message
                
        finally:
            os.unlink(temp_file_path)

    @pytest.mark.asyncio
    async def test_validate_file_format_permission_error(self, document_processor, caplog):
        """Test que verifica el manejo de PermissionError en _validate_file_format"""
        test_file_path = str(document_processor.uploads_dir / "test_file.txt")
        
        # Mock Path.stat para lanzar PermissionError
        with patch('pathlib.Path.stat', side_effect=PermissionError("Permission denied")):
            with pytest.raises(ValidationError, match="Error accediendo al archivo"):
                await document_processor._validate_file_format(test_file_path)
        
        # Verificar que los logs no exponen paths completos
        log_messages = [record.message for record in caplog.records if record.levelname == 'ERROR']
        assert len(log_messages) > 0
        
        for message in log_messages:
            # No debería contener path completo
            assert test_file_path not in message
            # Debería contener solo el nombre del archivo
            assert "test_file.txt" in message
            # Debería indicar el tipo de error
            assert "PermissionError" in message

    @pytest.mark.asyncio
    async def test_validate_file_format_os_error(self, document_processor, caplog):
        """Test que verifica el manejo de OSError en _validate_file_format"""
        test_file_path = str(document_processor.uploads_dir / "test_file.txt")
        
        # Mock Path.exists para lanzar OSError
        with patch('pathlib.Path.exists', side_effect=OSError("I/O error")):
            with pytest.raises(ValidationError, match="Error accediendo al archivo"):
                await document_processor._validate_file_format(test_file_path)
        
        # Verificar que los logs no exponen paths completos
        log_messages = [record.message for record in caplog.records if record.levelname == 'ERROR']
        assert len(log_messages) > 0
        
        for message in log_messages:
            # No debería contener path completo
            assert test_file_path not in message
            # Debería contener solo el nombre del archivo
            assert "test_file.txt" in message
            # Debería indicar el tipo de error
            assert "OSError" in message

    @pytest.mark.asyncio
    async def test_validate_file_format_stat_permission_error(self, document_processor, caplog):
        """Test que verifica el manejo de PermissionError específicamente en Path.stat()"""
        # Crear archivo real para que Path.exists() pase
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt', 
                                       dir=document_processor.uploads_dir) as temp_file:
            temp_file.write(b"test content")
            temp_file_path = temp_file.name
        
        try:
            # Mock solo Path.stat para simular permission error en file size check
            with patch.object(Path, 'stat', side_effect=PermissionError("Cannot access file stats")):
                with pytest.raises(ValidationError, match="Error accediendo al archivo"):
                    await document_processor._validate_file_format(temp_file_path)
            
            # Verificar logging seguro
            log_messages = [record.message for record in caplog.records if record.levelname == 'ERROR']
            assert len(log_messages) > 0
            
            for message in log_messages:
                # No debería exponer path completo
                assert temp_file_path not in message
                # Debería contener solo filename
                filename = Path(temp_file_path).name
                assert filename in message
                # Debería indicar tipo de error
                assert "PermissionError" in message
                
        finally:
            try:
                os.unlink(temp_file_path)
            except FileNotFoundError:
                pass

    @pytest.mark.asyncio
    async def test_validate_file_format_multiple_os_errors(self, document_processor, caplog):
        """Test que verifica el manejo de múltiples tipos de OSError"""
        test_file_path = str(document_processor.uploads_dir / "test_file.txt")
        
        # Test diferentes tipos de OSError
        os_errors = [
            OSError("I/O error"),
            FileNotFoundError("File not found"),
            IsADirectoryError("Is a directory"),
            PermissionError("Permission denied")
        ]
        
        for error in os_errors:
            caplog.clear()  # Limpiar logs entre tests
            
            with patch('pathlib.Path.resolve', side_effect=error):
                with pytest.raises(ValidationError, match="Error accediendo al archivo"):
                    await document_processor._validate_file_format(test_file_path)
            
            # Verificar logging seguro para cada tipo de error
            log_messages = [record.message for record in caplog.records if record.levelname == 'ERROR']
            assert len(log_messages) > 0
            
            for message in log_messages:
                # No debería exponer path completo
                assert test_file_path not in message
                # Debería contener solo filename
                assert "test_file.txt" in message
                # Debería indicar tipo de error
                assert type(error).__name__ in message
    
    @pytest.mark.asyncio
    async def test_uploads_directory_creation(self):
        """Test que verifica la creación automática del directorio de uploads"""
        with tempfile.TemporaryDirectory() as temp_dir:
            uploads_path = Path(temp_dir) / "test_uploads"
            
            # El directorio no existe inicialmente
            assert not uploads_path.exists()
            
            # Crear DocumentProcessor debería crear el directorio
            processor = DocumentProcessor(
                ai_engine_client=None,
                vector_store_client=None,
                uploads_dir=str(uploads_path),
                create_uploads_dir=True
            )
            
            # Verificar que el directorio fue creado
            assert uploads_path.exists()
            assert uploads_path.is_dir()
            assert processor.uploads_dir == uploads_path.resolve()
    
    @pytest.mark.asyncio
    async def test_uploads_directory_validation_failure_no_create(self):
        """Test que verifica fallo cuando directorio no existe y create_if_missing=False"""
        with tempfile.TemporaryDirectory() as temp_dir:
            non_existent_path = Path(temp_dir) / "non_existent"
            
            # Debería fallar si el directorio no existe y no se permite crear
            with pytest.raises(ValidationError, match="Uploads directory does not exist"):
                DocumentProcessor(
                    ai_engine_client=None,
                    vector_store_client=None,
                    uploads_dir=str(non_existent_path),
                    create_uploads_dir=False
                )
    
    @pytest.mark.asyncio
    async def test_uploads_directory_restricted_path_validation(self):
        """Test que verifica la validación de paths restringidos del sistema"""
        restricted_paths = [
            "/etc/passwd",
            "/sys/kernel",
            "/proc/version",
            "/root/sensitive"
        ]
        
        # En Windows, agregar paths específicos
        if os.name == 'nt':
            restricted_paths.extend([
                "C:/Windows/System32",
                "C:/Program Files/test"
            ])
        
        for restricted_path in restricted_paths:
            with pytest.raises(ValidationError, match="restricted system path"):
                DocumentProcessor(
                    ai_engine_client=None,
                    vector_store_client=None,
                    uploads_dir=restricted_path,
                    create_uploads_dir=True
                )
    
    @pytest.mark.asyncio
    async def test_uploads_directory_not_directory_validation(self):
        """Test que verifica fallo cuando el path es un archivo, no directorio"""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_path = temp_file.name
        
        try:
            # Debería fallar si el path es un archivo
            with pytest.raises(ValidationError, match="not a directory"):
                DocumentProcessor(
                    ai_engine_client=None,
                    vector_store_client=None,
                    uploads_dir=temp_file_path,
                    create_uploads_dir=False
                )
        finally:
            os.unlink(temp_file_path)
    
    @pytest.mark.asyncio
    async def test_uploads_directory_permission_validation(self):
        """Test que verifica la validación de permisos de lectura/escritura"""
        with tempfile.TemporaryDirectory() as temp_dir:
            uploads_path = Path(temp_dir) / "test_uploads"
            uploads_path.mkdir()
            
            # Crear DocumentProcessor debería verificar permisos
            processor = DocumentProcessor(
                ai_engine_client=None,
                vector_store_client=None,
                uploads_dir=str(uploads_path),
                create_uploads_dir=False
            )
            
            # Verificar que el directorio fue validado correctamente
            assert processor.uploads_dir == uploads_path.resolve()
    
    @pytest.mark.asyncio
    async def test_uploads_directory_default_path(self):
        """Test que verifica el uso del path por defecto cuando no se especifica"""
        # Mock para evitar crear directorio real en /app/uploads
        with patch.object(DocumentProcessor, '_setup_uploads_directory') as mock_setup:
            processor = DocumentProcessor(
                ai_engine_client=None,
                vector_store_client=None,
                uploads_dir=None,  # Usar path por defecto
                create_uploads_dir=True
            )
            
            # Verificar que se usó el path por defecto
            expected_path = DocumentProcessor.UPLOADS_DIR.resolve()
            assert processor.uploads_dir == expected_path
            
            # Verificar que se llamó el setup
            mock_setup.assert_called_once_with(True)
    
    @pytest.mark.asyncio
    async def test_uploads_directory_setup_error_handling(self):
        """Test que verifica el manejo de errores durante setup del directorio"""
        with tempfile.TemporaryDirectory() as temp_dir:
            uploads_path = Path(temp_dir) / "test_uploads"
            
            # Mock mkdir para simular error de creación
            with patch.object(Path, 'mkdir', side_effect=OSError("Permission denied")):
                with pytest.raises(ValidationError, match="Cannot create uploads directory"):
                    DocumentProcessor(
                        ai_engine_client=None,
                        vector_store_client=None,
                        uploads_dir=str(uploads_path),
                        create_uploads_dir=True
                    )
    
    @pytest.mark.asyncio
    async def test_uploads_directory_write_permission_test(self):
        """Test que verifica la prueba de permisos de escritura"""
        with tempfile.TemporaryDirectory() as temp_dir:
            uploads_path = Path(temp_dir) / "test_uploads"
            uploads_path.mkdir()
            
            # Mock touch para simular fallo de escritura
            with patch.object(Path, 'touch', side_effect=PermissionError("Write denied")):
                with pytest.raises(ValidationError, match="No write permissions"):
                    DocumentProcessor(
                        ai_engine_client=None,
                        vector_store_client=None,
                        uploads_dir=str(uploads_path),
                        create_uploads_dir=False
                    )
```

### Tests para WebSocketManager

```python
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import WebSocket
from shared.services.websocket_manager import WebSocketManager

class TestWebSocketManager:
    
    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client para testing"""
        mock_redis = AsyncMock()
        mock_redis.hset = AsyncMock()
        mock_redis.hgetall = AsyncMock()
        mock_redis.hdel = AsyncMock()
        return mock_redis
    
    @pytest.fixture
    def websocket_manager(self, mock_redis_client):
        """Fixture para crear instancia de WebSocketManager"""
        manager = WebSocketManager("redis://test:6379")
        # Mock el cliente Redis
        with patch.object(manager, '_get_redis_client', return_value=mock_redis_client):
            yield manager
    
    @pytest.fixture
    def mock_websocket(self):
        """Mock WebSocket para testing"""
        websocket = AsyncMock(spec=WebSocket)
        websocket.accept = AsyncMock()
        websocket.send_json = AsyncMock()
        websocket.close = AsyncMock()
        return websocket
    
    @pytest.mark.asyncio
    async def test_connect_adds_connection_to_registry(self, websocket_manager, mock_websocket, mock_redis_client):
        """Test que verifica que connect agrega la conexión al registry"""
        creator_id = "creator_123"
        session_id = "session_456"
        expected_connection_id = f"{creator_id}_{session_id}"
        
        await websocket_manager.connect(mock_websocket, creator_id, session_id)
        
        # Verificar que WebSocket fue aceptado
        mock_websocket.accept.assert_called_once()
        
        # Verificar que la conexión fue agregada al registry local
        assert expected_connection_id in websocket_manager.active_connections
        assert websocket_manager.active_connections[expected_connection_id] == mock_websocket
        
        # Verificar que la conexión fue registrada en Redis
        mock_redis_client.hset.assert_called_once()
        call_args = mock_redis_client.hset.call_args
        assert call_args[0][0] == "active_connections"
        assert call_args[0][1] == expected_connection_id
        
        # Verificar el contenido del JSON almacenado en Redis
        stored_data = json.loads(call_args[0][2])
        assert stored_data["creator_id"] == creator_id
        assert stored_data["session_id"] == session_id
        assert "connected_at" in stored_data
    
    @pytest.mark.asyncio
    async def test_send_message_success(self, websocket_manager, mock_websocket):
        """Test que verifica el envío exitoso de mensajes"""
        connection_id = "creator_123_session_456"
        message = {"type": "test", "content": "Hello World"}
        
        # Agregar conexión manualmente al registry
        async with websocket_manager._connections_lock:
            websocket_manager.active_connections[connection_id] = mock_websocket
        
        await websocket_manager.send_message(connection_id, message)
        
        # Verificar que el mensaje fue enviado
        mock_websocket.send_json.assert_called_once_with(message)
    
    @pytest.mark.asyncio
    async def test_send_message_handles_connection_error(self, websocket_manager, mock_websocket):
        """Test que verifica el manejo de errores en envío de mensajes"""
        connection_id = "creator_123_session_456"
        message = {"type": "test", "content": "Hello World"}
        
        # Configurar WebSocket para lanzar excepción
        mock_websocket.send_json.side_effect = Exception("Connection closed")
        
        # Agregar conexión al registry
        async with websocket_manager._connections_lock:
            websocket_manager.active_connections[connection_id] = mock_websocket
        
        # Mock _remove_connection para verificar que se llama
        with patch.object(websocket_manager, '_remove_connection') as mock_remove:
            await websocket_manager.send_message(connection_id, message)
            
            # Verificar que se intentó remover la conexión
            mock_remove.assert_called_once_with(connection_id)
    
    @pytest.mark.asyncio
    async def test_get_creator_connections_filters_by_creator(self, websocket_manager, mock_redis_client):
        """Test que verifica el filtrado de conexiones por creador"""
        creator_id = "creator_123"
        
        # Mock datos de Redis
        mock_redis_data = {
            "creator_123_session_1": json.dumps({
                "creator_id": "creator_123",
                "session_id": "session_1",
                "connected_at": "2023-01-01T00:00:00"
            }),
            "creator_456_session_2": json.dumps({
                "creator_id": "creator_456",
                "session_id": "session_2",
                "connected_at": "2023-01-01T00:00:00"
            }),
            "creator_123_session_3": json.dumps({
                "creator_id": "creator_123",
                "session_id": "session_3",
                "connected_at": "2023-01-01T00:00:00"
            })
        }
        
        mock_redis_client.hgetall.return_value = mock_redis_data
        
        # Agregar algunas conexiones al registry local
        async with websocket_manager._connections_lock:
            websocket_manager.active_connections["creator_123_session_1"] = AsyncMock()
            websocket_manager.active_connections["creator_123_session_3"] = AsyncMock()
        
        connections = await websocket_manager.get_creator_connections(creator_id)
        
        # Verificar que solo se devuelven conexiones del creador especificado
        assert len(connections) == 2
        assert "creator_123_session_1" in connections
        assert "creator_123_session_3" in connections
        assert "creator_456_session_2" not in connections
    
    @pytest.mark.asyncio
    async def test_remove_connection_cleans_up_properly(self, websocket_manager, mock_redis_client):
        """Test que verifica la limpieza correcta de conexiones"""
        connection_id = "creator_123_session_456"
        
        # Agregar conexión al registry local
        async with websocket_manager._connections_lock:
            websocket_manager.active_connections[connection_id] = AsyncMock()
        
        await websocket_manager._remove_connection(connection_id)
        
        # Verificar que la conexión fue removida del registry local
        assert connection_id not in websocket_manager.active_connections
        
        # Verificar que la conexión fue removida de Redis
        mock_redis_client.hdel.assert_called_once_with("active_connections", connection_id)
    
    @pytest.mark.asyncio
    async def test_disconnect_closes_websocket_and_removes_connection(self, websocket_manager, mock_websocket):
        """Test que verifica que disconnect cierra el WebSocket y remueve la conexión"""
        connection_id = "creator_123_session_456"
        
        # Agregar conexión al registry
        async with websocket_manager._connections_lock:
            websocket_manager.active_connections[connection_id] = mock_websocket
        
        # Mock _remove_connection
        with patch.object(websocket_manager, '_remove_connection') as mock_remove:
            await websocket_manager.disconnect(connection_id)
            
            # Verificar que el WebSocket fue cerrado
            mock_websocket.close.assert_called_once()
            
            # Verificar que la conexión fue removida
            mock_remove.assert_called_once_with(connection_id)
    
    @pytest.mark.asyncio
    async def test_thread_safety_with_concurrent_operations(self, websocket_manager):
        """Test que verifica thread safety con operaciones concurrentes"""
        connection_ids = [f"creator_123_session_{i}" for i in range(10)]
        mock_websockets = [AsyncMock(spec=WebSocket) for _ in range(10)]
        
        # Función para agregar conexión
        async def add_connection(conn_id, websocket):
            async with websocket_manager._connections_lock:
                websocket_manager.active_connections[conn_id] = websocket
        
        # Función para remover conexión
        async def remove_connection(conn_id):
            async with websocket_manager._connections_lock:
                if conn_id in websocket_manager.active_connections:
                    del websocket_manager.active_connections[conn_id]
        
        # Ejecutar operaciones concurrentes
        tasks = []
        for i, (conn_id, websocket) in enumerate(zip(connection_ids, mock_websockets)):
            if i % 2 == 0:
                tasks.append(add_connection(conn_id, websocket))
            else:
                tasks.append(remove_connection(conn_id))
        
        await asyncio.gather(*tasks)
        
        # Verificar que el estado final es consistente
        # Solo las conexiones con índice par deberían estar presentes
        expected_connections = [conn_id for i, conn_id in enumerate(connection_ids) if i % 2 == 0]
        
        async with websocket_manager._connections_lock:
            actual_connections = list(websocket_manager.active_connections.keys())
        
        assert set(actual_connections) == set(expected_connections)
    
    @pytest.mark.asyncio
    async def test_concurrent_connect_disconnect_operations(self, websocket_manager, mock_redis_client):
        """Test que verifica operaciones concurrentes de connect y disconnect"""
        # Crear múltiples WebSockets mock
        websockets = [AsyncMock(spec=WebSocket) for _ in range(20)]
        connection_ids = []
        
        # Función para conectar
        async def connect_websocket(index):
            creator_id = f"creator_{index % 5}"  # 5 creadores diferentes
            session_id = f"session_{index}"
            connection_id = f"{creator_id}_{session_id}"
            connection_ids.append(connection_id)
            
            await websocket_manager.connect(websockets[index], creator_id, session_id)
            return connection_id
        
        # Función para desconectar
        async def disconnect_websocket(connection_id):
            await websocket_manager.disconnect(connection_id)
        
        # Ejecutar conexiones concurrentes
        connect_tasks = [connect_websocket(i) for i in range(20)]
        connected_ids = await asyncio.gather(*connect_tasks)
        
        # Verificar que todas las conexiones fueron establecidas
        async with websocket_manager._connections_lock:
            assert len(websocket_manager.active_connections) == 20
        
        # Ejecutar desconexiones concurrentes para la mitad de las conexiones
        disconnect_tasks = [disconnect_websocket(conn_id) for conn_id in connected_ids[:10]]
        await asyncio.gather(*disconnect_tasks)
        
        # Verificar que solo quedan 10 conexiones
        async with websocket_manager._connections_lock:
            assert len(websocket_manager.active_connections) == 10
        
        # Verificar que las conexiones correctas permanecen
        remaining_ids = connected_ids[10:]
        async with websocket_manager._connections_lock:
            for conn_id in remaining_ids:
                assert conn_id in websocket_manager.active_connections
    
    @pytest.mark.asyncio
    async def test_concurrent_send_message_operations(self, websocket_manager):
        """Test que verifica envío concurrente de mensajes"""
        # Configurar conexiones
        connection_ids = [f"creator_123_session_{i}" for i in range(10)]
        websockets = [AsyncMock(spec=WebSocket) for _ in range(10)]
        
        # Agregar conexiones al registry
        async with websocket_manager._connections_lock:
            for conn_id, ws in zip(connection_ids, websockets):
                websocket_manager.active_connections[conn_id] = ws
        
        # Función para enviar mensaje
        async def send_test_message(conn_id, message_id):
            message = {"type": "test", "id": message_id, "content": f"Message {message_id}"}
            await websocket_manager.send_message(conn_id, message)
        
        # Enviar múltiples mensajes concurrentemente
        tasks = []
        for i, conn_id in enumerate(connection_ids):
            for j in range(5):  # 5 mensajes por conexión
                tasks.append(send_test_message(conn_id, f"{i}_{j}"))
        
        await asyncio.gather(*tasks)
        
        # Verificar que todos los WebSockets recibieron los mensajes correctos
        for ws in websockets:
            assert ws.send_json.call_count == 5
    
    @pytest.mark.asyncio
    async def test_stale_connection_cleanup_logic(self, websocket_manager, mock_redis_client):
        """Test que verifica la lógica de limpieza de conexiones stale"""
        creator_id = "creator_123"
        
        # Mock datos de Redis con conexiones stale y activas
        mock_redis_data = {
            "creator_123_session_active": json.dumps({
                "creator_id": "creator_123",
                "session_id": "session_active",
                "connected_at": "2023-01-01T00:00:00"
            }),
            "creator_123_session_stale1": json.dumps({
                "creator_id": "creator_123",
                "session_id": "session_stale1",
                "connected_at": "2023-01-01T00:00:00"
            }),
            "creator_123_session_stale2": json.dumps({
                "creator_id": "creator_123",
                "session_id": "session_stale2",
                "connected_at": "2023-01-01T00:00:00"
            })
        }
        
        mock_redis_client.hgetall.return_value = mock_redis_data
        
        # Solo agregar una conexión activa al registry local
        async with websocket_manager._connections_lock:
            websocket_manager.active_connections["creator_123_session_active"] = AsyncMock()
        
        # Llamar get_creator_connections que debería limpiar conexiones stale
        connections = await websocket_manager.get_creator_connections(creator_id)
        
        # Verificar que solo se devuelve la conexión activa
        assert len(connections) == 1
        assert "creator_123_session_active" in connections
        
        # Verificar que las conexiones stale fueron removidas de Redis
        expected_hdel_calls = [
            (("active_connections", "creator_123_session_stale1"),),
            (("active_connections", "creator_123_session_stale2"),)
        ]
        
        actual_hdel_calls = mock_redis_client.hdel.call_args_list
        assert len(actual_hdel_calls) == 2
        
        # Verificar que se llamó hdel para las conexiones stale
        for call in actual_hdel_calls:
            assert call[0] in [call[0] for call in expected_hdel_calls]
    
    @pytest.mark.asyncio
    async def test_stale_connection_detection_with_corrupted_data(self, websocket_manager, mock_redis_client):
        """Test que verifica la detección de conexiones stale con datos corruptos"""
        creator_id = "creator_123"
        
        # Mock datos de Redis con JSON corrupto
        mock_redis_data = {
            "creator_123_session_valid": json.dumps({
                "creator_id": "creator_123",
                "session_id": "session_valid",
                "connected_at": "2023-01-01T00:00:00"
            }),
            "creator_123_session_corrupted": "invalid json data",
            "creator_123_session_missing_fields": json.dumps({
                "session_id": "session_missing",
                # creator_id faltante
                "connected_at": "2023-01-01T00:00:00"
            })
        }
        
        mock_redis_client.hgetall.return_value = mock_redis_data
        
        # Agregar conexión válida al registry local
        async with websocket_manager._connections_lock:
            websocket_manager.active_connections["creator_123_session_valid"] = AsyncMock()
        
        connections = await websocket_manager.get_creator_connections(creator_id)
        
        # Verificar que solo se devuelve la conexión válida
        assert len(connections) == 1
        assert "creator_123_session_valid" in connections
        
        # Verificar que las conexiones con datos corruptos fueron removidas
        assert mock_redis_client.hdel.call_count == 2
        
        # Verificar los argumentos de las llamadas hdel
        hdel_calls = mock_redis_client.hdel.call_args_list
        removed_connections = [call[0][1] for call in hdel_calls]
        assert "creator_123_session_corrupted" in removed_connections
        assert "creator_123_session_missing_fields" in removed_connections
    
    @pytest.mark.asyncio
    async def test_redis_connection_failure_handling(self, websocket_manager):
        """Test que verifica el manejo de fallos de conexión Redis"""
        from redis.exceptions import ConnectionError as RedisConnectionError
        
        # Mock Redis client que falla
        mock_redis_client = AsyncMock()
        mock_redis_client.hgetall.side_effect = RedisConnectionError("Redis connection failed")
        
        with patch.object(websocket_manager, '_get_redis_client', return_value=mock_redis_client):
            # get_creator_connections debería manejar el error gracefully
            connections = await websocket_manager.get_creator_connections("creator_123")
            
            # Debería devolver lista vacía en caso de error
            assert connections == []
            
            # Verificar que se intentó conectar a Redis
            mock_redis_client.hgetall.assert_called_once_with("active_connections")
    
    @pytest.mark.asyncio
    async def test_websocket_manager_with_fakeredis(self):
        """Test usando fakeredis para simular Redis real"""
        try:
            import fakeredis.aioredis as fakeredis
        except ImportError:
            pytest.skip("fakeredis not available")
        
        # Crear WebSocketManager con fakeredis
        fake_redis = fakeredis.FakeRedis(decode_responses=True)
        websocket_manager = WebSocketManager()
        websocket_manager.redis_client = fake_redis
        
        # Test completo con Redis simulado
        creator_id = "creator_test"
        session_id = "session_test"
        connection_id = f"{creator_id}_{session_id}"
        
        mock_websocket = AsyncMock(spec=WebSocket)
        
        # Conectar
        await websocket_manager.connect(mock_websocket, creator_id, session_id)
        
        # Verificar que la conexión está en Redis
        redis_data = await fake_redis.hgetall("active_connections")
        assert connection_id in redis_data
        
        # Verificar que get_creator_connections funciona
        connections = await websocket_manager.get_creator_connections(creator_id)
        assert connection_id in connections
        
        # Desconectar
        await websocket_manager.disconnect(connection_id)
        
        # Verificar que la conexión fue removida
        redis_data = await fake_redis.hgetall("active_connections")
        assert connection_id not in redis_data
    
    @pytest.mark.asyncio
    async def test_redis_client_initialization_with_decode_responses(self, websocket_manager):
        """Test que verifica que el cliente Redis se inicializa con decode_responses=True"""
        with patch('redis.asyncio.from_url') as mock_from_url:
            mock_client = AsyncMock()
            mock_from_url.return_value = mock_client
            
            # Llamar _get_redis_client para inicializar el cliente
            client = await websocket_manager._get_redis_client()
            
            # Verificar que from_url fue llamado con decode_responses=True
            mock_from_url.assert_called_once_with(
                websocket_manager.redis_url, 
                decode_responses=True
            )
            
            assert client == mock_client
    
    @pytest.mark.asyncio
    async def test_redis_client_initialization_failure(self):
        """Test que verifica el manejo de fallos en inicialización de Redis client"""
        from redis.exceptions import ConnectionError as RedisConnectionError
        
        websocket_manager = WebSocketManager("redis://invalid:6379")
        
        with patch('redis.asyncio.from_url') as mock_from_url:
            mock_client = AsyncMock()
            mock_client.ping.side_effect = RedisConnectionError("Connection refused")
            mock_from_url.return_value = mock_client
            
            # La inicialización debería fallar con excepción específica
            with pytest.raises(RedisConnectionError):
                await websocket_manager._get_redis_client()
            
            # Verificar que se intentó hacer ping
            mock_client.ping.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_with_redis_failure(self, mock_redis_client):
        """Test que verifica connect cuando Redis falla"""
        from redis.exceptions import TimeoutError as RedisTimeoutError
        
        websocket_manager = WebSocketManager()
        mock_websocket = AsyncMock(spec=WebSocket)
        
        # Configurar Redis client que falla en hset
        mock_redis_client.hset.side_effect = RedisTimeoutError("Redis timeout")
        
        with patch.object(websocket_manager, '_get_redis_client', return_value=mock_redis_client):
            # Connect debería completarse a pesar del error de Redis
            await websocket_manager.connect(mock_websocket, "creator_123", "session_456")
            
            # Verificar que WebSocket fue aceptado
            mock_websocket.accept.assert_called_once()
            
            # Verificar que la conexión está en el registry local
            connection_id = "creator_123_session_456"
            async with websocket_manager._connections_lock:
                assert connection_id in websocket_manager.active_connections
    
    @pytest.mark.asyncio
    async def test_graceful_shutdown(self, websocket_manager, mock_redis_client):
        """Test que verifica el shutdown graceful del WebSocketManager"""
        # Configurar múltiples conexiones activas
        connection_ids = [f"creator_{i}_session_{i}" for i in range(5)]
        websockets = [AsyncMock(spec=WebSocket) for _ in range(5)]
        
        # Configurar WebSocket mocks
        for ws in websockets:
            ws.client_state = MagicMock()
            ws.client_state.DISCONNECTED = False
            ws.close = AsyncMock()
        
        # Agregar conexiones al registry
        async with websocket_manager._connections_lock:
            for conn_id, ws in zip(connection_ids, websockets):
                websocket_manager.active_connections[conn_id] = ws
        
        # Configurar Redis client mock
        websocket_manager.redis_client = mock_redis_client
        mock_redis_client.close = AsyncMock()
        mock_redis_client.hdel = AsyncMock()
        
        # Ejecutar shutdown
        await websocket_manager.shutdown()
        
        # Verificar que todas las conexiones WebSocket fueron cerradas
        for ws in websockets:
            ws.close.assert_called_once_with(code=1001, reason="Server shutdown")
        
        # Verificar que el registry local fue limpiado
        async with websocket_manager._connections_lock:
            assert len(websocket_manager.active_connections) == 0
        
        # Verificar que Redis client fue cerrado
        mock_redis_client.close.assert_called_once()
        
        # Verificar que las conexiones fueron removidas de Redis
        assert mock_redis_client.hdel.call_count == 5
    
    @pytest.mark.asyncio
    async def test_shutdown_with_websocket_errors(self, websocket_manager, mock_redis_client):
        """Test que verifica shutdown cuando algunos WebSockets fallan al cerrar"""
        # Configurar conexiones donde algunas fallan al cerrar
        connection_ids = [f"creator_1_session_{i}" for i in range(3)]
        websockets = [AsyncMock(spec=WebSocket) for _ in range(3)]
        
        # Configurar el primer WebSocket para que falle
        websockets[0].client_state = MagicMock()
        websockets[0].client_state.DISCONNECTED = False
        websockets[0].close = AsyncMock(side_effect=Exception("Connection already closed"))
        
        # Configurar los otros WebSockets normalmente
        for ws in websockets[1:]:
            ws.client_state = MagicMock()
            ws.client_state.DISCONNECTED = False
            ws.close = AsyncMock()
        
        # Agregar conexiones al registry
        async with websocket_manager._connections_lock:
            for conn_id, ws in zip(connection_ids, websockets):
                websocket_manager.active_connections[conn_id] = ws
        
        websocket_manager.redis_client = mock_redis_client
        mock_redis_client.close = AsyncMock()
        mock_redis_client.hdel = AsyncMock()
        
        # Shutdown debería completarse exitosamente a pesar del error
        await websocket_manager.shutdown()
        
        # Verificar que se intentó cerrar todas las conexiones
        for ws in websockets:
            ws.close.assert_called_once()
        
        # Verificar que el registry fue limpiado
        async with websocket_manager._connections_lock:
            assert len(websocket_manager.active_connections) == 0
        
        # Verificar que Redis client fue cerrado
        mock_redis_client.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_shutdown_with_redis_error(self, websocket_manager):
        """Test que verifica shutdown cuando Redis falla"""
        # Configurar conexión
        connection_id = "creator_1_session_1"
        websocket = AsyncMock(spec=WebSocket)
        websocket.client_state = MagicMock()
        websocket.client_state.DISCONNECTED = False
        websocket.close = AsyncMock()
        
        async with websocket_manager._connections_lock:
            websocket_manager.active_connections[connection_id] = websocket
        
        # Configurar Redis client que falla
        mock_redis_client = AsyncMock()
        mock_redis_client.close = AsyncMock(side_effect=Exception("Redis connection lost"))
        mock_redis_client.hdel = AsyncMock(side_effect=Exception("Redis connection lost"))
        websocket_manager.redis_client = mock_redis_client
        
        # Shutdown debería completarse a pesar de errores de Redis
        await websocket_manager.shutdown()
        
        # Verificar que WebSocket fue cerrado
        websocket.close.assert_called_once()
        
        # Verificar que el registry fue limpiado
        async with websocket_manager._connections_lock:
            assert len(websocket_manager.active_connections) == 0
        
        # Verificar que se intentó cerrar Redis client
        mock_redis_client.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_shutdown_timeout_handling(self, websocket_manager):
        """Test que verifica el manejo de timeout durante shutdown"""
        # Configurar WebSocket que nunca responde al close
        connection_id = "creator_1_session_1"
        websocket = AsyncMock(spec=WebSocket)
        websocket.client_state = MagicMock()
        websocket.client_state.DISCONNECTED = False
        
        # Simular WebSocket que tarda mucho en cerrar
        async def slow_close(*args, **kwargs):
            await asyncio.sleep(35)  # Más que el timeout de 30 segundos
        
        websocket.close = slow_close
        
        async with websocket_manager._connections_lock:
            websocket_manager.active_connections[connection_id] = websocket
        
        mock_redis_client = AsyncMock()
        mock_redis_client.close = AsyncMock()
        websocket_manager.redis_client = mock_redis_client
        
        # Shutdown debería completarse con timeout
        start_time = asyncio.get_event_loop().time()
        await websocket_manager.shutdown()
        end_time = asyncio.get_event_loop().time()
        
        # Verificar que no tardó más de 35 segundos (timeout + margen)
        assert end_time - start_time < 35
        
        # Verificar que el registry fue limpiado
        async with websocket_manager._connections_lock:
            assert len(websocket_manager.active_connections) == 0
        
        # Verificar que Redis client fue cerrado
        mock_redis_client.close.assert_called_once()
```