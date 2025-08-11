# AI Engine API Specification

## Overview

The AI Engine API provides intelligent conversation handling, content generation, proactive engagement, and user profiling capabilities. This API is primarily used by channel services and the Creator Hub to deliver AI-powered coaching experiences.

## Authentication

All AI Engine API endpoints require service-to-service authentication using API keys or JWT tokens with appropriate scopes.

```http
Authorization: Bearer <service_token>
X-API-Key: <service_api_key>
```

## Conversation AI API

### Generate Response
```http
POST /api/v1/ai/conversation/generate
Content-Type: application/json

{
  "user_message": "I'm struggling to stay motivated with my fitness goals",
  "conversation_context": {
    "conversation_id": "uuid",
    "user_id": "uuid",
    "creator_id": "uuid",
    "channel": "web",
    "conversation_history": [
      {
        "role": "user",
        "content": "Hi, I want to start a fitness routine",
        "timestamp": "2024-01-01T10:00:00Z"
      },
      {
        "role": "assistant",
        "content": "That's great! What are your main fitness goals?",
        "timestamp": "2024-01-01T10:00:05Z"
      }
    ]
  },
  "user_profile": {
    "goals": ["lose weight", "build muscle"],
    "preferences": {
      "communication_style": "encouraging",
      "expertise_level": "beginner"
    },
    "progress": {
      "current_program": "uuid",
      "completion_percentage": 0.3
    }
  },
  "creator_context": {
    "methodology": "Focus on sustainable habits and positive reinforcement",
    "communication_style": "warm and supportive",
    "expertise_areas": ["fitness", "nutrition", "habit formation"]
  },
  "generation_options": {
    "max_tokens": 500,
    "temperature": 0.7,
    "include_suggestions": true,
    "response_format": "conversational"
  }
}
```

**Response:**
```json
{
  "response": {
    "content": "I understand that motivation can be challenging! It's completely normal to have ups and downs in your fitness journey. Based on what you've shared, you've already made great progress - you're 30% through your current program, which is fantastic!\n\nHere are a few strategies that might help:\n1. Focus on small wins - celebrate completing each workout\n2. Remember your 'why' - you wanted to lose weight and build muscle\n3. Consider finding a workout buddy for accountability\n\nWhat specific part of staying motivated is most challenging for you right now?",
    "confidence_score": 0.92,
    "response_type": "supportive_guidance",
    "suggestions": [
      "Tell me about your current workout routine",
      "What motivates you most?",
      "Let's set a small goal for this week"
    ],
    "metadata": {
      "knowledge_sources": ["motivation_strategies.pdf", "habit_formation_guide.pdf"],
      "response_time_ms": 1250,
      "model_used": "llama3:8b",
      "tokens_used": 156
    }
  },
  "conversation_updates": {
    "user_profile_updates": {
      "current_challenges": ["motivation"],
      "engagement_score": 0.75
    },
    "next_proactive_check": "2024-01-02T10:00:00Z"
  },
  "escalation_recommendation": {
    "should_escalate": false,
    "confidence": 0.95,
    "reason": null
  }
}
```

### Batch Generate Responses
```http
POST /api/v1/ai/conversation/batch-generate
Content-Type: application/json

{
  "requests": [
    {
      "request_id": "req_1",
      "user_message": "How do I start meal planning?",
      "conversation_context": {},
      "user_profile": {},
      "creator_context": {}
    },
    {
      "request_id": "req_2",
      "user_message": "I missed my workout yesterday",
      "conversation_context": {},
      "user_profile": {},
      "creator_context": {}
    }
  ],
  "generation_options": {
    "max_tokens": 300,
    "temperature": 0.7
  }
}
```

**Response:**
```json
{
  "responses": [
    {
      "request_id": "req_1",
      "response": {
        "content": "Meal planning is a great way to stay on track with your nutrition goals!...",
        "confidence_score": 0.88,
        "metadata": {}
      }
    },
    {
      "request_id": "req_2",
      "response": {
        "content": "Don't worry about missing one workout - consistency matters more than perfection!...",
        "confidence_score": 0.91,
        "metadata": {}
      }
    }
  ],
  "batch_metadata": {
    "total_processing_time_ms": 2100,
    "successful_responses": 2,
    "failed_responses": 0
  }
}
```

