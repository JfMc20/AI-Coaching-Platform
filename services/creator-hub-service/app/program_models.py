"""
Visual Program Builder - Core Models
Modular program definition models for scalable coaching program automation
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator
from shared.models.base import TenantAwareEntity


# ==================== CORE ENUMS & TYPES ====================

class ProgramStatus(str, Enum):
    """Program lifecycle status"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    TEMPLATE = "template"


class ExecutionStrategy(str, Enum):
    """Program execution strategies"""
    SEQUENTIAL = "sequential"          # One step at a time
    PARALLEL_LIMITED = "parallel_limited"    # Limited parallel execution
    CONDITIONAL_FLOW = "conditional_flow"    # Flow based on conditions
    USER_PACED = "user_paced"         # User controls progression
    TIME_BASED = "time_based"         # Schedule-driven execution


class StepType(str, Enum):
    """Types of program steps"""
    MESSAGE = "message"               # Send personalized message
    TASK = "task"                    # Assign task or exercise
    EVALUATION = "evaluation"        # Assessment or quiz
    CHECKPOINT = "checkpoint"        # Progress checkpoint
    CONDITIONAL = "conditional"      # Conditional branching
    DELAY = "delay"                 # Time delay or wait
    CONTENT_DELIVERY = "content_delivery"  # Rich content delivery
    MILESTONE = "milestone"         # Achievement milestone
    FEEDBACK_REQUEST = "feedback_request"  # Request user feedback
    CUSTOM = "custom"               # Custom extensible step


class TriggerType(str, Enum):
    """Step trigger types"""
    IMMEDIATE = "immediate"          # Execute immediately
    TIME_DELAY = "time_delay"       # Execute after delay
    SCHEDULED = "scheduled"         # Execute at specific time
    USER_ACTION = "user_action"     # Triggered by user action
    CONDITIONAL = "conditional"     # Triggered by condition
    EXTERNAL = "external"           # Triggered by external system
    COMPLETION_BASED = "completion_based"  # After previous step completion


class ActionType(str, Enum):
    """Action types for step execution"""
    SEND_MESSAGE = "send_message"
    ASSIGN_TASK = "assign_task"
    REQUEST_INPUT = "request_input"
    EVALUATE_RESPONSE = "evaluate_response"
    UPDATE_PROGRESS = "update_progress"
    BRANCH_FLOW = "branch_flow"
    SCHEDULE_FOLLOWUP = "schedule_followup"
    TRIGGER_INTEGRATION = "trigger_integration"
    COLLECT_FEEDBACK = "collect_feedback"
    CUSTOM_ACTION = "custom_action"


class ChannelType(str, Enum):
    """Communication channels"""
    WEB_WIDGET = "web_widget"
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    SMS = "sms"
    PUSH_NOTIFICATION = "push_notification"
    IN_APP = "in_app"
    API_WEBHOOK = "api_webhook"


class CompletionCriteriaType(str, Enum):
    """Criteria for step completion"""
    USER_RESPONSE = "user_response"
    TIME_ELAPSED = "time_elapsed"
    TASK_SUBMITTED = "task_submitted"
    EVALUATION_PASSED = "evaluation_passed"
    EXTERNAL_CONFIRMATION = "external_confirmation"
    AUTOMATIC = "automatic"


class DebugLevel(str, Enum):
    """Debug logging levels"""
    MINIMAL = "minimal"
    STANDARD = "standard"
    DETAILED = "detailed"
    DEEP = "deep"
    TRACE = "trace"


# ==================== CONFIGURATION MODELS ====================

class PersonalityConfig(BaseModel):
    """Modular personality configuration for programs"""
    default_personality_emphasis: List[str] = Field(
        default_factory=list,
        description="Default personality traits to emphasize"
    )
    step_specific_overrides: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Step-specific personality overrides"
    )
    consistency_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Minimum personality consistency score"
    )
    adaptive_personality: bool = Field(
        default=True,
        description="Enable adaptive personality based on user responses"
    )
    personality_intensity: float = Field(
        default=1.0,
        ge=0.1,
        le=2.0,
        description="Personality expression intensity (0.1=subtle, 2.0=strong)"
    )


