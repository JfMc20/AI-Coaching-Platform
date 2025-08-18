"""
Personality Consistency Monitoring Engine
Validates AI responses against creator personality to ensure authentic digital twin behavior
"""

import asyncio
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4

from .personality_models import (
    PersonalityProfile, PersonalityTrait, PersonalityDimension,
    ConsistencyCheck, ConsistencyMonitoringRequest, ConsistencyMonitoringResponse,
    PersonalitySystemConfig, CommunicationStyle, ApproachType, InteractionMode,
    QuestioningStyle, FeedbackDelivery
)
from .ai_client import get_ai_client, ConversationResponse

logger = logging.getLogger(__name__)


class PersonalityConsistencyMonitor:
    """
    Monitors AI responses for consistency with creator personality profile
    """
    
    def __init__(self, config: Optional[PersonalitySystemConfig] = None):
        self.config = config or PersonalitySystemConfig()
        self.ai_client = get_ai_client()
        
        # Initialize consistency patterns
        self.consistency_patterns = self._initialize_consistency_patterns()
        
        logger.info("Personality Consistency Monitor initialized")
    
    def _initialize_consistency_patterns(self) -> Dict[str, Dict[str, List[str]]]:
        """Initialize patterns for detecting personality consistency in responses"""
        return {
            PersonalityDimension.COMMUNICATION_STYLE: {
                CommunicationStyle.DIRECT: [
                    r"\\b(clearly|directly|simply put|straightforward)\\b",
                    r"\\b(bottom line|let me be frank|here's the reality)\\b",
                    r"\\b(cut to the chase|no beating around the bush)\\b"
                ],
                CommunicationStyle.COLLABORATIVE: [
                    r"\\b(together|we can|let's explore|partnership)\\b",
                    r"\\b(what do you think|your thoughts|our approach)\\b",
                    r"\\b(collaborate|co-create|joint effort|team up)\\b"
                ],
                CommunicationStyle.SUPPORTIVE: [
                    r"\\b(support|encourage|believe in you|here for you)\\b",
                    r"\\b(you can do|trust yourself|have faith)\\b",
                    r"\\b(gentle|understanding|compassionate|patient)\\b"
                ],
                CommunicationStyle.CHALLENGING: [
                    r"\\b(challenge|push|stretch|uncomfortable truth)\\b",
                    r"\\b(what if|consider this|tough question)\\b",
                    r"\\b(step up|rise to|beyond your comfort zone)\\b"
                ]
            },
            PersonalityDimension.APPROACH_TYPE: {
                ApproachType.STRUCTURED: [
                    r"\\b(step-by-step|framework|systematic|process)\\b",
                    r"\\b(first|second|third|next step|in order)\\b",
                    r"\\b(structure|organize|plan|methodical)\\b"
                ],
                ApproachType.FLEXIBLE: [
                    r"\\b(adapt|adjust|flexible|see what emerges)\\b",
                    r"\\b(depends|varies|different approaches|alternatives)\\b",
                    r"\\b(organic|fluid|responsive|evolving)\\b"
                ],
                ApproachType.INTUITIVE: [
                    r"\\b(feel|sense|intuition|gut feeling)\\b",
                    r"\\b(trust your instincts|inner wisdom|natural)\\b",
                    r"\\b(what feels right|tune in|listen within)\\b"
                ],
                ApproachType.ANALYTICAL: [
                    r"\\b(analyze|examine|data|evidence|logical)\\b",
                    r"\\b(consider the facts|look at|evaluate|assess)\\b",
                    r"\\b(rational|systematic|breakdown|measure)\\b"
                ]
            },
            PersonalityDimension.QUESTIONING_STYLE: {
                QuestioningStyle.PROBING: [
                    r"\\b(tell me more|dig deeper|what else|elaborate)\\b",
                    r"\\b(help me understand|explain further|what's behind)\\b",
                    r"\\b(probe|investigate|uncover|discover more)\\b"
                ],
                QuestioningStyle.EXPLORATORY: [
                    r"\\b(what if|imagine|possibilities|explore)\\b",
                    r"\\b(wonder|curious|what might|alternatives)\\b",
                    r"\\b(adventure|journey|discover|experiment)\\b"
                ],
                QuestioningStyle.CLARIFYING: [
                    r"\\b(clarify|understand correctly|make sure|confirm)\\b",
                    r"\\b(what do you mean|can you explain|be specific)\\b",
                    r"\\b(clear|precise|exact|verify)\\b"
                ],
                QuestioningStyle.REFLECTIVE: [
                    r"\\b(reflect|think about|consider|contemplate)\\b",
                    r"\\b(look back|examine|review|ponder)\\b",
                    r"\\b(meaning|significance|learning|insight)\\b"
                ]
            },
            PersonalityDimension.FEEDBACK_DELIVERY: {
                FeedbackDelivery.GENTLE: [
                    r"\\b(gently|softly|kindly|with care)\\b",
                    r"\\b(might consider|perhaps|maybe|could try)\\b",
                    r"\\b(thoughtfully|carefully|tenderly)\\b"
                ],
                FeedbackDelivery.DIRECT: [
                    r"\\b(need to|must|should|have to|requires)\\b",
                    r"\\b(honestly|frankly|directly|clearly)\\b",
                    r"\\b(the reality is|fact is|truth is)\\b"
                ],
                FeedbackDelivery.ENCOURAGING: [
                    r"\\b(great job|well done|excellent|fantastic)\\b",
                    r"\\b(you can|believe|potential|strength)\\b",
                    r"\\b(encourage|motivate|inspire|uplift)\\b"
                ],
                FeedbackDelivery.CONSTRUCTIVE: [
                    r"\\b(improve|enhance|develop|grow|build)\\b",
                    r"\\b(opportunity|suggestion|consider|try)\\b",
                    r"\\b(constructive|helpful|useful|beneficial)\\b"
                ]
            }
        }
    
    async def monitor_response_consistency(
        self,
        request: ConsistencyMonitoringRequest,
        personality_profile: PersonalityProfile
    ) -> ConsistencyMonitoringResponse:
        """
        Monitor AI response for personality consistency
        
        Args:
            request: Consistency monitoring request
            personality_profile: Creator's personality profile
            
        Returns:
            ConsistencyMonitoringResponse with analysis results
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Monitoring consistency for creator {request.creator_id}")
            
            # Perform pattern-based consistency check
            pattern_scores = self._check_pattern_consistency(
                request.ai_response, personality_profile
            )
            
            # Perform AI-enhanced consistency analysis
            ai_analysis = await self._ai_analyze_consistency(
                request, personality_profile
            )
            
            # Calculate individual consistency scores
            personality_alignment = self._calculate_personality_alignment(
                pattern_scores, ai_analysis, personality_profile
            )
            
            tone_consistency = self._calculate_tone_consistency(
                request.ai_response, personality_profile
            )
            
            methodology_adherence = self._calculate_methodology_adherence(
                request.ai_response, personality_profile
            )
            
            # Identify deviations and positive indicators
            trait_deviations = self._identify_trait_deviations(
                pattern_scores, personality_profile
            )
            
            positive_indicators = self._identify_positive_indicators(
                pattern_scores, personality_profile
            )
            
            # Generate improvement suggestions
            improvement_suggestions = self._generate_improvement_suggestions(
                trait_deviations, personality_profile
            )
            
            # Create consistency check
            check_id = f"check_{uuid4().hex[:8]}"
            
            consistency_check = ConsistencyCheck(
                check_id=check_id,
                creator_id=request.creator_id,
                conversation_id=request.conversation_id,
                ai_response=request.ai_response,
                personality_alignment=personality_alignment,
                tone_consistency=tone_consistency,
                methodology_adherence=methodology_adherence,
                trait_deviations=trait_deviations,
                positive_indicators=positive_indicators,
                improvement_suggestions=improvement_suggestions
            )
            
            # Calculate overall consistency score
            overall_score = (
                personality_alignment * 0.4 + 
                tone_consistency * 0.3 + 
                methodology_adherence * 0.3
            )
            
            # Determine if response is consistent
            is_consistent = overall_score >= self.config.consistency_alert_threshold
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                consistency_check, overall_score, personality_profile
            )
            
            logger.info(
                f"Consistency check completed for creator {request.creator_id}: "
                f"score={overall_score:.2f}, consistent={is_consistent}"
            )
            
            return ConsistencyMonitoringResponse(
                check_id=check_id,
                creator_id=request.creator_id,
                consistency_result=consistency_check,
                overall_score=overall_score,
                is_consistent=is_consistent,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Consistency monitoring failed: {str(e)}")
            
            # Return fallback response
            return ConsistencyMonitoringResponse(
                check_id=f"error_{uuid4().hex[:8]}",
                creator_id=request.creator_id,
                consistency_result=ConsistencyCheck(
                    check_id=f"error_{uuid4().hex[:8]}",
                    creator_id=request.creator_id,
                    conversation_id=request.conversation_id,
                    ai_response=request.ai_response,
                    personality_alignment=0.5,
                    tone_consistency=0.5,
                    methodology_adherence=0.5,
                    trait_deviations=["Error in analysis"],
                    positive_indicators=[],
                    improvement_suggestions=["Analysis failed, manual review recommended"]
                ),
                overall_score=0.5,
                is_consistent=False,
                recommendations=["Manual review recommended due to analysis error"]
            )
    
    def _check_pattern_consistency(
        self,
        ai_response: str,
        personality_profile: PersonalityProfile
    ) -> Dict[str, float]:
        """Check consistency using pattern matching"""
        
        pattern_scores = {}
        
        # Get creator's dominant traits
        trait_by_dimension = {}
        for trait in personality_profile.traits:
            dimension = trait.dimension
            if dimension not in trait_by_dimension or trait.confidence_score > trait_by_dimension[dimension].confidence_score:
                trait_by_dimension[dimension] = trait
        
        # Check each dimension
        for dimension, expected_trait in trait_by_dimension.items():
            if dimension in self.consistency_patterns:
                dimension_patterns = self.consistency_patterns[dimension]
                
                # Count matches for expected trait
                expected_matches = 0
                if expected_trait.trait_value in dimension_patterns:
                    patterns = dimension_patterns[expected_trait.trait_value]
                    for pattern in patterns:
                        matches = re.finditer(pattern, ai_response, re.IGNORECASE)
                        expected_matches += len(list(matches))
                
                # Count matches for conflicting traits
                conflicting_matches = 0
                for trait_value, patterns in dimension_patterns.items():
                    if trait_value != expected_trait.trait_value:
                        for pattern in patterns:
                            matches = re.finditer(pattern, ai_response, re.IGNORECASE)
                            conflicting_matches += len(list(matches))
                
                # Calculate consistency score for this dimension
                total_matches = expected_matches + conflicting_matches
                if total_matches > 0:
                    consistency_score = expected_matches / total_matches
                else:
                    consistency_score = 0.7  # Neutral if no pattern matches
                
                pattern_scores[dimension] = consistency_score
        
        return pattern_scores
    
    async def _ai_analyze_consistency(
        self,
        request: ConsistencyMonitoringRequest,
        personality_profile: PersonalityProfile
    ) -> Dict[str, Any]:
        """Use AI to analyze personality consistency"""
        
        try:
            # Create personality analysis prompt
            personality_description = self._build_personality_description(personality_profile)
            
            analysis_prompt = f\"\"\"
            Analyze the following AI response for personality consistency:
            
            Expected personality: {personality_description}
            
            AI Response to analyze: {request.ai_response[:800]}...
            
            Original user query: {request.user_query or "Not provided"}
            
            Rate personality consistency on a scale of 0-1 for:
            1. Communication style alignment
            2. Approach consistency  
            3. Tone appropriateness
            4. Methodology usage
            
            Identify any personality mismatches and positive alignments.
            Format: [SCORE]:[CATEGORY]:[VALUE]:[EXPLANATION]
            \"\"\"
            
            # Get AI analysis
            ai_response = await self.ai_client.process_conversation_with_knowledge(
                message=analysis_prompt,
                creator_id="system",
                conversation_id=f"consistency_analysis_{uuid4().hex[:8]}"
            )
            
            # Parse AI response
            return self._parse_ai_consistency_response(ai_response.response)
            
        except Exception as e:
            logger.warning(f"AI consistency analysis failed: {str(e)}")
            return {"scores": {}, "insights": []}
    
    def _parse_ai_consistency_response(self, ai_response: str) -> Dict[str, Any]:
        """Parse AI consistency analysis response"""
        
        scores = {}
        insights = []
        
        # Look for score patterns
        score_pattern = r"\\[([0-9.]+):([^:]+):([^:]+):([^\\]]+)\\]"
        matches = re.finditer(score_pattern, ai_response)
        
        for match in matches:
            try:
                score = float(match.group(1))
                category = match.group(2).strip()
                value = match.group(3).strip()
                explanation = match.group(4).strip()
                
                scores[category] = score
                insights.append(f"{category}: {explanation}")
                
            except ValueError:
                continue
        
        return {"scores": scores, "insights": insights}
    
    def _calculate_personality_alignment(
        self,
        pattern_scores: Dict[str, float],
        ai_analysis: Dict[str, Any],
        personality_profile: PersonalityProfile
    ) -> float:
        """Calculate overall personality alignment score"""
        
        # Combine pattern-based and AI-based scores
        pattern_avg = sum(pattern_scores.values()) / len(pattern_scores) if pattern_scores else 0.7
        
        ai_scores = ai_analysis.get("scores", {})
        ai_avg = sum(ai_scores.values()) / len(ai_scores) if ai_scores else 0.7
        
        # Weight based on personality profile confidence
        profile_confidence = personality_profile.confidence_score
        
        # Combined score
        alignment = (pattern_avg * 0.6 + ai_avg * 0.4) * profile_confidence + (1 - profile_confidence) * 0.7
        
        return min(1.0, max(0.0, alignment))
    
    def _calculate_tone_consistency(
        self,
        ai_response: str,
        personality_profile: PersonalityProfile
    ) -> float:
        """Calculate tone consistency score"""
        
        # Simple tone analysis based on response characteristics
        response_lower = ai_response.lower()
        
        # Positive tone indicators
        positive_indicators = ["help", "support", "guide", "understand", "together", "can", "will"]
        positive_count = sum(1 for word in positive_indicators if word in response_lower)
        
        # Professional tone indicators
        professional_indicators = ["consider", "explore", "examine", "develop", "approach"]
        professional_count = sum(1 for word in professional_indicators if word in response_lower)
        
        # Calculate tone score based on response characteristics
        response_words = len(response_lower.split())
        tone_density = (positive_count + professional_count) / max(response_words, 1) * 100
        
        # Normalize to 0-1 scale
        tone_score = min(1.0, tone_density / 5.0 + 0.5)  # Base score of 0.5
        
        return tone_score
    
    def _calculate_methodology_adherence(
        self,
        ai_response: str,
        personality_profile: PersonalityProfile
    ) -> float:
        """Calculate methodology adherence score"""
        
        if not personality_profile.key_methodologies:
            return 0.8  # Neutral score if no methodologies defined
        
        response_lower = ai_response.lower()
        methodology_mentions = 0
        
        # Check for methodology-related terms
        methodology_patterns = {
            "GROW": ["goal", "reality", "options", "way forward", "grow"],
            "SMART": ["specific", "measurable", "achievable", "relevant", "time"],
            "Solution Focused": ["solution", "focus", "positive", "strengths"],
            "Strengths Based": ["strengths", "talents", "abilities", "potential"],
            "Mindfulness": ["mindful", "present", "awareness", "moment", "breathe"]
        }
        
        for methodology in personality_profile.key_methodologies:
            if methodology in methodology_patterns:
                patterns = methodology_patterns[methodology]
                for pattern in patterns:
                    if pattern in response_lower:
                        methodology_mentions += 1
                        break
        
        # Calculate adherence score
        expected_methodologies = len(personality_profile.key_methodologies)
        adherence_score = methodology_mentions / expected_methodologies if expected_methodologies > 0 else 0.8
        
        return min(1.0, adherence_score + 0.3)  # Base score boost
    
    def _identify_trait_deviations(
        self,
        pattern_scores: Dict[str, float],
        personality_profile: PersonalityProfile
    ) -> List[str]:
        """Identify personality trait deviations"""
        
        deviations = []
        
        for dimension, score in pattern_scores.items():
            if score < 0.5:  # Below threshold
                # Find the expected trait for this dimension
                expected_trait = None
                for trait in personality_profile.traits:
                    if trait.dimension == dimension:
                        expected_trait = trait
                        break
                
                if expected_trait:
                    deviations.append(
                        f"{dimension.replace('_', ' ').title()}: Expected {expected_trait.trait_value} "
                        f"but response shows different style (score: {score:.2f})"
                    )
        
        return deviations
    
    def _identify_positive_indicators(
        self,
        pattern_scores: Dict[str, float],
        personality_profile: PersonalityProfile
    ) -> List[str]:
        """Identify positive personality indicators"""
        
        positive_indicators = []
        
        for dimension, score in pattern_scores.items():
            if score > 0.8:  # Strong alignment
                # Find the trait for this dimension
                trait = None
                for t in personality_profile.traits:
                    if t.dimension == dimension:
                        trait = t
                        break
                
                if trait:
                    positive_indicators.append(
                        f"Strong {dimension.replace('_', ' ')} alignment: {trait.trait_value} "
                        f"(score: {score:.2f})"
                    )
        
        return positive_indicators
    
    def _generate_improvement_suggestions(
        self,
        trait_deviations: List[str],
        personality_profile: PersonalityProfile
    ) -> List[str]:
        """Generate suggestions for improving personality consistency"""
        
        suggestions = []
        
        if trait_deviations:
            suggestions.append("Review personality profile to ensure AI responses align with creator's authentic style")
            
            # Specific suggestions based on deviations
            for deviation in trait_deviations[:3]:  # Limit to top 3
                if "communication" in deviation.lower():
                    suggestions.append("Adjust communication style to match creator's natural approach")
                elif "approach" in deviation.lower():
                    suggestions.append("Modify problem-solving approach to align with creator's methodology")
                elif "questioning" in deviation.lower():
                    suggestions.append("Refine questioning technique to match creator's style")
                elif "feedback" in deviation.lower():
                    suggestions.append("Adjust feedback delivery to match creator's natural manner")
        
        if personality_profile.confidence_score < 0.7:
            suggestions.append("Consider additional personality analysis to strengthen profile accuracy")
        
        if not suggestions:
            suggestions.append("Personality consistency is good - continue current approach")
        
        return suggestions
    
    def _generate_recommendations(
        self,
        consistency_check: ConsistencyCheck,
        overall_score: float,
        personality_profile: PersonalityProfile
    ) -> List[str]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        if overall_score < 0.6:
            recommendations.append("⚠️ Low consistency detected - review AI response for personality alignment")
        elif overall_score < 0.8:
            recommendations.append("⚡ Moderate consistency - minor adjustments recommended")
        else:
            recommendations.append("✅ Good personality consistency maintained")
        
        # Add specific recommendations
        if consistency_check.personality_alignment < 0.6:
            recommendations.append("Focus on maintaining creator's communication style and approach")
        
        if consistency_check.tone_consistency < 0.6:
            recommendations.append("Adjust tone to better match creator's natural voice")
        
        if consistency_check.methodology_adherence < 0.6:
            recommendations.append("Incorporate more of creator's preferred methodologies")
        
        # Add suggestions from consistency check
        recommendations.extend(consistency_check.improvement_suggestions[:2])
        
        return recommendations
    
    def _build_personality_description(self, personality_profile: PersonalityProfile) -> str:
        """Build comprehensive personality description for AI analysis"""
        
        description_parts = []
        
        if personality_profile.personality_summary:
            description_parts.append(f"Summary: {personality_profile.personality_summary}")
        
        # Add trait descriptions
        for trait in personality_profile.traits:
            description_parts.append(f"{trait.dimension}: {trait.trait_value} (confidence: {trait.confidence_score:.2f})")
        
        # Add methodologies
        if personality_profile.key_methodologies:
            description_parts.append(f"Methodologies: {', '.join(personality_profile.key_methodologies)}")
        
        return "; ".join(description_parts)


# Global consistency monitor instance
_consistency_monitor: Optional[PersonalityConsistencyMonitor] = None


def get_consistency_monitor() -> PersonalityConsistencyMonitor:
    """Get global consistency monitor instance"""
    global _consistency_monitor
    if _consistency_monitor is None:
        _consistency_monitor = PersonalityConsistencyMonitor()
    return _consistency_monitor