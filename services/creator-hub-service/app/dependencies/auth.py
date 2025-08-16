"""
Authentication dependencies for Creator Hub Service
Provides JWT validation and user context
"""

import logging
from typing import Dict, Any

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError, JWTClaimsError

from shared.config.env_constants import get_env_value, JWT_SECRET_KEY, JWT_ALGORITHM
from shared.models.database import Creator
from ..database import get_db, set_tenant_context

logger = logging.getLogger(__name__)

# Security scheme for OpenAPI documentation
security = HTTPBearer(
    scheme_name="JWT Bearer Token",
    description="JWT Bearer token for authentication"
)


async def get_current_creator_id(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> str:
    """
    Extract and validate JWT token to get current creator ID
    Also sets the tenant context for multi-tenant database access
    """
    try:
        token = credentials.credentials
        
        # Get JWT configuration
        secret_key = get_env_value(JWT_SECRET_KEY, fallback=True)
        algorithm = get_env_value(JWT_ALGORITHM, fallback=True)
        
        if not secret_key:
            logger.error("JWT_SECRET_KEY not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication configuration error"
            )
        
        # Decode JWT token
        try:
            payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except JWTClaimsError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token claims",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except JWTError as e:
            logger.error(f"JWT decode error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Extract creator ID from token
        creator_id: str = payload.get("sub")
        if creator_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify creator exists in database
        try:
            stmt = select(Creator).where(Creator.id == creator_id)
            result = await db.execute(stmt)
            creator = result.scalar_one_or_none()
            
            if creator is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Creator not found",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Set tenant context for RLS
            await set_tenant_context(creator_id, db)
            
            return creator_id
            
        except Exception as e:
            logger.error(f"Database error during authentication: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication database error"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_current_creator_id: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal authentication error"
        )


async def get_current_creator(
    creator_id: str = Depends(get_current_creator_id),
    db: AsyncSession = Depends(get_db)
) -> Creator:
    """
    Get current authenticated creator details
    """
    try:
        stmt = select(Creator).where(Creator.id == creator_id)
        result = await db.execute(stmt)
        creator = result.scalar_one_or_none()
        
        if creator is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Creator not found"
            )
        
        return creator
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching creator: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch creator"
        )