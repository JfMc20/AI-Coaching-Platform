"""
Creator Profile Management Router
Handles creator profile operations and dashboard metrics
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.database import get_tenant_session
from shared.security.auth import get_current_creator_id
from shared.exceptions.auth import AuthenticationError
from shared.exceptions.base import NotFoundError, DatabaseError

from ..models import (
    CreatorProfile, CreatorProfileUpdate, DashboardMetrics,
    ConversationSummary, ConversationListResponse, TimeRange, AnalyticsRequest
)
from ..database import CreatorProfileService, AnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/creators", tags=["creators"])


# ==================== CREATOR PROFILE ENDPOINTS ====================

@router.get("/profile", response_model=CreatorProfile)
async def get_creator_profile(
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_tenant_session)
):
    """Get creator profile information"""
    try:
        profile = await CreatorProfileService.get_creator_profile(creator_id, session)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Creator profile not found"
            )
        
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get creator profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve creator profile"
        )


@router.put("/profile", response_model=CreatorProfile)
async def update_creator_profile(
    profile_data: CreatorProfileUpdate,
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_tenant_session)
):
    """Update creator profile information"""
    try:
        updated_profile = await CreatorProfileService.update_creator_profile(
            creator_id, profile_data, session
        )
        
        if not updated_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Creator profile not found"
            )
        
        logger.info(f"Creator profile updated: {creator_id}")
        return updated_profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update creator profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update creator profile"
        )


# ==================== DASHBOARD METRICS ENDPOINTS ====================

@router.get("/dashboard/metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    period_days: int = Query(default=30, ge=1, le=365, description="Period in days"),
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_tenant_session)
):
    """Get creator dashboard metrics"""
    try:
        metrics = await AnalyticsService.get_dashboard_metrics(
            creator_id, period_days, session
        )
        
        logger.info(f"Dashboard metrics retrieved for creator: {creator_id}")
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get dashboard metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard metrics"
        )


@router.post("/analytics", response_model=DashboardMetrics)
async def get_analytics_data(
    analytics_request: AnalyticsRequest,
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_tenant_session)
):
    """Get detailed analytics data with custom parameters"""
    try:
        # Calculate period based on time range
        period_days_map = {
            TimeRange.DAY: 1,
            TimeRange.WEEK: 7,
            TimeRange.MONTH: 30,
            TimeRange.QUARTER: 90,
            TimeRange.YEAR: 365
        }
        
        period_days = period_days_map.get(analytics_request.time_range, 30)
        
        # If custom dates provided, calculate period
        if analytics_request.start_date and analytics_request.end_date:
            period_days = (analytics_request.end_date - analytics_request.start_date).days
        
        metrics = await AnalyticsService.get_dashboard_metrics(
            creator_id, period_days, session
        )
        
        logger.info(f"Custom analytics retrieved for creator: {creator_id}")
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get analytics data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics data"
        )


# ==================== CONVERSATION MANAGEMENT ENDPOINTS ====================

@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(default=None, description="Filter by status"),
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_tenant_session)
):
    """List creator's conversations"""
    try:
        # For MVP, return mock conversation data
        # In production, this would query actual conversation records
        mock_conversations = [
            ConversationSummary(
                id=f"conv_{i}",
                creator_id=creator_id,
                title=f"Conversation with User {i}",
                user_name=f"User {i}",
                status="active" if i % 3 == 0 else "completed",
                message_count=15 + (i * 3),
                last_message_at=None,
                satisfaction_rating=4 if i % 2 == 0 else 5,
                tags=["coaching", "support"] if i % 2 == 0 else ["consultation"],
                created_at=None,
                updated_at=None
            )
            for i in range(1, 26)  # 25 mock conversations
        ]
        
        # Apply status filter if provided
        if status_filter:
            mock_conversations = [
                conv for conv in mock_conversations 
                if conv.status == status_filter
            ]
        
        # Apply pagination
        total_count = len(mock_conversations)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_conversations = mock_conversations[start_idx:end_idx]
        
        return ConversationListResponse(
            conversations=paginated_conversations,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=end_idx < total_count
        )
        
    except Exception as e:
        logger.error(f"Failed to list conversations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversations"
        )


@router.get("/conversations/{conversation_id}", response_model=ConversationSummary)
async def get_conversation(
    conversation_id: str,
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_tenant_session)
):
    """Get conversation details"""
    try:
        # For MVP, return mock conversation data
        # In production, this would query actual conversation records
        if not conversation_id.startswith("conv_"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        conversation = ConversationSummary(
            id=conversation_id,
            creator_id=creator_id,
            title=f"Conversation Details - {conversation_id}",
            user_name="Sample User",
            status="active",
            message_count=23,
            last_message_at=None,
            satisfaction_rating=4,
            tags=["coaching", "career-development"],
            created_at=None,
            updated_at=None
        )
        
        logger.info(f"Conversation retrieved: {conversation_id}")
        return conversation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation"
        )