# Webhooks and Integrations API Specification

## Overview

This document covers webhook endpoints for receiving external events and API specifications for third-party integrations including WhatsApp Business API, Telegram Bot API, payment processors, and other external services.

## Webhook Security

### Webhook Verification
All webhooks implement signature verification to ensure authenticity:

```python
import hmac
import hashlib

def verify_webhook_signature(payload, signature, secret):
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"sha256={expected_signature}", signature)
```

### Common Headers
```http
X-Webhook-Signature: sha256=<signature>
X-Webhook-Timestamp: 1640995200
X-Webhook-Event: <event_type>
Content-Type: application/json
User-Agent: Platform-Webhook/1.0
```

## WhatsApp Business API Integration

### Webhook Configuration
```http
POST /api/v1/integrations/whatsapp/webhook/configure
Authorization: Bearer <creator_token>
Content-Type: application/json

{
  "business_account_id": "business_account_id",
  "phone_number_id": "phone_number_id",
  "access_token": "whatsapp_access_token",
  "verify_token": "custom_verify_token",
  "webhook_fields": ["messages", "message_deliveries", "message_reads"]
}
```

**Response:**
```json
{
  "webhook_url": "https://api.platform.com/webhooks/whatsapp/{creator_id}",
  "verify_token": "custom_verify_token",
  "configuration_status": "active",
  "supported_events": [
    "message_received",
    "message_delivered",
    "message_read",
    "message_failed"
  ]
}
```

### Message Received Webhook
```http
POST /webhooks/whatsapp/{creator_id}
X-Webhook-Signature: sha256=<signature>
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
            "contacts": [
              {
                "profile": {
                  "name": "John Doe"
                },
                "wa_id": "user_phone_number"
              }
            ],
            "messages": [
              {
                "from": "user_phone_number",
                "id": "whatsapp_message_id",
                "timestamp": "1640995200",
                "text": {
                  "body": "I need help with my fitness routine"
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
  "message_id": "whatsapp_message_id",
  "processed": true,
  "conversation_id": "uuid",
  "user_id": "uuid"
}
```

### Message Status Webhook
```http
POST /webhooks/whatsapp/{creator_id}
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
                "recipient_id": "user_phone_number",
                "conversation": {
                  "id": "conversation_id",
                  "expiration_timestamp": "1641081600"
                },
                "pricing": {
                  "billable": true,
                  "pricing_model": "CBP",
                  "category": "business_initiated"
                }
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

### Send WhatsApp Message
```http
POST /api/v1/integrations/whatsapp/messages/send
Authorization: Bearer <creator_token>
Content-Type: application/json

{
  "phone_number_id": "phone_number_id",
  "to": "user_phone_number",
  "type": "text",
  "text": {
    "preview_url": false,
    "body": "Thanks for reaching out! I'd love to help you with your fitness routine. What specific goals do you have in mind?"
  },
  "context": {
    "message_id": "whatsapp_message_id"
  }
}
```

**Response:**
```json
{
  "messaging_product": "whatsapp",
  "messages": [
    {
      "id": "sent_message_id",
      "message_status": "accepted"
    }
  ]
}
```

### Send Template Message
```http
POST /api/v1/integrations/whatsapp/messages/send
Authorization: Bearer <creator_token>
Content-Type: application/json

{
  "phone_number_id": "phone_number_id",
  "to": "user_phone_number",
  "type": "template",
  "template": {
    "name": "welcome_message",
    "language": {
      "code": "en_US"
    },
    "components": [
      {
        "type": "header",
        "parameters": [
          {
            "type": "text",
            "text": "John"
          }
        ]
      },
      {
        "type": "body",
        "parameters": [
          {
            "type": "text",
            "text": "Fitness Coaching Program"
          }
        ]
      }
    ]
  }
}
```

## Telegram Bot API Integration

### Set Webhook
```http
POST /api/v1/integrations/telegram/webhook/set
Authorization: Bearer <creator_token>
Content-Type: application/json

