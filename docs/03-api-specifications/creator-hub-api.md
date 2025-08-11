# Creator Hub API Specification

## Overview

The Creator Hub API provides comprehensive endpoints for creators to manage their coaching platform, including knowledge bases, program creation, user management, analytics, and channel configuration. All endpoints require authentication and follow RESTful principles.

## Authentication

### Bearer Token Authentication
```http
Authorization: Bearer <jwt_token>
```

### Token Refresh
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 900
}
```

## Knowledge Management API

### Upload Document
```http
POST /api/v1/knowledge-bases/{knowledge_base_id}/documents
Content-Type: multipart/form-data

file: <file>
title: string (optional)
metadata: json (optional)
```

**Response:**
```json
{
  "id": "uuid",
  "title": "string",
  "file_type": "string",
  "file_size_bytes": 1024,
  "processing_status": "pending",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### List Documents
```http
GET /api/v1/knowledge-bases/{knowledge_base_id}/documents
Query Parameters:
  - page: integer (default: 1)
  - limit: integer (default: 20, max: 100)
  - status: string (pending|processing|completed|failed)
  - search: string
```

**Response:**
```json
{
  "documents": [
    {
      "id": "uuid",
      "title": "string",
      "file_type": "string",
      "file_size_bytes": 1024,
      "processing_status": "completed",
      "created_at": "2024-01-01T00:00:00Z",
      "chunk_count": 15
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "pages": 5
  }
}
```

### Get Document Details
```http
GET /api/v1/knowledge-bases/{knowledge_base_id}/documents/{document_id}
```

**Response:**
```json
{
  "id": "uuid",
  "title": "string",
  "content": "string",
  "file_type": "string",
  "file_size_bytes": 1024,
  "processing_status": "completed",
  "metadata": {},
  "created_at": "2024-01-01T00:00:00Z",
  "processed_at": "2024-01-01T00:05:00Z",
  "chunk_count": 15,
  "chunks": [
    {
      "id": "uuid",
      "chunk_index": 0,
      "content": "string",
      "metadata": {}
    }
  ]
}
```

### Update Document
```http
PUT /api/v1/knowledge-bases/{knowledge_base_id}/documents/{document_id}
Content-Type: application/json

{
  "title": "string",
  "metadata": {}
}
```

### Delete Document
```http
DELETE /api/v1/knowledge-bases/{knowledge_base_id}/documents/{document_id}
```

**Response:**
```json
{
  "message": "Document deleted successfully"
}
```

### Create Knowledge Base
```http
POST /api/v1/knowledge-bases
Content-Type: application/json

{
  "name": "string",
  "description": "string",
  "settings": {
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "embedding_model": "nomic-embed-text"
  }
}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "settings": {},
  "created_at": "2024-01-01T00:00:00Z",
  "document_count": 0,
  "total_size_bytes": 0
}
```

## Program Builder API

### Create Program
```http
POST /api/v1/programs
Content-Type: application/json

{
  "name": "string",
  "description": "string",
  "flow_definition": {
    "nodes": [
      {
        "id": "start",
        "type": "start",
        "position": {"x": 0, "y": 0},
        "data": {}
      },
      {
        "id": "message_1",
        "type": "send_message",
        "position": {"x": 200, "y": 0},
        "data": {
          "message": "Welcome to the program!",
          "delay_hours": 0
        }
      }
    ],
    "edges": [
      {
        "id": "e1",
        "source": "start",
        "target": "message_1"
      }
    ]
  },
  "settings": {
    "auto_enroll": false,
    "completion_badge": "uuid"
  }
}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "flow_definition": {},
  "status": "draft",
  "version": 1,
  "settings": {},
  "created_at": "2024-01-01T00:00:00Z",
  "enrollment_count": 0
}
```

### List Programs
```http
GET /api/v1/programs
Query Parameters:
  - page: integer (default: 1)
  - limit: integer (default: 20)
  - status: string (draft|published|archived)
  - search: string
```

**Response:**
```json
{
  "programs": [
    {
      "id": "uuid",
      "name": "string",
      "description": "string",
      "status": "published",
      "version": 1,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "enrollment_count": 25,
      "completion_rate": 0.8
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 10,
    "pages": 1
  }
}
```

### Get Program Details
```http
GET /api/v1/programs/{program_id}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "flow_definition": {
    "nodes": [],
    "edges": []
  },
  "status": "published",
  "version": 1,
  "settings": {},
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "published_at": "2024-01-01T01:00:00Z",
  "enrollment_count": 25,
  "completion_rate": 0.8,
  "analytics": {
    "total_enrollments": 25,
    "active_enrollments": 20,
    "completed_enrollments": 20,
    "average_completion_time_days": 14,
    "engagement_score": 0.85
  }
}
```

### Update Program
```http
PUT /api/v1/programs/{program_id}
Content-Type: application/json

{
  "name": "string",
  "description": "string",
  "flow_definition": {},
  "settings": {}
}
```

### Publish Program
```http
POST /api/v1/programs/{program_id}/publish
```

**Response:**
```json
{
  "id": "uuid",
  "status": "published",
  "published_at": "2024-01-01T00:00:00Z",
  "version": 2
}
```

### Archive Program
```http
POST /api/v1/programs/{program_id}/archive
```

## User Management API

### List Users
```http
GET /api/v1/users
Query Parameters:
  - page: integer (default: 1)
  - limit: integer (default: 20)
  - channel: string (web|whatsapp|telegram|mobile)
  - status: string (active|inactive)
  - search: string
  - sort: string (created_at|last_active_at|engagement_score)
  - order: string (asc|desc)
```

**Response:**
```json
{
  "users": [
    {
      "id": "uuid",
      "external_id": "string",
      "channel": "web",
      "profile_data": {
        "name": "John Doe",
        "goals": ["lose weight", "build habits"]
      },
      "created_at": "2024-01-01T00:00:00Z",
      "last_active_at": "2024-01-02T00:00:00Z",
      "is_active": true,
      "engagement_score": 0.75,
      "program_enrollments": 2,
      "total_interactions": 45
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8
  }
}
```

### Get User Details
```http
GET /api/v1/users/{user_id}
```

**Response:**
```json
{
  "id": "uuid",
  "external_id": "string",
  "channel": "web",
  "profile_data": {
    "name": "John Doe",
    "goals": ["lose weight", "build habits"],
    "preferences": {
      "communication_style": "encouraging",
      "frequency": "daily"
    }
  },
  "created_at": "2024-01-01T00:00:00Z",
  "last_active_at": "2024-01-02T00:00:00Z",
  "is_active": true,
  "timezone": "America/New_York",
  "language": "en",
  "engagement_score": 0.75,
  "program_enrollments": [
    {
      "program_id": "uuid",
      "program_name": "Weight Loss Journey",
      "status": "active",
      "progress": 0.6,
      "enrolled_at": "2024-01-01T00:00:00Z"
    }
  ],
  "recent_interactions": [
    {
      "id": "uuid",
      "interaction_type": "message_sent",
      "created_at": "2024-01-02T00:00:00Z",
      "channel": "web"
    }
  ],
  "badges_earned": [
    {
      "badge_id": "uuid",
      "badge_name": "First Week Complete",
      "earned_at": "2024-01-07T00:00:00Z"
    }
  ]
}
```

### Update User Profile
```http
PUT /api/v1/users/{user_id}
Content-Type: application/json

{
  "profile_data": {
    "name": "John Doe",
    "goals": ["lose weight", "build habits"],
    "preferences": {
      "communication_style": "encouraging",
      "frequency": "daily"
    }
  },
  "timezone": "America/New_York",
  "language": "en"
}
```

### Enroll User in Program
```http
POST /api/v1/users/{user_id}/programs/{program_id}/enroll
```

**Response:**
```json
{
  "enrollment_id": "uuid",
  "program_id": "uuid",
  "user_id": "uuid",
  "status": "active",
  "enrolled_at": "2024-01-01T00:00:00Z"
}
```

## Channel Management API

### List Channels
```http
GET /api/v1/channels
```

**Response:**
```json
{
  "channels": [
    {
      "id": "uuid",
      "channel_type": "web",
      "channel_name": "Website Widget",
      "status": "active",
      "configuration": {
        "widget_color": "#007bff",
        "welcome_message": "Hello! How can I help you today?"
      },
      "created_at": "2024-01-01T00:00:00Z",
      "user_count": 50,
      "last_activity_at": "2024-01-02T00:00:00Z"
    }
  ]
}
```

### Create Channel
```http
POST /api/v1/channels
Content-Type: application/json

{
  "channel_type": "whatsapp",
  "channel_name": "WhatsApp Business",
  "configuration": {
    "phone_number": "+1234567890",
    "business_account_id": "string",
    "access_token": "string",
    "webhook_verify_token": "string"
  }
}
```

**Response:**
```json
{
  "id": "uuid",
  "channel_type": "whatsapp",
  "channel_name": "WhatsApp Business",
  "status": "pending_verification",
  "configuration": {
    "phone_number": "+1234567890",
    "webhook_url": "https://api.platform.com/webhooks/whatsapp/{channel_id}"
  },
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Update Channel Configuration
```http
PUT /api/v1/channels/{channel_id}
Content-Type: application/json

{
  "channel_name": "Updated Channel Name",
  "configuration": {
    "widget_color": "#28a745",
    "welcome_message": "Welcome! I'm here to help with your coaching journey."
  }
}
```

### Get Channel Analytics
```http
GET /api/v1/channels/{channel_id}/analytics
Query Parameters:
  - start_date: string (YYYY-MM-DD)
  - end_date: string (YYYY-MM-DD)
  - metrics: string (comma-separated: messages,users,engagement)
```

**Response:**
```json
{
  "channel_id": "uuid",
  "date_range": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  },
  "metrics": {
    "total_messages": 1250,
    "unique_users": 75,
    "new_users": 25,
    "average_response_time_seconds": 2.5,
    "user_satisfaction_score": 4.2,
    "engagement_rate": 0.68
  },
  "daily_breakdown": [
    {
      "date": "2024-01-01",
      "messages": 45,
      "users": 12,
      "new_users": 3
    }
  ]
}
```

## Analytics and Reporting API

### Get Dashboard Overview
```http
GET /api/v1/analytics/overview
Query Parameters:
  - period: string (7d|30d|90d|1y)
