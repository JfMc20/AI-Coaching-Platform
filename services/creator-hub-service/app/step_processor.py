"""
Visual Program Builder - Step Processor
Modular step processing system with Phase 1 & 2 integrations
"""

import asyncio
import logging
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Type
from abc import ABC, abstractmethod
from .program_engine import (
    StepHandler,
    TriggerHandler,
    ActionHandler,
    ExecutionContext,
    StepExecutionResult,
    DebugSession,
    StepDebugSession,
)
from .step_models import (
    ProgramStep,
    TriggerConfig,
    ActionConfig,
    ValidationConfig,
    StepType,
    TriggerType,
    ActionType,
    ChannelType,
)

# Import integrations with Phase 1 & 2
from .personality_models import PersonalizedPromptRequest
from .personality_engine import get_personality_engine
from .prompt_generator import get_prompt_generator
from .consistency_monitor import get_consistency_monitor
from .ai_client import get_ai_client
from .database import KnowledgeBaseService

logger = logging.getLogger(__name__)


# ==================== INTEGRATION MODULES ====================


class PersonalityIntegration:
    """Integration with Phase 2 personality system"""

    def __init__(self):
        self.personality_engine = get_personality_engine()
        self.prompt_generator = get_prompt_generator()
        self.consistency_monitor = get_consistency_monitor()

    async def enhance_step(
        self, step: ProgramStep, context: ExecutionContext, debug: StepDebugSession
    ) -> Dict[str, Any]:
        """Enhance step with personality integration"""

        try:
            debug.log_milestone("personality_enhancement_started")

            # Get creator's personality profile
            analysis_response = (
                await self.personality_engine.analyze_creator_personality(
                    creator_id=context.creator_id,
                    session=None,  # Would pass actual session in real implementation
                    force_reanalysis=False,
                )
            )

            if not analysis_response.personality_profile:
                debug.log_milestone(
                    "no_personality_profile", "Using default personality"
                )
                return {"personality_available": False}

            # Generate personalized prompt if content-based step
            enhanced_content = None
            if step.action_config.action_type in [
                ActionType.SEND_MESSAGE,
                ActionType.ASSIGN_TASK,
            ]:
                prompt_request = PersonalizedPromptRequest(
                    creator_id=context.creator_id,
                    context=f"Program step: {step.title}",
                    user_query=step.description or "Program step execution",
                    personality_emphasis=step.action_config.personality_overrides,
                )

                prompt_response = (
                    await self.prompt_generator.generate_personalized_prompt(
                        request=prompt_request,
                        personality_profile=analysis_response.personality_profile,
                        session=None,  # Would pass actual session
                    )
                )

                enhanced_content = prompt_response.personalized_prompt

            enhancement = {
                "personality_available": True,
                "personality_summary": analysis_response.personality_profile.personality_summary,
                "dominant_traits": [
                    {
                        "dimension": trait.dimension,
                        "value": trait.trait_value,
                        "confidence": trait.confidence_score,
                    }
                    for trait in analysis_response.personality_profile.traits[:3]
                ],
                "enhanced_content": enhanced_content,
                "personality_confidence": analysis_response.personality_profile.confidence_score,
            }

            debug.record_enhancement("personality", enhancement)
            debug.log_milestone(
                "personality_enhancement_completed",
                {
                    "traits_count": len(analysis_response.personality_profile.traits),
                    "content_enhanced": enhanced_content is not None,
                },
            )

            return enhancement

        except Exception as e:
            debug.log_error("personality_enhancement_failed", e)
            return {"personality_available": False, "error": str(e)}

    async def validate_response_consistency(
        self, response: str, context: ExecutionContext, debug: StepDebugSession
    ) -> Dict[str, Any]:
        """Validate response consistency with personality"""

        try:
            from .personality_models import ConsistencyMonitoringRequest

            monitoring_request = ConsistencyMonitoringRequest(
                creator_id=context.creator_id,
                ai_response=response,
                conversation_id=context.execution_id,
                user_query=f"Step execution for user {context.user_id}",
            )

            # Get personality profile for monitoring
            analysis_response = (
                await self.personality_engine.analyze_creator_personality(
                    creator_id=context.creator_id, session=None, force_reanalysis=False
                )
            )

            if analysis_response.personality_profile:
                monitoring_response = (
                    await self.consistency_monitor.monitor_response_consistency(
                        request=monitoring_request,
                        personality_profile=analysis_response.personality_profile,
                    )
                )

                return {
                    "consistency_check_performed": True,
                    "overall_score": monitoring_response.overall_score,
                    "is_consistent": monitoring_response.is_consistent,
                    "recommendations": monitoring_response.recommendations,
                }

            return {
                "consistency_check_performed": False,
                "reason": "No personality profile",
            }

        except Exception as e:
            debug.log_error("consistency_validation_failed", e)
            return {"consistency_check_performed": False, "error": str(e)}


