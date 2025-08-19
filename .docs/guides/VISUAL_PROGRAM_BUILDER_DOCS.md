# Visual Program Builder Documentation

**PHASE 3: Visual Program Builder** - Complete modular backend system for creating automated coaching program flows.

## 🎯 Overview

The Visual Program Builder enables creators to design automated coaching programs without code through a comprehensive backend API. It integrates seamlessly with Phase 1 (AI Engine/Knowledge) and Phase 2 (Personality System) to create intelligent, personalized coaching experiences.

## 🏗️ Architecture

### Core Components

```
📦 Visual Program Builder (Phase 3)
├── 🎯 program_models.py          # Core models and enums
├── 📋 step_models.py             # Modular step configuration  
├── ⚙️ program_engine.py          # Handler registration system
├── 🔄 step_processor.py          # Phase 1 & 2 integrations
├── 🧮 condition_evaluator.py     # Complex logic flows
├── 📊 debug_analytics.py         # Debugging and analytics
└── 🌐 routers/programs.py        # REST API endpoints
```

### Integration Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PHASE 1       │    │   PHASE 2       │    │   PHASE 3       │
│ AI Engine/      │◄──►│ Personality     │◄──►│ Visual Program  │
│ Knowledge       │    │ System          │    │ Builder         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Creator Hub Service                          │
│                      (Port 8002)                               │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Key Features

### 1. **Modular Program Definition**
- **ProgramDefinition**: Core program structure with configurations
- **ExecutionStrategy**: Sequential, parallel, or conditional execution
- **Multi-tenant isolation** with creator-based access control

### 2. **Flexible Step System**
- **StepType**: MESSAGE, TASK, SURVEY, WAIT, CONDITION, TRIGGER
- **TriggerConfig**: Time-based, event-based, condition-based triggers
- **ActionConfig**: Send message, assign task, collect input, branch flow

### 3. **Advanced Condition Logic**
- **Expression Parser**: Complex boolean expressions with variables
- **Built-in Functions**: COUNT(), SUM(), AVG(), NOW(), DAYS_AGO()
- **Custom Operators**: Standard comparison and logical operators

### 4. **Comprehensive Analytics**
- **ExecutionAnalytics**: Performance metrics and success rates
- **UserJourneyAnalytics**: Engagement and completion tracking
- **PersonalityAnalytics**: Consistency monitoring
- **Real-time Insights**: Automated recommendations

### 5. **Debugging System**
- **Debug Sessions**: Step-by-step execution tracing
- **Event Logging**: Comprehensive execution logs
- **Performance Monitoring**: Bottleneck detection
- **Error Tracking**: Detailed error analysis

## 📡 API Reference

### Program Management

#### Create Program
```http
POST /api/v1/creators/programs/
Content-Type: multipart/form-data

title=My Coaching Program
description=A comprehensive wellness program
execution_strategy=SEQUENTIAL
enable_personality=true
enable_analytics=true
```

#### List Programs
```http
GET /api/v1/creators/programs/?status_filter=PUBLISHED&page=1&page_size=20
```

#### Get Program Details
```http
GET /api/v1/creators/programs/{program_id}
```

### Step Management

#### Add Step to Program
```http
POST /api/v1/creators/programs/{program_id}/steps
Content-Type: multipart/form-data

step_type=MESSAGE
step_name=Welcome Message
step_description=Send welcome message to user
trigger_type=TIME_BASED
action_type=SEND_MESSAGE
trigger_config_json={"schedule": "daily", "time": "09:00"}
action_config_json={"message_template": "Good morning! Ready for today's session?"}
order_index=1
```

#### List Program Steps
```http
GET /api/v1/creators/programs/{program_id}/steps
```

### Program Execution

#### Execute Program
```http
POST /api/v1/creators/programs/{program_id}/execute
Content-Type: multipart/form-data

user_context=User wants to improve wellness habits
simulation_mode=false
debug_mode=true
```

#### Get Execution History
```http
GET /api/v1/creators/programs/{program_id}/executions?page=1&page_size=20
```

### Validation & Testing

#### Validate Program
```http
POST /api/v1/creators/programs/{program_id}/validate
Content-Type: multipart/form-data

comprehensive=true
```

#### Test Conditions
```http
POST /api/v1/creators/programs/{program_id}/test-conditions
Content-Type: application/json

{
  "test_expressions": [
    {
      "expression": "user_completed_steps >= 5",
      "expected_result": true,
      "description": "User has completed at least 5 steps"
    }
  ],
  "variables": {"user_completed_steps": 7},
  "user_variables": {"engagement_score": 0.8}
}
```

### Analytics & Insights

#### Get Program Analytics
```http
GET /api/v1/creators/programs/{program_id}/analytics?time_range_days=30&analytics_type=execution
```

#### Generate Insights
```http
POST /api/v1/creators/programs/{program_id}/insights
Content-Type: multipart/form-data

time_range_days=30
```

### Debugging

#### List Debug Sessions
```http
GET /api/v1/creators/programs/{program_id}/debug/sessions
```

