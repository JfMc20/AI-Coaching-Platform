"""
AI Engine Client - Creator Hub Service Integration
Handles communication with AI Engine Service for document processing and knowledge management
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
import httpx
from pydantic import BaseModel, Field

from shared.config.env_constants import get_env_value
# Use the same environment variable name as Channel Service
AI_ENGINE_URL = "AI_ENGINE_SERVICE_URL"

logger = logging.getLogger(__name__)


# ==================== REQUEST/RESPONSE MODELS ====================

class DocumentProcessRequest(BaseModel):
    """Request model for document processing via AI Engine"""
    creator_id: str = Field(..., description="Creator identifier for tenant isolation")
    document_id: Optional[str] = Field(None, description="Optional custom document ID")
    filename: str = Field(..., description="Original filename")
    file_content: bytes = Field(..., description="Document file content")


class DocumentProcessResponse(BaseModel):
    """Response model from AI Engine document processing"""
    document_id: str = Field(..., description="Generated document identifier")
    status: str = Field(..., description="Processing status")
    total_chunks: int = Field(..., ge=0, description="Number of chunks created")
    processing_time_seconds: float = Field(..., ge=0, description="Processing time in seconds")
    filename: str = Field(..., description="Original filename")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata")


class DocumentSearchRequest(BaseModel):
    """Request model for document search via AI Engine"""
    query: str = Field(..., description="Search query", min_length=1, max_length=1000)
    creator_id: str = Field(..., description="Creator identifier for tenant isolation")
    limit: int = Field(5, ge=1, le=20, description="Maximum number of results")
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Minimum similarity score")


class DocumentSearchResult(BaseModel):
    """Individual search result from AI Engine"""
    document_id: str = Field(..., description="Document identifier")
    chunk_index: int = Field(..., description="Chunk index within document")
    content: str = Field(..., description="Chunk content")
    similarity_score: float = Field(..., description="Similarity score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk metadata")


class DocumentSearchResponse(BaseModel):
    """Response model from AI Engine document search"""
    query: str = Field(..., description="Original search query")
    results: List[DocumentSearchResult] = Field(default_factory=list, description="Search results")
    total_results: int = Field(..., description="Total number of results found")
    search_time_ms: float = Field(..., description="Search time in milliseconds")


class ConversationRequest(BaseModel):
    """Request model for AI conversation processing"""
    query: str = Field(..., description="User query to process")
    creator_id: str = Field(..., description="Creator ID for context")
    conversation_id: str = Field(..., description="Conversation identifier")


class ConversationResponse(BaseModel):
    """Response model from AI conversation processing"""
    model_config = {"protected_namespaces": ()}
    
    response: str = Field(..., description="AI-generated response")
    conversation_id: str = Field(..., description="Conversation identifier")
    confidence: float = Field(..., description="Response confidence score")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    model_used: str = Field(..., description="AI model used for generation")
    sources_count: int = Field(..., description="Number of knowledge sources used")
    sources: list = Field(default_factory=list, description="Knowledge sources used")


# ==================== AI ENGINE CLIENT ====================

class AIEngineClient:
    """Client for communicating with AI Engine Service from Creator Hub"""
    
    def __init__(self):
        # Use the same pattern as Channel Service
        self.base_url = get_env_value(AI_ENGINE_URL, fallback=True) or "http://ai-engine-service:8003"
        
        # Convert localhost to service name for Docker networking
        if "localhost" in self.base_url:
            self.base_url = self.base_url.replace("localhost", "ai-engine-service")
        
        # Ensure protocol is included
        if not self.base_url.startswith(('http://', 'https://')):
            self.base_url = f"http://{self.base_url}"
            
        self.timeout = 60.0  # 60 seconds timeout for document processing
        logger.info(f"AI Engine Client initialized with URL: {self.base_url}")
    
    async def process_document(
        self,
        creator_id: str,
        filename: str,
        file_content: bytes,
        document_id: Optional[str] = None,
        auth_token: Optional[str] = None
    ) -> DocumentProcessResponse:
        """
        Process a document through the AI Engine
        
        Args:
            creator_id: Creator ID for tenant isolation
            filename: Original filename
            file_content: Document file content as bytes
            document_id: Optional custom document ID
            auth_token: Optional authentication token
            
        Returns:
            DocumentProcessResponse with processing results
            
        Raises:
            Exception: If AI Engine request fails
        """
        try:
            headers = {
                "Accept": "application/json"
            }
            
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"
            
            # Prepare multipart form data
            files = {
                "file": (filename, file_content, "application/octet-stream")
            }
            
            data = {
                "creator_id": creator_id
            }
            
            if document_id:
                data["document_id"] = document_id
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/ai/documents/process",
                    files=files,
                    data=data,
                    headers=headers
                )
                
                response.raise_for_status()
                response_data = response.json()
                
                return DocumentProcessResponse(**response_data)
                
        except httpx.TimeoutException:
            logger.error(f"AI Engine document processing timeout for creator {creator_id}, file {filename}")
            raise Exception("AI service is currently unavailable (timeout)")
            
        except httpx.HTTPStatusError as e:
            logger.error(f"AI Engine HTTP error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"AI service error: {e.response.status_code}")
            
        except Exception as e:
            logger.error(f"Unexpected error in AI Engine document processing: {str(e)}")
            raise Exception("Failed to process document with AI service")
    
    async def search_documents(
        self,
        query: str,
        creator_id: str,
        limit: int = 5,
        similarity_threshold: float = 0.7,
        auth_token: Optional[str] = None
    ) -> DocumentSearchResponse:
        """
        Search documents using semantic similarity
        
        Args:
            query: Search query
            creator_id: Creator ID for tenant isolation
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score
            auth_token: Optional authentication token
            
        Returns:
            DocumentSearchResponse with search results
        """
        try:
            request_data = DocumentSearchRequest(
                query=query,
                creator_id=creator_id,
                limit=limit,
                similarity_threshold=similarity_threshold
            )
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/ai/documents/search",
                    json=request_data.dict(),
                    headers=headers
                )
                
                response.raise_for_status()
                response_data = response.json()
                
                return DocumentSearchResponse(**response_data)
                
        except Exception as e:
            logger.error(f"Failed to search documents: {str(e)}")
            raise Exception("Failed to search documents with AI service")
    
    async def get_creator_knowledge_context(
        self,
        creator_id: str,
        query: str,
        limit: int = 10,
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get knowledge context for a creator query
        
        Args:
            creator_id: Creator ID for context
            query: Query to get context for
            limit: Maximum number of context items
            auth_token: Optional authentication token
            
        Returns:
            Dictionary with creator knowledge context
        """
        try:
            # Use document search to get relevant knowledge
            search_response = await self.search_documents(
                query=query,
                creator_id=creator_id,
                limit=limit,
                similarity_threshold=0.5,
                auth_token=auth_token
            )
            
            # Format as knowledge context
            context = {
                "creator_id": creator_id,
                "query": query,
                "knowledge_chunks": [
                    {
                        "content": result.content,
                        "similarity": result.similarity_score,
                        "source_document": result.document_id,
                        "chunk_index": result.chunk_index,
                        "metadata": result.metadata
                    }
                    for result in search_response.results
                ],
                "total_chunks": search_response.total_results,
                "search_time_ms": search_response.search_time_ms
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to get creator knowledge context: {str(e)}")
            return {
                "creator_id": creator_id,
                "query": query,
                "knowledge_chunks": [],
                "total_chunks": 0,
                "error": str(e)
            }
    
    async def process_conversation_with_knowledge(
        self,
        message: str,
        creator_id: str,
        conversation_id: str,
        auth_token: Optional[str] = None
    ) -> ConversationResponse:
        """
        Process a conversation with creator knowledge context
        
        Args:
            message: User message to process
            creator_id: Creator ID for context
            conversation_id: Conversation identifier
            auth_token: Optional authentication token
            
        Returns:
            ConversationResponse with AI-generated response
        """
        try:
            request_data = ConversationRequest(
                query=message,
                creator_id=creator_id,
                conversation_id=conversation_id
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
                
        except Exception as e:
            logger.error(f"Failed to process conversation with knowledge: {str(e)}")
            raise Exception("Failed to process conversation with AI service")
    
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


# ==================== GLOBAL CLIENT INSTANCE ====================

# Global AI client instance
_ai_client: Optional[AIEngineClient] = None


def get_ai_client() -> AIEngineClient:
    """Get global AI Engine client instance"""
    global _ai_client
    if _ai_client is None:
        _ai_client = AIEngineClient()
    return _ai_client