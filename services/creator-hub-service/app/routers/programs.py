"""
Visual Program Builder Router
Handles automated coaching program creation, execution, and management
"""

import logging
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status, Form, Query, Body
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from shared.exceptions.base import NotFoundError, DatabaseError

# Import dependencies from our app layer
from ..database import get_db
from ..dependencies.auth import get_current_creator_id

# Import Visual Program Builder models
from ..program_models import (
    ProgramDefinition, ProgramStatus, ProgramStep, StepType,
    ProgramExecutionResult, ExecutionStatus, ExecutionStrategy,
    PersonalityConfig, ExecutionConfig, AnalyticsConfig, NotificationConfig
)
from ..step_models import (
    TriggerConfig, ActionConfig, ValidationConfig, ConditionalConfig,
    TriggerType, ActionType, ValidationRule, ConditionOperator
)

# Import engine components
from ..program_engine import get_program_engine
from ..step_processor import get_step_processor
from ..condition_evaluator import get_condition_evaluator
from ..debug_analytics import get_analytics_system, get_debug_manager

# Import personality system components
from ..personality_models import PersonalityAnalysisRequest
from ..personality_engine import get_personality_engine
from ..prompt_generator import get_prompt_generator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/creators/programs", tags=["programs"])


# ==================== PROGRAM DEFINITION ENDPOINTS ====================

@router.post("/", response_model=ProgramDefinition)
async def create_program(
    title: str = Form(..., description="Program title"),
    description: str = Form(..., description="Program description"),
    version: str = Form(default="1.0", description="Program version"),
    execution_strategy: ExecutionStrategy = Form(default=ExecutionStrategy.SEQUENTIAL, description="Execution strategy"),
    enable_personality: bool = Form(default=True, description="Enable personality enhancement"),
    enable_analytics: bool = Form(default=True, description="Enable analytics collection"),
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db)
):
    """Create a new coaching program definition"""
    try:
        # Create program configurations
        personality_config = PersonalityConfig(
            enabled=enable_personality,
            enhance_content=True,
            enforce_consistency=True,
            adaptation_level="moderate"
        )
        
        execution_config = ExecutionConfig(
            strategy=execution_strategy,
            parallel_limit=3,
            timeout_seconds=300,
            retry_failed_steps=True,
            max_retries=2
        )
        
        analytics_config = AnalyticsConfig(
            enabled=enable_analytics,
            track_performance=True,
            track_user_journey=True,
            store_debug_info=True,
            real_time_insights=True
        )
        
        notification_config = NotificationConfig(
            enabled=True,
            notify_completion=True,
            notify_errors=True,
            email_notifications=False,
            webhook_notifications=False
        )
        
        # Create program definition
        program = ProgramDefinition(
            program_id=str(uuid4()),
            creator_id=creator_id,
            title=title,
            description=description,
            version=version,
            status=ProgramStatus.DRAFT,
            personality_config=personality_config,
            execution_config=execution_config,
            analytics_config=analytics_config,
            notification_config=notification_config,
            steps=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Get program engine and create program
        program_engine = get_program_engine()
        created_program = await program_engine.create_program(
            creator_id=creator_id,
            program_definition=program,
            session=session
        )
        
        logger.info(f"Program created: {created_program.program_id} for creator {creator_id}")
        
        return created_program
        
    except Exception as e:
        logger.error(f"Failed to create program: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create program"
        )


@router.get("/", response_model=List[ProgramDefinition])
async def list_programs(
    status_filter: Optional[ProgramStatus] = Query(default=None, description="Filter by status"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db)
):
    """List creator's programs"""
    try:
        program_engine = get_program_engine()
        programs = await program_engine.list_programs(
            creator_id=creator_id,
            status_filter=status_filter,
            page=page,
            page_size=page_size,
            session=session
        )
        
        logger.info(f"Programs listed for creator: {creator_id} (page {page})")
        
        return programs
        
    except Exception as e:
        logger.error(f"Failed to list programs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve programs"
        )


@router.get("/{program_id}", response_model=ProgramDefinition)
async def get_program(
    program_id: str,
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db)
):
    """Get program details"""
    try:
        program_engine = get_program_engine()
        program = await program_engine.get_program(
            creator_id=creator_id,
            program_id=program_id,
            session=session
        )
        
        if not program:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Program not found"
            )
        
        logger.info(f"Program retrieved: {program_id}")
        return program
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get program: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve program"
        )