{
  "bot_token": "bot_token",
  "webhook_url": "https://api.platform.com/webhooks/telegram/{creator_id}",
  "allowed_updates": ["message", "edited_message", "callback_query", "inline_query"],
  "drop_pending_updates": true,
  "secret_token": "webhook_secret_token"
}
```

**Response:**
```json
{
  "ok": true,
  "result": true,
  "webhook_info": {
    "url": "https://api.platform.com/webhooks/telegram/{creator_id}",
    "has_custom_certificate": false,
    "pending_update_count": 0,
    "last_error_date": null,
    "max_connections": 40,
    "allowed_updates": ["message", "callback_query"]
  }
}
```

### Message Update Webhook
```http
POST /webhooks/telegram/{creator_id}
X-Telegram-Bot-Api-Secret-Token: webhook_secret_token
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
      "username": "johndoe",
      "language_code": "en"
    },
    "chat": {
      "id": 987654321,
      "first_name": "John",
      "last_name": "Doe",
      "username": "johndoe",
      "type": "private"
    },
    "date": 1640995200,
    "text": "I want to start a morning routine",
    "entities": [
      {
        "offset": 0,
        "length": 6,
        "type": "bot_command"
      }
    ]
  }
}
```

**Response:**
```json
{
  "status": "received",
  "update_id": 123456789,
  "processed": true,
  "conversation_id": "uuid",
  "user_id": "uuid"
}
```

### Callback Query Webhook
```http
POST /webhooks/telegram/{creator_id}
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
      "from": {
        "id": 123456789,
        "is_bot": true,
        "first_name": "CoachBot",
        "username": "coach_bot"
      },
      "chat": {
        "id": 987654321,
        "first_name": "John",
        "type": "private"
      },
      "date": 1640995260,
      "text": "What type of routine interests you most?",
      "reply_markup": {
        "inline_keyboard": [
          [
            {
              "text": "Morning Routine",
              "callback_data": "routine_morning"
            }
          ]
        ]
      }
    },
    "data": "routine_morning"
  }
}
```

### Send Telegram Message
```http
POST /api/v1/integrations/telegram/messages/send
Authorization: Bearer <creator_token>
Content-Type: application/json

{
  "bot_token": "bot_token",
  "chat_id": 987654321,
  "text": "Great choice! Morning routines can be transformative. Let's start with something simple - what time do you usually wake up?",
  "parse_mode": "Markdown",
  "reply_markup": {
    "inline_keyboard": [
      [
        {
          "text": "Before 6 AM",
          "callback_data": "wake_before_6"
        },
        {
          "text": "6-8 AM",
          "callback_data": "wake_6_8"
        }
      ],
      [
        {
          "text": "After 8 AM",
          "callback_data": "wake_after_8"
        }
      ]
    ]
  }
}
```

## Payment Processing Integration (Stripe)

### Webhook Configuration
```http
POST /api/v1/integrations/stripe/webhook/configure
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "webhook_endpoint": "https://api.platform.com/webhooks/stripe",
  "enabled_events": [
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted",
    "invoice.payment_succeeded",
    "invoice.payment_failed",
    "customer.created",
    "customer.updated"
  ]
}
```

### Subscription Event Webhook
```http
POST /webhooks/stripe
Stripe-Signature: t=1640995200,v1=<signature>
Content-Type: application/json