class ExecutionConfig(BaseModel):
    """Modular execution configuration"""
    execution_strategy: ExecutionStrategy = Field(
        default=ExecutionStrategy.SEQUENTIAL,
        description="Program execution strategy"
    )
    parallel_execution_limit: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum parallel step executions"
    )
    default_step_timeout: int = Field(
        default=300,
        description="Default step timeout in seconds"
    )
    retry_attempts: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Number of retry attempts for failed steps"
    )
    retry_delay_seconds: int = Field(
        default=30,
        ge=1,
        description="Delay between retry attempts"
    )
    enable_error_recovery: bool = Field(
        default=True,
        description="Enable automatic error recovery"
    )
    preserve_execution_state: bool = Field(
        default=True,
        description="Preserve state between executions"
    )


class AnalyticsConfig(BaseModel):
    """Modular analytics configuration"""
    detailed_logging: bool = Field(
        default=True,
        description="Enable detailed execution logging"
    )
    performance_tracking: bool = Field(
        default=True,
        description="Track performance metrics"
    )
    user_journey_mapping: bool = Field(
        default=True,
        description="Map complete user journey"
    )
    a_b_testing_enabled: bool = Field(
        default=False,
        description="Enable A/B testing capabilities"
    )
    retention_days: int = Field(
        default=90,
        ge=1,
        le=365,
        description="Analytics data retention period"
    )
    real_time_monitoring: bool = Field(
        default=True,
        description="Enable real-time execution monitoring"
    )


class NotificationConfig(BaseModel):
    """Notification and communication configuration"""
    preferred_channels: List[ChannelType] = Field(
        default_factory=lambda: [ChannelType.WEB_WIDGET],
        description="Preferred communication channels in order"
    )
    channel_fallback_enabled: bool = Field(
        default=True,
        description="Enable fallback to alternative channels"
    )
    notification_timing: Dict[str, Any] = Field(
        default_factory=dict,
        description="Timing preferences for notifications"
    )
    quiet_hours: Optional[Dict[str, str]] = Field(
        default=None,
        description="Quiet hours when notifications are paused"
    )
    max_daily_notifications: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum notifications per day"
    )


# ==================== CORE PROGRAM MODELS ====================

class ProgramDefinition(TenantAwareEntity):
    """Main program definition - Core modular structure"""
    
    # Basic information
    title: str = Field(..., max_length=200, description="Program title")
    description: str = Field(..., max_length=1000, description="Program description")
    version: str = Field(default="1.0", description="Program version")
    status: ProgramStatus = Field(default=ProgramStatus.DRAFT, description="Program status")
    
    # Duration and scope
    estimated_duration_days: Optional[int] = Field(
        None,
        ge=1,
        le=365,
        description="Estimated duration in days"
    )
    estimated_daily_engagement_minutes: int = Field(
        default=15,
        ge=1,
        le=120,
        description="Estimated daily engagement time"
    )
    
    # Modular configurations
    personality_config: PersonalityConfig = Field(
        default_factory=PersonalityConfig,
        description="Personality system configuration"
    )
    execution_config: ExecutionConfig = Field(
        default_factory=ExecutionConfig,
        description="Execution engine configuration"
    )
    analytics_config: AnalyticsConfig = Field(
        default_factory=AnalyticsConfig,
        description="Analytics and monitoring configuration"
    )
    notification_config: NotificationConfig = Field(
        default_factory=NotificationConfig,
        description="Notification and channel configuration"
    )
    
    # Program structure
    entry_step_ids: List[str] = Field(
        default_factory=list,
        description="Entry point step IDs"
    )
    exit_conditions: List[str] = Field(
        default_factory=list,
        description="Program completion conditions"
    )
    
    # Metadata for scalability
    tags: List[str] = Field(default_factory=list, description="Program tags")
    category: str = Field(default="general", description="Program category")
    complexity_level: int = Field(
        default=1,
        ge=1,
        le=5,
        description="Program complexity (1=basic, 5=advanced)"
    )
    target_audience: List[str] = Field(
        default_factory=list,
        description="Target audience characteristics"
    )
    learning_objectives: List[str] = Field(
        default_factory=list,
        description="Expected learning outcomes"
    )
    
    # Template and cloning
    is_template: bool = Field(default=False, description="Whether this is a template")
    template_source_id: Optional[str] = Field(
        None,
        description="Source template ID if cloned"
    )
    clone_count: int = Field(default=0, description="Number of times cloned")
    
    # Usage statistics
    total_enrollments: int = Field(default=0, description="Total enrollments")
    active_enrollments: int = Field(default=0, description="Currently active enrollments")
    completion_rate: float = Field(default=0.0, description="Overall completion rate")
    average_rating: Optional[float] = Field(None, description="Average user rating")
    
    @validator('title')
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError('Program title cannot be empty')
        return v.strip()
    
    @validator('entry_step_ids')
    def validate_entry_steps(cls, v):
        if not v:
            raise ValueError('Program must have at least one entry step')
        return v