@router.put("/{program_id}", response_model=ProgramDefinition)
async def update_program(
    program_id: str,
    title: Optional[str] = Form(None, description="Program title"),
    description: Optional[str] = Form(None, description="Program description"),
    version: Optional[str] = Form(None, description="Program version"),
    status: Optional[ProgramStatus] = Form(None, description="Program status"),
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db)
):
    """Update program details"""
    try:
        program_engine = get_program_engine()
        
        # Get existing program
        program = await program_engine.get_program(
            creator_id=creator_id,
            program_id=program_id,
            session=session
        )
        
        if not program:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Program not found"
            )
        
        # Update fields
        updates = {}
        if title is not None:
            updates["title"] = title
        if description is not None:
            updates["description"] = description
        if version is not None:
            updates["version"] = version
        if status is not None:
            updates["status"] = status
        
        if updates:
            updates["updated_at"] = datetime.utcnow()
            updated_program = await program_engine.update_program(
                creator_id=creator_id,
                program_id=program_id,
                updates=updates,
                session=session
            )
            
            logger.info(f"Program updated: {program_id}")
            return updated_program
        
        return program
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update program: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update program"
        )


@router.delete("/{program_id}")
async def delete_program(
    program_id: str,
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db)
):
    """Delete a program"""
    try:
        program_engine = get_program_engine()
        
        # Check if program exists
        program = await program_engine.get_program(
            creator_id=creator_id,
            program_id=program_id,
            session=session
        )
        
        if not program:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Program not found"
            )
        
        # Delete program
        deleted = await program_engine.delete_program(
            creator_id=creator_id,
            program_id=program_id,
            session=session
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Program not found"
            )
        
        logger.info(f"Program deleted: {program_id}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Program deleted successfully", "program_id": program_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete program: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete program"
        )


# ==================== PROGRAM STEP MANAGEMENT ENDPOINTS ====================

@router.post("/{program_id}/steps", response_model=ProgramStep)
async def add_program_step(
    program_id: str,
    step_type: StepType = Form(..., description="Type of step"),
    step_name: str = Form(..., description="Step name"),
    step_description: str = Form(..., description="Step description"),
    trigger_type: TriggerType = Form(..., description="Trigger type"),
    action_type: ActionType = Form(..., description="Action type"),
    trigger_config_json: str = Form(..., description="Trigger configuration JSON"),
    action_config_json: str = Form(..., description="Action configuration JSON"),
    conditional_config_json: Optional[str] = Form(None, description="Conditional configuration JSON"),
    order_index: int = Form(default=0, description="Step execution order"),
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db)
):
    """Add a step to a program"""
    try:
        # Validate program exists
        program_engine = get_program_engine()
        program = await program_engine.get_program(
            creator_id=creator_id,
            program_id=program_id,
            session=session
        )
        
        if not program:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Program not found"
            )
        
        # Parse configurations
        try:
            trigger_config_dict = json.loads(trigger_config_json)
            action_config_dict = json.loads(action_config_json)
            
            trigger_config = TriggerConfig(
                trigger_type=trigger_type,
                **trigger_config_dict
            )
            
            action_config = ActionConfig(
                action_type=action_type,
                **action_config_dict
            )
            
            conditional_config = None
            if conditional_config_json:
                conditional_dict = json.loads(conditional_config_json)
                conditional_config = ConditionalConfig(**conditional_dict)
                
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON configuration: {str(e)}"
            )
        
        # Create step
        step = ProgramStep(
            step_id=str(uuid4()),
            program_id=program_id,
            creator_id=creator_id,
            step_type=step_type,
            name=step_name,
            description=step_description,
            order_index=order_index,
            trigger_config=trigger_config,
            action_config=action_config,
            conditional_config=conditional_config,
            validation_config=ValidationConfig(),
            enabled=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Add step to program
        created_step = await program_engine.add_step(
            creator_id=creator_id,
            program_id=program_id,
            step=step,
            session=session
        )
        
        logger.info(f"Step added to program {program_id}: {created_step.step_id}")
        
        return created_step
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add step: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add step to program"
        )


