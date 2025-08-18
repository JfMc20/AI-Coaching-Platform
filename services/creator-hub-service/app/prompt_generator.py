"""
Dynamic Prompt Generation Engine
Generates personality-aware prompts based on creator personality traits and conversation context
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4

from .personality_models import (
    PersonalityProfile, PersonalityTrait, PersonalityDimension,
    PromptTemplate, PersonalizedPromptRequest, PersonalizedPromptResponse,
    CommunicationStyle, ApproachType, InteractionMode, QuestioningStyle, FeedbackDelivery
)
from .ai_client import get_ai_client, ConversationResponse
from .database import KnowledgeBaseService

logger = logging.getLogger(__name__)


class DynamicPromptGenerator:
    """
    Generates personalized prompts based on creator personality and conversation context
    """
    
    def __init__(self):
        self.ai_client = get_ai_client()
        
        # Initialize prompt templates
        self.prompt_templates = self._initialize_prompt_templates()
        
        logger.info("Dynamic Prompt Generator initialized")
    
    def _initialize_prompt_templates(self) -> Dict[str, PromptTemplate]:
        """Initialize base prompt templates for different use cases"""
        return {
            "general_coaching": PromptTemplate(
                template_id="general_coaching",
                name="General Coaching Response",
                description="General coaching conversation template",
                base_prompt="""You are {creator_name}, a {experience_description} coach. 

Your personality:
{personality_description}

Communication style: {communication_style}
Approach: {approach_type}
Interaction mode: {interaction_mode}

User context: {user_context}
User query: {user_query}

Respond in your authentic voice, following your natural coaching style. {specific_instructions}""",
                personality_variables=["communication_style", "approach_type", "interaction_mode", "personality_description"],
                context_variables=["user_context", "user_query", "creator_name", "experience_description"],
                use_cases=["general_conversation", "coaching_session", "question_answering"]
            ),
            
            "goal_setting": PromptTemplate(
                template_id="goal_setting",
                name="Goal Setting Session",
                description="Template for goal setting conversations",
                base_prompt="""You are {creator_name}, helping with goal setting.

Your coaching approach: {approach_type}
Your questioning style: {questioning_style}
Your feedback delivery: {feedback_delivery}

The user wants to work on: {user_query}

Current context: {user_context}

Guide them through goal setting using your natural {questioning_style} questioning style and {approach_type} approach. {methodology_guidance}""",
                personality_variables=["approach_type", "questioning_style", "feedback_delivery"],
                context_variables=["user_context", "user_query", "creator_name", "methodology_guidance"],
                use_cases=["goal_setting", "planning", "visioning"]
            ),
            
            "feedback_delivery": PromptTemplate(
                template_id="feedback_delivery",
                name="Feedback and Assessment",
                description="Template for giving feedback and assessments",
                base_prompt="""You are {creator_name}, providing feedback and guidance.

Your feedback style: {feedback_delivery}
Your communication approach: {communication_style}

User's situation: {user_context}
User's request: {user_query}

Provide feedback using your natural {feedback_delivery} style and {communication_style} communication approach. {supportive_guidance}""",
                personality_variables=["feedback_delivery", "communication_style"],
                context_variables=["user_context", "user_query", "creator_name", "supportive_guidance"],
                use_cases=["feedback", "assessment", "progress_review"]
            ),
            
            "problem_solving": PromptTemplate(
                template_id="problem_solving",
                name="Problem Solving Session",
                description="Template for problem-solving conversations",
                base_prompt="""You are {creator_name}, helping solve a challenge.

Your problem-solving approach: {approach_type}
Your interaction style: {interaction_mode}
Your questioning method: {questioning_style}

Challenge presented: {user_query}
Background context: {user_context}

Use your {approach_type} approach and {questioning_style} questioning to help them work through this. {methodology_application}""",
                personality_variables=["approach_type", "interaction_mode", "questioning_style"],
                context_variables=["user_context", "user_query", "creator_name", "methodology_application"],
                use_cases=["problem_solving", "challenge_resolution", "decision_making"]
            ),
            
            "motivational_support": PromptTemplate(
                template_id="motivational_support",
                name="Motivational Support",
                description="Template for motivational and support conversations",
                base_prompt="""You are {creator_name}, providing motivational support.

Your supportive style: {communication_style}
Your interaction approach: {interaction_mode}
Your encouragement method: {feedback_delivery}

User's challenge: {user_query}
Current situation: {user_context}

