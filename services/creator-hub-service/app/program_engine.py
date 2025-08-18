"""
Visual Program Builder - Program Engine
Core modular engine with extensible handler registration system
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Type, Callable, Union
from uuid import uuid4
from abc import ABC, abstractmethod

from .program_models import (
    ProgramDefinition, ExecutionStrategy, ProgramStatus, DebugLevel
)
from .step_models import (
    ProgramStep, StepExecution, StepType, TriggerType, ActionType,
    TriggerConfig, ActionConfig, ValidationConfig
)

logger = logging.getLogger(__name__)


# ==================== EXECUTION CONTEXT & RESULTS ====================

class ExecutionContext(BaseModel):
    """Context for program and step execution"""
    program_id: str = Field(..., description="Program being executed")
    user_id: str = Field(..., description="User for whom program is executed")
    creator_id: str = Field(..., description="Creator who owns the program")
    
    # Execution state
    execution_id: str = Field(..., description="Unique execution identifier")
    session_id: Optional[str] = Field(None, description="User session identifier")
    
    # User context
    user_profile: Dict[str, Any] = Field(default_factory=dict, description="User profile data")
    user_preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")
    user_history: List[str] = Field(default_factory=list, description="User interaction history")
    
    # Program state
    completed_steps: List[str] = Field(default_factory=list, description="Completed step IDs")
    active_steps: List[str] = Field(default_factory=list, description="Currently active step IDs")
    failed_steps: List[str] = Field(default_factory=list, description="Failed step IDs")
    
    # Dynamic variables
    variables: Dict[str, Any] = Field(default_factory=dict, description="Execution variables")
    metrics: Dict[str, float] = Field(default_factory=dict, description="Execution metrics")
    
    # Configuration
    debug_enabled: bool = Field(default=False, description="Whether debugging is enabled")
    debug_level: DebugLevel = Field(default=DebugLevel.STANDARD, description="Debug level")
    
    # Timing and constraints
    started_at: datetime = Field(default_factory=datetime.utcnow, description="Execution start time")
    max_execution_time: Optional[int] = Field(None, description="Maximum execution time in seconds")
    
    # Integration flags
    personality_enabled: bool = Field(default=True, description="Enable personality integration")
    knowledge_enabled: bool = Field(default=True, description="Enable knowledge integration")
    ai_enhancement_enabled: bool = Field(default=True, description="Enable AI enhancements")


class ProgramExecutionResult(BaseModel):
    """Result of program execution"""
    execution_id: str = Field(..., description="Execution identifier")
    program_id: str = Field(..., description="Program identifier")
    user_id: str = Field(..., description="User identifier")
    
    # Execution status
    status: str = Field(..., description="Execution status")
    completion_percentage: float = Field(default=0.0, description="Completion percentage")
    
    # Step results
    step_results: List['StepExecutionResult'] = Field(
        default_factory=list,
        description="Individual step execution results"
    )
    total_steps_executed: int = Field(default=0, description="Total steps executed")
    successful_steps: int = Field(default=0, description="Successfully executed steps")
    failed_steps: int = Field(default=0, description="Failed steps")
    
    # Performance metrics
    execution_time_seconds: float = Field(default=0.0, description="Total execution time")
    average_step_time: float = Field(default=0.0, description="Average step execution time")
    
    # Quality metrics
    user_engagement_score: float = Field(default=0.0, description="User engagement score")
    personality_consistency_score: float = Field(default=0.0, description="Personality consistency")
    content_effectiveness_score: float = Field(default=0.0, description="Content effectiveness")
    
    # Outcomes
    learning_objectives_met: List[str] = Field(
        default_factory=list,
        description="Learning objectives achieved"
    )
    user_feedback: Optional[str] = Field(None, description="User feedback")
    user_satisfaction_score: Optional[float] = Field(None, description="User satisfaction (1-5)")
    
    # Next steps
    recommended_next_programs: List[str] = Field(
        default_factory=list,
        description="Recommended follow-up programs"
    )
    completion_rewards: List[str] = Field(
        default_factory=list,
        description="Completion rewards earned"
    )


class StepExecutionResult(BaseModel):
    """Result of individual step execution"""
    step_id: str = Field(..., description="Step identifier")
    execution_id: str = Field(..., description="Execution identifier")
    
    # Execution details
    status: str = Field(..., description="Execution status")
    started_at: datetime = Field(..., description="Execution start time")
    completed_at: Optional[datetime] = Field(None, description="Execution completion time")
    execution_time_seconds: float = Field(default=0.0, description="Execution time")
    
    # Results
    success: bool = Field(..., description="Whether execution was successful")
    result_data: Dict[str, Any] = Field(default_factory=dict, description="Step result data")
    user_response: Optional[str] = Field(None, description="User response")
    
    # Quality metrics
    success_score: float = Field(default=0.0, description="Success score (0-1)")
    engagement_score: float = Field(default=0.0, description="User engagement score")
    personality_consistency: float = Field(default=0.0, description="Personality consistency")
    
    # Error handling
    error_message: Optional[str] = Field(None, description="Error message if failed")
    retry_count: int = Field(default=0, description="Number of retries attempted")
    recovery_actions: List[str] = Field(default_factory=list, description="Recovery actions taken")
    
    # Next steps
    next_step_recommendations: List[str] = Field(
        default_factory=list,
        description="Recommended next steps"
    )
    conditional_outcomes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Outcomes for conditional logic"
    )


# ==================== HANDLER INTERFACES ====================

class StepHandler(ABC):
    """Abstract base class for step handlers"""
    
    @abstractmethod
    async def can_handle(self, step: ProgramStep) -> bool:
        """Check if this handler can process the given step"""
        pass
    
    @abstractmethod
    async def execute(
        self, 
        step: ProgramStep, 
        context: ExecutionContext,
        debug_session: 'DebugSession'
    ) -> StepExecutionResult:
        """Execute the step and return result"""
        pass
    
    @abstractmethod
    async def validate(self, step: ProgramStep) -> List[str]:
        """Validate step configuration and return issues"""
        pass
    
    async def prepare(self, step: ProgramStep, context: ExecutionContext) -> Dict[str, Any]:
        """Prepare for step execution (optional override)"""
        return {}
    
    async def cleanup(self, step: ProgramStep, context: ExecutionContext, result: StepExecutionResult):
        """Cleanup after step execution (optional override)"""
        pass


class TriggerHandler(ABC):
    """Abstract base class for trigger handlers"""
    
    @abstractmethod
    async def can_handle(self, trigger_config: TriggerConfig) -> bool:
        """Check if this handler can process the given trigger"""
        pass
    
    @abstractmethod
    async def should_trigger(
        self, 
        trigger_config: TriggerConfig, 
        context: ExecutionContext
    ) -> bool:
        """Check if trigger conditions are met"""
        pass
    
    @abstractmethod
    async def setup_trigger(
        self, 
        trigger_config: TriggerConfig, 
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Setup trigger monitoring"""
        pass