class KnowledgeIntegration:
    """Integration with Phase 1 knowledge system"""

    def __init__(self):
        self.ai_client = get_ai_client()

    async def enhance_step(
        self, step: ProgramStep, context: ExecutionContext, debug: StepDebugSession
    ) -> Dict[str, Any]:
        """Enhance step with knowledge base integration"""

        try:
            debug.log_milestone("knowledge_enhancement_started")

            # Only enhance content-based steps
            if step.action_config.action_type not in [
                ActionType.SEND_MESSAGE,
                ActionType.ASSIGN_TASK,
            ]:
                return {
                    "knowledge_available": False,
                    "reason": "Not content-based step",
                }

            # Build knowledge query from step context
            knowledge_query = self._build_knowledge_query(step, context)

            # Get creator's knowledge context
            knowledge_context = (
                await KnowledgeBaseService.get_creator_knowledge_context(
                    creator_id=context.creator_id,
                    query=knowledge_query,
                    limit=5,
                    similarity_threshold=0.7,
                    session=None,  # Would pass actual session
                )
            )

            if not knowledge_context.get("knowledge_chunks"):
                debug.log_milestone("no_knowledge_found", knowledge_query)
                return {
                    "knowledge_available": False,
                    "reason": "No relevant knowledge found",
                }

            # Extract relevant knowledge snippets
            knowledge_snippets = []
            for chunk in knowledge_context["knowledge_chunks"][:3]:  # Top 3 chunks
                knowledge_snippets.append(
                    {
                        "content": chunk["content"][:200]
                        + "...",  # Limit snippet length
                        "source": chunk.get("document_title", "Unknown"),
                        "similarity": chunk["similarity"],
                    }
                )

            # Generate knowledge-enhanced content
            enhanced_content = await self._generate_knowledge_enhanced_content(
                step, knowledge_snippets, context, debug
            )

            enhancement = {
                "knowledge_available": True,
                "knowledge_snippets": knowledge_snippets,
                "enhanced_content": enhanced_content,
                "knowledge_sources_count": len(knowledge_context["knowledge_chunks"]),
            }

            debug.record_enhancement("knowledge", enhancement)
            debug.log_milestone(
                "knowledge_enhancement_completed",
                {
                    "snippets_count": len(knowledge_snippets),
                    "content_enhanced": enhanced_content is not None,
                },
            )

            return enhancement

        except Exception as e:
            debug.log_error("knowledge_enhancement_failed", e)
            return {"knowledge_available": False, "error": str(e)}

    def _build_knowledge_query(
        self, step: ProgramStep, context: ExecutionContext
    ) -> str:
        """Build knowledge query from step context"""
        query_parts = []

        if step.title:
            query_parts.append(step.title)

        if step.description:
            query_parts.append(step.description)

        # Add content tags
        if step.content_tags:
            query_parts.extend(step.content_tags)

        # Add dynamic content keywords
        if step.action_config.dynamic_content:
            # Extract keywords from dynamic content
            words = re.findall(r"\b\w+\b", step.action_config.dynamic_content)
            query_parts.extend(words[:5])  # First 5 words

        return " ".join(query_parts)

    async def _generate_knowledge_enhanced_content(
        self,
        step: ProgramStep,
        knowledge_snippets: List[Dict[str, Any]],
        context: ExecutionContext,
        debug: StepDebugSession,
    ) -> Optional[str]:
        """Generate content enhanced with knowledge"""

        try:
            # Create enhancement prompt
            base_content = (
                step.action_config.dynamic_content or step.description or step.title
            )

            knowledge_text = "\n".join(
                [
                    f"- {snippet['content']} (from {snippet['source']})"
                    for snippet in knowledge_snippets
                ]
            )

            enhancement_prompt = f"""
            Enhance this coaching step content with relevant knowledge:
            
            Original content: {base_content}
            
            Relevant knowledge:
            {knowledge_text}
            
            Create an enhanced version that incorporates the relevant knowledge naturally.
            Keep the same tone and intent but add valuable insights from the knowledge base.
            """

            # Use AI client to enhance content
            response = await self.ai_client.process_conversation_with_knowledge(
                message=enhancement_prompt,
                creator_id="system",
                conversation_id=f"knowledge_enhancement_{context.execution_id}",
            )

            return response.response

        except Exception as e:
            debug.log_error("knowledge_content_generation_failed", e)
            return None


