"""
AI Engine Service - MVP Coaching AI Platform
Handles AI processing, RAG pipeline, and document processing
"""

import os
import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException, status, Field, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from shared.config.settings import validate_service_environment
from shared.config.env_constants import CORS_ORIGINS, REQUIRED_VARS_BY_SERVICE, get_env_value
from shared.ai.chromadb_manager import get_chromadb_manager, close_chromadb_manager
from shared.ai.ollama_manager import get_ollama_manager, close_ollama_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables validation using centralized configuration constants
required_env_vars = REQUIRED_VARS_BY_SERVICE["ai_engine_service"]

validate_service_environment(required_env_vars, logger)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("🚀 AI Engine Service starting up...")
    
    # Startup logic
    startup_tasks = []
    
    try:
        # Initialize ChromaDB manager
        chromadb_manager = get_chromadb_manager()
        startup_tasks.append(("ChromaDB", chromadb_manager.health_check()))
        
        # Initialize Ollama manager
        ollama_manager = get_ollama_manager()
        startup_tasks.append(("Ollama", ollama_manager.health_check()))
        
        # Run health checks concurrently
        logger.info("Running startup health checks...")
        for service_name, task in startup_tasks:
            try:
                result = await task
                logger.info(f"✅ {service_name} health check passed: {result['status']}")
            except Exception as e:
                logger.error(f"❌ {service_name} health check failed: {str(e)}")
                # Continue startup even if health checks fail (for development)
        
        # Ensure required models are available
        try:
            logger.info("Ensuring AI models are available...")
            model_status = await ollama_manager.ensure_models_available()
            logger.info(f"✅ Models availability: {model_status}")
        except Exception as e:
            logger.warning(f"⚠️ Model availability check failed: {str(e)}")
        
        logger.info("🎉 AI Engine Service startup completed")
        
    except Exception as e:
        logger.error(f"💥 AI Engine Service startup failed: {str(e)}")
        # Don't raise exception to allow service to start in development
    
    yield
    
    logger.info("🛑 AI Engine Service shutting down...")
    
    # Cleanup logic
    try:
        await close_chromadb_manager()
        await close_ollama_manager()
        logger.info("✅ AI Engine Service cleanup completed")
    except Exception as e:
        logger.error(f"❌ AI Engine Service cleanup failed: {str(e)}")


# Create FastAPI application
app = FastAPI(
    title="AI Engine Service API",
    description="AI processing and RAG service for MVP Coaching AI Platform",
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "conversations",
            "description": "AI conversation processing"
        },
        {
            "name": "documents",
            "description": "Document processing and embedding"
        },
        {
            "name": "models",
            "description": "AI model management"
        },
        {
            "name": "health",
            "description": "Service health checks"
        }
    ]
)

