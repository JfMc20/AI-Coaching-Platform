# Channel APIs Specification

## Overview

The Channel APIs handle user-facing interactions across multiple communication channels including web widget, WhatsApp, Telegram, and mobile app. Each channel has specific requirements and capabilities while maintaining a unified user experience.

## Common Channel Patterns

### Message Format
All channels use a standardized internal message format:

```json
{
  "message_id": "uuid",
  "conversation_id": "uuid",
  "user_id": "uuid",
  "channel": "web|whatsapp|telegram|mobile",
  "message_type": "text|image|audio|video|file|interactive",
  "content": {
    "text": "string",
    "media_url": "string",
    "media_type": "string",
    "interactive_data": {}
  },
  "metadata": {
    "timestamp": "2024-01-01T00:00:00Z",
    "user_agent": "string",
    "ip_address": "string",
    "channel_specific": {}
  }
}
```

### Authentication
Channel APIs use different authentication methods based on the channel:
- **Web Widget**: Session-based authentication
- **WhatsApp/Telegram**: Webhook verification tokens
- **Mobile App**: JWT tokens with refresh mechanism

## Web Widget API

### Initialize Widget
```http
POST /api/v1/channels/web/initialize
Content-Type: application/json

{
  "creator_id": "uuid",
  "widget_config": {
    "theme": {
      "primary_color": "#007bff",
      "secondary_color": "#6c757d",
      "font_family": "Inter, sans-serif"
    },
    "welcome_message": "Hi! I'm here to help you with your coaching journey. How can I assist you today?",
    "placeholder_text": "Type your message here...",
    "position": "bottom-right",
    "size": "medium"
  },
  "user_context": {
    "page_url": "https://example.com/coaching",
    "referrer": "https://google.com",
    "user_agent": "Mozilla/5.0...",
    "session_id": "uuid"
  }
}
```

**Response:**
```json
{
  "widget_id": "uuid",
  "conversation_id": "uuid",
  "user_id": "uuid",
  "widget_config": {
    "theme": {},
    "welcome_message": "string",
    "features": {
      "file_upload": true,
      "voice_messages": false,
      "typing_indicators": true,
      "read_receipts": true
    }
  },
  "initial_messages": [
    {
      "message_id": "uuid",
      "sender": "assistant",
      "content": {
        "text": "Hi! I'm here to help you with your coaching journey. How can I assist you today?"
      },
      "timestamp": "2024-01-01T00:00:00Z"
    }
  ],
  "websocket_url": "wss://api.platform.com/ws/widget/{widget_id}"
}
```

### Send Message
```http
POST /api/v1/channels/web/messages
Content-Type: application/json

{
  "conversation_id": "uuid",
  "user_id": "uuid",
  "message": {
    "type": "text",
    "content": {
      "text": "I need help with building a morning routine"
    }
  },
  "context": {
    "page_url": "https://example.com/coaching",
    "session_duration": 300
  }
}
```

**Response:**
```json
{
  "message_id": "uuid",
  "status": "sent",
  "timestamp": "2024-01-01T00:00:00Z",
  "ai_response": {
    "message_id": "uuid",
    "content": {
      "text": "I'd love to help you build a sustainable morning routine! What time do you typically wake up, and what are your main goals for your mornings?",
      "suggestions": [
        "I want to exercise in the morning",
        "I need help with productivity",
        "I struggle with consistency"
      ]
    },
    "response_time_ms": 1250,
    "confidence_score": 0.92
  }
}
```

### Upload File
```http
POST /api/v1/channels/web/upload
Content-Type: multipart/form-data

conversation_id: uuid
user_id: uuid
file: <file>
message_text: "Here's my current routine" (optional)
```

**Response:**
```json
{
  "upload_id": "uuid",
  "file_url": "https://storage.platform.com/uploads/{file_id}",
  "file_type": "image/jpeg",
  "file_size": 1024000,
  "message_id": "uuid",
  "processing_status": "completed",
  "ai_analysis": {
    "content_type": "routine_schedule",
    "extracted_text": "6:00 AM - Wake up\n6:30 AM - Exercise\n7:30 AM - Breakfast",
    "insights": [
      "Well-structured morning routine",
      "Good balance of activities",
      "Consider adding meditation time"
    ]
  }
}
```

