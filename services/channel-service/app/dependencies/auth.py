"""
Authentication dependencies for Channel Service
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
    Extract and validate creator ID from JWT token
    
    Args:
        request: FastAPI request object
        credentials: HTTP Authorization credentials
        db: Database session
        
    Returns:
        str: Creator ID from validated JWT token
        
    Raises:
        HTTPException: If token is invalid or creator not found
    """
    try:
        # Get JWT configuration
        secret_key = get_env_value(JWT_SECRET_KEY, fallback=True)
        algorithm = get_env_value(JWT_ALGORITHM, "HS256")
        
        # Decode and validate token
        token = credentials.credentials
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        
        # Extract creator ID from token
        creator_id: str = payload.get("sub")
        if not creator_id:
            logger.warning("Token missing creator ID (sub claim)")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing creator ID"
            )
        
        # Verify creator exists in database
        result = await db.execute(
            select(Creator).where(Creator.id == creator_id)
        )
        creator = result.scalar_one_or_none()
        
        if not creator:
            logger.warning(f"Creator {creator_id} not found in database")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Creator not found"
            )
        
        # Set tenant context for Row Level Security
        await set_tenant_context(db, creator_id)
        
        logger.debug(f"Authenticated creator: {creator_id}")
        return creator_id
        
    except ExpiredSignatureError:
        logger.warning("Token has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except JWTClaimsError as e:
        logger.warning(f"Invalid token claims: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims"
        )
    except JWTError as e:
        logger.warning(f"JWT validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_current_creator_id: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )


async def get_current_creator(
    creator_id: str = Depends(get_current_creator_id),
    db: AsyncSession = Depends(get_db)
) -> Creator:
    """
    Get current authenticated creator object
    
    Args:
        creator_id: Creator ID from JWT token
        db: Database session
        
    Returns:
        Creator: Complete creator object
        
    Raises:
        HTTPException: If creator not found
    """
    try:
        result = await db.execute(
            select(Creator).where(Creator.id == creator_id)
        )
        creator = result.scalar_one_or_none()
        
        if not creator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Creator not found"
            )
        
        return creator
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving creator {creator_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving creator information"
        )