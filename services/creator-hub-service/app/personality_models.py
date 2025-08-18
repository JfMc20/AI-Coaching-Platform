"""
Creator Personality System Models
Defines data structures for personality analysis, traits, and AI digital twin characteristics
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, validator
from shared.models.base import TenantAwareEntity


# ==================== PERSONALITY TRAITS & DIMENSIONS ====================

class PersonalityDimension(str, Enum):
    """Core personality dimensions for coaching style analysis"""
    COMMUNICATION_STYLE = "communication_style"  # Direct, Collaborative, Supportive, Challenging
    APPROACH_TYPE = "approach_type"              # Structured, Flexible, Intuitive, Analytical  
    INTERACTION_MODE = "interaction_mode"        # Formal, Casual, Empathetic, Results-focused
    QUESTIONING_STYLE = "questioning_style"      # Probing, Exploratory, Clarifying, Reflective
    FEEDBACK_DELIVERY = "feedback_delivery"      # Gentle, Direct, Encouraging, Constructive


class CommunicationStyle(str, Enum):
    """Communication style traits"""
    DIRECT = "direct"
    COLLABORATIVE = "collaborative"
    SUPPORTIVE = "supportive"
    CHALLENGING = "challenging"


class ApproachType(str, Enum):
    """Coaching approach traits"""
    STRUCTURED = "structured"
    FLEXIBLE = "flexible"
    INTUITIVE = "intuitive"
    ANALYTICAL = "analytical"


class InteractionMode(str, Enum):
    """Interaction mode traits"""
    FORMAL = "formal"
    CASUAL = "casual"
    EMPATHETIC = "empathetic"
    RESULTS_FOCUSED = "results_focused"


class QuestioningStyle(str, Enum):
    """Questioning style traits"""
    PROBING = "probing"
    EXPLORATORY = "exploratory"
    CLARIFYING = "clarifying"
    REFLECTIVE = "reflective"


class FeedbackDelivery(str, Enum):
    """Feedback delivery traits"""
    GENTLE = "gentle"
    DIRECT = "direct"
    ENCOURAGING = "encouraging"
    CONSTRUCTIVE = "constructive"


# ==================== PERSONALITY ANALYSIS MODELS ====================

class PersonalityTrait(BaseModel):
    """Individual personality trait with confidence score"""
    dimension: PersonalityDimension = Field(..., description="Personality dimension")
    trait_value: str = Field(..., description="Specific trait value")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in this trait (0-1)")
    evidence_count: int = Field(default=0, description="Number of supporting evidences")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last analysis update")


class PersonalityEvidence(BaseModel):
    """Evidence supporting a personality trait"""
    document_id: str = Field(..., description="Source document ID")
    chunk_index: int = Field(..., description="Chunk index in document")
    content_snippet: str = Field(..., max_length=500, description="Supporting content snippet")
    trait_indicators: List[str] = Field(default_factory=list, description="Detected trait indicators")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Evidence confidence")
    extracted_at: datetime = Field(default_factory=datetime.utcnow, description="When evidence was extracted")


class PersonalityProfile(TenantAwareEntity):
    """Complete personality profile for a creator"""
    creator_id: str = Field(..., description="Creator identifier")
    display_name: str = Field(..., description="Creator display name")
    
    # Core personality traits
    traits: List[PersonalityTrait] = Field(default_factory=list, description="Analyzed personality traits")
    
    # Personality summary
    personality_summary: Optional[str] = Field(None, max_length=1000, description="AI-generated personality summary")
    coaching_philosophy: Optional[str] = Field(None, max_length=1000, description="Extracted coaching philosophy")
    key_methodologies: List[str] = Field(default_factory=list, description="Key coaching methodologies used")
    
    # Analysis metadata
    analysis_version: str = Field(default="1.0", description="Personality analysis version")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall personality profile confidence")
    documents_analyzed: int = Field(default=0, description="Number of documents analyzed")
    last_analysis: Optional[datetime] = Field(None, description="Last personality analysis timestamp")
    
    # Consistency tracking
    consistency_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Personality consistency across documents")
    trait_stability: Dict[str, float] = Field(default_factory=dict, description="Stability score per trait")


class PersonalityAnalysisRequest(BaseModel):
    """Request for personality analysis"""
    creator_id: str = Field(..., description="Creator to analyze")
    force_reanalysis: bool = Field(default=False, description="Force complete reanalysis")
    include_documents: Optional[List[str]] = Field(None, description="Specific documents to analyze")
    analysis_depth: str = Field(default="standard", description="Analysis depth: quick, standard, deep")


class PersonalityAnalysisResponse(BaseModel):
    """Response from personality analysis"""
    creator_id: str = Field(..., description="Analyzed creator ID")
    analysis_status: str = Field(..., description="Analysis completion status")
    personality_profile: Optional[PersonalityProfile] = Field(None, description="Generated personality profile")
    traits_discovered: int = Field(default=0, description="Number of traits discovered")
    processing_time_seconds: float = Field(..., description="Analysis processing time")
    documents_processed: int = Field(default=0, description="Documents processed in this analysis")
    error_message: Optional[str] = Field(None, description="Error message if analysis failed")


# ==================== DYNAMIC PROMPT GENERATION MODELS ====================

class PromptTemplate(BaseModel):
    """Template for generating personality-aware prompts"""
    template_id: str = Field(..., description="Unique template identifier")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    base_prompt: str = Field(..., description="Base prompt template")
    personality_variables: List[str] = Field(default_factory=list, description="Personality variables to inject")
    context_variables: List[str] = Field(default_factory=list, description="Context variables to inject")
    use_cases: List[str] = Field(default_factory=list, description="Applicable use cases")


class PersonalizedPromptRequest(BaseModel):
    """Request for personalized prompt generation"""
    creator_id: str = Field(..., description="Creator for personalization")
    template_id: Optional[str] = Field(None, description="Specific template to use")
    context: str = Field(..., description="Conversation context")
    user_query: str = Field(..., description="User's original query")
    conversation_history: List[Dict[str, str]] = Field(default_factory=list, description="Recent conversation history")
    personality_emphasis: Optional[List[str]] = Field(None, description="Specific personality traits to emphasize")


class PersonalizedPromptResponse(BaseModel):
    """Response with personalized prompt"""
    creator_id: str = Field(..., description="Creator ID")
    personalized_prompt: str = Field(..., description="Generated personalized prompt")
    template_used: str = Field(..., description="Template that was used")
    personality_factors: Dict[str, Any] = Field(default_factory=dict, description="Personality factors applied")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Personalization confidence")
    generation_time_ms: float = Field(..., description="Prompt generation time")


# ==================== CONSISTENCY MONITORING MODELS ====================

class ConsistencyCheck(BaseModel):
    """Individual consistency check result"""
    check_id: str = Field(..., description="Unique check identifier")
    creator_id: str = Field(..., description="Creator being checked")
    conversation_id: str = Field(..., description="Conversation being analyzed")
    ai_response: str = Field(..., description="AI response to analyze")
    
    # Consistency scores
    personality_alignment: float = Field(..., ge=0.0, le=1.0, description="Personality alignment score")
    tone_consistency: float = Field(..., ge=0.0, le=1.0, description="Tone consistency score")
    methodology_adherence: float = Field(..., ge=0.0, le=1.0, description="Methodology adherence score")
    
    # Detailed analysis
    trait_deviations: List[str] = Field(default_factory=list, description="Detected trait deviations")
    positive_indicators: List[str] = Field(default_factory=list, description="Positive personality indicators")
    improvement_suggestions: List[str] = Field(default_factory=list, description="Suggestions for improvement")
    
    # Metadata
    checked_at: datetime = Field(default_factory=datetime.utcnow, description="When check was performed")
    check_version: str = Field(default="1.0", description="Consistency check version")


class ConsistencyMonitoringRequest(BaseModel):
    """Request for consistency monitoring"""
    creator_id: str = Field(..., description="Creator to monitor")
    ai_response: str = Field(..., description="AI response to check")
    conversation_id: str = Field(..., description="Conversation context")
    user_query: Optional[str] = Field(None, description="Original user query")
    expected_traits: Optional[List[str]] = Field(None, description="Expected personality traits")


class ConsistencyMonitoringResponse(BaseModel):
    """Response from consistency monitoring"""
    check_id: str = Field(..., description="Generated check ID")
    creator_id: str = Field(..., description="Creator ID")
    consistency_result: ConsistencyCheck = Field(..., description="Detailed consistency analysis")
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Overall consistency score")
    is_consistent: bool = Field(..., description="Whether response is consistent")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")


# ==================== PERSONALITY ANALYTICS MODELS ====================

class PersonalityMetrics(BaseModel):
    """Personality system performance metrics"""
    creator_id: str = Field(..., description="Creator ID")
    period_start: datetime = Field(..., description="Metrics period start")
    period_end: datetime = Field(..., description="Metrics period end")
    
    # Usage metrics
    total_conversations: int = Field(default=0, description="Total conversations processed")
    personality_enhanced_responses: int = Field(default=0, description="Responses with personality enhancement")
    consistency_checks_performed: int = Field(default=0, description="Consistency checks performed")
    
    # Quality metrics  
    average_consistency_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Average consistency score")
    personality_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Average personality confidence")
    user_satisfaction_correlation: Optional[float] = Field(None, description="Correlation with user satisfaction")
    
    # Improvement tracking
    trait_stability_trend: Dict[str, List[float]] = Field(default_factory=dict, description="Trait stability over time")
    consistency_trend: List[float] = Field(default_factory=list, description="Consistency score trend")
    personality_evolution: Dict[str, Any] = Field(default_factory=dict, description="How personality profile evolved")


class PersonalityDashboardData(BaseModel):
    """Data for personality analytics dashboard"""
    creator_id: str = Field(..., description="Creator ID")
    personality_profile: Optional[PersonalityProfile] = Field(None, description="Current personality profile")
    recent_metrics: PersonalityMetrics = Field(..., description="Recent performance metrics")
    trait_breakdown: Dict[str, float] = Field(default_factory=dict, description="Trait confidence breakdown")
    consistency_history: List[ConsistencyCheck] = Field(default_factory=list, description="Recent consistency checks")
    improvement_opportunities: List[str] = Field(default_factory=list, description="Areas for personality improvement")
    personality_strength_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall personality strength")


# ==================== VALIDATION AND HELPERS ====================

class PersonalitySystemConfig(BaseModel):
    """Configuration for personality system"""
    analysis_confidence_threshold: float = Field(default=0.7, description="Minimum confidence for trait detection")
    consistency_alert_threshold: float = Field(default=0.6, description="Threshold for consistency alerts")
    reanalysis_trigger_threshold: float = Field(default=0.5, description="Threshold to trigger reanalysis")
    max_evidence_per_trait: int = Field(default=10, description="Maximum evidence items per trait")
    personality_cache_duration_hours: int = Field(default=24, description="How long to cache personality data")


def get_trait_enum_by_dimension(dimension: PersonalityDimension) -> type:
    """Get the appropriate trait enum for a personality dimension"""
    trait_map = {
        PersonalityDimension.COMMUNICATION_STYLE: CommunicationStyle,
        PersonalityDimension.APPROACH_TYPE: ApproachType,
        PersonalityDimension.INTERACTION_MODE: InteractionMode,
        PersonalityDimension.QUESTIONING_STYLE: QuestioningStyle,
        PersonalityDimension.FEEDBACK_DELIVERY: FeedbackDelivery,
    }
    return trait_map.get(dimension, str)