class AIEnhancement:
    """AI-powered step enhancement"""

    def __init__(self):
        self.ai_client = get_ai_client()

    async def enhance_step(
        self,
        step: ProgramStep,
        context: ExecutionContext,
        existing_enhancements: Dict[str, Any],
        debug: StepDebugSession,
    ) -> Dict[str, Any]:
        """Apply AI enhancements based on existing integrations"""

        try:
            debug.log_milestone("ai_enhancement_started")

            # Combine all available enhancements
            personality_data = existing_enhancements.get("personality", {})
            knowledge_data = existing_enhancements.get("knowledge", {})

            if not personality_data.get(
                "personality_available"
            ) and not knowledge_data.get("knowledge_available"):
                return {
                    "ai_enhancement_applied": False,
                    "reason": "No base enhancements available",
                }

            # Create comprehensive enhancement prompt
            enhancement_prompt = self._create_enhancement_prompt(
                step, context, personality_data, knowledge_data
            )

            # Get AI enhancement
            response = await self.ai_client.process_conversation_with_knowledge(
                message=enhancement_prompt,
                creator_id=context.creator_id,
                conversation_id=f"ai_enhancement_{context.execution_id}",
            )

            # Parse AI response for actionable enhancements
            ai_enhancement = self._parse_ai_enhancement(response.response)

            enhancement = {
                "ai_enhancement_applied": True,
                "enhanced_content": ai_enhancement.get("content"),
                "suggested_improvements": ai_enhancement.get("improvements", []),
                "user_engagement_tips": ai_enhancement.get("engagement_tips", []),
                "personalization_level": ai_enhancement.get(
                    "personalization_score", 0.5
                ),
            }

            debug.record_enhancement("ai", enhancement)
            debug.log_milestone(
                "ai_enhancement_completed",
                {
                    "content_enhanced": bool(ai_enhancement.get("content")),
                    "improvements_count": len(ai_enhancement.get("improvements", [])),
                },
            )

            return enhancement

        except Exception as e:
            debug.log_error("ai_enhancement_failed", e)
            return {"ai_enhancement_applied": False, "error": str(e)}

    def _create_enhancement_prompt(
        self,
        step: ProgramStep,
        context: ExecutionContext,
        personality_data: Dict[str, Any],
        knowledge_data: Dict[str, Any],
    ) -> str:
        """Create comprehensive enhancement prompt"""

        prompt_parts = [
            "Enhance this coaching step for maximum effectiveness:",
            "",  # Empty line for visual separation
            f"Step: {step.title}",
            f"Description: {step.description or 'No description'}",
            f"Type: {step.step_type}",
            f"Target: User {context.user_id}",
            "",  # Empty line for visual separation
        ]

        # Add personality context
        if personality_data.get("personality_available"):
            prompt_parts.extend(
                [
                    "Creator Personality:",
                    f"- Summary: {personality_data.get('personality_summary', 'N/A')}",
                    f"- Key traits: {', '.join([t['dimension'] + ':' + t['value'] for t in personality_data.get('dominant_traits', [])])}",
                    "",
                ]
            )

        # Add knowledge context
        if knowledge_data.get("knowledge_available"):
            prompt_parts.extend(
                [
                    "Available Knowledge:",
                    f"- {len(knowledge_data.get('knowledge_snippets', []))} relevant knowledge chunks available",
                    f"- Sources: {', '.join([s['source'] for s in knowledge_data.get('knowledge_snippets', [])])}",
                    "",
                ]
            )

        prompt_parts.extend(
            [
                "Please provide:",
                "1. Enhanced content that combines personality + knowledge",
                "2. Specific improvements for user engagement",
                "3. Tips for maximizing step effectiveness",
                "4. Personalization score (0-1)",
                "",
                "Format as JSON with keys: content, improvements, engagement_tips, personalization_score",
            ]
        )

        return "\n".join(prompt_parts)

    def _parse_ai_enhancement(self, ai_response: str) -> Dict[str, Any]:
        """Parse AI enhancement response with robust JSON extraction"""

        def create_fallback_response(content: str, error_context: str = None) -> Dict[str, Any]:
            """Create consistent fallback response with full content preserved"""
            return {
                "content": content,  # Preserve full content, no truncation
                "improvements": [],
                "engagement_tips": [],
                "personalization_score": 0.5,
                "parsing_error": error_context,  # Include error context for debugging
            }

        try:
            # Method 1: Try non-greedy regex pattern to find JSON objects
            json_matches = re.finditer(r'\{.*?\}', ai_response, re.DOTALL)
            
            for match in json_matches:
                try:
                    json_candidate = match.group()
                    parsed_json = json.loads(json_candidate)
                    
                    # Validate that it has the expected structure
                    if isinstance(parsed_json, dict):
                        # Ensure all expected keys exist with defaults
                        result = {
                            "content": parsed_json.get("content", ai_response),
                            "improvements": parsed_json.get("improvements", []),
                            "engagement_tips": parsed_json.get("engagement_tips", []),
                            "personalization_score": parsed_json.get("personalization_score", 0.5),
                        }
                        
                        # Validate data types
                        if (isinstance(result["improvements"], list) and 
                            isinstance(result["engagement_tips"], list) and
                            isinstance(result["personalization_score"], (int, float))):
                            
                            logger.debug(f"Successfully parsed JSON from AI response using non-greedy regex")
                            return result
                            
                except json.JSONDecodeError as e:
                    logger.debug(f"Failed to parse JSON candidate with non-greedy regex: {e}")
                    continue
                except Exception as e:
                    logger.debug(f"Unexpected error parsing JSON candidate: {e}")
                    continue

            # Method 2: Try streaming/decoder approach for more complex JSON
            try:
                decoder = json.JSONDecoder()
                idx = 0
                
                while idx < len(ai_response):
                    # Find potential start of JSON object
                    start_idx = ai_response.find('{', idx)
                    if start_idx == -1:
                        break
                    
                    try:
                        # Attempt to decode JSON starting from this position
                        parsed_json, end_idx = decoder.raw_decode(ai_response, start_idx)
                        
                        if isinstance(parsed_json, dict):
                            # Ensure all expected keys exist with defaults
                            result = {
                                "content": parsed_json.get("content", ai_response),
                                "improvements": parsed_json.get("improvements", []),
                                "engagement_tips": parsed_json.get("engagement_tips", []),
                                "personalization_score": parsed_json.get("personalization_score", 0.5),
                            }
                            
                            # Validate data types
                            if (isinstance(result["improvements"], list) and 
                                isinstance(result["engagement_tips"], list) and
                                isinstance(result["personalization_score"], (int, float))):
                                
                                logger.debug(f"Successfully parsed JSON from AI response using JSONDecoder")
                                return result
                                
                    except json.JSONDecodeError:
                        # Move to next potential JSON start
                        idx = start_idx + 1
                        continue
                    except Exception as e:
                        logger.debug(f"Unexpected error in JSONDecoder approach: {e}")
                        idx = start_idx + 1
                        continue
                        
            except Exception as e:
                logger.warning(f"JSONDecoder approach failed: {e}")

            # Method 3: Try greedy pattern as last resort (original approach)
            try:
                json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                if json_match:
                    parsed_json = json.loads(json_match.group())
                    
                    if isinstance(parsed_json, dict):
                        result = {
                            "content": parsed_json.get("content", ai_response),
                            "improvements": parsed_json.get("improvements", []),
                            "engagement_tips": parsed_json.get("engagement_tips", []),
                            "personalization_score": parsed_json.get("personalization_score", 0.5),
                        }
                        
                        logger.debug(f"Successfully parsed JSON from AI response using greedy regex")
                        return result
                        
            except json.JSONDecodeError as e:
                logger.warning(f"Greedy regex JSON parsing failed: {e}")
            except Exception as e:
                logger.warning(f"Unexpected error in greedy regex approach: {e}")

            # No valid JSON found - return fallback with full content
            logger.info("No valid JSON found in AI response, using fallback with full content")
            return create_fallback_response(ai_response, "No valid JSON structure found")

        except Exception as e:
            # Log the exception with full context
            logger.error(f"Critical error in _parse_ai_enhancement: {e}", exc_info=True)
            logger.error(f"AI response length: {len(ai_response)}")
            logger.error(f"AI response preview: {ai_response[:200]}...")
            
            # Return fallback with full content and error context
            return create_fallback_response(
                ai_response, 
                f"Critical parsing error: {str(e)}"
            )


