"""
Creator Personality Analysis Engine
Core engine for analyzing creator personality from documents and generating digital twin characteristics
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4

from .personality_models import (
    PersonalityProfile, PersonalityTrait, PersonalityEvidence,
    PersonalityDimension, CommunicationStyle, ApproachType, InteractionMode,
    QuestioningStyle, FeedbackDelivery, PersonalityAnalysisRequest,
    PersonalityAnalysisResponse, PersonalitySystemConfig,
    get_trait_enum_by_dimension
)
from .ai_client import get_ai_client, ConversationResponse
from .database import KnowledgeBaseService

logger = logging.getLogger(__name__)


class PersonalityAnalysisEngine:
    """
    Core engine for analyzing creator personality from their documents and content
    """
    
    def __init__(self, config: Optional[PersonalitySystemConfig] = None):
        self.config = config or PersonalitySystemConfig()
        self.ai_client = get_ai_client()
        
        # Personality detection patterns
        self.trait_patterns = self._initialize_trait_patterns()
        
        logger.info("Personality Analysis Engine initialized")
    
    def _initialize_trait_patterns(self) -> Dict[str, Dict[str, List[str]]]:
        """Initialize regex patterns for detecting personality traits in text"""
        return {
            PersonalityDimension.COMMUNICATION_STYLE: {
                CommunicationStyle.DIRECT: [
                    r"\b(direct|straightforward|clear|explicit|frank)\b",
                    r"\b(tell\s+you\s+straight|cut\s+to\s+the\s+chase|bottom\s+line)\b",
                    r"\b(no\s+sugarcoating|honest\s+feedback|brutal\s+truth)\b"
                ],
                CommunicationStyle.COLLABORATIVE: [
                    r"\b(together|partnership|collaborate|co-create)\b",
                    r"\b(let's\s+work|we\s+can\s+explore|joint\s+effort)\b",
                    r"\b(build\s+on|share\s+ideas|mutual)\b"
                ],
                CommunicationStyle.SUPPORTIVE: [
                    r"\b(support|encourage|nurture|guide)\b",
                    r"\b(you\s+can\s+do|believe\s+in\s+you|here\s+for\s+you)\b",
                    r"\b(gentle|understanding|patient|compassionate)\b"
                ],
                CommunicationStyle.CHALLENGING: [
                    r"\b(challenge|push|stretch|uncomfortable)\b",
                    r"\b(step\s+up|rise\s+to|beyond\s+comfort\s+zone)\b",
                    r"\b(tough\s+questions|hard\s+truths|difficult\s+conversations)\b"
                ]
            },
            PersonalityDimension.APPROACH_TYPE: {
                ApproachType.STRUCTURED: [
                    r"\b(structure|framework|system|methodology)\b",
                    r"\b(step\s+by\s+step|process|sequence|order)\b",
                    r"\b(plan|organize|systematic|methodical)\b"
                ],
                ApproachType.FLEXIBLE: [
                    r"\b(flexible|adapt|adjust|customize)\b",
                    r"\b(go\s+with\s+flow|see\s+what\s+emerges|organic)\b",
                    r"\b(responsive|dynamic|evolving)\b"
                ],
                ApproachType.INTUITIVE: [
                    r"\b(intuition|feel|sense|gut)\b",
                    r"\b(instinct|inner\s+wisdom|trust\s+yourself)\b",
                    r"\b(natural|spontaneous|emerging)\b"
                ],
                ApproachType.ANALYTICAL: [
                    r"\b(analyze|data|metrics|measure)\b",
                    r"\b(logical|rational|systematic|evidence)\b",
                    r"\b(breakdown|examine|assess|evaluate)\b"
                ]
            },
            PersonalityDimension.INTERACTION_MODE: {
                InteractionMode.FORMAL: [
                    r"\b(professional|formal|structured|business)\b",
                    r"\b(objectives|goals|outcomes|deliverables)\b",
                    r"\b(protocol|standards|procedure)\b"
                ],
                InteractionMode.CASUAL: [
                    r"\b(casual|relaxed|informal|friendly)\b",
                    r"\b(chat|conversation|easy|comfortable)\b",
                    r"\b(down\s+to\s+earth|approachable|laid\s+back)\b"
                ],
                InteractionMode.EMPATHETIC: [
                    r"\b(understand|empathy|feelings|emotions)\b",
                    r"\b(hear\s+you|validate|acknowledge)\b",
                    r"\b(compassion|caring|sensitive|aware)\b"
                ],
                InteractionMode.RESULTS_FOCUSED: [
                    r"\b(results|outcomes|achievement|success)\b",
                    r"\b(goals|targets|metrics|performance)\b",
                    r"\b(action|implementation|execution|delivery)\b"
                ]
            },
            PersonalityDimension.QUESTIONING_STYLE: {
                QuestioningStyle.PROBING: [
                    r"\b(dig\s+deeper|explore\s+further|tell\s+me\s+more)\b",
                    r"\b(what\s+else|what\s+if|what\s+about)\b",
                    r"\b(probe|investigate|uncover|discover)\b"
                ],
                QuestioningStyle.EXPLORATORY: [
                    r"\b(explore|discover|journey|adventure)\b",
                    r"\b(possibilities|options|alternatives|directions)\b",
                    r"\b(wonder|curious|investigate|examine)\b"
                ],
                QuestioningStyle.CLARIFYING: [
                    r"\b(clarify|understand|clear|specific)\b",
                    r"\b(what\s+do\s+you\s+mean|can\s+you\s+explain)\b",
                    r"\b(make\s+sure|confirm|verify|check)\b"
                ],
                QuestioningStyle.REFLECTIVE: [
                    r"\b(reflect|think\s+about|consider|ponder)\b",
                    r"\b(look\s+back|examine|review|contemplate)\b",
                    r"\b(meaning|significance|learning|insight)\b"
                ]
            },
            PersonalityDimension.FEEDBACK_DELIVERY: {
                FeedbackDelivery.GENTLE: [
                    r"\b(gentle|soft|kind|tender)\b",
                    r"\b(might\s+consider|perhaps|maybe|could\s+try)\b",
                    r"\b(with\s+care|thoughtfully|gently)\b"
                ],
                FeedbackDelivery.DIRECT: [
                    r"\b(directly|clearly|frankly|honestly)\b",
                    r"\b(need\s+to|must|should|have\s+to)\b",
                    r"\b(reality\s+is|fact\s+is|truth\s+is)\b"
                ],
                FeedbackDelivery.ENCOURAGING: [
                    r"\b(encourage|motivate|inspire|uplift)\b",
                    r"\b(you\s+can|great\s+job|well\s+done|keep\s+going)\b",
                    r"\b(believe|confidence|strength|potential)\b"
                ],
                FeedbackDelivery.CONSTRUCTIVE: [
                    r"\b(constructive|helpful|useful|productive)\b",
                    r"\b(improve|enhance|develop|grow)\b",
                    r"\b(opportunity|suggestion|recommendation)\b"
                ]
            }
        }
    
    async def analyze_creator_personality(
        self,
        creator_id: str,
        session,
        force_reanalysis: bool = False,
        include_documents: Optional[List[str]] = None
    ) -> PersonalityAnalysisResponse:
        """
        Analyze creator's personality from their documents
        
        Args:
            creator_id: Creator to analyze
            session: Database session
            force_reanalysis: Force complete reanalysis
            include_documents: Specific documents to analyze
            
        Returns:
            PersonalityAnalysisResponse with analysis results
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting personality analysis for creator {creator_id}")
            
            # Get creator's documents for analysis
            documents_data = await self._get_documents_for_analysis(
                creator_id, session, include_documents
            )
            
            if not documents_data:
                return PersonalityAnalysisResponse(
                    creator_id=creator_id,
                    analysis_status="no_documents",
                    processing_time_seconds=0.0,
                    error_message="No documents available for personality analysis"
                )
            
            # Extract personality traits from documents
            extracted_traits = await self._extract_personality_traits(
                creator_id, documents_data, session
            )
            
            # Generate personality profile
            personality_profile = await self._generate_personality_profile(
                creator_id, extracted_traits, documents_data, session
            )
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(
                f"Personality analysis completed for creator {creator_id}: "
                f"{len(extracted_traits)} traits discovered in {processing_time:.2f}s"
            )
            
            return PersonalityAnalysisResponse(
                creator_id=creator_id,
                analysis_status="completed",
                personality_profile=personality_profile,
                traits_discovered=len(extracted_traits),
                processing_time_seconds=processing_time,
                documents_processed=len(documents_data)
            )
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Personality analysis failed for creator {creator_id}: {str(e)}")
            
            return PersonalityAnalysisResponse(
                creator_id=creator_id,
                analysis_status="failed",
                processing_time_seconds=processing_time,
                error_message=str(e)
            )
    
    async def _get_documents_for_analysis(
        self,
        creator_id: str,
        session,
        include_documents: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get creator's documents that can be used for personality analysis"""
        try:
            # Get knowledge context from all creator's documents
            context = await KnowledgeBaseService.get_creator_knowledge_context(
                creator_id=creator_id,
                query="coaching style personality approach methodology",
                limit=50,  # Get more chunks for comprehensive analysis
                similarity_threshold=0.3,  # Lower threshold for broader analysis
                session=session
            )
            
            # Group chunks by document
            documents_data = {}
            for chunk in context.get("knowledge_chunks", []):
                doc_id = chunk["source_document"]
                if include_documents and doc_id not in include_documents:
                    continue
                    
                if doc_id not in documents_data:
                    documents_data[doc_id] = {
                        "document_id": doc_id,
                        "chunks": [],
                        "title": chunk.get("document_title", "Unknown"),
                        "filename": chunk.get("document_filename", "Unknown")
                    }
                
                documents_data[doc_id]["chunks"].append({
                    "content": chunk["content"],
                    "chunk_index": chunk["chunk_index"],
                    "similarity": chunk["similarity"]
                })
            
            return list(documents_data.values())
            
        except Exception as e:
            logger.error(f"Failed to get documents for analysis: {str(e)}")
            return []
    
    async def _extract_personality_traits(
        self,
        creator_id: str,
        documents_data: List[Dict[str, Any]],
        session
    ) -> List[Tuple[PersonalityTrait, List[PersonalityEvidence]]]:
        """Extract personality traits from document content"""
        extracted_traits = []
        
        for doc_data in documents_data:
            doc_id = doc_data["document_id"]
            
            for chunk in doc_data["chunks"]:
                content = chunk["content"]
                chunk_index = chunk["chunk_index"]
                
                # Pattern-based trait detection
                detected_traits = await self._detect_traits_in_content(
                    content, doc_id, chunk_index
                )
                
                # AI-enhanced trait analysis
                ai_traits = await self._ai_analyze_traits(
                    content, doc_id, chunk_index
                )
                
                # Combine and deduplicate traits
                all_traits = detected_traits + ai_traits
                extracted_traits.extend(all_traits)
        
        # Consolidate similar traits
        consolidated_traits = self._consolidate_traits(extracted_traits)
        
        return consolidated_traits
    
    async def _detect_traits_in_content(
        self,
        content: str,
        doc_id: str,
        chunk_index: int
    ) -> List[Tuple[PersonalityTrait, List[PersonalityEvidence]]]:
        """Detect personality traits using pattern matching"""
        detected_traits = []
        
        for dimension, trait_patterns in self.trait_patterns.items():
            for trait_value, patterns in trait_patterns.items():
                evidence_items = []
                
                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        # Extract context around the match
                        start = max(0, match.start() - 50)
                        end = min(len(content), match.end() + 50)
                        context_snippet = content[start:end].strip()
                        
                        evidence = PersonalityEvidence(
                            document_id=doc_id,
                            chunk_index=chunk_index,
                            content_snippet=context_snippet,
                            trait_indicators=[match.group()],
                            confidence=0.7  # Pattern-based confidence
                        )
                        evidence_items.append(evidence)
                
                if evidence_items:
                    # Calculate trait confidence based on evidence
                    confidence = min(0.9, len(evidence_items) * 0.2 + 0.5)
                    
                    trait = PersonalityTrait(
                        dimension=dimension,
                        trait_value=trait_value,
                        confidence_score=confidence,
                        evidence_count=len(evidence_items)
                    )
                    
                    detected_traits.append((trait, evidence_items))
        
        return detected_traits
    
    async def _ai_analyze_traits(
        self,
        content: str,
        doc_id: str,
        chunk_index: int
    ) -> List[Tuple[PersonalityTrait, List[PersonalityEvidence]]]:
        """Use AI to analyze personality traits in content"""
        try:
            # Create AI prompt for personality analysis
            analysis_prompt = f"""
            Analyze the following coaching content for personality traits:
            
            Content: {content[:1000]}...
            
            Identify the coaching style and personality characteristics. Focus on:
            1. Communication style (direct, collaborative, supportive, challenging)
            2. Approach type (structured, flexible, intuitive, analytical)
            3. Interaction mode (formal, casual, empathetic, results-focused)
            4. Questioning style (probing, exploratory, clarifying, reflective)
            5. Feedback delivery (gentle, direct, encouraging, constructive)
            
            Provide specific examples from the text that support each trait.
            Format: [TRAIT_DIMENSION]:[TRAIT_VALUE]:[CONFIDENCE]:[EVIDENCE]
            """
            
            # Get AI analysis using conversation endpoint
            ai_response = await self.ai_client.process_conversation_with_knowledge(
                message=analysis_prompt,
                creator_id="system",  # Use system context for analysis
                conversation_id=f"personality_analysis_{uuid4().hex[:8]}"
            )
            
            # Parse AI response for traits
            return self._parse_ai_trait_response(
                ai_response.response, doc_id, chunk_index
            )
            
        except Exception as e:
            logger.warning(f"AI trait analysis failed: {str(e)}")
            return []
    
    def _parse_ai_trait_response(
        self,
        ai_response: str,
        doc_id: str,
        chunk_index: int
    ) -> List[Tuple[PersonalityTrait, List[PersonalityEvidence]]]:
        """Parse AI response for personality traits"""
        traits = []
        
        # Look for trait patterns in AI response
        trait_pattern = r"\[([^:]+):([^:]+):([^:]+):([^\]]+)\]"
        matches = re.finditer(trait_pattern, ai_response)
        
        for match in matches:
            try:
                dimension_str = match.group(1).strip().upper()
                trait_value = match.group(2).strip().lower()
                confidence_str = match.group(3).strip()
                evidence_text = match.group(4).strip()
                
                # Map dimension string to enum
                dimension = None
                for dim in PersonalityDimension:
                    if dimension_str in dim.value.upper():
                        dimension = dim
                        break
                
                if not dimension:
                    continue
                
                # Parse confidence
                try:
                    confidence = float(confidence_str)
                    confidence = max(0.0, min(1.0, confidence))
                except ValueError:
                    confidence = 0.6  # Default confidence
                
                # Create trait and evidence
                trait = PersonalityTrait(
                    dimension=dimension,
                    trait_value=trait_value,
                    confidence_score=confidence,
                    evidence_count=1
                )
                
                evidence = PersonalityEvidence(
                    document_id=doc_id,
                    chunk_index=chunk_index,
                    content_snippet=evidence_text[:500],
                    trait_indicators=["AI_DETECTED"],
                    confidence=confidence
                )
                
                traits.append((trait, [evidence]))
                
            except Exception as e:
                logger.warning(f"Failed to parse AI trait: {str(e)}")
                continue
        
        return traits
    
    def _consolidate_traits(
        self,
        extracted_traits: List[Tuple[PersonalityTrait, List[PersonalityEvidence]]]
    ) -> List[Tuple[PersonalityTrait, List[PersonalityEvidence]]]:
        """Consolidate similar traits and combine evidence"""
        # Group traits by dimension and value
        trait_groups = {}
        
        for trait, evidence_list in extracted_traits:
            key = f"{trait.dimension}:{trait.trait_value}"
            
            if key not in trait_groups:
                trait_groups[key] = {
                    "trait": trait,
                    "evidence": evidence_list
                }
            else:
                # Combine evidence and update confidence
                existing = trait_groups[key]
                existing["evidence"].extend(evidence_list)
                
                # Update confidence based on evidence count
                total_evidence = len(existing["evidence"])
                avg_confidence = sum(e.confidence for e in existing["evidence"]) / total_evidence
                
                existing["trait"].confidence_score = min(0.95, avg_confidence * (1 + total_evidence * 0.1))
                existing["trait"].evidence_count = total_evidence
        
        # Filter traits by confidence threshold
        consolidated = [
            (data["trait"], data["evidence"])
            for data in trait_groups.values()
            if data["trait"].confidence_score >= self.config.analysis_confidence_threshold
        ]
        
        return consolidated
    
    async def _generate_personality_profile(
        self,
        creator_id: str,
        extracted_traits: List[Tuple[PersonalityTrait, List[PersonalityEvidence]]],
        documents_data: List[Dict[str, Any]],
        session
    ) -> PersonalityProfile:
        """Generate comprehensive personality profile"""
        
        # Extract just traits for profile
        traits = [trait for trait, evidence in extracted_traits]
        
        # Generate personality summary using AI
        personality_summary = await self._generate_personality_summary(
            creator_id, traits, session
        )
        
        # Extract key methodologies
        methodologies = self._extract_methodologies(documents_data)
        
        # Calculate overall confidence
        if traits:
            overall_confidence = sum(t.confidence_score for t in traits) / len(traits)
        else:
            overall_confidence = 0.0
        
        # Calculate consistency score
        consistency_score = self._calculate_consistency_score(traits)
        
        # Calculate trait stability
        trait_stability = {
            trait.dimension: trait.confidence_score
            for trait in traits
        }
        
        return PersonalityProfile(
            creator_id=creator_id,
            display_name="Creator",  # Would get from creator profile
            traits=traits,
            personality_summary=personality_summary,
            key_methodologies=methodologies,
            confidence_score=overall_confidence,
            documents_analyzed=len(documents_data),
            last_analysis=datetime.utcnow(),
            consistency_score=consistency_score,
            trait_stability=trait_stability
        )
    
    async def _generate_personality_summary(
        self,
        creator_id: str,
        traits: List[PersonalityTrait],
        session
    ) -> Optional[str]:
        """Generate AI-powered personality summary"""
        if not traits:
            return None
        
        try:
            # Create summary prompt
            trait_descriptions = []
            for trait in traits:
                trait_descriptions.append(
                    f"{trait.dimension}: {trait.trait_value} "
                    f"(confidence: {trait.confidence_score:.2f})"
                )
            
            summary_prompt = f"""
            Create a comprehensive personality summary for a coach/creator based on these traits:
            
            {chr(10).join(trait_descriptions)}
            
            Write a 2-3 sentence summary that captures their unique coaching personality, 
            communication style, and approach. Make it professional and insightful.
            """
            
            # Get AI summary
            ai_response = await self.ai_client.process_conversation_with_knowledge(
                message=summary_prompt,
                creator_id="system",
                conversation_id=f"personality_summary_{uuid4().hex[:8]}"
            )
            
            return ai_response.response[:1000]  # Limit summary length
            
        except Exception as e:
            logger.warning(f"Failed to generate personality summary: {str(e)}")
            return None
    
    def _extract_methodologies(self, documents_data: List[Dict[str, Any]]) -> List[str]:
        """Extract key coaching methodologies from documents"""
        methodologies = set()
        
        # Common coaching methodology patterns
        methodology_patterns = [
            r"\b(GROW|grow)\s+model\b",
            r"\b(SMART|smart)\s+goals?\b",
            r"\b(solution\s+focused|solution-focused)\b",
            r"\b(cognitive\s+behavioral|CBT)\b",
            r"\b(neuro-linguistic|NLP)\b",
            r"\b(appreciative\s+inquiry)\b",
            r"\b(strengths?\s+based)\b",
            r"\b(mindfulness\s+based)\b",
            r"\b(positive\s+psychology)\b",
            r"\b(transformational\s+coaching)\b"
        ]
        
        for doc_data in documents_data:
            for chunk in doc_data["chunks"]:
                content = chunk["content"]
                for pattern in methodology_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        methodologies.add(match.group().title())
        
        return list(methodologies)[:10]  # Limit to top 10
    
    def _calculate_consistency_score(self, traits: List[PersonalityTrait]) -> float:
        """Calculate personality consistency score"""
        if not traits:
            return 0.0
        
        # Group traits by dimension
        dimension_traits = {}
        for trait in traits:
            if trait.dimension not in dimension_traits:
                dimension_traits[trait.dimension] = []
            dimension_traits[trait.dimension].append(trait)
        
        # Calculate consistency within each dimension
        dimension_consistencies = []
        for dimension, dim_traits in dimension_traits.items():
            if len(dim_traits) == 1:
                # Single trait = perfectly consistent
                dimension_consistencies.append(1.0)
            else:
                # Multiple traits = check for conflicts
                confidences = [t.confidence_score for t in dim_traits]
                max_confidence = max(confidences)
                avg_confidence = sum(confidences) / len(confidences)
                
                # Consistency is how dominant the top trait is
                consistency = max_confidence / (avg_confidence + 0.1)
                consistency = min(1.0, consistency)
                dimension_consistencies.append(consistency)
        
        # Overall consistency is average of dimension consistencies
        return sum(dimension_consistencies) / len(dimension_consistencies)


# Global personality engine instance
_personality_engine: Optional[PersonalityAnalysisEngine] = None


def get_personality_engine() -> PersonalityAnalysisEngine:
    """Get global personality engine instance"""
    global _personality_engine
    if _personality_engine is None:
        _personality_engine = PersonalityAnalysisEngine()
    return _personality_engine