```

**Response:**
```json
{
  "period": "30d",
  "summary": {
    "total_users": 150,
    "new_users": 25,
    "active_users": 120,
    "total_interactions": 2500,
    "ai_interactions": 2000,
    "human_escalations": 50,
    "average_engagement_score": 0.72,
    "program_completions": 18
  },
  "trends": {
    "user_growth_rate": 0.15,
    "engagement_trend": "increasing",
    "satisfaction_trend": "stable"
  },
  "top_programs": [
    {
      "program_id": "uuid",
      "program_name": "Weight Loss Journey",
      "enrollments": 45,
      "completion_rate": 0.8
    }
  ]
}
```

### Get Detailed Analytics
```http
GET /api/v1/analytics/detailed
Query Parameters:
  - metric: string (users|interactions|programs|channels)
  - start_date: string (YYYY-MM-DD)
  - end_date: string (YYYY-MM-DD)
  - granularity: string (day|week|month)
  - segment: string (channel|program|user_type)
```

**Response:**
```json
{
  "metric": "interactions",
  "date_range": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  },
  "granularity": "day",
  "data": [
    {
      "date": "2024-01-01",
      "value": 85,
      "segments": {
        "web": 45,
        "whatsapp": 25,
        "telegram": 15
      }
    }
  ],
  "totals": {
    "total_value": 2500,
    "average_daily": 80.6,
    "peak_value": 125,
    "peak_date": "2024-01-15"
  }
}
```

### Export Analytics Data
```http
POST /api/v1/analytics/export
Content-Type: application/json

