"""
Auth Service - MVP Coaching AI Platform
Handles authentication, authorization, and user management
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import logging
from contextlib import asynccontextmanager

from .database import get_db_manager, init_database, close_db
from .routes.auth import router as auth_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Environment variables validation
required_env_vars = [
    "DATABASE_URL",
    "JWT_SECRET_KEY"
]

missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    logger.error(f"Missing required environment variables: {missing_vars}")
    raise RuntimeError(f"Missing required environment variables: {missing_vars}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("🚀 Auth Service starting up...")
    
    try:
        # Initialize database
        await init_database()
        logger.info("✅ Database initialized successfully")
        
        # Verify database connectivity
        db_manager = get_db_manager()
        if await db_manager.health_check():
            logger.info("✅ Database health check passed")
        else:
            logger.error("❌ Database health check failed")
            raise RuntimeError("Database connectivity check failed")
        
        # TODO: Initialize Redis connection
        # TODO: Validate JWT keys
        
        logger.info("🎉 Auth Service startup completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Auth Service startup failed: {e}")
        raise
    
    yield
    
    logger.info("🛑 Auth Service shutting down...")
    
    try:
        # Cleanup database connections
        await close_db()
        logger.info("✅ Database connections closed")
        
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title="Auth Service API",
    description="Authentication and authorization service for MVP Coaching AI Platform",
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "authentication",
            "description": "Creator authentication operations - registration, login, token management"
        },
        {
            "name": "authorization", 
            "description": "User authorization and permissions management"
        },
        {
            "name": "health",
            "description": "Service health checks and monitoring"
        }
    ]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include authentication routes
app.include_router(auth_router)


@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint for load balancers and monitoring
    
    Returns basic service status without external dependencies
    """
    return {
        "status": "healthy",
        "service": "auth-service",
        "version": "1.0.0",
        "timestamp": "2024-01-01T00:00:00Z"
    }


@app.get("/ready", tags=["health"])
async def readiness_check():
    """
    Readiness check endpoint with dependency validation
    
    Checks external dependencies before marking service as ready
    """
    checks = {
        "database": "unknown",
        "jwt_config": "unknown"
    }
    
    try:
        # Check database connectivity
        db_manager = get_db_manager()
        if await db_manager.health_check():
            checks["database"] = "connected"
        else:
            checks["database"] = "disconnected"
        
        # Check JWT configuration
        if os.getenv("JWT_SECRET_KEY"):
            checks["jwt_config"] = "configured"
        else:
            checks["jwt_config"] = "missing"
        
        # Determine overall status
        all_healthy = all(
            status in ["connected", "configured"] 
            for status in checks.values()
        )
        
        status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        
        return JSONResponse(
            status_code=status_code,
            content={
                "status": "ready" if all_healthy else "not_ready",
                "service": "auth-service",
                "checks": checks,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        )
        
    except Exception as e:
        logger.exception(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "service": "auth-service",
                "checks": checks,
                "error": str(e),
                "timestamp": "2024-01-01T00:00:00Z"
            }
        )


@app.get("/", tags=["health"])
async def root():
    """Root endpoint with service information"""
    return {
        "message": "Auth Service API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "ready": "/ready",
        "description": "Authentication and authorization service for MVP Coaching AI Platform"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    logger.exception(f"Unhandled exception in {request.method} {request.url}: {exc}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "type": "internal_error",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0", 
        port=8001,
        reload=True,
        log_level="info"
    )