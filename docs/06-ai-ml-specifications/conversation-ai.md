# Conversation AI Specification

## Overview

The Conversation AI system manages multi-turn dialogues, maintains context across sessions, adapts to user communication styles, and ensures consistent personality while integrating with the creator's knowledge base and coaching methodology.

## Conversation Management Architecture

### Dialogue State Management
```python
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum
import json
from datetime import datetime, timedelta

class ConversationState(Enum):
    GREETING = "greeting"
    GOAL_SETTING = "goal_setting"
    COACHING = "coaching"
    PROBLEM_SOLVING = "problem_solving"
    CELEBRATION = "celebration"
    ESCALATION = "escalation"
    CLOSING = "closing"

@dataclass
class ConversationContext:
    conversation_id: str
    user_id: str
    creator_id: str
    current_state: ConversationState
    session_start: datetime
    last_activity: datetime
    message_count: int
    context_memory: Dict[str, Any]
    user_profile: Dict[str, Any]
    creator_profile: Dict[str, Any]
    conversation_goals: List[str]
    emotional_state: Dict[str, float]
    topics_discussed: List[str]
    unresolved_issues: List[str]

class ConversationManager:
    def __init__(self):
        self.state_machine = ConversationStateMachine()
        self.context_manager = ContextManager()
        self.memory_manager = MemoryManager()
        self.personality_engine = PersonalityEngine()
        self.response_generator = ResponseGenerator()
    
    async def process_message(
        self,
        user_message: str,
        conversation_context: ConversationContext
    ):
        """Process incoming user message and generate appropriate response"""
        
        # Update conversation context
        updated_context = await self.context_manager.update_context(
            conversation_context, user_message
        )
        
        # Determine conversation state transition
        new_state = await self.state_machine.transition(
            updated_context.current_state, user_message, updated_context
        )
        updated_context.current_state = new_state
        
        # Generate response based on current state
        response = await self.response_generator.generate_response(
            user_message, updated_context
        )
        
        # Update memory with new interaction
        await self.memory_manager.store_interaction(
            updated_context.conversation_id,
            user_message,
            response,
            updated_context
        )
        
        return {
            'response': response,
            'updated_context': updated_context,
            'state_transition': {
                'from': conversation_context.current_state,
                'to': new_state
            }
        }

### Context Management System
```python
class ContextManager:
    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer()
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()
        self.topic_tracker = TopicTracker()
        self.emotional_state_tracker = EmotionalStateTracker()
    
    async def update_context(
        self,
        context: ConversationContext,
        user_message: str
    ) -> ConversationContext:
        """Update conversation context with new message information"""
        
        # Analyze message
        sentiment = await self.sentiment_analyzer.analyze(user_message)
        intent = await self.intent_classifier.classify(user_message, context)
        entities = await self.entity_extractor.extract(user_message)
        topics = await self.topic_tracker.identify_topics(user_message, context)
        
        # Update emotional state
        emotional_state = await self.emotional_state_tracker.update(
            context.emotional_state, sentiment, user_message
        )
        
        # Update context
        context.last_activity = datetime.utcnow()
        context.message_count += 1
        context.emotional_state = emotional_state
        context.topics_discussed.extend(topics)
        
        # Update context memory
        context.context_memory.update({
            'last_intent': intent,
            'last_sentiment': sentiment,
            'last_entities': entities,
            'recent_topics': topics[-5:],  # Keep last 5 topics
            'session_duration': (datetime.utcnow() - context.session_start).total_seconds()
        })
        
        return context
    
    async def get_relevant_context(
        self,
        context: ConversationContext,
        lookback_messages: int = 10
    ) -> Dict[str, Any]:
        """Extract relevant context for response generation"""
        
        recent_history = await self.memory_manager.get_recent_messages(
            context.conversation_id, lookback_messages
        )
        
        return {
            'conversation_summary': await self._summarize_conversation(recent_history),
            'user_goals': context.conversation_goals,
            'emotional_trajectory': self._analyze_emotional_trajectory(context),
            'key_topics': self._extract_key_topics(context.topics_discussed),
            'unresolved_issues': context.unresolved_issues,
            'user_preferences': context.user_profile.get('preferences', {}),
            'session_context': {
                'duration': context.context_memory.get('session_duration', 0),
                'message_count': context.message_count,
                'engagement_level': self._calculate_engagement_level(context)
            }
        }