class ProgramTemplate(BaseModel):
    """Template for creating new programs"""
    template_id: str = Field(..., description="Unique template identifier")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    category: str = Field(..., description="Template category")
    
    # Template structure
    base_program: ProgramDefinition = Field(..., description="Base program definition")
    customizable_fields: List[str] = Field(
        default_factory=list,
        description="Fields that can be customized"
    )
    required_personalizations: List[str] = Field(
        default_factory=list,
        description="Required personalizations before use"
    )
    
    # Usage and popularity
    usage_count: int = Field(default=0, description="Number of times used")
    average_success_rate: float = Field(default=0.0, description="Average success rate")
    recommended_for: List[str] = Field(
        default_factory=list,
        description="Recommended use cases"
    )


class ProgramMetrics(BaseModel):
    """Program performance metrics"""
    program_id: str = Field(..., description="Program identifier")
    measurement_period_start: datetime = Field(..., description="Measurement period start")
    measurement_period_end: datetime = Field(..., description="Measurement period end")
    
    # Engagement metrics
    total_participants: int = Field(default=0, description="Total participants")
    active_participants: int = Field(default=0, description="Currently active participants")
    completion_rate: float = Field(default=0.0, description="Completion rate")
    dropout_rate: float = Field(default=0.0, description="Dropout rate")
    average_engagement_time: float = Field(default=0.0, description="Average daily engagement minutes")
    
    # Quality metrics
    user_satisfaction_score: float = Field(default=0.0, description="User satisfaction (1-5)")
    personality_consistency_score: float = Field(default=0.0, description="Personality consistency")
    content_effectiveness_score: float = Field(default=0.0, description="Content effectiveness")
    
    # Performance metrics
    average_step_completion_time: float = Field(default=0.0, description="Average step completion time")
    error_rate: float = Field(default=0.0, description="Execution error rate")
    system_response_time: float = Field(default=0.0, description="Average system response time")
    
    # Behavioral insights
    most_engaging_steps: List[str] = Field(default_factory=list, description="Most engaging step IDs")
    common_drop_points: List[str] = Field(default_factory=list, description="Common dropout step IDs")
    user_feedback_themes: List[str] = Field(default_factory=list, description="Common feedback themes")


# ==================== REQUEST/RESPONSE MODELS ====================

class ProgramCreateRequest(BaseModel):
    """Request model for creating new programs"""
    title: str = Field(..., max_length=200, description="Program title")
    description: str = Field(..., max_length=1000, description="Program description")
    category: str = Field(default="general", description="Program category")
    tags: List[str] = Field(default_factory=list, description="Program tags")
    
    # Optional configurations
    personality_config: Optional[PersonalityConfig] = None
    execution_config: Optional[ExecutionConfig] = None
    analytics_config: Optional[AnalyticsConfig] = None
    notification_config: Optional[NotificationConfig] = None
    
    # Template-based creation
    template_id: Optional[str] = Field(None, description="Template to base program on")
    template_customizations: Dict[str, Any] = Field(
        default_factory=dict,
        description="Customizations to apply to template"
    )


class ProgramUpdateRequest(BaseModel):
    """Request model for updating programs"""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[ProgramStatus] = None
    tags: Optional[List[str]] = None
    
    # Configuration updates
    personality_config: Optional[PersonalityConfig] = None
    execution_config: Optional[ExecutionConfig] = None
    analytics_config: Optional[AnalyticsConfig] = None
    notification_config: Optional[NotificationConfig] = None


class ProgramListResponse(BaseModel):
    """Response model for program listing"""
    programs: List[ProgramDefinition] = Field(..., description="List of programs")
    total_count: int = Field(..., ge=0, description="Total number of programs")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Page size")
    has_next: bool = Field(..., description="Whether there are more pages")
    filter_summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Applied filters summary"
    )


