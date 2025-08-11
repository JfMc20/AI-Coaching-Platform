"""
Auth Service - MVP Coaching AI Platform
Handles authentication, authorization, and user management
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import logging
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables validation
required_env_vars = [
    "DATABASE_URL",
    "REDIS_URL", 
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
    
    # Startup logic here
    # - Database connection
    # - Redis connection
    # - JWT key validation
    
    yield
    
    logger.info("🛑 Auth Service shutting down...")
    # Cleanup logic here


# Create FastAPI application
app = FastAPI(
    title="Auth Service API",
    description="Authentication and authorization service for MVP Coaching AI Platform",
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "authentication",
            "description": "User authentication operations"
        },
        {
            "name": "authorization", 
            "description": "User authorization and permissions"
        },
        {
            "name": "health",
            "description": "Service health checks"
        }
    ]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "auth-service",
        "version": "1.0.0"
    }


@app.get("/ready", tags=["health"])
async def readiness_check():
    """Readiness check endpoint"""
    # TODO: Check database and Redis connectivity
    return {
        "status": "ready",
        "service": "auth-service",
        "checks": {
            "database": "connected",
            "redis": "connected"
        }
    }


@app.get("/", tags=["health"])
async def root():
    """Root endpoint"""
    return {
        "message": "Auth Service API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# Authentication endpoints (to be implemented in subsequent tasks)
@app.post("/api/v1/auth/register", tags=["authentication"])
async def register_creator():
    """Register a new creator"""
    # TODO: Implement in task 2.2
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint will be implemented in task 2.2"
    )


@app.post("/api/v1/auth/login", tags=["authentication"])
async def login():
    """Authenticate creator and return JWT tokens"""
    # TODO: Implement in task 2.2
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint will be implemented in task 2.2"
    )


@app.post("/api/v1/auth/refresh", tags=["authentication"])
async def refresh_token():
    """Refresh JWT access token"""
    # TODO: Implement in task 2.3
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint will be implemented in task 2.3"
    )


@app.get("/api/v1/auth/me", tags=["authentication"])
async def get_current_user():
    """Get current authenticated user info"""
    # TODO: Implement in task 2.3
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint will be implemented in task 2.3"
    )


@app.post("/api/v1/auth/logout", tags=["authentication"])
async def logout():
    """Logout and invalidate tokens"""
    # TODO: Implement in task 2.3
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint will be implemented in task 2.3"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)