### Memory Management
```python
class MemoryManager:
    def __init__(self):
        self.short_term_memory = ShortTermMemory()
        self.long_term_memory = LongTermMemory()
        self.episodic_memory = EpisodicMemory()
        self.semantic_memory = SemanticMemory()
    
    async def store_interaction(
        self,
        conversation_id: str,
        user_message: str,
        ai_response: str,
        context: ConversationContext
    ):
        """Store interaction in appropriate memory systems"""
        
        interaction = {
            'timestamp': datetime.utcnow(),
            'user_message': user_message,
            'ai_response': ai_response,
            'context_snapshot': context.context_memory,
            'emotional_state': context.emotional_state,
            'conversation_state': context.current_state
        }
        
        # Store in short-term memory (recent interactions)
        await self.short_term_memory.store(conversation_id, interaction)
        
        # Extract important information for long-term storage
        if self._is_significant_interaction(interaction, context):
            await self.long_term_memory.store(conversation_id, interaction)
        
        # Store episodic memories (specific events/achievements)
        episodes = self._extract_episodes(interaction, context)
        for episode in episodes:
            await self.episodic_memory.store(conversation_id, episode)
        
        # Update semantic memory (facts about user)
        semantic_updates = self._extract_semantic_information(interaction, context)
        await self.semantic_memory.update(context.user_id, semantic_updates)
    
    async def retrieve_relevant_memories(
        self,
        conversation_id: str,
        current_context: ConversationContext,
        query: str
    ) -> Dict[str, List]:
        """Retrieve relevant memories for response generation"""
        
        return {
            'recent_interactions': await self.short_term_memory.retrieve(
                conversation_id, limit=5
            ),
            'relevant_episodes': await self.episodic_memory.search(
                conversation_id, query, limit=3
            ),
            'user_facts': await self.semantic_memory.get_relevant_facts(
                current_context.user_id, query
            ),
            'similar_conversations': await self.long_term_memory.find_similar(
                conversation_id, current_context, limit=2
            )
        }

### Personality and Voice Consistency
```python
class PersonalityEngine:
    def __init__(self):
        self.personality_model = PersonalityModel()
        self.voice_adapter = VoiceAdapter()
        self.consistency_monitor = ConsistencyMonitor()
        self.trait_manager = TraitManager()
    
    async def initialize_personality(self, creator_context: Dict) -> Dict:
        """Initialize AI personality based on creator profile"""
        
        personality_traits = {
            'warmth': creator_context.get('warmth_level', 0.8),
            'professionalism': creator_context.get('professionalism_level', 0.7),
            'enthusiasm': creator_context.get('enthusiasm_level', 0.6),
            'directness': creator_context.get('directness_level', 0.5),
            'empathy': creator_context.get('empathy_level', 0.9),
            'humor': creator_context.get('humor_level', 0.4),
            'authority': creator_context.get('authority_level', 0.6)
        }
        
        communication_style = {
            'formality': creator_context.get('formality', 'casual_professional'),
            'complexity': creator_context.get('complexity', 'moderate'),
            'response_length': creator_context.get('preferred_length', 'medium'),
            'emoji_usage': creator_context.get('emoji_usage', 'moderate'),
            'question_style': creator_context.get('question_style', 'open_ended')
        }
        
        return {
            'personality_traits': personality_traits,
            'communication_style': communication_style,
            'signature_phrases': creator_context.get('signature_phrases', []),
            'coaching_methodology': creator_context.get('methodology', {}),
            'expertise_areas': creator_context.get('expertise_areas', [])
        }
    
    async def adapt_response_to_personality(
        self,
        base_response: str,
        personality_profile: Dict,
        context: ConversationContext
    ) -> str:
        """Adapt response to match creator's personality"""
        
        adapted_response = base_response
        
        # Apply personality traits
        adapted_response = await self.voice_adapter.apply_warmth(
            adapted_response, personality_profile['personality_traits']['warmth']
        )
        
        adapted_response = await self.voice_adapter.apply_enthusiasm(
            adapted_response, personality_profile['personality_traits']['enthusiasm']
        )
        
        adapted_response = await self.voice_adapter.apply_empathy(
            adapted_response, personality_profile['personality_traits']['empathy']
        )
        
        # Apply communication style
        adapted_response = await self.voice_adapter.adjust_formality(
            adapted_response, personality_profile['communication_style']['formality']
        )
        
        adapted_response = await self.voice_adapter.adjust_complexity(
            adapted_response, personality_profile['communication_style']['complexity']
        )
        
        # Add signature elements
        adapted_response = await self.voice_adapter.add_signature_elements(
            adapted_response, personality_profile['signature_phrases']
        )
        
        # Validate consistency
        consistency_score = await self.consistency_monitor.check_consistency(
            adapted_response, personality_profile, context
        )
        
        if consistency_score < 0.7:
            adapted_response = await self.voice_adapter.improve_consistency(
                adapted_response, personality_profile, context
            )
        
        return adapted_response

