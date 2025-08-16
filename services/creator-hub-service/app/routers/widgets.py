"""
Widget Configuration Router
Handles widget setup, customization, and embed code generation
"""

import logging
from typing import Optional, Dict, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from shared.exceptions.base import NotFoundError, DatabaseError

# Import dependencies from our app layer
from ..database import get_db
from ..dependencies.auth import get_current_creator_id

from ..models import (
    WidgetConfiguration, WidgetSettings, WidgetEmbedCode,
    WidgetTheme, WidgetPosition
)
from ..database import WidgetConfigService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/creators/widget", tags=["widgets"])


# ==================== WIDGET CONFIGURATION ENDPOINTS ====================

@router.get("/config", response_model=WidgetConfiguration)
async def get_widget_config(
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db)
):
    """Get widget configuration"""
    try:
        config = await WidgetConfigService.get_widget_config(creator_id, session)
        
        if not config:
            # Create default configuration if none exists
            config = WidgetConfiguration(
                id=str(uuid4()),
                creator_id=creator_id,
                name="Default Widget",
                description="Default widget configuration",
                is_active=True,
                settings=WidgetSettings(),
                welcome_message="Hello! How can I help you today?",
                placeholder_text="Type your message...",
                enable_file_upload=True,
                enable_voice_input=False,
                allowed_domains=[],
                rate_limit_messages=10,
                track_analytics=True
            )
        
        logger.info(f"Widget configuration retrieved for creator: {creator_id}")
        return config
        
    except Exception as e:
        logger.error(f"Failed to get widget configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve widget configuration"
        )


@router.put("/config", response_model=WidgetConfiguration)
async def update_widget_config(
    config_update: Dict[str, Any],
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db)
):
    """Update widget configuration"""
    try:
        updated_config = await WidgetConfigService.update_widget_config(
            creator_id=creator_id,
            config_data=config_update,
            session=session
        )
        
        logger.info(f"Widget configuration updated for creator: {creator_id}")
        return updated_config
        
    except Exception as e:
        logger.error(f"Failed to update widget configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update widget configuration"
        )


# ==================== WIDGET APPEARANCE ENDPOINTS ====================

@router.put("/config/appearance")
async def update_widget_appearance(
    settings: WidgetSettings,
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db)
):
    """Update widget appearance settings"""
    try:
        config_update = {
            "settings": settings.dict()
        }
        
        updated_config = await WidgetConfigService.update_widget_config(
            creator_id=creator_id,
            config_data=config_update,
            session=session
        )
        
        logger.info(f"Widget appearance updated for creator: {creator_id}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Widget appearance updated successfully",
                "settings": settings.dict()
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to update widget appearance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update widget appearance"
        )


@router.put("/config/behavior")
async def update_widget_behavior(
    welcome_message: Optional[str] = None,
    placeholder_text: Optional[str] = None,
    enable_file_upload: Optional[bool] = None,
    enable_voice_input: Optional[bool] = None,
    rate_limit_messages: Optional[int] = None,
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db)
):
    """Update widget behavior settings"""
    try:
        config_update = {}
        
        if welcome_message is not None:
            config_update["welcome_message"] = welcome_message
        if placeholder_text is not None:
            config_update["placeholder_text"] = placeholder_text
        if enable_file_upload is not None:
            config_update["enable_file_upload"] = enable_file_upload
        if enable_voice_input is not None:
            config_update["enable_voice_input"] = enable_voice_input
        if rate_limit_messages is not None:
            config_update["rate_limit_messages"] = rate_limit_messages
        
        if not config_update:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No behavior settings provided"
            )
        
        updated_config = await WidgetConfigService.update_widget_config(
            creator_id=creator_id,
            config_data=config_update,
            session=session
        )
        
        logger.info(f"Widget behavior updated for creator: {creator_id}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Widget behavior updated successfully",
                "updated_settings": config_update
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update widget behavior: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update widget behavior"
        )


# ==================== WIDGET EMBED CODE ENDPOINTS ====================