{
  "id": "evt_stripe_event_id",
  "object": "event",
  "api_version": "2020-08-27",
  "created": 1640995200,
  "data": {
    "object": {
      "id": "sub_stripe_subscription_id",
      "object": "subscription",
      "application_fee_percent": null,
      "billing_cycle_anchor": 1640995200,
      "cancel_at_period_end": false,
      "canceled_at": null,
      "created": 1640995200,
      "current_period_end": 1643673600,
      "current_period_start": 1640995200,
      "customer": "cus_stripe_customer_id",
      "items": {
        "object": "list",
        "data": [
          {
            "id": "si_stripe_item_id",
            "object": "subscription_item",
            "price": {
              "id": "price_professional_monthly",
              "object": "price",
              "active": true,
              "billing_scheme": "per_unit",
              "created": 1640995000,
              "currency": "usd",
              "metadata": {
                "tier": "professional"
              },
              "nickname": "Professional Monthly",
              "product": "prod_coaching_platform",
              "recurring": {
                "aggregate_usage": null,
                "interval": "month",
                "interval_count": 1,
                "usage_type": "licensed"
              },
              "unit_amount": 9900,
              "unit_amount_decimal": "99.00"
            },
            "quantity": 1
          }
        ]
      },
      "metadata": {
        "creator_id": "uuid",
        "platform": "coaching_platform"
      },
      "status": "active"
    }
  },
  "livemode": false,
  "pending_webhooks": 1,
  "request": {
    "id": "req_stripe_request_id",
    "idempotency_key": null
  },
  "type": "customer.subscription.created"
}
```

**Response:**
```json
{
  "received": true,
  "event_id": "evt_stripe_event_id",
  "processed": true,
  "actions_taken": [
    "subscription_activated",
    "creator_tier_updated",
    "welcome_email_sent"
  ]
}
```

### Payment Failed Webhook
```http
POST /webhooks/stripe
Stripe-Signature: t=1640995200,v1=<signature>
Content-Type: application/json

{
  "id": "evt_payment_failed",
  "object": "event",
  "type": "invoice.payment_failed",
  "data": {
    "object": {
      "id": "in_stripe_invoice_id",
      "object": "invoice",
      "amount_due": 9900,
      "amount_paid": 0,
      "amount_remaining": 9900,
      "attempt_count": 1,
      "attempted": true,
      "auto_advance": true,
      "billing_reason": "subscription_cycle",
      "customer": "cus_stripe_customer_id",
      "customer_email": "creator@example.com",
      "metadata": {
        "creator_id": "uuid"
      },
      "status": "open",
      "subscription": "sub_stripe_subscription_id"
    }
  }
}
```

### Create Stripe Customer
```http
POST /api/v1/integrations/stripe/customers
Authorization: Bearer <creator_token>
Content-Type: application/json

{
  "email": "creator@example.com",
  "name": "John Creator",
  "metadata": {
    "creator_id": "uuid",
    "platform": "coaching_platform"
  },
  "payment_method": "pm_stripe_payment_method_id"
}
```

**Response:**
```json
{
  "id": "cus_stripe_customer_id",
  "object": "customer",
  "created": 1640995200,
  "email": "creator@example.com",
  "metadata": {
    "creator_id": "uuid",
    "platform": "coaching_platform"
  },
  "default_source": null,
  "invoice_settings": {
    "default_payment_method": "pm_stripe_payment_method_id"
  }
}
```

### Create Subscription
```http
POST /api/v1/integrations/stripe/subscriptions
Authorization: Bearer <creator_token>
Content-Type: application/json

{
  "customer": "cus_stripe_customer_id",
  "items": [
    {
      "price": "price_professional_monthly"
    }
  ],
  "metadata": {
    "creator_id": "uuid",
    "tier": "professional"
  },
  "trial_period_days": 14,
  "expand": ["latest_invoice.payment_intent"]
}
```

## Email Service Integration (SendGrid)

### Webhook Configuration
```http
POST /api/v1/integrations/sendgrid/webhook/configure
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "webhook_url": "https://api.platform.com/webhooks/sendgrid",
  "events": [
    "delivered",
    "opened",
    "clicked",
    "bounce",
    "dropped",
    "spam_report",
    "unsubscribe"
  ],
  "friendly_name": "Coaching Platform Webhook"
}
```

### Email Event Webhook
```http
POST /webhooks/sendgrid
Content-Type: application/json