# CORS middleware using centralized configuration constants
app.add_middleware(
    CORSMiddleware,
    allow_origins=(get_env_value(CORS_ORIGINS, fallback=True) or "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ai-engine-service",
        "version": "1.0.0"
    }


@app.get("/ready", tags=["health"])
async def readiness_check():
    """Readiness check endpoint"""
    checks = {}
    overall_status = "ready"
    
    try:
        # Check ChromaDB connectivity
        chromadb_manager = get_chromadb_manager()
        chromadb_health = await chromadb_manager.health_check()
        checks["chromadb"] = "connected"
    except Exception as e:
        checks["chromadb"] = f"failed: {str(e)}"
        overall_status = "not_ready"
    
    try:
        # Check Ollama connectivity
        ollama_manager = get_ollama_manager()
        ollama_health = await ollama_manager.health_check()
        checks["ollama"] = "connected"
        checks["embedding_model"] = "available" if ollama_health["embedding_model"]["available"] else "not_available"
        checks["chat_model"] = "available" if ollama_health["chat_model"]["available"] else "not_available"
    except Exception as e:
        checks["ollama"] = f"failed: {str(e)}"
        checks["embedding_model"] = "unknown"
        checks["chat_model"] = "unknown"
        overall_status = "not_ready"
    
    # TODO: Add database and Redis checks in future tasks
    checks["database"] = "not_implemented"
    checks["redis"] = "not_implemented"
    
    return {
        "status": overall_status,
        "service": "ai-engine-service",
        "checks": checks
    }


@app.get("/", tags=["health"])
async def root():
    """Root endpoint"""
    return {
        "message": "AI Engine Service API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# Import RAG pipeline and rate limiting
from .rag_pipeline import get_rag_pipeline, RAGError, ConversationError
from .embedding_manager import get_embedding_manager, EmbeddingError
from shared.models.conversations import Message, MessageRole
from shared.security.rate_limiter import RateLimiter, RateLimitType

# Request/Response models for conversation endpoints
class ConversationRequest(BaseModel):
    """Request model for conversation processing"""
    query: str = Field(..., description="User's query/message", min_length=1, max_length=4000)
    creator_id: str = Field(..., description="Creator identifier for tenant isolation")
    conversation_id: str = Field(..., description="Conversation identifier")
    context_window: Optional[int] = Field(None, ge=1000, le=8000, description="Override context window size")

class ConversationResponse(BaseModel):
    """Response model for conversation processing"""
    response: str = Field(..., description="AI generated response")
    conversation_id: str = Field(..., description="Conversation identifier")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Response confidence score")
    processing_time_ms: float = Field(..., ge=0, description="Processing time in milliseconds")
    model_used: str = Field(..., description="AI model used for generation")
    sources_count: int = Field(..., ge=0, description="Number of knowledge sources used")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Knowledge sources used")

class ContextResponse(BaseModel):
    """Response model for conversation context"""
    conversation_id: str = Field(..., description="Conversation identifier")
    messages: List[Dict[str, Any]] = Field(default_factory=list, description="Recent conversation messages")
    total_messages: int = Field(..., ge=0, description="Total messages in conversation")
    summary: Optional[Dict[str, Any]] = Field(None, description="Conversation summary statistics")

# AI conversation endpoints
@app.post("/api/v1/ai/conversations", 
          response_model=ConversationResponse,
          tags=["conversations"],
          summary="Process conversation with AI",
          description="Process a user query through the RAG pipeline and return AI response with sources")
async def process_conversation(request: ConversationRequest):
    """Process a conversation with AI using RAG pipeline"""
    try:
        # Get RAG pipeline instance
        rag_pipeline = get_rag_pipeline()
        
        # Process query through RAG pipeline
        ai_response = await rag_pipeline.process_query(
            query=request.query,
            creator_id=request.creator_id,
            conversation_id=request.conversation_id,
            context_window=request.context_window
        )
        
        # Format sources for response
        sources = [
            {
                "document_id": source.document_id,
                "chunk_index": source.chunk_index,
                "similarity_score": source.similarity_score,
                "rank": source.rank,
                "content_preview": source.content[:200] + "..." if len(source.content) > 200 else source.content,
                "metadata": source.metadata
            }
            for source in ai_response.sources
        ]
        
        return ConversationResponse(
            response=ai_response.response,
            conversation_id=ai_response.conversation_id,
            confidence=ai_response.confidence,
            processing_time_ms=ai_response.processing_time_ms,
            model_used=ai_response.model_used,
            sources_count=len(ai_response.sources),
            sources=sources
        )
        
    except RAGError as e:
        logger.error(f"RAG pipeline error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG processing failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Conversation processing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conversation processing failed: {str(e)}"
        )


@app.get("/api/v1/ai/conversations/{conversation_id}/context", 
         response_model=ContextResponse,
         tags=["conversations"],
         summary="Get conversation context",
         description="Retrieve conversation context and history for AI processing")
async def get_conversation_context(
    conversation_id: str = Field(..., description="Conversation identifier"),
    max_messages: int = Field(10, ge=1, le=100, description="Maximum messages to retrieve")
):
    """Get conversation context for AI processing"""
    try:
        # Get RAG pipeline instance
        rag_pipeline = get_rag_pipeline()
        
        # Get conversation context (using system as default creator_id for now)
        # TODO: Extract creator_id from JWT token in future implementation
        creator_id = "system"  # Placeholder - should come from authentication
        
        messages = await rag_pipeline.conversation_manager.get_context(
            conversation_id=conversation_id,
            max_messages=max_messages,
            creator_id=creator_id
        )
        
        # Get conversation summary
        summary = await rag_pipeline.conversation_manager.get_conversation_summary(
            conversation_id=conversation_id,
            creator_id=creator_id
        )
        
        # Format messages for response
        formatted_messages = [
            {
                "id": msg.id,
                "role": msg.role.value,
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
                "processing_time_ms": msg.processing_time_ms,
                "metadata": msg.metadata
            }
            for msg in messages
        ]
        
        return ContextResponse(
            conversation_id=conversation_id,
            messages=formatted_messages,
            total_messages=len(formatted_messages),
            summary=summary
        )
        
    except ConversationError as e:
        logger.error(f"Conversation context error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation context: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Context retrieval error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Context retrieval failed: {str(e)}"
        )


# Import document processor
from .document_processor import get_document_processor, DocumentProcessingError, ProcessingConfig
from fastapi import UploadFile, File, Form

# Document processing request/response models
class DocumentProcessResponse(BaseModel):
    """Response model for document processing"""
    document_id: str = Field(..., description="Generated document identifier")
    status: str = Field(..., description="Processing status")
    total_chunks: int = Field(..., ge=0, description="Number of chunks created")
    processing_time_seconds: float = Field(..., ge=0, description="Processing time in seconds")
    filename: str = Field(..., description="Original filename")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata")

# Document processing endpoints
@app.post("/api/v1/ai/documents/process", 
          response_model=DocumentProcessResponse,
          tags=["documents"],
          summary="Process document for embedding and storage",
          description="Upload and process a document through security scanning, text extraction, chunking, and embedding generation")
async def process_document(
    file: UploadFile = File(..., description="Document file to process"),
    creator_id: str = Form(..., description="Creator identifier for tenant isolation"),
    document_id: Optional[str] = Form(None, description="Optional custom document ID")
):
    """Process a document for embedding and storage"""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No filename provided"
            )
        
        # Read file content
        file_content = await file.read()
        
        if not file_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file uploaded"
            )
        
        # Get document processor
        document_processor = get_document_processor()
        
        # Process document
        result = await document_processor.process_document(
            file_content=file_content,
            filename=file.filename,
            creator_id=creator_id,
            document_id=document_id
        )
        
        # Return response
        return DocumentProcessResponse(
            document_id=result.document_id,
            status=result.status.value,
            total_chunks=result.total_chunks,
            processing_time_seconds=result.processing_time_seconds,
            filename=file.filename,
            error_message=result.error_message,
            metadata=result.metadata
        )
        
    except DocumentProcessingError as e:
        logger.error(f"Document processing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Document processing failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Document processing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing failed: {str(e)}"
        )