### Multi-Turn Dialogue Management
```python
class DialogueManager:
    def __init__(self):
        self.turn_tracker = TurnTracker()
        self.coherence_manager = CoherenceManager()
        self.topic_manager = TopicManager()
        self.goal_tracker = GoalTracker()
    
    async def manage_dialogue_flow(
        self,
        user_message: str,
        context: ConversationContext,
        conversation_history: List[Dict]
    ):
        """Manage multi-turn dialogue flow and coherence"""
        
        # Track dialogue turns
        current_turn = await self.turn_tracker.get_current_turn(context)
        
        # Analyze topic continuity
        topic_analysis = await self.topic_manager.analyze_topic_flow(
            user_message, conversation_history
        )
        
        # Check goal progress
        goal_progress = await self.goal_tracker.assess_progress(
            context.conversation_goals, conversation_history
        )
        
        # Determine dialogue strategy
        dialogue_strategy = await self._determine_strategy(
            current_turn, topic_analysis, goal_progress, context
        )
        
        return {
            'current_turn': current_turn,
            'topic_analysis': topic_analysis,
            'goal_progress': goal_progress,
            'recommended_strategy': dialogue_strategy,
            'coherence_score': await self.coherence_manager.calculate_coherence(
                conversation_history
            )
        }
    
    async def _determine_strategy(
        self,
        current_turn: Dict,
        topic_analysis: Dict,
        goal_progress: Dict,
        context: ConversationContext
    ) -> Dict:
        """Determine optimal dialogue strategy"""
        
        strategies = []
        
        # Topic-based strategies
        if topic_analysis['topic_drift'] > 0.7:
            strategies.append({
                'type': 'topic_refocus',
                'priority': 'high',
                'action': 'gently_redirect_to_main_topic'
            })
        
        # Goal-based strategies
        if goal_progress['stagnation_detected']:
            strategies.append({
                'type': 'goal_progression',
                'priority': 'medium',
                'action': 'introduce_new_perspective_or_approach'
            })
        
        # Engagement-based strategies
        if context.context_memory.get('engagement_level', 0.5) < 0.3:
            strategies.append({
                'type': 'engagement_boost',
                'priority': 'high',
                'action': 'ask_engaging_question_or_share_story'
            })
        
        # Emotional state strategies
        if context.emotional_state.get('frustration', 0) > 0.6:
            strategies.append({
                'type': 'emotional_support',
                'priority': 'high',
                'action': 'provide_empathy_and_encouragement'
            })
        
        return {
            'primary_strategy': max(strategies, key=lambda x: x['priority']) if strategies else None,
            'all_strategies': strategies,
            'confidence': self._calculate_strategy_confidence(strategies, context)
        }

### Response Generation Engine
```python
class ResponseGenerator:
    def __init__(self):
        self.llm = Ollama(model="llama3:8b", temperature=0.7)
        self.prompt_builder = PromptBuilder()
        self.response_validator = ResponseValidator()
        self.personality_engine = PersonalityEngine()
        self.rag_system = RAGSystem()
    
    async def generate_response(
        self,
        user_message: str,
        context: ConversationContext
    ) -> Dict:
        """Generate contextually appropriate response"""
        
        # Get relevant context and memories
        relevant_context = await self.context_manager.get_relevant_context(context)
        relevant_memories = await self.memory_manager.retrieve_relevant_memories(
            context.conversation_id, context, user_message
        )
        
        # Retrieve relevant knowledge
        knowledge_context = await self.rag_system.retrieve_context(
            user_message, context.creator_id, context.user_profile
        )
        
        # Build comprehensive prompt
        prompt = await self.prompt_builder.build_conversation_prompt(
            user_message=user_message,
            conversation_context=relevant_context,
            memories=relevant_memories,
            knowledge_context=knowledge_context,
            personality_profile=context.creator_profile,
            user_profile=context.user_profile
        )
        
        # Generate base response
        base_response = await self.llm.agenerate([prompt])
        response_text = base_response.generations[0][0].text
        
        # Adapt to personality
        adapted_response = await self.personality_engine.adapt_response_to_personality(
            response_text, context.creator_profile, context
        )
        
        # Validate response
        validation_result = await self.response_validator.validate_response(
            adapted_response, context, user_message
        )
        
        # Generate follow-up suggestions
        follow_up_suggestions = await self._generate_follow_up_suggestions(
            adapted_response, context
        )
        
        return {
            'response_text': adapted_response,
            'validation': validation_result,
            'follow_up_suggestions': follow_up_suggestions,
            'confidence_score': validation_result.get('confidence', 0.8),
            'response_metadata': {
                'generation_time': datetime.utcnow(),
                'knowledge_sources_used': len(knowledge_context.get('sources', [])),
                'personality_adaptation_score': validation_result.get('personality_score', 0.8)
            }
        }