# ==================== ENHANCED STEP MODELS ====================


class EnhancedProgramStep:
    """Step enhanced with all integrations"""

    def __init__(
        self,
        base_step: ProgramStep,
        enhancements: Dict[str, Any],
        enhancement_metadata: Dict[str, Any],
    ):
        self.base_step = base_step
        self.enhancements = enhancements
        self.enhancement_metadata = enhancement_metadata

    def get_enhanced_content(self) -> str:
        """Get the best enhanced content available"""

        # Priority order: AI > Personality > Knowledge > Base
        if self.enhancements.get("ai", {}).get("enhanced_content"):
            return self.enhancements["ai"]["enhanced_content"]

        if self.enhancements.get("personality", {}).get("enhanced_content"):
            return self.enhancements["personality"]["enhanced_content"]

        if self.enhancements.get("knowledge", {}).get("enhanced_content"):
            return self.enhancements["knowledge"]["enhanced_content"]

        # Fallback to base content
        return (
            self.base_step.action_config.dynamic_content
            or self.base_step.description
            or self.base_step.title
        )

    def get_personalization_score(self) -> float:
        """Get overall personalization score"""
        scores = []

        if self.enhancements.get("personality", {}).get("personality_confidence"):
            scores.append(self.enhancements["personality"]["personality_confidence"])

        if self.enhancements.get("ai", {}).get("personalization_level"):
            scores.append(self.enhancements["ai"]["personalization_level"])

        return sum(scores) / len(scores) if scores else 0.5

    def get_quality_indicators(self) -> Dict[str, Any]:
        """Get quality indicators for this enhanced step"""
        return {
            "personality_enhanced": bool(
                self.enhancements.get("personality", {}).get("personality_available")
            ),
            "knowledge_enhanced": bool(
                self.enhancements.get("knowledge", {}).get("knowledge_available")
            ),
            "ai_enhanced": bool(
                self.enhancements.get("ai", {}).get("ai_enhancement_applied")
            ),
            "personalization_score": self.get_personalization_score(),
            "enhancement_count": len(self.enhancements),
            "content_sources": list(self.enhancements.keys()),
        }