@router.get("/embed-code", response_model=WidgetEmbedCode)
async def get_embed_code(
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db)
):
    """Get widget embed code"""
    try:
        # Get widget configuration
        config = await WidgetConfigService.get_widget_config(creator_id, session)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Widget configuration not found"
            )
        
        # Generate widget ID
        widget_id = f"widget_{creator_id}"
        
        # Generate embed code
        embed_code = f"""
<!-- AI Coaching Widget -->
<div id="{widget_id}"></div>
<script>
  (function() {{
    var widget = document.createElement('div');
    widget.id = '{widget_id}-container';
    widget.style.cssText = `
      position: fixed;
      {config.settings.position.replace('-', ': 20px; ').replace('-', ': 20px;')};
      z-index: 999999;
      font-family: {config.settings.font_family}, -apple-system, BlinkMacSystemFont, sans-serif;
    `;
    
    var iframe = document.createElement('iframe');
    iframe.src = 'https://widget.yourplatform.com/{creator_id}';
    iframe.style.cssText = `
      width: 350px;
      height: 500px;
      border: none;
      border-radius: {config.settings.border_radius}px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.15);
      background: {config.settings.background_color};
    `;
    
    widget.appendChild(iframe);
    document.body.appendChild(widget);
    
    // Widget initialization
    window.AIChatWidget = {{
      config: {{
        theme: '{config.settings.theme}',
        primaryColor: '{config.settings.primary_color}',
        welcomeMessage: '{config.welcome_message}',
        enableFileUpload: {str(config.enable_file_upload).lower()},
        enableVoiceInput: {str(config.enable_voice_input).lower()}
      }}
    }};
  }})();
</script>
<!-- End AI Coaching Widget -->""".strip()
        
        # Generate preview URL
        preview_url = f"https://widget.yourplatform.com/preview/{creator_id}"
        
        # Installation instructions
        instructions = f"""
## Widget Installation Instructions

1. **Copy the embed code** below and paste it into your website's HTML
2. **Place it before the closing </body> tag** for best performance
3. **Customize appearance** in your Creator Hub dashboard
4. **Test the widget** using the preview URL

### Allowed Domains
{', '.join(config.allowed_domains) if config.allowed_domains else 'All domains (configure in settings)'}

### Widget Features
- Theme: {config.settings.theme}
- File Upload: {'Enabled' if config.enable_file_upload else 'Disabled'}
- Voice Input: {'Enabled' if config.enable_voice_input else 'Disabled'}
- Rate Limit: {config.rate_limit_messages} messages/minute

### Support
If you need help with installation, contact support or check our documentation.
        """.strip()
        
        embed_response = WidgetEmbedCode(
            embed_code=embed_code,
            widget_id=widget_id,
            installation_instructions=instructions,
            preview_url=preview_url
        )
        
        logger.info(f"Embed code generated for creator: {creator_id}")
        return embed_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate embed code: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate embed code"
        )


@router.post("/preview")
async def generate_preview_token(
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db)
):
    """Generate a preview token for testing widget"""
    try:
        # Generate temporary preview token
        preview_token = f"preview_{uuid4().hex[:16]}"
        
        # In a real implementation, this would be stored with expiration
        # For MVP, return a mock preview configuration
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "preview_token": preview_token,
                "preview_url": f"https://widget.yourplatform.com/preview/{creator_id}?token={preview_token}",
                "expires_in": 3600,  # 1 hour
                "message": "Preview token generated successfully"
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to generate preview token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate preview token"
        )


# ==================== WIDGET ANALYTICS ENDPOINTS ====================

@router.get("/analytics")
async def get_widget_analytics(
    days: int = 30,
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db)
):
    """Get widget usage analytics"""
    try:
        # For MVP, return mock analytics data
        # In production, this would query actual widget usage metrics
        
        mock_analytics = {
            "period_days": days,
            "total_interactions": 1247,
            "unique_visitors": 892,
            "avg_session_duration": 4.2,  # minutes
            "conversion_rate": 0.15,  # 15%
            "top_pages": [
                {"url": "/pricing", "interactions": 234},
                {"url": "/features", "interactions": 189},
                {"url": "/", "interactions": 156}
            ],
            "daily_stats": [
                {"date": "2025-01-15", "interactions": 45, "visitors": 32},
                {"date": "2025-01-14", "interactions": 52, "visitors": 38},
                {"date": "2025-01-13", "interactions": 38, "visitors": 29},
                {"date": "2025-01-12", "interactions": 61, "visitors": 45},
                {"date": "2025-01-11", "interactions": 43, "visitors": 31}
            ],
            "user_satisfaction": {
                "average_rating": 4.3,
                "total_ratings": 89,
                "distribution": {
                    "5_star": 45,
                    "4_star": 28,
                    "3_star": 12,
                    "2_star": 3,
                    "1_star": 1
                }
            }
        }
        
        logger.info(f"Widget analytics retrieved for creator: {creator_id}")
        return mock_analytics
        
    except Exception as e:
        logger.error(f"Failed to get widget analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve widget analytics"
        )