class ProgramAnalyticsResponse(BaseModel):
    """Response model for program analytics"""
    program_id: str = Field(..., description="Program identifier")
    analytics_data: Dict[str, Any] = Field(..., description="Analytics data")
    insights: List[str] = Field(default_factory=list, description="Generated insights")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")
    benchmark_comparison: Optional[Dict[str, float]] = Field(
        None,
        description="Comparison with benchmark programs"
    )


# ==================== VALIDATION & UTILITY MODELS ====================

class ProgramValidationResult(BaseModel):
    """Result of program validation"""
    is_valid: bool = Field(..., description="Whether program is valid")
    validation_errors: List[str] = Field(default_factory=list, description="Validation errors")
    validation_warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    completeness_score: float = Field(default=0.0, description="Program completeness score")
    estimated_setup_time: int = Field(default=0, description="Estimated setup time in minutes")


class ProgramCloneRequest(BaseModel):
    """Request for cloning a program"""
    source_program_id: str = Field(..., description="Source program to clone")
    new_title: str = Field(..., description="Title for cloned program")
    new_description: Optional[str] = Field(None, description="Description for cloned program")
    customizations: Dict[str, Any] = Field(
        default_factory=dict,
        description="Customizations to apply during cloning"
    )
    preserve_analytics: bool = Field(
        default=False,
        description="Whether to preserve analytics configuration"
    )


class ProgramExportRequest(BaseModel):
    """Request for exporting program data"""
    program_id: str = Field(..., description="Program to export")
    export_format: str = Field(default="json", description="Export format (json, yaml, xml)")
    include_analytics: bool = Field(default=False, description="Include analytics data")
    include_execution_history: bool = Field(default=False, description="Include execution history")
    date_range: Optional[Dict[str, datetime]] = Field(None, description="Date range for historical data")


# ==================== EXTENSION MODELS ====================

class ExtensionHook(str, Enum):
    """Extension points for future modularity"""
    PRE_PROGRAM_CREATION = "pre_program_creation"
    POST_PROGRAM_CREATION = "post_program_creation"
    PRE_PROGRAM_EXECUTION = "pre_program_execution"
    POST_PROGRAM_EXECUTION = "post_program_execution"
    PROGRAM_VALIDATION = "program_validation"
    ANALYTICS_COLLECTION = "analytics_collection"
    CONTENT_ENHANCEMENT = "content_enhancement"


class ProgramExtension(BaseModel):
    """Base model for program extensions"""
    extension_id: str = Field(..., description="Unique extension identifier")
    name: str = Field(..., description="Extension name")
    version: str = Field(..., description="Extension version")
    description: str = Field(..., description="Extension description")
    supported_hooks: List[ExtensionHook] = Field(..., description="Supported extension hooks")
    configuration: Dict[str, Any] = Field(default_factory=dict, description="Extension configuration")
    is_active: bool = Field(default=True, description="Whether extension is active")


# ==================== HELPER FUNCTIONS ====================

def generate_program_id() -> str:
    """Generate unique program ID"""
    return f"prog_{uuid4().hex[:12]}"


def generate_step_id() -> str:
    """Generate unique step ID"""
    return f"step_{uuid4().hex[:8]}"


def validate_program_structure(program: ProgramDefinition) -> ProgramValidationResult:
    """Validate program structure and configuration"""
    errors = []
    warnings = []
    
    # Basic validation
    if not program.title.strip():
        errors.append("Program title cannot be empty")
    
    if not program.entry_step_ids:
        errors.append("Program must have at least one entry step")
    
    # Configuration validation
    if program.personality_config.consistency_threshold < 0.5:
        warnings.append("Low personality consistency threshold may affect user experience")
    
    if program.execution_config.parallel_execution_limit > 5:
        warnings.append("High parallel execution limit may impact performance")
    
    # Calculate completeness score
    completeness_factors = [
        bool(program.title),
        bool(program.description),
        bool(program.entry_step_ids),
        bool(program.tags),
        bool(program.learning_objectives)
    ]
    completeness_score = sum(completeness_factors) / len(completeness_factors)
    
    return ProgramValidationResult(
        is_valid=len(errors) == 0,
        validation_errors=errors,
        validation_warnings=warnings,
        completeness_score=completeness_score,
        estimated_setup_time=len(program.entry_step_ids) * 5  # 5 minutes per entry step
    )