#### Get Debug Session Details
```http
GET /api/v1/creators/programs/{program_id}/debug/sessions/{session_id}
```

## 🔧 Integration Guide

### Phase 1 Integration (AI Engine/Knowledge)

The Visual Program Builder integrates with the Knowledge Service for:

1. **Content Enhancement**: Steps can reference creator's knowledge base
2. **Context Retrieval**: Dynamic content based on user queries
3. **Document Processing**: Automated content generation from uploaded materials

```python
# Example: Step with knowledge context
{
  "step_type": "MESSAGE",
  "action_config": {
    "action_type": "SEND_MESSAGE",
    "use_knowledge_context": true,
    "context_query": "wellness tips",
    "message_template": "Based on your materials: {knowledge_context}"
  }
}
```

### Phase 2 Integration (Personality System)

The Visual Program Builder integrates with the Personality System for:

1. **Personalized Content**: Messages adapted to creator's coaching style
2. **Consistency Monitoring**: Ensures AI responses match creator personality
3. **Dynamic Prompts**: Context-aware prompt generation

```python
# Example: Step with personality enhancement
{
  "step_type": "MESSAGE", 
  "personality_config": {
    "enhance_content": true,
    "enforce_consistency": true,
    "adaptation_level": "high"
  },
  "action_config": {
    "action_type": "SEND_MESSAGE",
    "use_personality": true,
    "message_template": "Let's work on {topic} together!"
  }
}
```

### Full Integration Example

```python
# Complete step with all integrations
{
  "step_id": "step_001",
  "step_type": "MESSAGE",
  "trigger_config": {
    "trigger_type": "CONDITION_BASED",
    "condition_expression": "user_engagement_score >= 0.7"
  },
  "action_config": {
    "action_type": "SEND_MESSAGE",
    "use_knowledge_context": true,
    "use_personality": true,
    "context_query": "motivation techniques",
    "message_template": "Great progress! Here's a personalized tip: {knowledge_context}"
  },
  "personality_config": {
    "enhance_content": true,
    "enforce_consistency": true
  }
}
```

## 📊 Data Models

### Core Models

#### ProgramDefinition
```python
{
  "program_id": "prog_123",
  "creator_id": "creator_456", 
  "title": "Wellness Journey",
  "description": "Complete wellness transformation program",
  "version": "1.0",
  "status": "PUBLISHED",
  "personality_config": {
    "enabled": true,
    "enhance_content": true,
    "enforce_consistency": true
  },
  "execution_config": {
    "strategy": "SEQUENTIAL",
    "parallel_limit": 3,
    "timeout_seconds": 300
  },
  "analytics_config": {
    "enabled": true,
    "track_performance": true,
    "real_time_insights": true
  },
  "steps": [...],
  "created_at": "2025-01-17T10:00:00Z",
  "updated_at": "2025-01-17T10:00:00Z"
}
```

#### ProgramStep
```python
{
  "step_id": "step_001",
  "program_id": "prog_123",
  "step_type": "MESSAGE",
  "name": "Daily Check-in",
  "description": "Send daily motivation message",
  "order_index": 1,
  "trigger_config": {
    "trigger_type": "TIME_BASED",
    "schedule": "daily",
    "time": "08:00"
  },
  "action_config": {
    "action_type": "SEND_MESSAGE",
    "message_template": "How are you feeling today?",
    "response_required": true
  },
  "conditional_config": {
    "condition_expression": "user_active_streak >= 3",
    "true_next_steps": ["step_002"],
    "false_next_steps": ["step_003"]
  },
  "enabled": true
}
```

## 🔍 Debugging & Analytics

### Debug Session Structure
```python
{
  "session_id": "debug_creator_456_prog_123_20250117_100000",
  "program_id": "prog_123", 
  "creator_id": "creator_456",
  "started_at": "2025-01-17T10:00:00Z",
  "completed_at": "2025-01-17T10:05:00Z",
  "status": "completed",
  "total_events": 25,
  "error_count": 0,
  "warning_count": 2,
  "events": [
    {
      "event_id": "event_001",
      "timestamp": "2025-01-17T10:00:01Z",
      "event_type": "step_execution",
      "event_name": "step_started",
      "severity": "info",
      "data": {"step_id": "step_001", "step_type": "MESSAGE"}
    }
  ],
  "metrics": [
    {
      "metric_name": "execution_time",
      "metric_value": 1.5,
      "unit": "seconds",
      "timestamp": "2025-01-17T10:00:01Z"
    }
  ]
}
```

### Analytics Summary
```python
{
  "program_id": "prog_123",
  "time_range": {
    "start_date": "2025-01-01T00:00:00Z",
    "end_date": "2025-01-17T23:59:59Z"
  },
  "analytics": {
    "execution": {
      "total_executions": 45,
      "successful_executions": 42,
      "success_percentage": 93.3,
      "average_execution_time_seconds": 2.1
    },
    "performance": {
      "average_response_time_ms": 150,
      "max_response_time_ms": 500,
      "min_response_time_ms": 50
    },
    "user_journey": {
      "average_engagement_score": 0.82,
      "total_unique_users": 28,
      "completion_rate": 0.76
    }
  },
  "insights": [
    {
      "type": "performance_optimization",
      "title": "Optimize Step 3 Response Time",
      "description": "Step 3 shows 40% higher response time",
      "recommendation": "Review message complexity and add caching"
    }
  ]
}
```

