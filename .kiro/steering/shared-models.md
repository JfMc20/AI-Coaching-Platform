---
inclusion: always
---

# Shared Models & Data Structures

## Model Organization Structure

All Pydantic models MUST follow this organization:

```
shared/
├── models/
│   ├── auth.py          # CreatorCreate, CreatorResponse, TokenResponse
│   ├── documents.py     # ProcessingResult, DocumentChunk, ProcessingStatus
│   ├── widgets.py       # WidgetConfig, WidgetTheme, WidgetBehavior
│   ├── conversations.py # Message, Conversation, ConversationContext
│   └── base.py          # BaseModel extensions, common validators
├── exceptions/
│   ├── base.py          # APIError, ValidationError, AuthenticationError
│   ├── auth.py          # AuthenticationError, AuthorizationError
│   ├── documents.py     # DocumentProcessingError
│   └── widgets.py       # WidgetConfigError
└── validators/
    ├── common.py        # Email, URL, domain validators
    └── business.py      # Business logic validators
```

## Base Model Requirements

### Mandatory Base Classes
Every model MUST inherit from appropriate base class:

```python
class BaseTimestampModel(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class BaseTenantModel(BaseTimestampModel):
    creator_id: str = Field(..., description="Creator/tenant identifier")
```

### Core Model Examples

**Authentication Models:**
```python
class CreatorCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)
    company_name: Optional[str] = Field(None, max_length=255)

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
```

**Document Processing Models:**
```python
class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class DocumentChunk(BaseModel):
    id: str
    content: str = Field(..., min_length=1, max_length=4000)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    chunk_index: int = Field(..., ge=0)
    token_count: int = Field(..., ge=0)
```

**Widget Configuration Models:**
```python
class WidgetTheme(BaseModel):
    primary_color: str = Field(default="#007bff", regex=r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$')
    secondary_color: str = Field(default="#6c757d", regex=r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$')
    background_color: str = Field(default="#ffffff")
    border_radius: int = Field(default=8, ge=0, le=50)

class WidgetConfig(BaseTenantModel):
    widget_id: str
    is_active: bool = Field(default=True)
    theme: WidgetTheme = Field(default_factory=WidgetTheme)
    allowed_domains: List[str] = Field(default_factory=list)
    rate_limit_per_minute: int = Field(default=10, ge=1, le=100)
```

## Validation Standards

### Required Validators
Use Pydantic v2 field validators for all models:

```python
from pydantic import field_validator
import re

class CommonValidators:
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if len(v) > 254:
            raise ValueError('Email too long')
        return v.lower()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain digit')
        return v
    
    @field_validator('domain')
    @classmethod
    def validate_domain(cls, v: str) -> str:
        pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        if not re.match(pattern, v):
            raise ValueError('Invalid domain format')
        return v.lower()
```

## Exception Standards

### Base Exception Classes
All custom exceptions MUST inherit from APIError:

```python
class APIError(Exception):
    def __init__(self, message: str, error_code: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

# Standard HTTP exceptions
class ValidationError(APIError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VALIDATION_ERROR", 422, details)

class AuthenticationError(APIError):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTH_ERROR", 401)

# Service-specific exceptions
class DocumentProcessingError(APIError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DOC_PROCESSING_ERROR", 422, details)

class AIEngineError(APIError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "AI_ENGINE_ERROR", 503, details)
```

## Usage Patterns

### Import Standards
Always import from specific model modules:

```python
# Correct imports
from shared.models.auth import CreatorCreate, CreatorResponse, TokenResponse
from shared.models.documents import ProcessingResult, DocumentChunk
from shared.models.widgets import WidgetConfig, WidgetTheme
from shared.exceptions.base import APIError, ValidationError
from shared.exceptions.documents import DocumentProcessingError
```

### FastAPI Integration
Use response_model for type safety and documentation:

```python
from fastapi import APIRouter
from shared.models.auth import CreatorResponse, TokenResponse

router = APIRouter()

@router.post("/register", response_model=CreatorResponse)
async def register_creator(creator_data: CreatorCreate) -> CreatorResponse:
    # Implementation
    pass
```

### Error Handler Registration
Register global exception handler for APIError:

```python
from fastapi import Request
from fastapi.responses import JSONResponse
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
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )
```

## Configuration & Testing

### Environment Models
Use Pydantic for configuration management:

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
```

### Test Factories
Use factory_boy for test data generation:

```python
import factory
from shared.models.auth import CreatorCreate

class CreatorCreateFactory(factory.Factory):
    class Meta:
        model = CreatorCreate
    
    email = factory.Sequence(lambda n: f"creator{n}@example.com")
    password = "TestPassword123!"
    full_name = factory.Faker('name')
    company_name = factory.Faker('company')
```

## Key Rules

- **Multi-tenancy**: All tenant models MUST inherit from `BaseTenantModel`
- **Timestamps**: All models MUST inherit from `BaseTimestampModel` 
- **Validation**: Use Pydantic v2 `field_validator` decorators
- **Exceptions**: All custom exceptions MUST inherit from `APIError`
- **Type Safety**: Always use response_model in FastAPI endpoints
- **Testing**: Use factory_boy for consistent test data generation