# ==================== CORE STEP PROCESSOR ====================


class StepProcessor:
    """Core modular step processor with full integration support"""

    def __init__(self):
        # Integration modules
        self.personality_integration = PersonalityIntegration()
        self.knowledge_integration = KnowledgeIntegration()
        self.ai_enhancement = AIEnhancement()

        # Handler registry
        self.step_handlers: Dict[StepType, StepHandler] = {}

        # Initialize default handlers
        self._initialize_default_handlers()

        logger.info("Step Processor initialized with full integrations")

    def _initialize_default_handlers(self):
        """Initialize default step handlers"""
        self.step_handlers[StepType.MESSAGE] = MessageStepHandler()
        self.step_handlers[StepType.TASK] = TaskStepHandler()
        self.step_handlers[StepType.EVALUATION] = EvaluationStepHandler()
        self.step_handlers[StepType.CHECKPOINT] = CheckpointStepHandler()
        self.step_handlers[StepType.CONDITIONAL] = ConditionalStepHandler()
        self.step_handlers[StepType.DELAY] = DelayStepHandler()

        logger.info(f"Initialized {len(self.step_handlers)} default step handlers")

    def register_step_handler(self, step_type: StepType, handler: StepHandler):
        """Register custom step handler"""
        self.step_handlers[step_type] = handler
        logger.info(
            f"Registered custom handler for {step_type}: {handler.__class__.__name__}"
        )

    async def process_step(
        self, step: ProgramStep, context: ExecutionContext, debug_session: DebugSession
    ) -> StepExecutionResult:
        """Main step processing with full integration support"""

        step_debug = debug_session.create_step_debug(step.step_id)
        start_time = datetime.utcnow()

        try:
            step_debug.log_milestone(
                "step_processing_started",
                {"step_type": step.step_type, "step_title": step.title},
            )

            # Step 1: Enhance step with all integrations
            enhanced_step = await self._enhance_step_with_integrations(
                step, context, step_debug
            )

            # Step 2: Select and validate handler
            handler = self.step_handlers.get(step.step_type)
            if not handler:
                raise ValueError(
                    f"No handler registered for step type: {step.step_type}"
                )

            step_debug.log_milestone(
                "handler_selected",
                {
                    "handler_class": handler.__class__.__name__,
                    "can_handle": await handler.can_handle(step),
                },
            )

            # Step 3: Execute step with handler
            execution_result = await handler.execute(
                enhanced_step.base_step, context, step_debug
            )

            # Step 4: Enhance result with integration data
            enhanced_result = await self._enhance_execution_result(
                execution_result, enhanced_step, context, step_debug
            )

            # Step 5: Validate consistency if applicable
            if enhanced_result.success and enhanced_result.result_data.get(
                "response_content"
            ):
                consistency_data = (
                    await self.personality_integration.validate_response_consistency(
                        enhanced_result.result_data["response_content"],
                        context,
                        step_debug,
                    )
                )
                enhanced_result.result_data["consistency_validation"] = consistency_data

            # Step 6: Update timing and metrics
            enhanced_result.started_at = start_time
            enhanced_result.completed_at = datetime.utcnow()
            enhanced_result.execution_time_seconds = (
                enhanced_result.completed_at - start_time
            ).total_seconds()

            # Step 7: Calculate quality scores
            quality_scores = self._calculate_quality_scores(
                enhanced_step, enhanced_result
            )
            enhanced_result.personality_consistency = quality_scores.get(
                "personality_consistency", 0.0
            )
            enhanced_result.engagement_score = quality_scores.get(
                "engagement_score", 0.0
            )
            enhanced_result.success_score = quality_scores.get("success_score", 0.0)

            step_debug.log_success(
                "step_processing_completed",
                {
                    "success": enhanced_result.success,
                    "quality_scores": quality_scores,
                    "integration_count": len(enhanced_step.enhancements),
                },
            )

            return enhanced_result

        except Exception as e:
            step_debug.log_error("step_processing_failed", e)

            # Attempt recovery
            recovery_result = await self._attempt_step_recovery(
                step, context, e, step_debug
            )

            return recovery_result

    async def _enhance_step_with_integrations(
        self, step: ProgramStep, context: ExecutionContext, debug: StepDebugSession
    ) -> EnhancedProgramStep:
        """Apply all integrations to enhance the step"""

        enhancements = {}

        # Phase 2: Personality Integration
        if context.personality_enabled:
            personality_enhancement = await self.personality_integration.enhance_step(
                step, context, debug
            )
            enhancements["personality"] = personality_enhancement

        # Phase 1: Knowledge Integration
        if context.knowledge_enabled:
            knowledge_enhancement = await self.knowledge_integration.enhance_step(
                step, context, debug
            )
            enhancements["knowledge"] = knowledge_enhancement

        # AI Enhancement (combines all)
        if context.ai_enhancement_enabled and enhancements:
            ai_enhancement = await self.ai_enhancement.enhance_step(
                step, context, enhancements, debug
            )
            enhancements["ai"] = ai_enhancement

        return EnhancedProgramStep(
            base_step=step,
            enhancements=enhancements,
            enhancement_metadata=debug.get_enhancement_metadata(),
        )

    async def _enhance_execution_result(
        self,
        result: StepExecutionResult,
        enhanced_step: EnhancedProgramStep,
        context: ExecutionContext,
        debug: StepDebugSession,
    ) -> StepExecutionResult:
        """Enhance execution result with integration data"""

        # Add enhancement metadata to result
        result.result_data["enhancements_applied"] = enhanced_step.enhancement_metadata
        result.result_data["quality_indicators"] = (
            enhanced_step.get_quality_indicators()
        )
        result.result_data["personalization_score"] = (
            enhanced_step.get_personalization_score()
        )

        # Add enhanced content to result
        if enhanced_step.get_enhanced_content():
            result.result_data["enhanced_content"] = (
                enhanced_step.get_enhanced_content()
            )

        # Add improvement suggestions
        improvements = []
        for enhancement_type, enhancement_data in enhanced_step.enhancements.items():
            if (
                isinstance(enhancement_data, dict)
                and "suggested_improvements" in enhancement_data
            ):
                improvements.extend(enhancement_data["suggested_improvements"])

        if improvements:
            result.result_data["improvement_suggestions"] = improvements

        return result

    def _calculate_quality_scores(
        self, enhanced_step: EnhancedProgramStep, result: StepExecutionResult
    ) -> Dict[str, float]:
        """Calculate comprehensive quality scores"""

        scores = {}

        # Personality consistency score
        personality_data = enhanced_step.enhancements.get("personality", {})
        if personality_data.get("personality_available"):
            scores["personality_consistency"] = personality_data.get(
                "personality_confidence", 0.5
            )
        else:
            scores["personality_consistency"] = 0.5  # Neutral if no personality

        # Engagement score (based on enhancement quality)
        enhancement_count = len(enhanced_step.enhancements)
        enhancement_quality = enhanced_step.get_personalization_score()
        scores["engagement_score"] = min(
            1.0, (enhancement_count * 0.3) + (enhancement_quality * 0.7)
        )

        # Success score (based on execution success and enhancements)
        base_success = 1.0 if result.success else 0.0
        enhancement_bonus = enhancement_quality * 0.2
        scores["success_score"] = min(1.0, base_success + enhancement_bonus)

        return scores

    async def _attempt_step_recovery(
        self,
        step: ProgramStep,
        context: ExecutionContext,
        error: Exception,
        debug: StepDebugSession,
    ) -> StepExecutionResult:
        """Attempt to recover from step execution failure"""

        debug.log_milestone("recovery_attempt_started", str(error))

        try:
            # Simple recovery: create minimal successful result
            recovery_result = StepExecutionResult(
                step_id=step.step_id,
                execution_id=context.execution_id,
                status="recovered",
                started_at=datetime.utcnow(),
                success=True,  # Mark as success to continue flow
                result_data={
                    "recovery_mode": True,
                    "original_error": str(error),
                    "recovery_content": f"Step {step.title} was automatically recovered.",
                },
                success_score=0.3,  # Low score for recovery
                error_message=f"Recovered from: {str(error)}",
            )

            debug.log_milestone("recovery_successful", recovery_result)
            return recovery_result

        except Exception as recovery_error:
            debug.log_error("recovery_failed", recovery_error)

            # Final fallback: failed result
            return StepExecutionResult(
                step_id=step.step_id,
                execution_id=context.execution_id,
                status="failed",
                started_at=datetime.utcnow(),
                success=False,
                error_message=f"Step failed: {str(error)}. Recovery failed: {str(recovery_error)}",
            )


