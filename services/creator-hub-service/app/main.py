"""
Creator Hub Service - MVP Coaching AI Platform
Handles creator management, content, and widget configuration
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from shared.config.settings import validate_service_environment
# Import centralized environment constants and helpers
from shared.config.env_constants import CORS_ORIGINS, REQUIRED_VARS_BY_SERVICE, get_env_value

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables validation using centralized configuration constants
required_env_vars = REQUIRED_VARS_BY_SERVICE["creator_hub_service"]

validate_service_environment(required_env_vars, logger)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("🚀 Creator Hub Service starting up...")
    
    # Startup logic here
    # - Database connection
    # - Redis connection
    # - File storage setup
    # - Service connectivity checks
    
    yield
    
    logger.info("🛑 Creator Hub Service shutting down...")
    # Cleanup logic here


# Create FastAPI application
app = FastAPI(
    title="Creator Hub Service API",
    description="Creator management and content service for MVP Coaching AI Platform",
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "creators",
            "description": "Creator profile management"
        },
        {
            "name": "knowledge",
            "description": "Knowledge base management"
        },
        {
            "name": "widgets",
            "description": "Widget configuration"
        },
        {
            "name": "programs",
            "description": "Visual Program Builder management"
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
        "service": "creator-hub-service",
        "version": "1.0.0"
    }


@app.get("/ready", tags=["health"])
async def readiness_check():
    """Readiness check endpoint"""
    # TODO: Check database, Redis, and service connectivity
    return {
        "status": "ready",
        "service": "creator-hub-service",
        "checks": {
            "database": "connected",
            "redis": "connected",
            "auth_service": "connected",
            "ai_engine_service": "connected"
        }
    }


@app.get("/", tags=["health"])
async def root():
    """Root endpoint"""
    return {
        "message": "Creator Hub Service API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# Import routers
from .routers import creators, knowledge, widgets, programs

# Include routers
app.include_router(creators.router)
app.include_router(knowledge.router)
app.include_router(widgets.router)
app.include_router(programs.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)