### WebSocket Events
```javascript
// Client-side WebSocket connection
const ws = new WebSocket('wss://api.platform.com/ws/widget/{widget_id}');

// Incoming message event
{
  "event": "message_received",
  "data": {
    "message_id": "uuid",
    "sender": "assistant",
    "content": {
      "text": "That's a great question! Here's what I recommend..."
    },
    "timestamp": "2024-01-01T00:00:00Z"
  }
}

// Typing indicator event
{
  "event": "typing_start",
  "data": {
    "sender": "assistant"
  }
}

// Connection status event
{
  "event": "connection_status",
  "data": {
    "status": "connected",
    "user_id": "uuid",
    "conversation_id": "uuid"
  }
}
```

## WhatsApp Business API

### Webhook Verification
```http
GET /api/v1/channels/whatsapp/webhook
Query Parameters:
  - hub.mode: subscribe
  - hub.challenge: string
  - hub.verify_token: string
```

**Response:**
```
{hub.challenge}
```

### Receive Message Webhook
```http
POST /api/v1/channels/whatsapp/webhook
Content-Type: application/json

{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "business_account_id",
      "changes": [
        {
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "+1234567890",
              "phone_number_id": "phone_number_id"
            },
            "messages": [
              {
                "from": "user_phone_number",
                "id": "message_id",
                "timestamp": "1640995200",
                "text": {
                  "body": "I need help with my fitness goals"
                },
                "type": "text"
              }
            ]
          },
          "field": "messages"
        }
      ]
    }
  ]
}
```

**Response:**
```json
{
  "status": "received",
  "processed_messages": [
    {
      "whatsapp_message_id": "message_id",
      "internal_message_id": "uuid",
      "conversation_id": "uuid",
      "user_id": "uuid",
      "processing_status": "queued"
    }
  ]
}
```

### Send Message
```http
POST /api/v1/channels/whatsapp/messages
Content-Type: application/json

{
  "phone_number_id": "phone_number_id",
  "to": "user_phone_number",
  "message": {
    "type": "text",
    "text": {
      "body": "Great! I'd love to help you with your fitness goals. What specific areas would you like to focus on?",
      "preview_url": false
    }
  },
  "context": {
    "conversation_id": "uuid",
    "user_id": "uuid",
    "creator_id": "uuid"
  }
}
```

**Response:**
```json
{
  "messaging_product": "whatsapp",
  "messages": [
    {
      "id": "whatsapp_message_id",
      "message_status": "sent"
    }
  ],
  "internal_data": {
    "message_id": "uuid",
    "conversation_id": "uuid",
    "sent_at": "2024-01-01T00:00:00Z"
  }
}
```

### Send Interactive Message
```http
POST /api/v1/channels/whatsapp/messages
Content-Type: application/json

{
  "phone_number_id": "phone_number_id",
  "to": "user_phone_number",
  "message": {
    "type": "interactive",
    "interactive": {
      "type": "button",
      "body": {
        "text": "What type of fitness goal interests you most?"
      },
      "action": {
        "buttons": [
          {
            "type": "reply",
            "reply": {
              "id": "weight_loss",
              "title": "Weight Loss"
            }
          },
          {
            "type": "reply",
            "reply": {
              "id": "muscle_building",
              "title": "Muscle Building"
            }
          },
          {
            "type": "reply",
            "reply": {
              "id": "general_fitness",
              "title": "General Fitness"
            }
          }
        ]
      }
    }
  }
}
```

### Send Media Message
```http
POST /api/v1/channels/whatsapp/messages
Content-Type: application/json

{
  "phone_number_id": "phone_number_id",
  "to": "user_phone_number",
  "message": {
    "type": "image",
    "image": {
      "link": "https://storage.platform.com/images/workout_plan.jpg",
      "caption": "Here's a beginner-friendly workout plan to get you started!"
    }
  }
}
```