@router.get("/{program_id}/steps", response_model=List[ProgramStep])
async def list_program_steps(
    program_id: str,
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db)
):
    """List steps in a program"""
    try:
        program_engine = get_program_engine()
        steps = await program_engine.get_program_steps(
            creator_id=creator_id,
            program_id=program_id,
            session=session
        )
        
        logger.info(f"Steps listed for program: {program_id}")
        
        return steps
        
    except Exception as e:
        logger.error(f"Failed to list steps: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve program steps"
        )


@router.put("/{program_id}/steps/{step_id}", response_model=ProgramStep)
async def update_program_step(
    program_id: str,
    step_id: str,
    step_name: Optional[str] = Form(None, description="Step name"),
    step_description: Optional[str] = Form(None, description="Step description"),
    enabled: Optional[bool] = Form(None, description="Step enabled status"),
    order_index: Optional[int] = Form(None, description="Step execution order"),
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db)
):
    """Update a program step"""
    try:
        program_engine = get_program_engine()
        
        # Build updates
        updates = {}
        if step_name is not None:
            updates["name"] = step_name
        if step_description is not None:
            updates["description"] = step_description
        if enabled is not None:
            updates["enabled"] = enabled
        if order_index is not None:
            updates["order_index"] = order_index
        
        if updates:
            updates["updated_at"] = datetime.utcnow()
            updated_step = await program_engine.update_step(
                creator_id=creator_id,
                program_id=program_id,
                step_id=step_id,
                updates=updates,
                session=session
            )
            
            if not updated_step:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Step not found"
                )
            
            logger.info(f"Step updated: {step_id} in program {program_id}")
            return updated_step
        
        # If no updates, return current step
        step = await program_engine.get_step(
            creator_id=creator_id,
            program_id=program_id,
            step_id=step_id,
            session=session
        )
        
        if not step:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Step not found"
            )
        
        return step
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update step: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update step"
        )


@router.delete("/{program_id}/steps/{step_id}")
async def delete_program_step(
    program_id: str,
    step_id: str,
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db)
):
    """Delete a program step"""
    try:
        program_engine = get_program_engine()
        
        deleted = await program_engine.delete_step(
            creator_id=creator_id,
            program_id=program_id,
            step_id=step_id,
            session=session
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Step not found"
            )
        
        logger.info(f"Step deleted: {step_id} from program {program_id}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Step deleted successfully", "step_id": step_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete step: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete step"
        )


# ==================== PROGRAM EXECUTION ENDPOINTS ====================

@router.post("/{program_id}/execute", response_model=ProgramExecutionResult)
async def execute_program(
    program_id: str,
    user_context: str = Form(..., description="User context for execution"),
    simulation_mode: bool = Form(default=False, description="Run in simulation mode"),
    debug_mode: bool = Form(default=False, description="Enable debug mode"),
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db)
):
    """Execute a coaching program"""
    try:
        # Validate program exists and is executable
        program_engine = get_program_engine()
        program = await program_engine.get_program(
            creator_id=creator_id,
            program_id=program_id,
            session=session
        )
        
        if not program:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Program not found"
            )
        
        if program.status != ProgramStatus.PUBLISHED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Program must be published to execute"
            )
        
        # Start debug session if enabled
        debug_session = None
        if debug_mode:
            debug_manager = get_debug_manager()
            debug_session = await debug_manager.start_debug_session(
                creator_id=creator_id,
                program_id=program_id,
                execution_type="api_execution"
            )
        
        # Execute program
        execution_result = await program_engine.execute_program(
            creator_id=creator_id,
            program_id=program_id,
            user_context=user_context,
            simulation_mode=simulation_mode,
            debug_session=debug_session,
            session=session
        )
        
        # Collect analytics if enabled
        if program.analytics_config.enabled:
            analytics_system = get_analytics_system()
            await analytics_system.collect_execution_analytics(execution_result)
        
        logger.info(
            f"Program execution completed: {program_id}, "
            f"status={execution_result.execution_status}, "
            f"steps_completed={execution_result.steps_completed}/{execution_result.total_steps}"
        )
        
        return execution_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute program: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute program"
        )


