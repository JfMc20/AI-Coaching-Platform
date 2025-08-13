---
inclusion: always
---

# Shared Models & Data Structures

## Pydantic Models Organization

### Core Model Structure
All Pydantic models MUST follow this organization pattern:

```
shared/
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

## Required Model Fields

### Base Model Requirements
Every model MUST inherit from a base class with these fields:
```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class BaseTimestampModel(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class BaseTenantModel(BaseTimestampModel):
    creator_id: str = Field(..., description="Creator/tenant identifier")
```

### Authentication Models
```python
class CreatorCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)
    company_name: Optional[str] = Field(None, max_length=255)

class CreatorResponse(BaseTenantModel):
    id: str
    email: str
    full_name: str
    company_name: Optional[str]
    is_active: bool
    subscription_tier: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
```

### Document Processing Models
```python
from enum import Enum
from typing import List, Dict, Any

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class DocumentChunk(BaseModel):
    id: str
    content: str = Field(..., min_length=1, max_length=4000)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding_vector: Optional[List[float]] = None
    chunk_index: int = Field(..., ge=0)
    token_count: int = Field(..., ge=0)

class ProcessingResult(BaseTenantModel):
    document_id: str
    status: ProcessingStatus
    chunks: List[DocumentChunk]
    total_chunks: int = Field(..., ge=0)
    processing_time_seconds: float = Field(..., ge=0)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

### Widget Configuration Models
```python
class WidgetTheme(BaseModel):
    primary_color: str = Field(
        default="#007bff", 
        regex=r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$',
        description="Primary brand color in hex format"
    )
    secondary_color: str = Field(
        default="#6c757d",
        regex=r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$',
        description="Secondary color in hex format"
    )
    background_color: str = Field(default="#ffffff")
    text_color: str = Field(default="#212529")
    border_radius: int = Field(default=8, ge=0, le=50)

class WidgetBehavior(BaseModel):
    auto_open: bool = Field(default=False)
    greeting_message: str = Field(
        default="¡Hola! ¿En qué puedo ayudarte?",
        max_length=500
    )
    placeholder_text: str = Field(
        default="Escribe tu mensaje...",
        max_length=100
    )
    show_typing_indicator: bool = Field(default=True)
    response_delay_ms: int = Field(default=1000, ge=0, le=5000)

class WidgetConfig(BaseTenantModel):
    widget_id: str
    is_active: bool = Field(default=True)
    theme: WidgetTheme = Field(default_factory=WidgetTheme)
    behavior: WidgetBehavior = Field(default_factory=WidgetBehavior)
    allowed_domains: List[str] = Field(default_factory=list)
    rate_limit_per_minute: int = Field(default=10, ge=1, le=100)
    embed_code: Optional[str] = None
```

## Validation Rules

### Common Validators
```python
from pydantic import validator
import re

class CommonValidators:
    @validator('email')
    def validate_email(cls, v):
        # Additional email validation beyond EmailStr
        if len(v) > 254:
            raise ValueError('Email too long')
        return v.lower()
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain digit')
        return v
    
    @validator('domain')
    def validate_domain(cls, v):
        pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        if not re.match(pattern, v):
            raise ValueError('Invalid domain format')
        return v.lower()
```

### Business Logic Validators
```python
class BusinessValidators:
    @validator('chunk_size')
    def validate_chunk_size(cls, v):
        if v < 100 or v > 2000:
            raise ValueError('Chunk size must be between 100 and 2000 tokens')
        return v
    
    @validator('allowed_domains')
    def validate_allowed_domains(cls, v):
        if len(v) > 50:
            raise ValueError('Maximum 50 allowed domains')
        for domain in v:
            if not cls.validate_domain(domain):
                raise ValueError(f'Invalid domain: {domain}')
        return v
```

## Exception Hierarchy

### Base Exceptions
```python
from typing import Optional, Dict, Any

class APIError(Exception):
    def __init__(
        self, 
        message: str,
        error_code: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

class ValidationError(APIError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VALIDATION_ERROR", 422, details)

class AuthenticationError(APIError):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTH_ERROR", 401)

class AuthorizationError(APIError):
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, "AUTHZ_ERROR", 403)
```

### Service-Specific Exceptions
```python
class DocumentProcessingError(APIError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DOC_PROCESSING_ERROR", 422, details)

class WidgetConfigError(APIError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "WIDGET_CONFIG_ERROR", 400, details)

class AIEngineError(APIError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "AI_ENGINE_ERROR", 503, details)
```

## Model Usage Guidelines

### Import Patterns
```python
# Correct import pattern
from shared.models.auth import CreatorCreate, CreatorResponse, TokenResponse
from shared.models.documents import ProcessingResult, DocumentChunk
from shared.models.widgets import WidgetConfig, WidgetTheme
from shared.exceptions.documents import DocumentProcessingError
from shared.validators.common import validate_email, validate_domain
```

### Response Model Usage
```python
from fastapi import APIRouter
from shared.models.auth import CreatorResponse, TokenResponse

router = APIRouter()

@router.post("/register", response_model=CreatorResponse)
async def register_creator(creator_data: CreatorCreate) -> CreatorResponse:
    # Implementation
    pass

@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest) -> TokenResponse:
    # Implementation
    pass
```

### Error Handling Integration
```python
from fastapi import HTTPException
from shared.exceptions.base import APIError

@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": getattr(request.state, 'request_id', None)
            }
        }
    )
```

## Configuration Models

### Environment Configuration
```python
class DatabaseConfig(BaseModel):
    host: str = Field(..., env='DB_HOST')
    port: int = Field(5432, env='DB_PORT')
    database: str = Field(..., env='DB_NAME')
    username: str = Field(..., env='DB_USER')
    password: str = Field(..., env='DB_PASSWORD')
    
    @property
    def url(self) -> str:
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

class RedisConfig(BaseModel):
    host: str = Field(..., env='REDIS_HOST')
    port: int = Field(6379, env='REDIS_PORT')
    password: Optional[str] = Field(None, env='REDIS_PASSWORD')
    db: int = Field(0, env='REDIS_DB')
    
    @property
    def url(self) -> str:
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"
```

## Testing Models

### Test Data Factories
```python
import factory
from shared.models.auth import CreatorCreate, CreatorResponse

class CreatorCreateFactory(factory.Factory):
    class Meta:
        model = CreatorCreate
    
    email = factory.Sequence(lambda n: f"creator{n}@example.com")
    password = "TestPassword123!"
    full_name = factory.Faker('name')
    company_name = factory.Faker('company')

class CreatorResponseFactory(factory.Factory):
    class Meta:
        model = CreatorResponse
    
    id = factory.Faker('uuid4')
    email = factory.Sequence(lambda n: f"creator{n}@example.com")
    full_name = factory.Faker('name')
    company_name = factory.Faker('company')
    is_active = True
    subscription_tier = "free"
    creator_id = factory.SelfAttribute('id')
```