### Validate Response Quality
```http
POST /api/v1/ai/conversation/validate
Content-Type: application/json

{
  "response_content": "That's a great question! Here's what I recommend...",
  "original_message": "How do I stay motivated?",
  "conversation_context": {},
  "creator_context": {},
  "validation_criteria": {
    "check_safety": true,
    "check_accuracy": true,
    "check_brand_consistency": true,
    "check_helpfulness": true
  }
}
```

**Response:**
```json
{
  "validation_result": {
    "is_valid": true,
    "overall_score": 0.89,
    "safety_check": {
      "is_safe": true,
      "confidence": 0.98,
      "detected_issues": []
    },
    "accuracy_check": {
      "is_accurate": true,
      "confidence": 0.85,
      "knowledge_alignment": 0.92
    },
    "brand_consistency": {
      "is_consistent": true,
      "confidence": 0.87,
      "style_match": 0.91
    },
    "helpfulness_score": 0.88,
    "recommendations": [
      "Consider adding a specific actionable step",
      "Response tone matches creator style well"
    ]
  }
}
```

## Knowledge Retrieval API

### Search Knowledge Base
```http
POST /api/v1/ai/knowledge/search
Content-Type: application/json

{
  "query": "How to build sustainable exercise habits",
  "creator_id": "uuid",
  "knowledge_base_ids": ["uuid1", "uuid2"],
  "search_options": {
    "max_results": 5,
    "similarity_threshold": 0.7,
    "include_metadata": true,
    "rerank_results": true
  },
  "context_filters": {
    "document_types": ["pdf", "docx"],
    "tags": ["habits", "exercise"],
    "date_range": {
      "start": "2024-01-01",
      "end": "2024-12-31"
    }
  }
}
```

**Response:**
```json
{
  "results": [
    {
      "chunk_id": "uuid",
      "document_id": "uuid",
      "document_title": "The Science of Habit Formation",
      "content": "Building sustainable exercise habits requires starting small and focusing on consistency rather than intensity. Research shows that habits form through a cue-routine-reward loop...",
      "similarity_score": 0.92,
      "metadata": {
        "page_number": 15,
        "section": "Chapter 3: Exercise Habits",
        "author": "Dr. Jane Smith",
        "tags": ["habits", "exercise", "psychology"]
      },
      "relevance_explanation": "Directly addresses sustainable exercise habit formation with scientific backing"
    },
    {
      "chunk_id": "uuid",
      "document_id": "uuid",
      "document_title": "Coaching Guide: Motivation Strategies",
      "content": "When helping clients build exercise habits, focus on intrinsic motivation and identity-based habits. Help them see themselves as someone who exercises regularly...",
      "similarity_score": 0.87,
      "metadata": {
        "section": "Habit Formation Strategies",
        "tags": ["coaching", "motivation", "habits"]
      },
      "relevance_explanation": "Provides coaching-specific strategies for habit formation"
    }
  ],
  "search_metadata": {
    "total_chunks_searched": 1250,
    "search_time_ms": 45,
    "query_embedding_time_ms": 12,
    "reranking_applied": true
  }
}
```

### Get Document Context
```http
GET /api/v1/ai/knowledge/documents/{document_id}/context
Query Parameters:
  - chunk_id: string (specific chunk to get context for)
  - context_window: integer (number of surrounding chunks, default: 2)
```

**Response:**
```json
{
  "document_id": "uuid",
  "document_title": "The Science of Habit Formation",
  "target_chunk": {
    "chunk_id": "uuid",
    "content": "Building sustainable exercise habits requires...",
    "chunk_index": 15
  },
  "context_chunks": [
    {
      "chunk_id": "uuid",
      "content": "Previous research on habit formation shows...",
      "chunk_index": 14,
      "position": "before"
    },
    {
      "chunk_id": "uuid",
      "content": "The key to successful habit formation is...",
      "chunk_index": 16,
      "position": "after"
    }
  ],
  "document_metadata": {
    "author": "Dr. Jane Smith",
    "publication_date": "2023-06-15",
    "total_chunks": 45
  }
}
```

### Update Knowledge Embeddings
```http
POST /api/v1/ai/knowledge/embeddings/update
Content-Type: application/json

{
  "document_ids": ["uuid1", "uuid2"],
  "creator_id": "uuid",
  "update_options": {
    "force_recompute": false,
    "batch_size": 50,
    "embedding_model": "nomic-embed-text"
  }
}
```