@router.get("/{program_id}/executions")
async def get_execution_history(
    program_id: str,
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db)
):
    """Get program execution history"""
    try:
        program_engine = get_program_engine()
        executions = await program_engine.get_execution_history(
            creator_id=creator_id,
            program_id=program_id,
            page=page,
            page_size=page_size,
            session=session
        )
        
        logger.info(f"Execution history retrieved for program: {program_id}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Execution history retrieved successfully",
                "executions": executions
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get execution history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve execution history"
        )


# ==================== PROGRAM VALIDATION ENDPOINTS ====================

@router.post("/{program_id}/validate")
async def validate_program(
    program_id: str,
    comprehensive: bool = Form(default=True, description="Run comprehensive validation"),
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db)
):
    """Validate program configuration and flow"""
    try:
        program_engine = get_program_engine()
        validation_result = await program_engine.validate_program(
            creator_id=creator_id,
            program_id=program_id,
            comprehensive=comprehensive,
            session=session
        )
        
        logger.info(
            f"Program validation completed: {program_id}, "
            f"valid={validation_result.is_valid}, "
            f"errors={len(validation_result.errors)}"
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Program validation completed",
                "validation_result": validation_result.dict()
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to validate program: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate program"
        )


@router.post("/{program_id}/test-conditions")
async def test_program_conditions(
    program_id: str,
    test_data: Dict[str, Any] = Body(..., description="Test data for condition evaluation"),
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db)
):
    """Test program conditional logic with sample data"""
    try:
        condition_evaluator = get_condition_evaluator()
        test_results = await condition_evaluator.test_program_conditions(
            creator_id=creator_id,
            program_id=program_id,
            test_data=test_data,
            session=session
        )
        
        logger.info(f"Condition testing completed for program: {program_id}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Condition testing completed",
                "test_results": test_results
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to test conditions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test program conditions"
        )


# ==================== ANALYTICS AND INSIGHTS ENDPOINTS ====================

@router.get("/{program_id}/analytics")
async def get_program_analytics(
    program_id: str,
    time_range_days: int = Query(default=30, ge=1, le=365, description="Time range in days"),
    analytics_type: Optional[str] = Query(default=None, description="Specific analytics type"),
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db)
):
    """Get program analytics and insights"""
    try:
        analytics_system = get_analytics_system()
        
        # Calculate time range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=time_range_days)
        
        analytics_data = await analytics_system.get_program_analytics(
            creator_id=creator_id,
            program_id=program_id,
            start_date=start_date,
            end_date=end_date,
            analytics_type=analytics_type
        )
        
        logger.info(f"Analytics retrieved for program: {program_id}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Analytics retrieved successfully",
                "analytics": analytics_data
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics"
        )


@router.post("/{program_id}/insights")
async def generate_program_insights(
    program_id: str,
    time_range_days: int = Form(default=30, ge=1, le=365, description="Time range in days"),
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db)
):
    """Generate actionable insights for program optimization"""
    try:
        analytics_system = get_analytics_system()
        
        # Calculate time range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=time_range_days)
        
        insights = await analytics_system.generate_program_insights(
            program_id=program_id,
            time_range={
                "start_date": start_date,
                "end_date": end_date
            }
        )
        
        logger.info(f"Insights generated for program: {program_id}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Insights generated successfully",
                "insights": insights
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to generate insights: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate program insights"
        )


# ==================== DEBUGGING ENDPOINTS ====================

@router.get("/{program_id}/debug/sessions")
async def list_debug_sessions(
    program_id: str,
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db)
):
    """List debug sessions for a program"""
    try:
        debug_manager = get_debug_manager()
        debug_sessions = await debug_manager.list_debug_sessions(
            creator_id=creator_id,
            program_id=program_id
        )
        
        logger.info(f"Debug sessions listed for program: {program_id}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Debug sessions retrieved successfully",
                "debug_sessions": debug_sessions
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to list debug sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve debug sessions"
        )


@router.get("/{program_id}/debug/sessions/{session_id}")
async def get_debug_session_details(
    program_id: str,
    session_id: str,
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db)
):
    """Get detailed debug session information"""
    try:
        debug_manager = get_debug_manager()
        debug_session = await debug_manager.get_debug_session(
            creator_id=creator_id,
            session_id=session_id
        )
        
        if not debug_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Debug session not found"
            )
        
        logger.info(f"Debug session details retrieved: {session_id}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Debug session details retrieved successfully",
                "debug_session": debug_session
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get debug session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve debug session details"
        )