[
  {
    "email": "creator@example.com",
    "timestamp": 1640995200,
    "event": "delivered",
    "sg_event_id": "sendgrid_event_id",
    "sg_message_id": "sendgrid_message_id",
    "smtp-id": "<smtp_id@sendgrid.net>",
    "category": ["welcome_email"],
    "unique_args": {
      "creator_id": "uuid",
      "email_type": "welcome"
    }
  },
  {
    "email": "creator@example.com",
    "timestamp": 1640995260,
    "event": "opened",
    "sg_event_id": "sendgrid_event_id_2",
    "sg_message_id": "sendgrid_message_id",
    "useragent": "Mozilla/5.0...",
    "ip": "192.168.1.1",
    "category": ["welcome_email"],
    "unique_args": {
      "creator_id": "uuid",
      "email_type": "welcome"
    }
  }
]
```

**Response:**
```json
{
  "received": true,
  "events_processed": 2,
  "status": "success"
}
```

### Send Email
```http
POST /api/v1/integrations/sendgrid/email/send
Authorization: Bearer <service_token>
Content-Type: application/json

{
  "personalizations": [
    {
      "to": [
        {
          "email": "creator@example.com",
          "name": "John Creator"
        }
      ],
      "subject": "Welcome to Your Coaching Platform!",
      "custom_args": {
        "creator_id": "uuid",
        "email_type": "welcome"
      }
    }
  ],
  "from": {
    "email": "noreply@coaching-platform.com",
    "name": "Coaching Platform"
  },
  "template_id": "d-welcome-template-id",
  "dynamic_template_data": {
    "creator_name": "John",
    "platform_url": "https://app.coaching-platform.com",
    "support_email": "support@coaching-platform.com"
  },
  "categories": ["welcome_email"],
  "tracking_settings": {
    "click_tracking": {
      "enable": true
    },
    "open_tracking": {
      "enable": true
    }
  }
}
```

## Analytics Integration (Google Analytics)

### Event Tracking
```http
POST /api/v1/integrations/analytics/events
Authorization: Bearer <creator_token>
Content-Type: application/json

{
  "measurement_id": "G-XXXXXXXXXX",
  "api_secret": "analytics_api_secret",
  "client_id": "user_client_id",
  "events": [
    {
      "name": "user_message_sent",
      "parameters": {
        "channel": "web",
        "creator_id": "uuid",
        "conversation_id": "uuid",
        "message_length": 45,
        "user_type": "returning"
      }
    },
    {
      "name": "ai_response_generated",
      "parameters": {
        "response_time_ms": 1250,
        "confidence_score": 0.92,
        "model_used": "llama3:8b",
        "creator_id": "uuid"
      }
    }
  ]
}
```

**Response:**
```json
{
  "events_sent": 2,
  "status": "success",
  "validation_messages": []
}
```

## Custom Webhook Endpoints

### Creator Webhook Configuration
```http
POST /api/v1/webhooks/configure
Authorization: Bearer <creator_token>
Content-Type: application/json

{
  "webhook_url": "https://creator-website.com/webhook",
  "events": [
    "user.created",
    "user.message_sent",
    "program.enrolled",
    "program.completed",
    "escalation.created"
  ],
  "secret": "webhook_secret_key",
  "active": true
}
```

**Response:**
```json
{
  "webhook_id": "uuid",
  "webhook_url": "https://creator-website.com/webhook",
  "events": ["user.created", "user.message_sent", "program.enrolled", "program.completed", "escalation.created"],
  "secret": "webhook_secret_key",
  "active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "last_delivery": null,
  "delivery_success_rate": null
}
```

### User Created Event
```http
POST https://creator-website.com/webhook
X-Webhook-Signature: sha256=<signature>
X-Webhook-Event: user.created
Content-Type: application/json

{
  "event": "user.created",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "user_id": "uuid",
    "creator_id": "uuid",
    "channel": "web",
    "profile_data": {
      "name": "John Doe",
      "goals": ["fitness", "productivity"]
    },
    "created_at": "2024-01-01T00:00:00Z"
  },
  "webhook_id": "uuid"
}
```

### Program Completed Event
```http
POST https://creator-website.com/webhook
X-Webhook-Signature: sha256=<signature>
X-Webhook-Event: program.completed
Content-Type: application/json