# Document search request/response models
class DocumentSearchRequest(BaseModel):
    """Request model for document search"""
    query: str = Field(..., description="Search query", min_length=1, max_length=1000)
    creator_id: str = Field(..., description="Creator identifier for tenant isolation")
    limit: int = Field(5, ge=1, le=20, description="Maximum number of results")
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Minimum similarity score")

class DocumentSearchResult(BaseModel):
    """Individual search result"""
    document_id: str = Field(..., description="Document identifier")
    chunk_index: int = Field(..., description="Chunk index within document")
    content: str = Field(..., description="Chunk content")
    similarity_score: float = Field(..., description="Similarity score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk metadata")

class DocumentSearchResponse(BaseModel):
    """Response model for document search"""
    query: str = Field(..., description="Original search query")
    results: List[DocumentSearchResult] = Field(default_factory=list, description="Search results")
    total_results: int = Field(..., description="Total number of results found")
    processing_time_ms: float = Field(..., description="Search processing time in milliseconds")

@app.post("/api/v1/ai/documents/search", 
          response_model=DocumentSearchResponse,
          tags=["documents"],
          summary="Search documents using semantic similarity",
          description="Search through processed documents using semantic similarity matching")
async def search_documents(request: DocumentSearchRequest):
    """Search documents using semantic similarity"""
    try:
        start_time = datetime.utcnow()
        
        # Get RAG pipeline for search functionality
        rag_pipeline = get_rag_pipeline()
        
        # Perform semantic search
        retrieved_chunks = await rag_pipeline.retrieve_knowledge(
            query=request.query,
            creator_id=request.creator_id,
            limit=request.limit
        )
        
        # Filter by similarity threshold
        filtered_chunks = [
            chunk for chunk in retrieved_chunks 
            if chunk.similarity_score >= request.similarity_threshold
        ]
        
        # Convert to response format
        results = [
            DocumentSearchResult(
                document_id=chunk.document_id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                similarity_score=chunk.similarity_score,
                metadata=chunk.metadata
            )
            for chunk in filtered_chunks
        ]
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return DocumentSearchResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Document search error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document search failed: {str(e)}"
        )