Provide support using your {communication_style} style and {feedback_delivery} encouragement approach. {emotional_support_guidance}""",
                personality_variables=["communication_style", "interaction_mode", "feedback_delivery"],
                context_variables=["user_context", "user_query", "creator_name", "emotional_support_guidance"],
                use_cases=["motivation", "support", "encouragement", "confidence_building"]
            )
        }
    
    async def generate_personalized_prompt(
        self,
        request: PersonalizedPromptRequest,
        personality_profile: PersonalityProfile,
        session
    ) -> PersonalizedPromptResponse:
        """
        Generate personalized prompt based on creator personality and context
        
        Args:
            request: Prompt generation request
            personality_profile: Creator's personality profile
            session: Database session
            
        Returns:
            PersonalizedPromptResponse with generated prompt
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Generating personalized prompt for creator {request.creator_id}")
            
            # Select appropriate template
            template = self._select_template(request, personality_profile)
            
            # Extract personality factors
            personality_factors = self._extract_personality_factors(personality_profile, request.personality_emphasis)
            
            # Generate context variables
            context_variables = await self._generate_context_variables(request, personality_profile, session)
            
            # Build personalized prompt
            personalized_prompt = self._build_prompt(template, personality_factors, context_variables)
            
            # Calculate confidence score
            confidence_score = self._calculate_personalization_confidence(personality_profile, template)
            
            # Calculate generation time
            generation_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.info(
                f"Personalized prompt generated for creator {request.creator_id}: "
                f"template={template.template_id}, confidence={confidence_score:.2f}"
            )
            
            return PersonalizedPromptResponse(
                creator_id=request.creator_id,
                personalized_prompt=personalized_prompt,
                template_used=template.template_id,
                personality_factors=personality_factors,
                confidence_score=confidence_score,
                generation_time_ms=generation_time
            )
            
        except Exception as e:
            generation_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(f"Failed to generate personalized prompt: {str(e)}")
            
            # Return fallback prompt
            return self._generate_fallback_prompt(request, generation_time)
    
    def _select_template(self, request: PersonalizedPromptRequest, personality_profile: PersonalityProfile) -> PromptTemplate:
        """Select the most appropriate template based on request context"""
        
        # Analyze user query for intent
        query_lower = request.user_query.lower()
        context_lower = request.context.lower()
        
        # Goal-setting keywords
        if any(keyword in query_lower for keyword in ["goal", "plan", "objective", "target", "achieve", "want to"]):
            return self.prompt_templates["goal_setting"]
        
        # Feedback keywords
        elif any(keyword in query_lower for keyword in ["feedback", "review", "assess", "evaluate", "how did i do", "progress"]):
            return self.prompt_templates["feedback_delivery"]
        
        # Problem-solving keywords
        elif any(keyword in query_lower for keyword in ["problem", "challenge", "stuck", "difficult", "issue", "solve", "help with"]):
            return self.prompt_templates["problem_solving"]
        
        # Motivational support keywords
        elif any(keyword in query_lower for keyword in ["motivated", "discouraged", "difficult", "struggling", "support", "encourage"]):
            return self.prompt_templates["motivational_support"]
        
        # Use specific template if requested
        elif request.template_id and request.template_id in self.prompt_templates:
            return self.prompt_templates[request.template_id]
        
        # Default to general coaching
        else:
            return self.prompt_templates["general_coaching"]
    
    def _extract_personality_factors(
        self, 
        personality_profile: PersonalityProfile, 
        emphasis_traits: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Extract personality factors for prompt customization"""
        
        factors = {
            "creator_name": personality_profile.display_name,
            "personality_description": personality_profile.personality_summary or "experienced coach",
            "key_methodologies": personality_profile.key_methodologies,
            "confidence_level": personality_profile.confidence_score
        }
        
        # Extract dominant traits for each dimension
        trait_by_dimension = {}
        for trait in personality_profile.traits:
            dimension = trait.dimension
            
            if dimension not in trait_by_dimension or trait.confidence_score > trait_by_dimension[dimension].confidence_score:
                trait_by_dimension[dimension] = trait
        
        # Map personality dimensions to prompt variables
        for dimension, trait in trait_by_dimension.items():
            if dimension == PersonalityDimension.COMMUNICATION_STYLE:
                factors["communication_style"] = self._describe_communication_style(trait.trait_value)
            elif dimension == PersonalityDimension.APPROACH_TYPE:
                factors["approach_type"] = self._describe_approach_type(trait.trait_value)
            elif dimension == PersonalityDimension.INTERACTION_MODE:
                factors["interaction_mode"] = self._describe_interaction_mode(trait.trait_value)
            elif dimension == PersonalityDimension.QUESTIONING_STYLE:
                factors["questioning_style"] = self._describe_questioning_style(trait.trait_value)
            elif dimension == PersonalityDimension.FEEDBACK_DELIVERY:
                factors["feedback_delivery"] = self._describe_feedback_delivery(trait.trait_value)
        
        # Apply emphasis if specified
        if emphasis_traits:
            factors["personality_emphasis"] = emphasis_traits
        
        return factors
    
    async def _generate_context_variables(
        self,
        request: PersonalizedPromptRequest,
        personality_profile: PersonalityProfile,
        session
    ) -> Dict[str, str]:
        """Generate context-specific variables for the prompt"""
        
        variables = {
            "user_query": request.user_query,
            "user_context": request.context,
            "creator_name": personality_profile.display_name
        }
        
        # Generate experience description
        variables["experience_description"] = self._generate_experience_description(personality_profile)
        
        # Generate methodology guidance based on creator's methodologies
        variables["methodology_guidance"] = self._generate_methodology_guidance(personality_profile.key_methodologies)
        
        # Generate specific instructions based on personality
        variables["specific_instructions"] = self._generate_specific_instructions(personality_profile)
        
        # Generate supportive guidance
        variables["supportive_guidance"] = self._generate_supportive_guidance(personality_profile)
        
        # Generate emotional support guidance
        variables["emotional_support_guidance"] = self._generate_emotional_support_guidance(personality_profile)
        
        # Generate methodology application guidance
        variables["methodology_application"] = self._generate_methodology_application(personality_profile)
        
        return variables
    
    def _build_prompt(
        self,
        template: PromptTemplate,
        personality_factors: Dict[str, Any],
        context_variables: Dict[str, str]
    ) -> str:
        """Build the final personalized prompt"""
        
        # Combine all variables
        all_variables = {**personality_factors, **context_variables}
        
        # Format the template
        try:
            formatted_prompt = template.base_prompt.format(**all_variables)
        except KeyError as e:
            # Handle missing variables gracefully
            logger.warning(f"Missing variable in template: {e}")
            # Replace missing variables with placeholders
            formatted_prompt = template.base_prompt
            for key, value in all_variables.items():
                formatted_prompt = formatted_prompt.replace(f"{{{key}}}", str(value))
        
        return formatted_prompt.strip()
    
    def _calculate_personalization_confidence(
        self,
        personality_profile: PersonalityProfile,
        template: PromptTemplate
    ) -> float:
        """Calculate confidence score for personalization quality"""
        
        base_confidence = personality_profile.confidence_score
        
        # Boost confidence if we have strong personality data
        trait_coverage = len(personality_profile.traits) / 5.0  # 5 dimensions
        trait_coverage = min(1.0, trait_coverage)
        
        # Consider consistency score
        consistency_factor = personality_profile.consistency_score
        
        # Template-specific factors
        template_factor = 0.9  # Most templates are well-designed
        
        # Combined confidence
        confidence = (base_confidence * 0.4 + 
                     trait_coverage * 0.3 + 
                     consistency_factor * 0.2 + 
                     template_factor * 0.1)
        
        return min(1.0, confidence)
    
    def _generate_fallback_prompt(
        self, 
        request: PersonalizedPromptRequest, 
        generation_time: float
    ) -> PersonalizedPromptResponse:
        """Generate fallback prompt when personalization fails"""
        
        fallback_prompt = f"""You are an experienced coach helping someone with their request.

User's question: {request.user_query}
Context: {request.context}

Please provide helpful guidance and support in a professional, empathetic manner."""
        
        return PersonalizedPromptResponse(
            creator_id=request.creator_id,
            personalized_prompt=fallback_prompt,
            template_used="fallback",
            personality_factors={"fallback_mode": True},
            confidence_score=0.3,
            generation_time_ms=generation_time
        )
    
    # Helper methods for describing personality traits
    
    def _describe_communication_style(self, trait_value: str) -> str:
        """Convert communication style trait to descriptive text"""
        descriptions = {
            CommunicationStyle.DIRECT: "direct and straightforward, getting to the point quickly",
            CommunicationStyle.COLLABORATIVE: "collaborative and inclusive, building solutions together",
            CommunicationStyle.SUPPORTIVE: "supportive and nurturing, providing encouragement",
            CommunicationStyle.CHALLENGING: "challenging and pushing boundaries, asking tough questions"
        }
        return descriptions.get(trait_value, "authentic and genuine")
    
    def _describe_approach_type(self, trait_value: str) -> str:
        """Convert approach type trait to descriptive text"""
        descriptions = {
            ApproachType.STRUCTURED: "structured and systematic, following clear frameworks",
            ApproachType.FLEXIBLE: "flexible and adaptive, adjusting to what emerges",
            ApproachType.INTUITIVE: "intuitive and feeling-based, trusting inner wisdom",
            ApproachType.ANALYTICAL: "analytical and data-driven, examining evidence carefully"
        }
        return descriptions.get(trait_value, "thoughtful and considered")
    
    def _describe_interaction_mode(self, trait_value: str) -> str:
        """Convert interaction mode trait to descriptive text"""
        descriptions = {
            InteractionMode.FORMAL: "professional and focused on objectives",
            InteractionMode.CASUAL: "relaxed and conversational",
            InteractionMode.EMPATHETIC: "deeply understanding and emotionally aware",
            InteractionMode.RESULTS_FOCUSED: "results-oriented and action-focused"
        }
        return descriptions.get(trait_value, "professional and caring")
    
    def _describe_questioning_style(self, trait_value: str) -> str:
        """Convert questioning style trait to descriptive text"""
        descriptions = {
            QuestioningStyle.PROBING: "probing deeply to uncover insights",
            QuestioningStyle.EXPLORATORY: "exploratory and curious about possibilities",
            QuestioningStyle.CLARIFYING: "clarifying and ensuring understanding",
            QuestioningStyle.REFLECTIVE: "reflective and contemplative"
        }
        return descriptions.get(trait_value, "thoughtful and insightful")
    
    def _describe_feedback_delivery(self, trait_value: str) -> str:
        """Convert feedback delivery trait to descriptive text"""
        descriptions = {
            FeedbackDelivery.GENTLE: "gentle and considerate in delivery",
            FeedbackDelivery.DIRECT: "direct and honest in feedback",
            FeedbackDelivery.ENCOURAGING: "encouraging and uplifting",
            FeedbackDelivery.CONSTRUCTIVE: "constructive and growth-focused"
        }
        return descriptions.get(trait_value, "helpful and supportive")
    
    def _generate_experience_description(self, personality_profile: PersonalityProfile) -> str:
        """Generate experience description based on profile"""
        if personality_profile.key_methodologies:
            return f"experienced coach specializing in {', '.join(personality_profile.key_methodologies[:3])}"
        else:
            return "experienced and dedicated coach"
    
    def _generate_methodology_guidance(self, methodologies: List[str]) -> str:
        """Generate methodology-specific guidance"""
        if not methodologies:
            return "Use proven coaching techniques that feel authentic to you."
        
        method_guidance = {
            "GROW Model": "Consider using GROW (Goal, Reality, Options, Way forward) structure",
            "SMART Goals": "Help them create SMART (Specific, Measurable, Achievable, Relevant, Time-bound) objectives",
            "Solution Focused": "Focus on solutions rather than dwelling on problems",
            "Strengths Based": "Identify and leverage their natural strengths",
            "Mindfulness Based": "Incorporate mindfulness and present-moment awareness"
        }
        
        relevant_guidance = []
        for methodology in methodologies[:2]:  # Limit to top 2
            if methodology in method_guidance:
                relevant_guidance.append(method_guidance[methodology])
        
        return " ".join(relevant_guidance) if relevant_guidance else "Apply your preferred coaching methodologies."
    
    def _generate_specific_instructions(self, personality_profile: PersonalityProfile) -> str:
        """Generate specific instructions based on personality"""
        instructions = []
        
        # Add methodology-specific instructions
        if personality_profile.key_methodologies:
            instructions.append(f"Draw from your expertise in {', '.join(personality_profile.key_methodologies[:2])}.")
        
        # Add confidence-based instructions
        if personality_profile.confidence_score > 0.8:
            instructions.append("You can speak with authority based on your strong personality profile.")
        
        return " ".join(instructions)
    
    def _generate_supportive_guidance(self, personality_profile: PersonalityProfile) -> str:
        """Generate supportive guidance based on personality"""
        if personality_profile.personality_summary:
            return f"Remember your approach: {personality_profile.personality_summary}"
        return "Provide guidance that feels authentic to your coaching style."
    
    def _generate_emotional_support_guidance(self, personality_profile: PersonalityProfile) -> str:
        """Generate emotional support guidance"""
        if "empathetic" in str(personality_profile.personality_summary).lower():
            return "Use your natural empathy to connect deeply with their emotional state."
        return "Acknowledge their feelings while maintaining your supportive presence."
    
    def _generate_methodology_application(self, personality_profile: PersonalityProfile) -> str:
        """Generate methodology application guidance"""
        if personality_profile.key_methodologies:
            primary_method = personality_profile.key_methodologies[0]
            return f"Apply {primary_method} principles to guide them through this challenge."
        return "Use your preferred problem-solving methodology."


# Global prompt generator instance
_prompt_generator: Optional[DynamicPromptGenerator] = None


def get_prompt_generator() -> DynamicPromptGenerator:
    """Get global prompt generator instance"""
    global _prompt_generator
    if _prompt_generator is None:
        _prompt_generator = DynamicPromptGenerator()
    return _prompt_generator