# ==================== DEFAULT STEP HANDLERS ====================


class MessageStepHandler(StepHandler):
    """Handler for message steps"""

    async def can_handle(self, step: ProgramStep) -> bool:
        return step.step_type == StepType.MESSAGE

    async def execute(
        self,
        step: ProgramStep,
        context: ExecutionContext,
        debug_session: StepDebugSession,
    ) -> StepExecutionResult:
        debug_session.log_milestone("message_step_execution_started")

        # Simulate message sending
        message_content = (
            step.action_config.dynamic_content
            or step.description
            or f"Message from step: {step.title}"
        )

        # Simulate channel delivery
        preferred_channel = (
            step.action_config.preferred_channels[0]
            if step.action_config.preferred_channels
            else ChannelType.WEB_WIDGET
        )

        debug_session.log_milestone(
            "message_sent",
            {"channel": preferred_channel, "content_length": len(message_content)},
        )

        return StepExecutionResult(
            step_id=step.step_id,
            execution_id=context.execution_id,
            status="completed",
            started_at=datetime.utcnow(),
            success=True,
            result_data={
                "action_type": "message_sent",
                "channel": preferred_channel,
                "response_content": message_content,
                "message_id": f"msg_{context.execution_id}_{step.step_id}",
            },
            success_score=0.9,
            engagement_score=0.8,
        )

    async def validate(self, step: ProgramStep) -> List[str]:
        issues = []
        if not step.action_config.dynamic_content and not step.description:
            issues.append("Message step requires content or description")
        return issues