class ActionHandler(ABC):
    """Abstract base class for action handlers"""
    
    @abstractmethod
    async def can_handle(self, action_config: ActionConfig) -> bool:
        """Check if this handler can process the given action"""
        pass
    
    @abstractmethod
    async def execute_action(
        self, 
        action_config: ActionConfig, 
        context: ExecutionContext,
        debug_session: 'DebugSession'
    ) -> Dict[str, Any]:
        """Execute the action and return result"""
        pass


# ==================== DEBUG SESSION ====================

class DebugSession:
    """Debug session for tracking execution details"""
    
    def __init__(self, program_id: str, user_id: str, debug_level: DebugLevel):
        self.program_id = program_id
        self.user_id = user_id
        self.debug_level = debug_level
        self.session_id = f"debug_{uuid4().hex[:8]}"
        self.started_at = datetime.utcnow()
        
        # Debug data storage
        self.milestones: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, float] = {}
        self.step_debugs: Dict[str, 'StepDebugSession'] = {}
        
        logger.info(f"Debug session started: {self.session_id}")
    
    def log_milestone(self, milestone_name: str, data: Any = None):
        """Log execution milestone"""
        if self.debug_level >= DebugLevel.STANDARD:
            milestone = {
                "name": milestone_name,
                "timestamp": datetime.utcnow(),
                "data": data
            }
            self.milestones.append(milestone)
            logger.debug(f"Milestone [{self.session_id}]: {milestone_name}")
    
    def log_error(self, error_type: str, error: Exception):
        """Log execution error"""
        error_data = {
            "type": error_type,
            "message": str(error),
            "timestamp": datetime.utcnow(),
            "exception_type": type(error).__name__
        }
        self.errors.append(error_data)
        logger.error(f"Error [{self.session_id}]: {error_type} - {error}")
    
    def record_metric(self, metric_name: str, value: float):
        """Record performance metric"""
        if self.debug_level >= DebugLevel.DETAILED:
            self.performance_metrics[metric_name] = value
            logger.debug(f"Metric [{self.session_id}]: {metric_name} = {value}")
    
    def create_step_debug(self, step_id: str) -> 'StepDebugSession':
        """Create debug session for step"""
        step_debug = StepDebugSession(step_id, self.debug_level, self.session_id)
        self.step_debugs[step_id] = step_debug
        return step_debug
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """Get all performance metrics"""
        metrics = self.performance_metrics.copy()
        metrics['total_execution_time'] = (datetime.utcnow() - self.started_at).total_seconds()
        metrics['milestones_count'] = len(self.milestones)
        metrics['errors_count'] = len(self.errors)
        return metrics
    
    def finalize(self):
        """Finalize debug session"""
        duration = (datetime.utcnow() - self.started_at).total_seconds()
        logger.info(f"Debug session finalized: {self.session_id} ({duration:.2f}s)")