**Response:**
```json
{
  "update_job_id": "uuid",
  "status": "processing",
  "documents_queued": 2,
  "estimated_completion": "2024-01-01T00:05:00Z",
  "progress": {
    "completed": 0,
    "total": 2,
    "current_document": "uuid1"
  }
}
```

## Content Generation API

### Generate Content
```http
POST /api/v1/ai/content/generate
Content-Type: application/json

{
  "content_type": "coaching_tip",
  "topic": "building morning routines",
  "creator_context": {
    "creator_id": "uuid",
    "expertise_areas": ["productivity", "habit formation"],
    "brand_voice": {
      "tone": "encouraging",
      "style": "practical",
      "key_phrases": ["small steps", "consistency", "progress over perfection"]
    },
    "target_audience": "busy professionals"
  },
  "content_requirements": {
    "length": "medium",
    "format": "structured_tip",
    "include_actionable_steps": true,
    "include_examples": true
  },
  "knowledge_context": {
    "reference_documents": ["morning_routine_guide.pdf"],
    "key_concepts": ["habit stacking", "implementation intentions"]
  }
}
```

**Response:**
```json
{
  "generated_content": {
    "title": "Building a Sustainable Morning Routine: Small Steps, Big Impact",
    "content": "Creating a morning routine doesn't have to be overwhelming. The key is starting small and building consistency over perfection.\n\n**The Foundation Approach:**\n1. Start with just ONE habit (5 minutes max)\n2. Stack it onto something you already do\n3. Celebrate the small win\n\n**Example for Busy Professionals:**\n- After I pour my coffee (existing habit)\n- I will write down 3 priorities for the day (new habit)\n- Then I'll take a moment to appreciate this small step (reward)\n\n**Remember:** Progress over perfection. Even 5 minutes of intentional morning time can transform your entire day.",
    "metadata": {
      "word_count": 127,
      "reading_time_minutes": 1,
      "key_concepts_used": ["habit stacking", "small wins"],
      "brand_voice_score": 0.94
    }
  },
  "generation_metadata": {
    "model_used": "llama3:8b",
    "generation_time_ms": 2100,
    "tokens_generated": 156,
    "knowledge_sources_used": 2,
    "creativity_score": 0.78
  },
  "quality_assessment": {
    "overall_quality": 0.91,
    "relevance_score": 0.93,
    "actionability_score": 0.89,
    "brand_consistency": 0.94,
    "engagement_potential": 0.87
  }
}
```

### Improve Content
```http
POST /api/v1/ai/content/improve
Content-Type: application/json

{
  "original_content": "Morning routines are important. You should wake up early and do things.",
  "improvement_goals": [
    "make_more_engaging",
    "add_specific_examples",
    "improve_structure",
    "match_brand_voice"
  ],
  "creator_context": {
    "brand_voice": {
      "tone": "encouraging",
      "style": "practical"
    }
  },
  "target_length": "expand"
}
```

**Response:**
```json
{
  "improved_content": {
    "content": "Transform Your Mornings, Transform Your Day\n\nA well-crafted morning routine isn't just about waking up early—it's about creating intentional moments that set you up for success...",
    "improvements_made": [
      "Added engaging headline",
      "Included specific examples",
      "Improved structure with clear sections",
      "Enhanced tone to match brand voice",
      "Expanded content with actionable advice"
    ]
  },
  "improvement_analysis": {
    "original_quality_score": 0.45,
    "improved_quality_score": 0.87,
    "key_enhancements": [
      "Engagement increased by 85%",
      "Actionability improved significantly",
      "Brand voice alignment achieved"
    ]
  }
}
```

## User Profiling API

### Update User Profile
```http
POST /api/v1/ai/profiling/update
Content-Type: application/json

{
  "user_id": "uuid",
  "interaction_data": {
    "message_content": "I've been struggling with consistency in my workouts",
    "interaction_type": "message_sent",
    "channel": "web",
    "timestamp": "2024-01-01T10:00:00Z",
    "response_time_seconds": 45,
    "engagement_indicators": {
      "message_length": 52,
      "question_asked": true,
      "emotional_tone": "frustrated"
    }
  },
  "conversation_context": {
    "conversation_id": "uuid",
    "message_count": 15,
    "conversation_duration_minutes": 25
  },
  "behavioral_signals": {
    "time_of_interaction": "morning",
    "device_type": "mobile",
    "session_duration_minutes": 8
  }
}
```

