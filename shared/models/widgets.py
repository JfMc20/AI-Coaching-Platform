"""Widget configuration models"""

from pydantic import BaseModel, Field, validator, HttpUrl
from datetime import datetime
from typing import Optional, List
from .base import TenantAwareEntity


class WidgetTheme(BaseModel):
    """Widget visual theme configuration"""
    primary_color: str = Field(default="#007bff", description="Primary brand color")
    secondary_color: str = Field(default="#6c757d", description="Secondary color")
    background_color: str = Field(default="#ffffff", description="Widget background")
    text_color: str = Field(default="#212529", description="Text color")
    border_radius: int = Field(default=8, ge=0, le=50, description="Border radius in pixels")
    
    @validator('primary_color', 'secondary_color', 'background_color', 'text_color')
    def validate_hex_color(cls, v):
        if not v.startswith('#') or len(v) != 7:
            raise ValueError('Color must be a valid hex color (e.g., #007bff)')
        try:
            int(v[1:], 16)
        except ValueError:
            raise ValueError('Invalid hex color format')
        return v.lower()


class WidgetBehavior(BaseModel):
    """Widget behavior configuration"""
    auto_open: bool = Field(default=False, description="Auto-open widget on page load")
    greeting_message: str = Field(default="¡Hola! ¿En qué puedo ayudarte?", description="Initial greeting")
    placeholder_text: str = Field(default="Escribe tu mensaje...", description="Input placeholder")
    show_typing_indicator: bool = Field(default=True, description="Show typing indicator")
    response_delay_ms: int = Field(default=1000, ge=0, le=5000, description="Simulated response delay")
    
    @validator('greeting_message', 'placeholder_text')
    def validate_text_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Text fields cannot be empty')
        return v.strip()


class WidgetConfig(TenantAwareEntity):
    """Complete widget configuration"""
    widget_id: str = Field(..., description="Unique widget identifier")
    is_active: bool = Field(default=True, description="Whether widget is active")
    theme: WidgetTheme = Field(default_factory=WidgetTheme, description="Visual theme")
    behavior: WidgetBehavior = Field(default_factory=WidgetBehavior, description="Behavior settings")
    allowed_domains: List[str] = Field(default_factory=list, description="Allowed domains for widget")
    rate_limit_per_minute: int = Field(default=10, ge=1, le=100, description="Messages per minute limit")
    embed_code: Optional[str] = Field(None, description="Generated embed code")
    
    @validator('allowed_domains')
    def validate_domains(cls, v):
        if not v:
            return v
        
        validated_domains = []
        for domain in v:
            domain = domain.strip().lower()
            if not domain:
                continue
            # Basic domain validation
            if '.' not in domain or domain.startswith('.') or domain.endswith('.'):
                raise ValueError(f'Invalid domain format: {domain}')
            validated_domains.append(domain)
        return validated_domains