class TaskStepHandler(StepHandler):
    """Handler for task assignment steps"""

    async def can_handle(self, step: ProgramStep) -> bool:
        return step.step_type == StepType.TASK

    async def execute(
        self,
        step: ProgramStep,
        context: ExecutionContext,
        debug_session: StepDebugSession,
    ) -> StepExecutionResult:
        debug_session.log_milestone("task_step_execution_started")

        task_instructions = (
            step.action_config.task_instructions
            or step.description
            or f"Complete task: {step.title}"
        )

        # Simulate task assignment
        task_id = f"task_{context.execution_id}_{step.step_id}"

        debug_session.log_milestone(
            "task_assigned",
            {"task_id": task_id, "instructions_length": len(task_instructions)},
        )

        return StepExecutionResult(
            step_id=step.step_id,
            execution_id=context.execution_id,
            status="completed",
            started_at=datetime.utcnow(),
            success=True,
            result_data={
                "action_type": "task_assigned",
                "task_id": task_id,
                "task_instructions": task_instructions,
                "due_date": None,  # Could be calculated from step config
                "response_content": f"Task assigned: {step.title}",
            },
            success_score=0.85,
            engagement_score=0.9,
        )

    async def validate(self, step: ProgramStep) -> List[str]:
        issues = []
        if not step.action_config.task_instructions and not step.description:
            issues.append("Task step requires instructions or description")
        return issues


class EvaluationStepHandler(StepHandler):
    """Handler for evaluation steps"""

    async def can_handle(self, step: ProgramStep) -> bool:
        return step.step_type == StepType.EVALUATION

    async def execute(
        self,
        step: ProgramStep,
        context: ExecutionContext,
        debug_session: StepDebugSession,
    ) -> StepExecutionResult:
        debug_session.log_milestone("evaluation_step_execution_started")

        evaluation_content = step.description or f"Evaluation: {step.title}"
        evaluation_type = step.action_config.evaluation_type or "assessment"

        # Simulate evaluation creation
        evaluation_id = f"eval_{context.execution_id}_{step.step_id}"

        debug_session.log_milestone(
            "evaluation_created",
            {"evaluation_id": evaluation_id, "type": evaluation_type},
        )

        return StepExecutionResult(
            step_id=step.step_id,
            execution_id=context.execution_id,
            status="completed",
            started_at=datetime.utcnow(),
            success=True,
            result_data={
                "action_type": "evaluation_created",
                "evaluation_id": evaluation_id,
                "evaluation_type": evaluation_type,
                "criteria": step.action_config.evaluation_criteria,
                "response_content": f"Evaluation created: {step.title}",
            },
            success_score=0.8,
            engagement_score=0.7,
        )

    async def validate(self, step: ProgramStep) -> List[str]:
        return []  # Basic validation


class CheckpointStepHandler(StepHandler):
    """Handler for checkpoint steps"""

    async def can_handle(self, step: ProgramStep) -> bool:
        return step.step_type == StepType.CHECKPOINT

    async def execute(
        self,
        step: ProgramStep,
        context: ExecutionContext,
        debug_session: StepDebugSession,
    ) -> StepExecutionResult:
        debug_session.log_milestone("checkpoint_step_execution_started")

        # Calculate progress based on completed steps
        total_steps = (
            len(context.completed_steps)
            + len(context.active_steps)
            + len(context.failed_steps)
        )
        progress_percentage = (len(context.completed_steps) / max(total_steps, 1)) * 100

        checkpoint_message = (
            f"Checkpoint reached: {step.title}. Progress: {progress_percentage:.1f}%"
        )

        debug_session.log_milestone(
            "checkpoint_reached",
            {
                "progress_percentage": progress_percentage,
                "completed_steps": len(context.completed_steps),
            },
        )

        return StepExecutionResult(
            step_id=step.step_id,
            execution_id=context.execution_id,
            status="completed",
            started_at=datetime.utcnow(),
            success=True,
            result_data={
                "action_type": "checkpoint_reached",
                "progress_percentage": progress_percentage,
                "completed_steps_count": len(context.completed_steps),
                "milestone_achieved": step.is_milestone,
                "response_content": checkpoint_message,
            },
            success_score=1.0,
            engagement_score=0.6,
        )

    async def validate(self, step: ProgramStep) -> List[str]:
        return []