**Response:**
```json
{
  "profile_updates": {
    "user_id": "uuid",
    "updated_attributes": {
      "current_challenges": ["consistency", "motivation"],
      "communication_patterns": {
        "preferred_time": "morning",
        "typical_message_length": "medium",
        "emotional_expression": "open"
      },
      "engagement_score": 0.78,
      "motivation_level": 0.65,
      "progress_indicators": {
        "workout_consistency": "struggling",
        "goal_clarity": "high"
      }
    },
    "confidence_scores": {
      "challenges_identification": 0.89,
      "communication_style": 0.76,
      "engagement_level": 0.82
    }
  },
  "recommendations": {
    "communication_adjustments": [
      "Use more encouraging tone",
      "Provide specific, actionable steps",
      "Check in more frequently about consistency"
    ],
    "content_suggestions": [
      "Share consistency strategies",
      "Provide accountability tools",
      "Offer flexible workout options"
    ],
    "proactive_triggers": [
      "Send motivation boost if no activity for 2 days",
      "Offer workout alternatives during busy periods"
    ]
  }
}
```

### Get User Profile
```http
GET /api/v1/ai/profiling/users/{user_id}
Query Parameters:
  - include_history: boolean (default: false)
  - include_predictions: boolean (default: true)
```

**Response:**
```json
{
  "user_id": "uuid",
  "profile": {
    "goals": ["lose weight", "build consistency"],
    "current_challenges": ["motivation", "time management"],
    "preferences": {
      "communication_style": "encouraging",
      "content_format": "structured",
      "interaction_frequency": "daily"
    },
    "behavioral_patterns": {
      "most_active_time": "morning",
      "typical_session_length": "5-10 minutes",
      "preferred_channel": "mobile",
      "response_style": "detailed"
    },
    "progress_indicators": {
      "engagement_score": 0.78,
      "motivation_level": 0.65,
      "goal_progress": 0.45,
      "consistency_score": 0.52
    },
    "learning_style": {
      "prefers_examples": true,
      "responds_to_encouragement": true,
      "needs_structure": true
    }
  },
  "predictions": {
    "abandonment_risk": 0.25,
    "success_probability": 0.75,
    "optimal_intervention_time": "2024-01-02T09:00:00Z",
    "recommended_program_adjustments": [
      "Reduce workout frequency to build consistency",
      "Add more check-in points",
      "Provide flexible alternatives"
    ]
  },
  "profile_metadata": {
    "last_updated": "2024-01-01T10:00:00Z",
    "data_points_used": 45,
    "confidence_score": 0.83,
    "profile_completeness": 0.78
  }
}
```

## Proactive Engagement API

### Evaluate Proactive Triggers
```http
POST /api/v1/ai/proactive/evaluate
Content-Type: application/json

{
  "user_id": "uuid",
  "creator_id": "uuid",
  "evaluation_context": {
    "current_time": "2024-01-01T10:00:00Z",
    "user_timezone": "America/New_York",
    "last_interaction": "2024-01-01T08:00:00Z",
    "recent_activity": {
      "messages_last_24h": 0,
      "program_progress_change": 0.0,
      "engagement_score_change": -0.1
    }
  },
  "trigger_rules": [
    {
      "rule_id": "inactivity_24h",
      "enabled": true
    },
    {
      "rule_id": "progress_stagnation",
      "enabled": true
    },
    {
      "rule_id": "motivation_drop",
      "enabled": true
    }
  ]
}
```

**Response:**
```json
{
  "evaluation_result": {
    "should_trigger": true,
    "triggered_rules": [
      {
        "rule_id": "inactivity_24h",
        "rule_name": "24-Hour Inactivity Check",
        "trigger_confidence": 0.95,
        "trigger_reason": "User has not interacted for 26 hours",
        "priority": "medium"
      },
      {
        "rule_id": "motivation_drop",
        "rule_name": "Motivation Level Drop",
        "trigger_confidence": 0.78,
        "trigger_reason": "Engagement score decreased by 10%",
        "priority": "high"
      }
    ],
    "recommended_action": {
      "action_type": "send_proactive_message",
      "priority": "high",
      "timing": "immediate",
      "message_type": "motivation_boost"
    }
  }
}
```