class StepDebugSession:
    """Debug session for individual step execution"""
    
    def __init__(self, step_id: str, debug_level: DebugLevel, parent_session_id: str):
        self.step_id = step_id
        self.debug_level = debug_level
        self.parent_session_id = parent_session_id
        self.session_id = f"step_{uuid4().hex[:6]}"
        self.started_at = datetime.utcnow()
        
        self.events: List[Dict[str, Any]] = []
        self.metrics: Dict[str, float] = {}
        self.enhancements: Dict[str, Any] = {}
    
    def log_milestone(self, event_name: str, data: Any = None):
        """Log step milestone"""
        if self.debug_level >= DebugLevel.DETAILED:
            event = {
                "name": event_name,
                "timestamp": datetime.utcnow(),
                "data": data
            }
            self.events.append(event)
    
    def log_error(self, error_type: str, error: Exception):
        """Log step error"""
        error_data = {
            "type": error_type,
            "message": str(error),
            "timestamp": datetime.utcnow()
        }
        self.events.append({"name": "error", "data": error_data})
    
    def log_success(self, event_name: str, result: Any):
        """Log successful completion"""
        self.events.append({
            "name": event_name,
            "timestamp": datetime.utcnow(),
            "data": result
        })
    
    def record_enhancement(self, enhancement_type: str, data: Any):
        """Record enhancement data"""
        self.enhancements[enhancement_type] = data
    
    def get_enhancement_metadata(self) -> Dict[str, Any]:
        """Get enhancement metadata"""
        return {
            "enhancements_applied": list(self.enhancements.keys()),
            "enhancement_count": len(self.enhancements),
            "enhancement_data": self.enhancements
        }


# ==================== CORE PROGRAM ENGINE ====================

