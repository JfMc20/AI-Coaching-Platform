"""
Visual Program Builder - Step Models
Modular step definition models with extensible configuration system
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator
from shared.models.base import TenantAwareEntity

from .program_models import (
    StepType, TriggerType, ActionType, ChannelType, 
    CompletionCriteriaType, DebugLevel
)


# ==================== STEP CONFIGURATION MODELS ====================

class TriggerConfig(BaseModel):
    """Modular trigger configuration for step execution"""
    trigger_type: TriggerType = Field(..., description="Type of trigger")
    
    # Time-based triggers
    delay_seconds: Optional[int] = Field(
        None,
        ge=0,
        description="Delay in seconds before execution"
    )
    scheduled_time: Optional[datetime] = Field(
        None,
        description="Specific time to execute (for scheduled triggers)"
    )
    time_window_start: Optional[str] = Field(
        None,
        description="Start of acceptable time window (HH:MM format)"
    )
    time_window_end: Optional[str] = Field(
        None,
        description="End of acceptable time window (HH:MM format)"
    )
    
    # Condition-based triggers
    trigger_conditions: Dict[str, Any] = Field(
        default_factory=dict,
        description="Conditions that must be met for trigger activation"
    )
    condition_evaluation_frequency: int = Field(
        default=60,
        description="How often to check conditions (seconds)"
    )
    
    # User action triggers
    required_user_actions: List[str] = Field(
        default_factory=list,
        description="User actions that trigger execution"
    )
    action_timeout_seconds: Optional[int] = Field(
        None,
        description="Timeout waiting for user action"
    )
    
    # External triggers
    webhook_url: Optional[str] = Field(None, description="Webhook URL for external triggers")
    api_endpoint: Optional[str] = Field(None, description="API endpoint to poll")
    integration_name: Optional[str] = Field(None, description="Integration service name")
    
    # Retry and error handling
    max_trigger_attempts: int = Field(default=3, description="Maximum trigger attempts")
    retry_delay_seconds: int = Field(default=30, description="Delay between retry attempts")
    fallback_trigger: Optional[TriggerType] = Field(
        None,
        description="Fallback trigger if primary fails"
    )


class ActionConfig(BaseModel):
    """Modular action configuration for step execution"""
    action_type: ActionType = Field(..., description="Type of action to perform")
    
    # Content configuration
    content_template_id: Optional[str] = Field(
        None,
        description="ID of content template to use"
    )
    dynamic_content: Optional[str] = Field(
        None,
        description="Dynamic content string with variables"
    )
    content_variables: Dict[str, Any] = Field(
        default_factory=dict,
        description="Variables for content personalization"
    )
    
    # Personality configuration
    personality_overrides: Optional[List[str]] = Field(
        None,
        description="Personality traits to emphasize for this step"
    )
    personality_intensity: float = Field(
        default=1.0,
        ge=0.1,
        le=2.0,
        description="Personality expression intensity"
    )
    
    # Channel configuration
    preferred_channels: List[ChannelType] = Field(
        default_factory=lambda: [ChannelType.WEB_WIDGET],
        description="Preferred communication channels in order"
    )
    channel_fallback_enabled: bool = Field(
        default=True,
        description="Enable fallback to alternative channels"
    )
    channel_specific_config: Dict[ChannelType, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Channel-specific configuration"
    )
    
    # Task and evaluation configuration
    task_instructions: Optional[str] = Field(None, description="Task instructions for user")
    evaluation_criteria: List[str] = Field(
        default_factory=list,
        description="Criteria for evaluating user response"
    )
    evaluation_type: Optional[str] = Field(None, description="Type of evaluation (quiz, survey, etc.)")
    
    # Input collection configuration
    input_type: Optional[str] = Field(None, description="Type of input expected (text, file, selection)")
    input_validation_rules: List[str] = Field(
        default_factory=list,
        description="Validation rules for user input"
    )
    input_options: List[str] = Field(
        default_factory=list,
        description="Options for selection-type inputs"
    )
    
    # Integration configuration
    integration_endpoint: Optional[str] = Field(None, description="Integration API endpoint")
    integration_payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Payload for integration calls"
    )
    integration_headers: Dict[str, str] = Field(
        default_factory=dict,
        description="Headers for integration calls"
    )
    
    # Timing and flow control
    execution_timeout_seconds: int = Field(
        default=300,
        description="Maximum execution time"
    )
    async_execution: bool = Field(
        default=False,
        description="Whether action can be executed asynchronously"
    )
    wait_for_completion: bool = Field(
        default=True,
        description="Whether to wait for action completion"
    )


class ValidationConfig(BaseModel):
    """Modular validation configuration for steps"""
    validation_rules: List[str] = Field(
        default_factory=list,
        description="Validation rules to apply"
    )
    
    # Completion criteria
    completion_criteria: List[CompletionCriteriaType] = Field(
        default_factory=list,
        description="Criteria required for step completion"
    )
    completion_timeout_seconds: Optional[int] = Field(
        None,
        description="Timeout for step completion"
    )
    auto_complete_after_timeout: bool = Field(
        default=False,
        description="Auto-complete step after timeout"
    )
    
    # Quality thresholds
    minimum_engagement_seconds: int = Field(
        default=30,
        description="Minimum engagement time required"
    )
    response_quality_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum response quality score"
    )
    personality_consistency_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Minimum personality consistency score"
    )
    
    # Success criteria
    success_criteria: List[str] = Field(
        default_factory=list,
        description="Criteria defining successful step completion"
    )
    failure_criteria: List[str] = Field(
        default_factory=list,
        description="Criteria defining step failure"
    )
    
    # Retry and recovery
    allow_retries: bool = Field(default=True, description="Allow step retries on failure")
    max_retry_attempts: int = Field(default=3, description="Maximum retry attempts")
    retry_delay_seconds: int = Field(default=60, description="Delay between retries")


class ConditionalConfig(BaseModel):
    """Configuration for conditional logic and branching"""
    condition_expression: str = Field(..., description="Boolean expression for condition evaluation")
    
    # Branching paths
    true_path_step_ids: List[str] = Field(
        default_factory=list,
        description="Steps to execute if condition is true"
    )
    false_path_step_ids: List[str] = Field(
        default_factory=list,
        description="Steps to execute if condition is false"
    )
    default_path_step_ids: List[str] = Field(
        default_factory=list,
        description="Default path if condition evaluation fails"
    )
    
    # Condition evaluation
    evaluation_context_variables: List[str] = Field(
        default_factory=list,
        description="Variables available for condition evaluation"
    )
    evaluation_timeout_seconds: int = Field(
        default=30,
        description="Timeout for condition evaluation"
    )
    cache_evaluation_result: bool = Field(
        default=True,
        description="Cache evaluation result for performance"
    )
    cache_duration_seconds: int = Field(
        default=300,
        description="Duration to cache evaluation result"
    )
    
    # Complex conditions
    nested_conditions: List['ConditionalConfig'] = Field(
        default_factory=list,
        description="Nested conditional configurations"
    )
    combine_operator: str = Field(
        default="AND",
        description="Operator for combining nested conditions (AND, OR)"
    )


# ==================== CORE STEP MODELS ====================

class ProgramStep(TenantAwareEntity):
    """Individual step in a coaching program - Fully modular"""
    
    # Basic identification
    step_id: str = Field(..., description="Unique step identifier")
    program_id: str = Field(..., description="Parent program identifier")
    step_type: StepType = Field(..., description="Type of step")
    
    # Step metadata
    title: str = Field(..., max_length=200, description="Step title")
    description: Optional[str] = Field(None, max_length=1000, description="Step description")
    step_order: int = Field(..., ge=0, description="Order within program")
    is_optional: bool = Field(default=False, description="Whether step is optional")
    is_milestone: bool = Field(default=False, description="Whether step is a milestone")
    
    # Modular configurations
    trigger_config: TriggerConfig = Field(..., description="Trigger configuration")
    action_config: ActionConfig = Field(..., description="Action configuration")
    validation_config: ValidationConfig = Field(
        default_factory=ValidationConfig,
        description="Validation configuration"
    )
    conditional_config: Optional[ConditionalConfig] = Field(
        None,
        description="Conditional logic configuration"
    )
    
    # Flow control
    prerequisites: List[str] = Field(
        default_factory=list,
        description="Step IDs that must be completed before this step"
    )
    next_steps: List[str] = Field(
        default_factory=list,
        description="Possible next steps after completion"
    )
    parallel_steps: List[str] = Field(
        default_factory=list,
        description="Steps that can run in parallel with this one"
    )
    
    # Timing and scheduling
    estimated_duration_minutes: int = Field(
        default=5,
        ge=1,
        description="Estimated completion time"
    )
    min_time_between_attempts: int = Field(
        default=0,
        description="Minimum time between attempts (seconds)"
    )
    max_daily_attempts: int = Field(
        default=3,
        description="Maximum attempts per day"
    )
    
    # Analytics and tracking
    complexity_score: float = Field(
        default=1.0,
        ge=0.1,
        le=5.0,
        description="Step complexity score"
    )
    importance_weight: float = Field(
        default=1.0,
        ge=0.1,
        le=3.0,
        description="Importance weight for analytics"
    )
    track_detailed_analytics: bool = Field(
        default=True,
        description="Whether to track detailed analytics"
    )
    
    # Content and personalization
    content_tags: List[str] = Field(
        default_factory=list,
        description="Tags for content categorization"
    )
    target_emotions: List[str] = Field(
        default_factory=list,
        description="Target emotional responses"
    )
    difficulty_level: int = Field(
        default=1,
        ge=1,
        le=5,
        description="Difficulty level (1=easy, 5=hard)"
    )
    
    # Version and iteration
    version: str = Field(default="1.0", description="Step version")
    changelog: List[str] = Field(
        default_factory=list,
        description="Version changelog"
    )
    a_b_test_variant: Optional[str] = Field(
        None,
        description="A/B test variant identifier"
    )
    
    @validator('step_id')
    def validate_step_id(cls, v):
        if not v or not v.strip():
            raise ValueError('Step ID cannot be empty')
        return v.strip()
    
    @validator('title')
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError('Step title cannot be empty')
        return v.strip()


class StepTemplate(BaseModel):
    """Template for creating new steps"""
    template_id: str = Field(..., description="Unique template identifier")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    step_type: StepType = Field(..., description="Step type this template creates")
    category: str = Field(..., description="Template category")
    
    # Template configuration
    base_step_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Base step configuration"
    )
    customizable_fields: List[str] = Field(
        default_factory=list,
        description="Fields that can be customized"
    )
    required_fields: List[str] = Field(
        default_factory=list,
        description="Fields that must be specified"
    )
    
    # Usage metadata
    usage_count: int = Field(default=0, description="Number of times used")
    success_rate: float = Field(default=0.0, description="Success rate of steps created from template")
    recommended_for: List[str] = Field(
        default_factory=list,
        description="Recommended use cases"
    )


class StepExecution(BaseModel):
    """Execution instance of a program step"""
    execution_id: str = Field(..., description="Unique execution identifier")
    step_id: str = Field(..., description="Step being executed")
    program_id: str = Field(..., description="Parent program")
    user_id: str = Field(..., description="User for whom step is executed")
    
    # Execution status
    status: str = Field(..., description="Current execution status")
    started_at: datetime = Field(..., description="Execution start time")
    completed_at: Optional[datetime] = Field(None, description="Execution completion time")
    
    # Execution results
    result_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Step execution results"
    )
    user_response: Optional[str] = Field(None, description="User's response")
    success_score: float = Field(default=0.0, description="Success score (0-1)")
    
    # Performance metrics
    execution_time_seconds: float = Field(default=0.0, description="Total execution time")
    personality_consistency_score: float = Field(default=0.0, description="Personality consistency")
    user_engagement_score: float = Field(default=0.0, description="User engagement level")
    
    # Error tracking
    error_message: Optional[str] = Field(None, description="Error message if failed")
    retry_count: int = Field(default=0, description="Number of retry attempts")
    recovery_actions_taken: List[str] = Field(
        default_factory=list,
        description="Recovery actions attempted"
    )
    
    # Context and environment
    execution_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Execution context variables"
    )
    channel_used: Optional[ChannelType] = Field(None, description="Channel used for execution")
    device_info: Optional[Dict[str, str]] = Field(None, description="User device information")


class StepCondition(BaseModel):
    """Condition for step execution or flow control"""
    condition_id: str = Field(..., description="Unique condition identifier")
    condition_type: str = Field(..., description="Type of condition")
    expression: str = Field(..., description="Condition expression")
    
    # Context and variables
    required_variables: List[str] = Field(
        default_factory=list,
        description="Variables required for evaluation"
    )
    default_values: Dict[str, Any] = Field(
        default_factory=dict,
        description="Default values for variables"
    )
    
    # Evaluation settings
    evaluation_timeout_seconds: int = Field(default=30, description="Evaluation timeout")
    cache_result: bool = Field(default=True, description="Whether to cache result")
    cache_duration_seconds: int = Field(default=300, description="Cache duration")
    
    # Metadata
    description: str = Field(..., description="Human-readable condition description")
    created_by: str = Field(..., description="Creator of the condition")
    tags: List[str] = Field(default_factory=list, description="Condition tags")


# ==================== STEP ANALYTICS MODELS ====================

class StepMetrics(BaseModel):
    """Analytics metrics for individual steps"""
    step_id: str = Field(..., description="Step identifier")
    program_id: str = Field(..., description="Program identifier")
    measurement_period_start: datetime = Field(..., description="Measurement period start")
    measurement_period_end: datetime = Field(..., description="Measurement period end")
    
    # Execution metrics
    total_executions: int = Field(default=0, description="Total executions")
    successful_executions: int = Field(default=0, description="Successful executions")
    failed_executions: int = Field(default=0, description="Failed executions")
    success_rate: float = Field(default=0.0, description="Success rate")
    
    # Performance metrics
    average_execution_time: float = Field(default=0.0, description="Average execution time")
    average_completion_time: float = Field(default=0.0, description="Average completion time")
    retry_rate: float = Field(default=0.0, description="Retry rate")
    
    # User engagement
    average_engagement_score: float = Field(default=0.0, description="Average engagement")
    completion_rate: float = Field(default=0.0, description="Completion rate")
    dropout_rate: float = Field(default=0.0, description="Dropout rate")
    user_satisfaction_score: float = Field(default=0.0, description="User satisfaction")
    
    # Quality metrics
    average_personality_consistency: float = Field(default=0.0, description="Personality consistency")
    content_effectiveness_score: float = Field(default=0.0, description="Content effectiveness")
    user_feedback_sentiment: float = Field(default=0.0, description="Feedback sentiment")


class StepInsights(BaseModel):
    """Generated insights for step performance"""
    step_id: str = Field(..., description="Step identifier")
    insights: List[str] = Field(..., description="Generated insights")
    recommendations: List[str] = Field(..., description="Improvement recommendations")
    optimization_opportunities: List[str] = Field(
        default_factory=list,
        description="Optimization opportunities"
    )
    benchmark_comparison: Optional[Dict[str, float]] = Field(
        None,
        description="Comparison with benchmark steps"
    )
    trend_analysis: Dict[str, Any] = Field(
        default_factory=dict,
        description="Trend analysis data"
    )


# ==================== REQUEST/RESPONSE MODELS ====================

class StepCreateRequest(BaseModel):
    """Request for creating a new step"""
    title: str = Field(..., max_length=200, description="Step title")
    description: Optional[str] = Field(None, max_length=1000, description="Step description")
    step_type: StepType = Field(..., description="Step type")
    step_order: int = Field(..., ge=0, description="Step order")
    
    # Configuration
    trigger_config: TriggerConfig = Field(..., description="Trigger configuration")
    action_config: ActionConfig = Field(..., description="Action configuration")
    validation_config: Optional[ValidationConfig] = None
    conditional_config: Optional[ConditionalConfig] = None
    
    # Flow control
    prerequisites: List[str] = Field(default_factory=list, description="Prerequisite step IDs")
    
    # Template-based creation
    template_id: Optional[str] = Field(None, description="Template to base step on")
    template_customizations: Dict[str, Any] = Field(
        default_factory=dict,
        description="Template customizations"
    )


class StepUpdateRequest(BaseModel):
    """Request for updating a step"""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    step_order: Optional[int] = Field(None, ge=0)
    
    # Configuration updates
    trigger_config: Optional[TriggerConfig] = None
    action_config: Optional[ActionConfig] = None
    validation_config: Optional[ValidationConfig] = None
    conditional_config: Optional[ConditionalConfig] = None
    
    # Flow control updates
    prerequisites: Optional[List[str]] = None
    next_steps: Optional[List[str]] = None


class StepExecutionRequest(BaseModel):
    """Request for executing a step"""
    step_id: str = Field(..., description="Step to execute")
    user_id: str = Field(..., description="User for execution")
    execution_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Execution context"
    )
    override_config: Optional[Dict[str, Any]] = Field(
        None,
        description="Configuration overrides for this execution"
    )
    debug_level: DebugLevel = Field(
        default=DebugLevel.STANDARD,
        description="Debug level for execution"
    )


class StepExecutionResponse(BaseModel):
    """Response from step execution"""
    execution_id: str = Field(..., description="Execution identifier")
    step_id: str = Field(..., description="Step that was executed")
    status: str = Field(..., description="Execution status")
    result: Dict[str, Any] = Field(..., description="Execution result")
    metrics: Dict[str, float] = Field(..., description="Execution metrics")
    next_steps: List[str] = Field(default_factory=list, description="Recommended next steps")
    debug_info: Optional[Dict[str, Any]] = Field(None, description="Debug information")


# ==================== UTILITY FUNCTIONS ====================

def generate_step_id() -> str:
    """Generate unique step ID"""
    return f"step_{uuid4().hex[:8]}"


def generate_execution_id() -> str:
    """Generate unique execution ID"""
    return f"exec_{uuid4().hex[:12]}"


def validate_step_configuration(step: ProgramStep) -> List[str]:
    """Validate step configuration and return list of issues"""
    issues = []
    
    # Basic validation
    if not step.title.strip():
        issues.append("Step title cannot be empty")
    
    # Trigger validation
    if step.trigger_config.trigger_type == TriggerType.SCHEDULED and not step.trigger_config.scheduled_time:
        issues.append("Scheduled trigger requires scheduled_time")
    
    # Action validation
    if step.action_config.action_type == ActionType.SEND_MESSAGE and not step.action_config.content_template_id and not step.action_config.dynamic_content:
        issues.append("Message action requires content_template_id or dynamic_content")
    
    # Conditional validation
    if step.step_type == StepType.CONDITIONAL and not step.conditional_config:
        issues.append("Conditional step requires conditional_config")
    
    return issues


def estimate_step_complexity(step: ProgramStep) -> float:
    """Estimate step complexity based on configuration"""
    complexity = 1.0
    
    # Add complexity for advanced triggers
    if step.trigger_config.trigger_type in [TriggerType.CONDITIONAL, TriggerType.EXTERNAL]:
        complexity += 0.5
    
    # Add complexity for advanced actions
    if step.action_config.action_type in [ActionType.EVALUATE_RESPONSE, ActionType.BRANCH_FLOW]:
        complexity += 0.5
    
    # Add complexity for conditional logic
    if step.conditional_config:
        complexity += 1.0
        if step.conditional_config.nested_conditions:
            complexity += len(step.conditional_config.nested_conditions) * 0.3
    
    # Add complexity for multiple prerequisites
    if len(step.prerequisites) > 2:
        complexity += (len(step.prerequisites) - 2) * 0.2
    
    return min(5.0, complexity)


# Fix forward reference for nested ConditionalConfig
ConditionalConfig.model_rebuild()