## 🛠️ Development Patterns

### Creating a Custom Step Handler

```python
from .program_engine import StepHandler
from .step_models import ProgramStep

class CustomStepHandler(StepHandler):
    async def execute(self, step: ProgramStep, context: ExecutionContext, debug: StepDebugSession):
        # Custom step logic here
        debug.log_milestone("custom_step_started")
        
        # Integrate with Phase 1 (Knowledge)
        if step.action_config.use_knowledge_context:
            knowledge_context = await self.get_knowledge_context(
                context.creator_id, 
                step.action_config.context_query
            )
            
        # Integrate with Phase 2 (Personality)
        if step.action_config.use_personality:
            personalized_content = await self.enhance_with_personality(
                context.creator_id,
                step.action_config.message_template,
                knowledge_context
            )
        
        return StepExecutionResult(
            step_id=step.step_id,
            success=True,
            output_data={"message": personalized_content}
        )

# Register handler
program_engine = get_program_engine()
program_engine.register_step_handler(StepType.CUSTOM, CustomStepHandler())
```

### Adding Custom Condition Functions

```python
from .condition_evaluator import BuiltinFunction

class CustomFunction(BuiltinFunction):
    async def execute(self, args: List[Any], context: ConditionContext) -> Any:
        # Custom function logic
        return result
    
    def get_function_name(self) -> str:
        return "CUSTOM_FUNCTION"

# Register function
condition_evaluator = get_condition_evaluator()
condition_evaluator.register_function(CustomFunction())
```

## 🚀 Quick Start

### 1. Create a Simple Program

```python
# Create program
program_data = {
    "title": "Daily Wellness Check",
    "description": "Simple daily check-in program",
    "execution_strategy": "SEQUENTIAL",
    "enable_personality": True,
    "enable_analytics": True
}

response = requests.post("/api/v1/creators/programs/", data=program_data)
program = response.json()
```

### 2. Add Steps

```python
# Add welcome step
step_data = {
    "step_type": "MESSAGE",
    "step_name": "Welcome",
    "step_description": "Welcome message",
    "trigger_type": "IMMEDIATE",
    "action_type": "SEND_MESSAGE",
    "trigger_config_json": '{"immediate": true}',
    "action_config_json": '{"message_template": "Welcome to your wellness journey!"}'
}

response = requests.post(f"/api/v1/creators/programs/{program['program_id']}/steps", data=step_data)
```

### 3. Execute Program

```python
# Execute for a user
execution_data = {
    "user_context": "User wants to start wellness journey",
    "simulation_mode": False,
    "debug_mode": True
}

response = requests.post(f"/api/v1/creators/programs/{program['program_id']}/execute", data=execution_data)
result = response.json()
```

## 📈 Performance & Scalability

### Optimizations Implemented

1. **Async Processing**: All I/O operations use async/await
2. **Caching**: Condition evaluation results cached by default
3. **Parallel Execution**: Limited parallelism for step execution
4. **Modular Storage**: Multiple storage backends for different data types
5. **Connection Pooling**: Efficient database connection management

### Monitoring

- **Execution Times**: Track step and program execution performance
- **Success Rates**: Monitor program completion and step success
- **User Engagement**: Track user interaction and satisfaction
- **Resource Usage**: Monitor memory and CPU usage during execution

## 🔒 Security

### Multi-Tenant Isolation
- All operations require `creator_id` authentication
- Database queries use Row Level Security (RLS)
- API endpoints validate creator ownership

### Input Validation
- Pydantic models for all request/response validation
- SQL injection prevention through parameterized queries
- File upload size and type restrictions

### Access Control
- JWT-based authentication required for all endpoints
- Creator-specific resource access only
- Debug sessions isolated by creator

## 🧪 Testing

### Test a Program Flow
```python
# Test program conditions
test_data = {
    "test_expressions": [
        {
            "expression": "user_completed_steps >= 3 AND engagement_score > 0.7",
            "expected_result": True,
            "description": "User is engaged and progressing"
        }
    ],
    "variables": {"user_completed_steps": 5, "engagement_score": 0.8}
}

response = requests.post(f"/api/v1/creators/programs/{program_id}/test-conditions", json=test_data)
```

### Validate Program Structure
```python
response = requests.post(f"/api/v1/creators/programs/{program_id}/validate", data={"comprehensive": True})
validation = response.json()
```

## 📝 Next Steps

1. **Database Implementation**: Replace mock methods with actual database operations
2. **Real-time Notifications**: Implement WebSocket for live updates
3. **Visual Interface**: Create drag-and-drop program builder UI
4. **Advanced Analytics**: ML-based insights and recommendations
5. **Integration Testing**: End-to-end testing with Phase 1 & 2

---

*For complete API documentation, see the `/docs` endpoint when running the Creator Hub Service.*