class ProgramEngine:
    """Core modular program execution engine"""
    
    def __init__(self):
        # Handler registries - Modular and extensible
        self.step_handlers: Dict[StepType, StepHandler] = {}
        self.trigger_handlers: Dict[TriggerType, TriggerHandler] = {}
        self.action_handlers: Dict[ActionType, ActionHandler] = {}
        
        # Extension points for future modularity
        self.execution_hooks: Dict[str, List[Callable]] = {
            'pre_execution': [],
            'post_execution': [],
            'pre_step': [],
            'post_step': [],
            'error_handler': []
        }
        
        # Performance monitoring
        self.execution_metrics: Dict[str, float] = {}
        
        logger.info("Program Engine initialized")
    
    # ==================== HANDLER REGISTRATION ====================
    
    def register_step_handler(self, step_type: StepType, handler: StepHandler):
        """Register step handler for extensibility"""
        self.step_handlers[step_type] = handler
        logger.info(f"Registered step handler for {step_type}: {handler.__class__.__name__}")
    
    def register_trigger_handler(self, trigger_type: TriggerType, handler: TriggerHandler):
        """Register trigger handler for extensibility"""
        self.trigger_handlers[trigger_type] = handler
        logger.info(f"Registered trigger handler for {trigger_type}: {handler.__class__.__name__}")
    
    def register_action_handler(self, action_type: ActionType, handler: ActionHandler):
        """Register action handler for extensibility"""
        self.action_handlers[action_type] = handler
        logger.info(f"Registered action handler for {action_type}: {handler.__class__.__name__}")
    
    def register_execution_hook(self, hook_name: str, callback: Callable):
        """Register execution hook for extensibility"""
        if hook_name not in self.execution_hooks:
            self.execution_hooks[hook_name] = []
        self.execution_hooks[hook_name].append(callback)
        logger.info(f"Registered execution hook: {hook_name}")
    
    # ==================== CORE EXECUTION ====================
    
    async def execute_program(
        self, 
        program: ProgramDefinition, 
        context: ExecutionContext
    ) -> ProgramExecutionResult:
        """Main program execution with comprehensive debugging"""
        
        debug_session = DebugSession(
            program.id, 
            context.user_id, 
            context.debug_level
        )
        
        start_time = datetime.utcnow()
        
        try:
            # Execute pre-execution hooks
            await self._execute_hooks('pre_execution', program, context, debug_session)
            debug_session.log_milestone("pre_execution_hooks_completed")
            
            # Validate program before execution
            validation_result = await self._validate_program_for_execution(program, context)
            if not validation_result.is_valid:
                raise ValueError(f"Program validation failed: {validation_result.errors}")
            debug_session.log_milestone("program_validated", validation_result)
            
            # Initialize execution state
            execution_state = await self._initialize_execution_state(program, context)
            debug_session.log_milestone("execution_state_initialized", execution_state)
            
            # Execute program steps based on strategy
            step_results = await self._execute_program_steps(
                program, context, execution_state, debug_session
            )
            debug_session.log_milestone("program_steps_executed", {
                "total_steps": len(step_results),
                "successful": sum(1 for r in step_results if r.success)
            })
            
            # Calculate final metrics
            final_metrics = await self._calculate_execution_metrics(
                program, context, step_results, debug_session
            )
            debug_session.record_metric("final_score", final_metrics.get("overall_score", 0))
            
            # Execute post-execution hooks
            await self._execute_hooks('post_execution', program, context, debug_session)
            
            # Create final result
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = ProgramExecutionResult(
                execution_id=context.execution_id,
                program_id=program.id,
                user_id=context.user_id,
                status="completed",
                completion_percentage=self._calculate_completion_percentage(step_results),
                step_results=step_results,
                total_steps_executed=len(step_results),
                successful_steps=sum(1 for r in step_results if r.success),
                failed_steps=sum(1 for r in step_results if not r.success),
                execution_time_seconds=execution_time,
                average_step_time=execution_time / max(len(step_results), 1),
                user_engagement_score=final_metrics.get("engagement_score", 0),
                personality_consistency_score=final_metrics.get("personality_consistency", 0),
                content_effectiveness_score=final_metrics.get("content_effectiveness", 0)
            )
            
            debug_session.log_milestone("execution_completed", result)
            logger.info(f"Program execution completed: {program.id} for user {context.user_id}")
            
            return result
            
        except Exception as e:
            debug_session.log_error("execution_failed", e)
            await self._execute_hooks('error_handler', program, context, debug_session, error=e)
            
            # Return failed execution result
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return ProgramExecutionResult(
                execution_id=context.execution_id,
                program_id=program.id,
                user_id=context.user_id,
                status="failed",
                completion_percentage=0.0,
                step_results=[],
                execution_time_seconds=execution_time,
                user_engagement_score=0.0
            )
        
        finally:
            debug_session.finalize()
    
    async def _execute_program_steps(
        self, 
        program: ProgramDefinition, 
        context: ExecutionContext,
        execution_state: Dict[str, Any],
        debug_session: DebugSession
    ) -> List[StepExecutionResult]:
        """Execute program steps based on execution strategy"""
        
        results = []
        
        if program.execution_config.execution_strategy == ExecutionStrategy.SEQUENTIAL:
            results = await self._execute_sequential_steps(
                program, context, execution_state, debug_session
            )
        elif program.execution_config.execution_strategy == ExecutionStrategy.PARALLEL_LIMITED:
            results = await self._execute_parallel_steps(
                program, context, execution_state, debug_session
            )
        elif program.execution_config.execution_strategy == ExecutionStrategy.CONDITIONAL_FLOW:
            results = await self._execute_conditional_flow(
                program, context, execution_state, debug_session
            )
        else:
            # Default to sequential
            results = await self._execute_sequential_steps(
                program, context, execution_state, debug_session
            )
        
        return results
    
    async def _execute_sequential_steps(
        self, 
        program: ProgramDefinition, 
        context: ExecutionContext,
        execution_state: Dict[str, Any],
        debug_session: DebugSession
    ) -> List[StepExecutionResult]:
        """Execute steps sequentially"""
        
        results = []
        current_steps = program.entry_step_ids.copy()
        
        while current_steps:
            # Execute current batch of steps
            batch_results = []
            
            for step_id in current_steps:
                step = await self._get_step_by_id(step_id, program)
                if step:
                    step_result = await self._execute_single_step(
                        step, context, debug_session
                    )
                    batch_results.append(step_result)
                    
                    # Update execution state
                    if step_result.success:
                        context.completed_steps.append(step_id)
                    else:
                        context.failed_steps.append(step_id)
            
            results.extend(batch_results)
            
            # Determine next steps
            current_steps = await self._determine_next_steps(
                batch_results, program, context, execution_state
            )
            
            debug_session.log_milestone("sequential_batch_completed", {
                "steps_processed": len(batch_results),
                "next_steps": len(current_steps)
            })
        
        return results
    
    async def _execute_parallel_steps(
        self, 
        program: ProgramDefinition, 
        context: ExecutionContext,
        execution_state: Dict[str, Any],
        debug_session: DebugSession
    ) -> List[StepExecutionResult]:
        """Execute steps with limited parallelism"""
        
        results = []
        current_steps = program.entry_step_ids.copy()
        parallel_limit = program.execution_config.parallel_execution_limit
        
        while current_steps:
            # Process steps in parallel batches
            batch_size = min(len(current_steps), parallel_limit)
            step_batch = current_steps[:batch_size]
            current_steps = current_steps[batch_size:]
            
            # Execute batch in parallel
            batch_tasks = []
            for step_id in step_batch:
                step = await self._get_step_by_id(step_id, program)
                if step:
                    task = asyncio.create_task(
                        self._execute_single_step(step, context, debug_session)
                    )
                    batch_tasks.append(task)
            
            # Wait for batch completion
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Process results and handle exceptions
            processed_results = []
            for i, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    # Create error result
                    step_id = step_batch[i]
                    error_result = StepExecutionResult(
                        step_id=step_id,
                        execution_id=context.execution_id,
                        status="failed",
                        started_at=datetime.utcnow(),
                        success=False,
                        error_message=str(result)
                    )
                    processed_results.append(error_result)
                else:
                    processed_results.append(result)
            
            results.extend(processed_results)
            
            # Update context
            for result in processed_results:
                if result.success:
                    context.completed_steps.append(result.step_id)
                else:
                    context.failed_steps.append(result.step_id)
            
            debug_session.log_milestone("parallel_batch_completed", {
                "batch_size": len(processed_results),
                "successful": sum(1 for r in processed_results if r.success)
            })
        
        return results
    
    async def _execute_conditional_flow(
        self, 
        program: ProgramDefinition, 
        context: ExecutionContext,
        execution_state: Dict[str, Any],
        debug_session: DebugSession
    ) -> List[StepExecutionResult]:
        """Execute steps based on conditional flow logic"""
        
        # For now, implement as sequential with conditional next-step determination
        # This can be expanded with a dedicated condition evaluator
        return await self._execute_sequential_steps(
            program, context, execution_state, debug_session
        )
    
    # ==================== HELPER METHODS ====================
    
    async def _execute_hooks(self, hook_name: str, *args, **kwargs):
        """Execute registered hooks"""
        for hook in self.execution_hooks.get(hook_name, []):
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook(*args, **kwargs)
                else:
                    hook(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Hook {hook_name} failed: {e}")
    
    async def _validate_program_for_execution(
        self, 
        program: ProgramDefinition, 
        context: ExecutionContext
    ) -> 'ProgramValidationResult':
        """Validate program before execution"""
        from .program_models import validate_program_structure
        return validate_program_structure(program)
    
    async def _initialize_execution_state(
        self, 
        program: ProgramDefinition, 
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Initialize execution state"""
        return {
            "program_variables": {},
            "step_outcomes": {},
            "user_responses": {},
            "conditional_results": {}
        }
    
    async def _get_step_by_id(self, step_id: str, program: ProgramDefinition) -> Optional[ProgramStep]:
        """Get step by ID - This would typically query the database"""
        # This is a placeholder - in real implementation would query database
        return None
    
    async def _execute_single_step(
        self, 
        step: ProgramStep, 
        context: ExecutionContext,
        debug_session: DebugSession
    ) -> StepExecutionResult:
        """Execute a single step using appropriate handler"""
        
        step_debug = debug_session.create_step_debug(step.step_id)
        start_time = datetime.utcnow()
        
        try:
            # Find appropriate handler
            handler = self.step_handlers.get(step.step_type)
            if not handler:
                raise ValueError(f"No handler registered for step type: {step.step_type}")
            
            step_debug.log_milestone("handler_selected", handler.__class__.__name__)
            
            # Execute step with handler
            result = await handler.execute(step, context, step_debug)
            
            # Update result timing
            result.started_at = start_time
            result.completed_at = datetime.utcnow()
            result.execution_time_seconds = (result.completed_at - start_time).total_seconds()
            
            step_debug.log_success("step_completed", result)
            return result
            
        except Exception as e:
            step_debug.log_error("step_execution_failed", e)
            
            # Create error result
            return StepExecutionResult(
                step_id=step.step_id,
                execution_id=context.execution_id,
                status="failed",
                started_at=start_time,
                completed_at=datetime.utcnow(),
                success=False,
                error_message=str(e)
            )
    
    async def _determine_next_steps(
        self, 
        batch_results: List[StepExecutionResult],
        program: ProgramDefinition,
        context: ExecutionContext,
        execution_state: Dict[str, Any]
    ) -> List[str]:
        """Determine next steps based on current results"""
        
        next_steps = []
        
        for result in batch_results:
            if result.success and result.next_step_recommendations:
                next_steps.extend(result.next_step_recommendations)
        
        # Remove duplicates and already completed steps
        next_steps = list(set(next_steps) - set(context.completed_steps))
        
        return next_steps
    
    async def _calculate_execution_metrics(
        self, 
        program: ProgramDefinition,
        context: ExecutionContext,
        step_results: List[StepExecutionResult],
        debug_session: DebugSession
    ) -> Dict[str, float]:
        """Calculate comprehensive execution metrics"""
        
        if not step_results:
            return {}
        
        metrics = {}
        
        # Basic success metrics
        successful_steps = [r for r in step_results if r.success]
        metrics['success_rate'] = len(successful_steps) / len(step_results)
        
        # Engagement metrics
        engagement_scores = [r.engagement_score for r in step_results if r.engagement_score > 0]
        metrics['engagement_score'] = sum(engagement_scores) / len(engagement_scores) if engagement_scores else 0
        
        # Personality consistency
        personality_scores = [r.personality_consistency for r in step_results if r.personality_consistency > 0]
        metrics['personality_consistency'] = sum(personality_scores) / len(personality_scores) if personality_scores else 0
        
        # Overall score
        metrics['overall_score'] = (
            metrics['success_rate'] * 0.4 +
            metrics['engagement_score'] * 0.3 +
            metrics['personality_consistency'] * 0.3
        )
        
        return metrics
    
    def _calculate_completion_percentage(self, step_results: List[StepExecutionResult]) -> float:
        """Calculate program completion percentage"""
        if not step_results:
            return 0.0
        
        successful_steps = sum(1 for r in step_results if r.success)
        return (successful_steps / len(step_results)) * 100


# ==================== GLOBAL ENGINE INSTANCE ====================

_program_engine: Optional[ProgramEngine] = None


def get_program_engine() -> ProgramEngine:
    """Get global program engine instance"""
    global _program_engine
    if _program_engine is None:
        _program_engine = ProgramEngine()
    return _program_engine


# Fix forward references
from pydantic import BaseModel, Field
StepExecutionResult.__annotations__['next_step_recommendations'] = List[str]
ProgramExecutionResult.model_rebuild()