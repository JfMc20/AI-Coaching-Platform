"""
FastAPI Endpoint Template for Multi-Tenant AI Platform
Use this template when creating new API endpoints
"""

from typing import Annotated, Any, Dict, List, Optional
from fastapi import Depends, HTTPException, Path, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

# Import authentication and database dependencies
from shared.models.database import BaseTenantModel
from shared.security.auth import get_current_user, UserContext
from shared.database import get_tenant_session
from shared.monitoring import trace_operation, OperationType

# Request/Response Models
class YourFeatureRequest(BaseModel):
    """Request model for your feature"""
    name: str = Field(..., description="Feature name", min_length=1, max_length=255)
    creator_id: str = Field(..., description="Creator identifier for tenant isolation")
    # Add other fields as needed

class YourFeatureResponse(BaseModel):
    """Response model for your feature"""
    id: str = Field(..., description="Feature identifier")
    name: str = Field(..., description="Feature name")
    creator_id: str = Field(..., description="Creator identifier")
    created_at: str = Field(..., description="Creation timestamp")
    # Add other fields as needed

# Database Model
class YourFeature(BaseTenantModel):
    """Database model for your feature - MUST inherit from BaseTenantModel"""
    __tablename__ = "your_features"
    
    name: str = Field(..., description="Feature name")
    # creator_id is inherited from BaseTenantModel
    # RLS policies automatically filter by creator_id

# API Endpoint
@app.post(
    "/api/v1/your-feature",
    response_model=YourFeatureResponse,
    tags=["your-feature"],
    summary="Create your feature",
    description="Create a new feature with multi-tenant isolation"
)
@trace_operation("create_your_feature", operation_type=OperationType.DATABASE)
async def create_your_feature(
    request: YourFeatureRequest,
    current_user: UserContext = Depends(get_current_user),  # JWT authentication
    session: AsyncSession = Depends(get_tenant_session),    # Multi-tenant session
):
    """Create a new feature with proper multi-tenant isolation"""
    try:
        # Validate creator access (user can only access their own data)
        if current_user.creator_id != request.creator_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cannot access other creator's data"
            )
        
        # Create feature instance
        new_feature = YourFeature(
            name=request.name,
            creator_id=request.creator_id
        )
        
        # Save to database (RLS automatically filters by creator_id)
        session.add(new_feature)
        await session.commit()
        await session.refresh(new_feature)
        
        # Return response
        return YourFeatureResponse(
            id=str(new_feature.id),
            name=new_feature.name,
            creator_id=new_feature.creator_id,
            created_at=new_feature.created_at.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Feature creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Feature creation failed: {str(e)}"
        )

@app.get(
    "/api/v1/your-feature/{feature_id}",
    response_model=YourFeatureResponse,
    tags=["your-feature"],
    summary="Get your feature",
    description="Retrieve a feature by ID with multi-tenant isolation"
)
async def get_your_feature(
    feature_id: Annotated[str, Path(description="Feature identifier")],
    current_user: UserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_tenant_session),
):
    """Get feature by ID with automatic multi-tenant filtering"""
    try:
        # Query with RLS automatically filtering by creator_id
        result = await session.execute(
            select(YourFeature).where(YourFeature.id == feature_id)
        )
        feature = result.scalar_one_or_none()
        
        if not feature:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feature not found"
            )
        
        return YourFeatureResponse(
            id=str(feature.id),
            name=feature.name,
            creator_id=feature.creator_id,
            created_at=feature.created_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feature retrieval error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Feature retrieval failed: {str(e)}"
        )