### Message Status Webhook
```http
POST /api/v1/channels/whatsapp/webhook
Content-Type: application/json

{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "business_account_id",
      "changes": [
        {
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "+1234567890",
              "phone_number_id": "phone_number_id"
            },
            "statuses": [
              {
                "id": "whatsapp_message_id",
                "status": "delivered",
                "timestamp": "1640995260",
                "recipient_id": "user_phone_number"
              }
            ]
          },
          "field": "messages"
        }
      ]
    }
  ]
}
```

## Telegram Bot API

### Set Webhook
```http
POST /api/v1/channels/telegram/webhook/set
Content-Type: application/json

{
  "bot_token": "bot_token",
  "webhook_url": "https://api.platform.com/api/v1/channels/telegram/webhook/{bot_id}",
  "allowed_updates": ["message", "callback_query", "inline_query"]
}
```

**Response:**
```json
{
  "ok": true,
  "result": true,
  "webhook_info": {
    "url": "https://api.platform.com/api/v1/channels/telegram/webhook/{bot_id}",
    "has_custom_certificate": false,
    "pending_update_count": 0,
    "max_connections": 40
  }
}
```

### Receive Update Webhook
```http
POST /api/v1/channels/telegram/webhook/{bot_id}
Content-Type: application/json

{
  "update_id": 123456789,
  "message": {
    "message_id": 1234,
    "from": {
      "id": 987654321,
      "is_bot": false,
      "first_name": "John",
      "last_name": "Doe",
      "username": "johndoe"
    },
    "chat": {
      "id": 987654321,
      "first_name": "John",
      "last_name": "Doe",
      "username": "johndoe",
      "type": "private"
    },
    "date": 1640995200,
    "text": "I want to improve my productivity habits"
  }
}
```

**Response:**
```json
{
  "status": "received",
  "update_id": 123456789,
  "processed_message": {
    "telegram_message_id": 1234,
    "internal_message_id": "uuid",
    "conversation_id": "uuid",
    "user_id": "uuid",
    "processing_status": "queued"
  }
}
```

### Send Message
```http
POST /api/v1/channels/telegram/messages
Content-Type: application/json

{
  "bot_token": "bot_token",
  "chat_id": 987654321,
  "message": {
    "text": "That's fantastic! Productivity habits can really transform your daily life. What specific area of productivity would you like to focus on first?",
    "parse_mode": "Markdown",
    "reply_markup": {
      "inline_keyboard": [
        [
          {
            "text": "Time Management",
            "callback_data": "productivity_time"
          },
          {
            "text": "Focus & Concentration",
            "callback_data": "productivity_focus"
          }
        ],
        [
          {
            "text": "Task Organization",
            "callback_data": "productivity_tasks"
          }
        ]
      ]
    }
  },
  "context": {
    "conversation_id": "uuid",
    "user_id": "uuid",
    "creator_id": "uuid"
  }
}
```

**Response:**
```json
{
  "ok": true,
  "result": {
    "message_id": 1235,
    "from": {
      "id": 123456789,
      "is_bot": true,
      "first_name": "CoachBot",
      "username": "your_coach_bot"
    },
    "chat": {
      "id": 987654321,
      "first_name": "John",
      "type": "private"
    },
    "date": 1640995260,
    "text": "That's fantastic! Productivity habits can really transform your daily life..."
  },
  "internal_data": {
    "message_id": "uuid",
    "conversation_id": "uuid",
    "sent_at": "2024-01-01T00:00:00Z"
  }
}
```

### Handle Callback Query
```http
POST /api/v1/channels/telegram/webhook/{bot_id}
Content-Type: application/json

{
  "update_id": 123456790,
  "callback_query": {
    "id": "callback_query_id",
    "from": {
      "id": 987654321,
      "first_name": "John",
      "username": "johndoe"
    },
    "message": {
      "message_id": 1235,
      "date": 1640995260,
      "text": "That's fantastic! Productivity habits can really transform your daily life..."
    },
    "data": "productivity_time"
  }
}
```