{
  "metrics": ["users", "interactions", "programs"],
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "format": "csv",
  "email": "creator@example.com"
}
```

**Response:**
```json
{
  "export_id": "uuid",
  "status": "processing",
  "estimated_completion": "2024-01-01T00:05:00Z"
}
```

## Proactive Engine API

### Configure Proactive Rules
```http
POST /api/v1/proactive-engine/rules
Content-Type: application/json

{
  "name": "Inactivity Follow-up",
  "description": "Send follow-up message after 24 hours of inactivity",
  "trigger_conditions": {
    "type": "inactivity",
    "threshold_hours": 24,
    "applies_to": "all_users"
  },
  "actions": [
    {
      "type": "send_message",
      "message_template": "Hey {user_name}! I noticed you haven't checked in today. How are you doing with your goals?",
      "delay_minutes": 0
    }
  ],
  "is_active": true
}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "Inactivity Follow-up",
  "description": "Send follow-up message after 24 hours of inactivity",
  "trigger_conditions": {},
  "actions": [],
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "triggered_count": 0
}
```

### List Proactive Rules
```http
GET /api/v1/proactive-engine/rules
```

**Response:**
```json
{
  "rules": [
    {
      "id": "uuid",
      "name": "Inactivity Follow-up",
      "description": "Send follow-up message after 24 hours of inactivity",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z",
      "triggered_count": 25,
      "success_rate": 0.8
    }
  ]
}
```

### Get Proactive Engine Analytics
```http
GET /api/v1/proactive-engine/analytics
Query Parameters:
  - start_date: string (YYYY-MM-DD)
  - end_date: string (YYYY-MM-DD)
