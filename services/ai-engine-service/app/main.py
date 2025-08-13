"""
AI Engine Service - MVP Coaching AI Platform
Handles AI processing, RAG pipeline, and document processing
"""

import os
import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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


# AI conversation endpoints (to be implemented in subsequent tasks)
@app.post("/api/v1/ai/conversations", tags=["conversations"])
async def process_conversation():
    """Process a conversation with AI"""
    # TODO: Implement in task 4.1
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint will be implemented in task 4.1"
    )


@app.get("/api/v1/ai/conversations/{conversation_id}/context", tags=["conversations"])
async def get_conversation_context(conversation_id: str):
    """Get conversation context for AI processing"""
    # TODO: Implement in task 4.1
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint will be implemented in task 4.1"
    )


# Document processing endpoints
@app.post("/api/v1/ai/documents/process", tags=["documents"])
async def process_document():
    """Process a document for embedding and storage"""
    # TODO: Implement in task 4.2
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint will be implemented in task 4.2"
    )


@app.post("/api/v1/ai/documents/search", tags=["documents"])
async def search_documents():
    """Search documents using semantic similarity"""
    # TODO: Implement in task 4.3
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint will be implemented in task 4.3"
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)