# Model management endpoints
@app.get("/api/v1/ai/models/status", tags=["models"])
async def get_models_status():
    """Get status of AI models"""
    try:
        ollama_manager = get_ollama_manager()
        
        # Get health check to see model availability
        health = await ollama_manager.health_check()
        
        # Get detailed model list
        models = await ollama_manager.list_models()
        
        return {
            "embedding_model": {
                "name": ollama_manager.embedding_model,
                "status": "available" if health["embedding_model"]["available"] else "not_available",
                "loaded": health["embedding_model"]["available"]
            },
            "chat_model": {
                "name": ollama_manager.chat_model,
                "status": "available" if health["chat_model"]["available"] else "not_available",
                "loaded": health["chat_model"]["available"]
            },
            "all_models": [
                {
                    "name": model.name,
                    "size": model.size,
                    "modified_at": model.modified_at,
                    "loaded": model.loaded
                }
                for model in models
            ],
            "server_status": health["status"],
            "timestamp": health["timestamp"]
        }
        
    except Exception as e:
        logger.error(f"Failed to get models status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to get models status: {str(e)}"
        )


@app.post("/api/v1/ai/models/reload", tags=["models"])
async def reload_models():
    """Reload AI models by ensuring they are available"""
    try:
        ollama_manager = get_ollama_manager()
        
        # Force refresh model cache and ensure availability
        model_status = await ollama_manager.ensure_models_available()
        
        return {
            "status": "success",
            "message": "Models reloaded successfully",
            "models": {
                "embedding_model": {
                    "name": ollama_manager.embedding_model,
                    "available": model_status["embedding_model"]
                },
                "chat_model": {
                    "name": ollama_manager.chat_model,
                    "available": model_status["chat_model"]
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to reload models: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to reload models: {str(e)}"
        )


# ChromaDB management endpoints
@app.get("/api/v1/ai/chromadb/health", tags=["models"])
async def get_chromadb_health():
    """Get ChromaDB health status"""
    try:
        chromadb_manager = get_chromadb_manager()
        health = await chromadb_manager.health_check()
        return health
    except Exception as e:
        logger.error(f"ChromaDB health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"ChromaDB health check failed: {str(e)}"
        )


@app.get("/api/v1/ai/chromadb/stats", tags=["models"])
async def get_chromadb_stats():
    """Get ChromaDB statistics for all shards"""
    try:
        chromadb_manager = get_chromadb_manager()
        stats = await chromadb_manager.get_all_shards_stats()
        
        return {
            "total_shards": len(stats),
            "shards": [
                {
                    "collection_name": stat.collection_name,
                    "document_count": stat.document_count,
                    "total_embeddings": stat.total_embeddings,
                    "creators_count": stat.creators_count,
                    "avg_embeddings_per_creator": stat.avg_embeddings_per_creator,
                    "last_updated": stat.last_updated.isoformat()
                }
                for stat in stats
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get ChromaDB stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to get ChromaDB stats: {str(e)}"
        )


# Ollama management endpoints
@app.get("/api/v1/ai/ollama/health", tags=["models"])
async def get_ollama_health():
    """Get Ollama health status"""
    try:
        ollama_manager = get_ollama_manager()
        health = await ollama_manager.health_check()
        return health
    except Exception as e:
        logger.error(f"Ollama health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ollama health check failed: {str(e)}"
        )


@app.post("/api/v1/ai/ollama/test-embedding", tags=["models"])
async def test_embedding_generation():
    """Test embedding generation with sample text"""
    try:
        ollama_manager = get_ollama_manager()
        
        # Test with sample text
        test_texts = [
            "This is a test document for embedding generation.",
            "ChromaDB is a vector database for AI applications."
        ]
        
        response = await ollama_manager.generate_embeddings(test_texts)
        
        return {
            "status": "success",
            "model": response.model,
            "embeddings_count": len(response.embeddings),
            "embedding_dimensions": len(response.embeddings[0]) if response.embeddings else 0,
            "processing_time_ms": response.processing_time_ms,
            "token_count": response.token_count,
            "test_texts": test_texts,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Embedding test failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Embedding test failed: {str(e)}"
        )


@app.post("/api/v1/ai/ollama/test-chat", tags=["models"])
async def test_chat_generation():
    """Test chat generation with sample prompt"""
    try:
        ollama_manager = get_ollama_manager()
        
        # Test with sample prompt
        test_prompt = "Hello! Can you tell me about AI and machine learning in one sentence?"
        
        response = await ollama_manager.generate_chat_response(
            prompt=test_prompt,
            temperature=0.7
        )
        
        return {
            "status": "success",
            "model": response.model,
            "prompt": test_prompt,
            "response": response.response,
            "processing_time_ms": response.processing_time_ms,
            "done": response.done,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Chat test failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Chat test failed: {str(e)}"
        )





# Additional AI Engine endpoints for task 4.4

@app.get("/api/v1/ai/embeddings/stats/{creator_id}", tags=["models"])
async def get_embedding_stats(creator_id: str):
    """Get embedding and search statistics for creator"""
    try:
        embedding_manager = get_embedding_manager()
        stats = await embedding_manager.get_embedding_stats(creator_id)
        
        return {
            "status": "success",
            "creator_id": creator_id,
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get embedding stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get embedding stats: {str(e)}"
        )


@app.delete("/api/v1/ai/cache/{creator_id}/document/{document_id}", tags=["models"])
async def invalidate_document_cache(creator_id: str, document_id: str):
    """Invalidate cache entries for a specific document"""
    try:
        embedding_manager = get_embedding_manager()
        success = await embedding_manager.invalidate_document_cache(creator_id, document_id)
        
        return {
            "status": "success" if success else "failed",
            "creator_id": creator_id,
            "document_id": document_id,
            "message": "Cache invalidated successfully" if success else "Cache invalidation failed",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to invalidate document cache: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to invalidate document cache: {str(e)}"
        )


@app.post("/api/v1/ai/cache/{creator_id}/warm", tags=["models"])
async def warm_search_cache(creator_id: str):
    """Warm search cache for popular queries"""
    try:
        embedding_manager = get_embedding_manager()
        warmed_count = await embedding_manager.search_cache.warm_popular_queries(creator_id)
        
        return {
            "status": "success",
            "creator_id": creator_id,
            "warmed_queries": warmed_count,
            "message": f"Warmed cache for {warmed_count} popular queries",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to warm search cache: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to warm search cache: {str(e)}"
        )


@app.get("/api/v1/ai/pipeline/performance", tags=["conversations"])
async def get_pipeline_performance():
    """Get RAG pipeline performance metrics"""
    try:
        rag_pipeline = get_rag_pipeline()
        stats = await rag_pipeline.get_pipeline_stats()
        
        return {
            "status": "success",
            "performance_stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get pipeline performance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pipeline performance: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)