{
  "event": "program.completed",
  "timestamp": "2024-01-15T00:00:00Z",
  "data": {
    "user_id": "uuid",
    "creator_id": "uuid",
    "program_id": "uuid",
    "program_name": "30-Day Fitness Challenge",
    "completion_date": "2024-01-15T00:00:00Z",
    "completion_time_days": 28,
    "final_score": 0.92,
    "badges_earned": [
      {
        "badge_id": "uuid",
        "badge_name": "Challenge Completer"
      }
    ]
  },
  "webhook_id": "uuid"
}
```

## Webhook Management

### List Webhooks
```http
GET /api/v1/webhooks
Authorization: Bearer <creator_token>
```

**Response:**
```json
{
  "webhooks": [
    {
      "webhook_id": "uuid",
      "webhook_url": "https://creator-website.com/webhook",
      "events": ["user.created", "program.completed"],
      "active": true,
      "created_at": "2024-01-01T00:00:00Z",
      "last_delivery": "2024-01-01T12:00:00Z",
      "delivery_success_rate": 0.98,
      "total_deliveries": 150,
      "failed_deliveries": 3
    }
  ]
}
```

### Test Webhook
```http
POST /api/v1/webhooks/{webhook_id}/test
Authorization: Bearer <creator_token>
Content-Type: application/json

{
  "event_type": "user.created",
  "test_data": {
    "user_id": "test_uuid",
    "creator_id": "uuid",
    "channel": "web"
  }
}
```

**Response:**
```json
{
  "test_id": "uuid",
  "status": "success",
  "response_code": 200,
  "response_time_ms": 245,
  "response_body": "OK",
  "delivered_at": "2024-01-01T00:00:00Z"
}
```

### Webhook Delivery Logs
```http
GET /api/v1/webhooks/{webhook_id}/deliveries
Authorization: Bearer <creator_token>
Query Parameters:
  - limit: integer (default: 50)
  - status: string (success|failed|pending)
  - start_date: string (YYYY-MM-DD)
  - end_date: string (YYYY-MM-DD)
```

**Response:**
```json
{
  "deliveries": [
    {
      "delivery_id": "uuid",
      "event_type": "user.created",
      "status": "success",
      "response_code": 200,
      "response_time_ms": 245,
      "delivered_at": "2024-01-01T12:00:00Z",
      "retry_count": 0,
      "next_retry": null
    },
    {
      "delivery_id": "uuid",
      "event_type": "program.completed",
      "status": "failed",
      "response_code": 500,
      "response_time_ms": 5000,
      "delivered_at": "2024-01-01T11:30:00Z",
      "retry_count": 2,
      "next_retry": "2024-01-01T13:00:00Z",
      "error_message": "Internal Server Error"
    }
  ],
  "pagination": {
    "total": 150,
    "limit": 50,
    "offset": 0,
    "has_more": true
  }
}
```

## Rate Limits and Error Handling

### Rate Limits
- **Webhook deliveries**: 1000 per hour per webhook
- **Integration API calls**: 5000 per hour per creator
- **Test webhook calls**: 100 per hour per webhook

### Retry Policy
Failed webhook deliveries are retried with exponential backoff:
- 1st retry: 1 minute
- 2nd retry: 5 minutes
- 3rd retry: 15 minutes
- 4th retry: 1 hour
- 5th retry: 6 hours
- Final retry: 24 hours

### Error Codes
- `WEBHOOK_DELIVERY_FAILED` (500): Failed to deliver webhook
- `INVALID_WEBHOOK_SIGNATURE` (401): Webhook signature verification failed
- `WEBHOOK_TIMEOUT` (408): Webhook endpoint timeout
- `INTEGRATION_UNAVAILABLE` (503): Third-party service unavailable
- `INVALID_INTEGRATION_CONFIG` (422): Integration configuration invalid