class ConditionalStepHandler(StepHandler):
    """Handler for conditional logic steps"""

    async def can_handle(self, step: ProgramStep) -> bool:
        return step.step_type == StepType.CONDITIONAL

    async def execute(
        self,
        step: ProgramStep,
        context: ExecutionContext,
        debug_session: StepDebugSession,
    ) -> StepExecutionResult:
        debug_session.log_milestone("conditional_step_execution_started")

        # Validate conditional_config exists and has required properties
        if not step.conditional_config:
            raise ValueError(
                "Conditional step requires conditional_config but it is None or missing"
            )

        if (
            not hasattr(step.conditional_config, "condition_expression")
            or not step.conditional_config.condition_expression
        ):
            raise ValueError(
                "Conditional step requires condition_expression in conditional_config"
            )

        # Simple condition evaluation (placeholder)
        # In real implementation, this would use a proper condition evaluator
        condition_expression = getattr(
            step.conditional_config, "condition_expression", ""
        )
        condition_result = self._evaluate_simple_condition(
            condition_expression, context
        )

        # Determine next steps based on condition with safe attribute access
        if condition_result:
            next_steps = getattr(step.conditional_config, "true_path_step_ids", [])
            path_taken = "true_path"
        else:
            next_steps = getattr(step.conditional_config, "false_path_step_ids", [])
            path_taken = "false_path"

        debug_session.log_milestone(
            "condition_evaluated",
            {
                "condition": getattr(
                    step.conditional_config, "condition_expression", "unknown"
                ),
                "result": condition_result,
                "path_taken": path_taken,
                "next_steps": next_steps,
            },
        )

        return StepExecutionResult(
            step_id=step.step_id,
            execution_id=context.execution_id,
            status="completed",
            started_at=datetime.utcnow(),
            success=True,
            result_data={
                "action_type": "condition_evaluated",
                "condition_expression": getattr(
                    step.conditional_config, "condition_expression", "unknown"
                ),
                "condition_result": condition_result,
                "path_taken": path_taken,
                "response_content": f"Condition evaluated: {path_taken}",
            },
            next_step_recommendations=next_steps,
            conditional_outcomes={
                "condition_result": condition_result,
                "path": path_taken,
            },
            success_score=1.0,
            engagement_score=0.5,
        )

    def _evaluate_simple_condition(
        self, expression: str, context: ExecutionContext
    ) -> bool:
        """Simple condition evaluation (placeholder)"""
        # This is a placeholder implementation
        # Real implementation would use a proper expression evaluator

        # Simple keyword-based evaluation
        if "completed_steps" in expression:
            return len(context.completed_steps) > 0
        elif "failed_steps" in expression:
            return len(context.failed_steps) > 0
        else:
            # Default to True for now
            return True

    async def validate(self, step: ProgramStep) -> List[str]:
        issues = []
        if not step.conditional_config:
            issues.append("Conditional step requires conditional_config")
        elif not hasattr(
            step.conditional_config, "condition_expression"
        ) or not getattr(step.conditional_config, "condition_expression", None):
            issues.append("Conditional step requires condition_expression")
        return issues


class DelayStepHandler(StepHandler):
    """Handler for delay steps"""

    async def can_handle(self, step: ProgramStep) -> bool:
        return step.step_type == StepType.DELAY

    async def execute(
        self,
        step: ProgramStep,
        context: ExecutionContext,
        debug_session: StepDebugSession,
    ) -> StepExecutionResult:
        debug_session.log_milestone("delay_step_execution_started")

        # Validate that trigger_config exists
        if not step.trigger_config:
            raise ValueError(
                "Delay step requires trigger_config but it is None or missing"
            )

        # Use default value if delay_seconds is not defined
        delay_seconds = (
            getattr(step.trigger_config, "delay_seconds", None) or 60
        )  # Default 1 minute

        # In real implementation, this would schedule future execution
        # For now, we'll simulate immediate completion
        debug_session.log_milestone(
            "delay_scheduled",
            {
                "delay_seconds": delay_seconds,
                "scheduled_for": datetime.utcnow().isoformat(),
            },
        )

        return StepExecutionResult(
            step_id=step.step_id,
            execution_id=context.execution_id,
            status="completed",
            started_at=datetime.utcnow(),
            success=True,
            result_data={
                "action_type": "delay_applied",
                "delay_seconds": delay_seconds,
                "delay_scheduled": True,
                "response_content": f"Delay of {delay_seconds} seconds applied",
            },
            success_score=1.0,
            engagement_score=0.3,
        )

    async def validate(self, step: ProgramStep) -> List[str]:
        issues = []

        # First check if trigger_config exists
        if not step.trigger_config:
            issues.append(
                "Delay step requires trigger_config but it is None or missing"
            )
            return issues

        # Then safely access delay_seconds property
        delay_seconds = getattr(step.trigger_config, "delay_seconds", None)
        if delay_seconds is not None and delay_seconds <= 0:
            issues.append("Delay step requires positive delay_seconds")

        return issues


# ==================== GLOBAL STEP PROCESSOR INSTANCE ====================

_step_processor: Optional[StepProcessor] = None


def get_step_processor() -> StepProcessor:
    """Get global step processor instance"""
    global _step_processor
    if _step_processor is None:
        _step_processor = StepProcessor()
    return _step_processor
