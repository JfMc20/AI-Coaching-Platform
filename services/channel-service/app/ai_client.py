"""
AI Engine Client - Channel Service Integration
Handles communication with AI Engine Service for message processing
"""

import asyncio
import logging
from typing import Dict, Any, Optional
import httpx
from pydantic import BaseModel, Field

from shared.config.env_constants import get_env_value, AI_ENGINE_URL

logger = logging.getLogger(__name__)


class ConversationRequest(BaseModel):
    """Request model for AI conversation processing"""
    message: str = Field(..., description="User message to process")
    creator_id: str = Field(..., description="Creator ID for context")
    conversation_id: str = Field(..., description="Conversation identifier")
    user_identifier: str = Field(None, description="User identifier (optional)")


class ConversationResponse(BaseModel):
    """Response model from AI conversation processing"""
    response: str = Field(..., description="AI-generated response")
    conversation_id: str = Field(..., description="Conversation identifier")
    creator_id: str = Field(..., description="Creator ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AIEngineClient:
    """Client for communicating with AI Engine Service"""
    
    def __init__(self):
        self.base_url = get_env_value(AI_ENGINE_URL, "http://ai-engine-service:8003")
        self.timeout = 30.0  # 30 seconds timeout for AI responses
        
    async def process_message(
        self,
        message: str,
        creator_id: str,
        conversation_id: str,
        user_identifier: Optional[str] = None,
        auth_token: Optional[str] = None
    ) -> ConversationResponse:
        """
        Process a message through the AI Engine
        
        Args:
            message: User message to process
            creator_id: Creator ID for context
            conversation_id: Conversation identifier
            user_identifier: Optional user identifier
            auth_token: Optional authentication token
            
        Returns:
            ConversationResponse with AI-generated response
            
        Raises:
            Exception: If AI Engine request fails
        """
        try:
            request_data = ConversationRequest(
                message=message,
                creator_id=creator_id,
                conversation_id=conversation_id,
                user_identifier=user_identifier
            )
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/ai/conversations",
                    json=request_data.dict(),
                    headers=headers
                )
                
                response.raise_for_status()
                response_data = response.json()
                
                return ConversationResponse(**response_data)
                
        except httpx.TimeoutException:
            logger.error(f"AI Engine request timeout for conversation {conversation_id}")
            raise Exception("AI service is currently unavailable (timeout)")
            
        except httpx.HTTPStatusError as e:
            logger.error(f"AI Engine HTTP error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"AI service error: {e.response.status_code}")
            
        except Exception as e:
            logger.error(f"Unexpected error in AI Engine request: {str(e)}")
            raise Exception("Failed to process message with AI service")
    
    async def get_conversation_context(
        self,
        conversation_id: str,
        creator_id: str,
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get conversation context from AI Engine
        
        Args:
            conversation_id: Conversation identifier
            creator_id: Creator ID for context
            auth_token: Optional authentication token
            
        Returns:
            Dictionary with conversation context
        """
        try:
            headers = {
                "Accept": "application/json"
            }
            
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/ai/conversations/{conversation_id}/context",
                    params={"creator_id": creator_id},
                    headers=headers
                )
                
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Failed to get conversation context: {str(e)}")
            return {}
    
    async def health_check(self) -> bool:
        """
        Check if AI Engine Service is healthy
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False


# Global AI client instance
_ai_client: Optional[AIEngineClient] = None


def get_ai_client() -> AIEngineClient:
    """Get global AI Engine client instance"""
    global _ai_client
    if _ai_client is None:
        _ai_client = AIEngineClient()
    return _ai_client