```

**Response:**
```json
{
  "date_range": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  },
  "summary": {
    "total_triggers": 150,
    "successful_engagements": 120,
    "success_rate": 0.8,
    "average_response_time_hours": 2.5
  },
  "rule_performance": [
    {
      "rule_id": "uuid",
      "rule_name": "Inactivity Follow-up",
      "triggers": 50,
      "successes": 40,
      "success_rate": 0.8
    }
  ]
}
```

## Error Handling

### Standard Error Response Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid data",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ],
    "request_id": "uuid"
  }
}
```

### Common Error Codes
- `AUTHENTICATION_REQUIRED` (401): Missing or invalid authentication
- `INSUFFICIENT_PERMISSIONS` (403): User lacks required permissions
- `RESOURCE_NOT_FOUND` (404): Requested resource doesn't exist
- `VALIDATION_ERROR` (422): Request data validation failed
- `RATE_LIMIT_EXCEEDED` (429): Too many requests
- `INTERNAL_SERVER_ERROR` (500): Unexpected server error

## Rate Limits

### Default Rate Limits
- **General API calls**: 1000 requests per hour per creator
- **AI interactions**: 100 requests per hour per creator
- **File uploads**: 50 uploads per hour per creator
- **Analytics exports**: 10 exports per day per creator

### Rate Limit Headers
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## Webhooks

### Webhook Events
- `user.created`: New user registered
- `user.updated`: User profile updated
- `program.enrolled`: User enrolled in program
- `program.completed`: User completed program
- `message.received`: New message from user
- `escalation.created`: Human escalation triggered

### Webhook Payload Example
```json
{
  "event": "user.created",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "user_id": "uuid",
    "channel": "web",
    "profile_data": {
      "name": "John Doe"
    }
  },
  "creator_id": "uuid"
}
```