### Send Photo/Document
```http
POST /api/v1/channels/telegram/messages
Content-Type: application/json

{
  "bot_token": "bot_token",
  "chat_id": 987654321,
  "message": {
    "type": "photo",
    "photo": "https://storage.platform.com/images/time_management_tips.jpg",
    "caption": "Here are some proven time management techniques that can help you get started! 📊\n\nWhich one resonates most with you?",
    "parse_mode": "Markdown"
  }
}
```

## Mobile App API

### User Authentication
```http
POST /api/v1/channels/mobile/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password",
  "device_info": {
    "device_id": "uuid",
    "platform": "ios",
    "app_version": "1.0.0",
    "os_version": "17.0",
    "push_token": "push_notification_token"
  }
}
```

**Response:**
```json
{
  "access_token": "jwt_token",
  "refresh_token": "refresh_token",
  "expires_in": 3600,
  "user": {
    "user_id": "uuid",
    "email": "user@example.com",
    "profile": {
      "name": "John Doe",
      "avatar_url": "https://storage.platform.com/avatars/user.jpg"
    },
    "creator_info": {
      "creator_id": "uuid",
      "creator_name": "Sarah Johnson",
      "coaching_focus": "Productivity & Habits"
    }
  },
  "app_config": {
    "features": {
      "push_notifications": true,
      "offline_mode": true,
      "voice_messages": true
    },
    "theme": {
      "primary_color": "#007bff",
      "creator_branding": true
    }
  }
}
```

### Get Conversations
```http
GET /api/v1/channels/mobile/conversations
Authorization: Bearer <jwt_token>
Query Parameters:
  - limit: integer (default: 20)
  - offset: integer (default: 0)
  - status: string (active|archived)
```

**Response:**
```json
{
  "conversations": [
    {
      "conversation_id": "uuid",
      "title": "Productivity Coaching",
      "last_message": {
        "content": "Great progress on your morning routine!",
        "timestamp": "2024-01-01T10:00:00Z",
        "sender": "assistant"
      },
      "unread_count": 2,
      "status": "active",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "pagination": {
    "total": 5,
    "limit": 20,
    "offset": 0,
    "has_more": false
  }
}
```

### Get Messages
```http
GET /api/v1/channels/mobile/conversations/{conversation_id}/messages
Authorization: Bearer <jwt_token>
Query Parameters:
  - limit: integer (default: 50)
  - before: string (message_id for pagination)
  - after: string (message_id for pagination)
```

**Response:**
```json
{
  "messages": [
    {
      "message_id": "uuid",
      "sender": "user",
      "content": {
        "text": "I completed my morning routine today!",
        "type": "text"
      },
      "timestamp": "2024-01-01T09:00:00Z",
      "status": "delivered"
    },
    {
      "message_id": "uuid",
      "sender": "assistant",
      "content": {
        "text": "That's fantastic! 🎉 How did it feel to complete your routine?",
        "type": "text",
        "suggestions": [
          "It felt great!",
          "It was challenging",
          "I want to adjust something"
        ]
      },
      "timestamp": "2024-01-01T09:00:05Z",
      "ai_metadata": {
        "confidence_score": 0.95,
        "response_time_ms": 1100
      }
    }
  ],
  "pagination": {
    "has_more": true,
    "next_cursor": "uuid"
  }
}
```

### Send Message
```http
POST /api/v1/channels/mobile/conversations/{conversation_id}/messages
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "message": {
    "type": "text",
    "content": {
      "text": "I'm struggling with staying consistent with my evening routine"
    }
  },
  "context": {
    "app_state": "active",
    "location": "home",
    "time_of_day": "evening"
  }
}
```

**Response:**
```json
{
  "message_id": "uuid",
  "status": "sent",
  "timestamp": "2024-01-01T20:00:00Z",
  "ai_response": {
    "message_id": "uuid",
    "content": {
      "text": "I understand that evening routines can be challenging, especially after a long day. Let's work together to make it more manageable.\n\nWhat part of your evening routine feels most difficult right now?",
      "suggestions": [
        "I'm too tired",
        "I get distracted",
        "It takes too long",
        "I forget to do it"
      ]
    },
    "response_time_ms": 1350,
    "confidence_score": 0.89
  }
}
```