### Generate Proactive Message
```http
POST /api/v1/ai/proactive/generate-message
Content-Type: application/json

{
  "user_id": "uuid",
  "creator_id": "uuid",
  "trigger_context": {
    "trigger_type": "inactivity",
    "trigger_reason": "No interaction for 24 hours",
    "user_last_message": "I'll try to work out tomorrow morning",
    "time_since_last_interaction": "26 hours"
  },
  "user_profile": {
    "goals": ["build exercise habit"],
    "current_challenges": ["consistency"],
    "preferences": {
      "communication_style": "encouraging"
    }
  },
  "message_options": {
    "tone": "supportive",
    "include_question": true,
    "include_suggestion": true,
    "max_length": 200
  }
}
```

**Response:**
```json
{
  "proactive_message": {
    "content": "Hey! I noticed you mentioned wanting to work out yesterday morning. How did that go? 💪\n\nRemember, building a habit is about progress, not perfection. Even if yesterday didn't go as planned, today is a fresh start!\n\nWhat's one small thing you could do today to move toward your fitness goals?",
    "message_type": "motivation_boost",
    "tone_analysis": {
      "supportive": 0.92,
      "encouraging": 0.88,
      "non_judgmental": 0.95
    },
    "engagement_elements": [
      "Personal reference to previous conversation",
      "Encouraging reframe",
      "Open-ended question",
      "Emoji for warmth"
    ]
  },
  "delivery_recommendations": {
    "optimal_time": "2024-01-01T09:00:00Z",
    "channel": "mobile",
    "follow_up_if_no_response": "2024-01-02T09:00:00Z"
  },
  "expected_outcomes": {
    "engagement_probability": 0.73,
    "positive_response_probability": 0.68,
    "goal_progress_impact": 0.15
  }
}
```

## Model Management API

### Get Available Models
```http
GET /api/v1/ai/models
```

**Response:**
```json
{
  "models": [
    {
      "model_id": "llama3:8b",
      "model_name": "Llama 3 8B",
      "capabilities": ["conversation", "content_generation", "analysis"],
      "context_length": 8192,
      "performance_tier": "high",
      "status": "active",
      "load_time_ms": 2000,
      "memory_usage_gb": 6.5
    },
    {
      "model_id": "mistral:7b",
      "model_name": "Mistral 7B",
      "capabilities": ["conversation", "content_generation"],
      "context_length": 4096,
      "performance_tier": "medium",
      "status": "active",
      "load_time_ms": 1500,
      "memory_usage_gb": 4.2
    }
  ],
  "default_model": "llama3:8b",
  "total_memory_usage_gb": 10.7
}
```

### Switch Model
```http
POST /api/v1/ai/models/switch
Content-Type: application/json

{
  "target_model": "mistral:7b",
  "switch_reason": "performance_optimization",
  "gradual_switch": true
}
```

**Response:**
```json
{
  "switch_id": "uuid",
  "status": "in_progress",
  "current_model": "llama3:8b",
  "target_model": "mistral:7b",
  "estimated_completion": "2024-01-01T00:02:00Z",
  "switch_strategy": "gradual",
  "progress": {
    "percentage": 25,
    "current_step": "loading_target_model"
  }
}
```

## Error Handling

### AI-Specific Error Codes
- `MODEL_UNAVAILABLE` (503): AI model is not available
- `GENERATION_FAILED` (500): Content generation failed
- `CONTEXT_TOO_LONG` (413): Input context exceeds model limits
- `UNSAFE_CONTENT` (422): Content flagged by safety filters
- `KNOWLEDGE_BASE_NOT_FOUND` (404): Specified knowledge base doesn't exist
- `EMBEDDING_FAILED` (500): Failed to generate embeddings

### Error Response Example
```json
{
  "error": {
    "code": "GENERATION_FAILED",
    "message": "AI model failed to generate response",
    "details": {
      "model_used": "llama3:8b",
      "failure_reason": "context_length_exceeded",
      "suggested_action": "reduce_input_length"
    },
    "request_id": "uuid",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```