### Conversation Analytics and Optimization
```python
class ConversationAnalytics:
    def __init__(self):
        self.engagement_analyzer = EngagementAnalyzer()
        self.satisfaction_predictor = SatisfactionPredictor()
        self.outcome_tracker = OutcomeTracker()
        self.improvement_identifier = ImprovementIdentifier()
    
    async def analyze_conversation_quality(
        self,
        conversation_id: str,
        timeframe: str = "session"
    ):
        """Analyze conversation quality and effectiveness"""
        
        conversation_data = await self.get_conversation_data(conversation_id, timeframe)
        
        analysis = {
            'engagement_metrics': await self.engagement_analyzer.analyze(conversation_data),
            'satisfaction_prediction': await self.satisfaction_predictor.predict(conversation_data),
            'goal_progress': await self.outcome_tracker.track_progress(conversation_data),
            'conversation_flow': await self._analyze_flow_quality(conversation_data),
            'response_quality': await self._analyze_response_quality(conversation_data)
        }
        
        overall_score = self._calculate_overall_quality_score(analysis)
        
        return {
            'overall_quality_score': overall_score,
            'detailed_analysis': analysis,
            'improvement_recommendations': await self.improvement_identifier.identify(analysis),
            'strengths': self._identify_strengths(analysis),
            'areas_for_improvement': self._identify_improvement_areas(analysis)
        }
    
    async def optimize_conversation_strategy(
        self,
        creator_id: str,
        user_segment: str,
        historical_data: Dict
    ):
        """Optimize conversation strategies based on historical performance"""
        
        successful_patterns = await self._identify_successful_patterns(
            creator_id, user_segment, historical_data
        )
        
        optimization_recommendations = {
            'personality_adjustments': await self._recommend_personality_adjustments(
                successful_patterns
            ),
            'response_timing_optimization': await self._optimize_response_timing(
                successful_patterns
            ),
            'topic_flow_optimization': await self._optimize_topic_flow(
                successful_patterns
            ),
            'engagement_strategies': await self._recommend_engagement_strategies(
                successful_patterns
            )
        }
        
        return {
            'optimization_recommendations': optimization_recommendations,
            'expected_improvement': self._estimate_improvement_impact(
                optimization_recommendations
            ),
            'implementation_priority': self._prioritize_optimizations(
                optimization_recommendations
            )
        }
```

This comprehensive conversation AI system ensures natural, contextual, and effective coaching conversations while maintaining consistency with the creator's personality and methodology across all interactions.