### Upload Media
```http
POST /api/v1/channels/mobile/conversations/{conversation_id}/media
Authorization: Bearer <jwt_token>
Content-Type: multipart/form-data

file: <file>
message_text: "Here's my progress photo!" (optional)
media_type: "image" | "audio" | "video"
```

**Response:**
```json
{
  "upload_id": "uuid",
  "message_id": "uuid",
  "media_url": "https://storage.platform.com/media/{file_id}",
  "media_type": "image/jpeg",
  "file_size": 2048000,
  "processing_status": "completed",
  "ai_analysis": {
    "content_description": "Progress photo showing workout completion",
    "detected_objects": ["person", "gym_equipment"],
    "sentiment": "positive",
    "coaching_response": "Amazing progress! I can see the dedication in your workout setup. How are you feeling about your fitness journey so far?"
  }
}
```

### Push Notifications
```http
POST /api/v1/channels/mobile/notifications/send
Authorization: Bearer <service_token>
Content-Type: application/json

{
  "user_id": "uuid",
  "notification": {
    "title": "Time for your evening routine! 🌙",
    "body": "You've been doing great with consistency. Ready for tonight's routine?",
    "type": "proactive_reminder",
    "data": {
      "conversation_id": "uuid",
      "action": "open_conversation",
      "deep_link": "app://conversation/{conversation_id}"
    }
  },
  "scheduling": {
    "send_at": "2024-01-01T20:00:00Z",
    "timezone": "America/New_York"
  }
}
```

**Response:**
```json
{
  "notification_id": "uuid",
  "status": "scheduled",
  "scheduled_for": "2024-01-01T20:00:00Z",
  "estimated_delivery": "2024-01-01T20:00:05Z"
}
```

## Channel Analytics API

### Get Channel Performance
```http
GET /api/v1/channels/{channel_type}/analytics
Authorization: Bearer <jwt_token>
Query Parameters:
  - start_date: string (YYYY-MM-DD)
  - end_date: string (YYYY-MM-DD)
  - metrics: string (comma-separated)
```

**Response:**
```json
{
  "channel_type": "whatsapp",
  "date_range": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  },
  "metrics": {
    "total_messages": 2500,
    "unique_users": 150,
    "new_users": 45,
    "message_delivery_rate": 0.98,
    "response_rate": 0.75,
    "average_response_time_seconds": 2.1,
    "user_satisfaction_score": 4.3,
    "engagement_rate": 0.68
  },
  "trends": {
    "message_volume_trend": "increasing",
    "user_growth_rate": 0.15,
    "engagement_trend": "stable"
  },
  "top_conversation_topics": [
    {
      "topic": "fitness_goals",
      "message_count": 450,
      "user_count": 75
    },
    {
      "topic": "habit_formation",
      "message_count": 380,
      "user_count": 62
    }
  ]
}
```

## Error Handling

### Channel-Specific Error Codes
- `CHANNEL_UNAVAILABLE` (503): Channel service is temporarily unavailable
- `MESSAGE_DELIVERY_FAILED` (500): Failed to deliver message to channel
- `INVALID_CHANNEL_CONFIG` (422): Channel configuration is invalid
- `RATE_LIMIT_EXCEEDED` (429): Channel rate limit exceeded
- `MEDIA_UPLOAD_FAILED` (500): Failed to upload media file
- `WEBHOOK_VERIFICATION_FAILED` (401): Webhook verification failed

### Error Response Format
```json
{
  "error": {
    "code": "MESSAGE_DELIVERY_FAILED",
    "message": "Failed to deliver message via WhatsApp",
    "details": {
      "channel": "whatsapp",
      "whatsapp_error": "Invalid phone number format",
      "retry_possible": true,
      "retry_after_seconds": 30
    },
    "request_id": "uuid"
  }
}
```