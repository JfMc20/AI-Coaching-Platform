# API Integration Guide - Frontend Service

## Overview

This document provides comprehensive information about integrating the Frontend Service with all backend services in the Multi-Channel AI Coaching Platform.

## Backend Services Architecture

### Service URLs and Ports
- **Auth Service**: http://localhost:8001 (Production ready ✅)
- **Creator Hub Service**: http://localhost:8002 (Foundation ready ⚠️) 
- **AI Engine Service**: http://localhost:8003 (Production ready ✅)
- **Channel Service**: http://localhost:8004 (Demo ready ✅)
- **Frontend Service**: http://localhost:8006 (Testing environment)

---

## 1. Auth Service (Port 8001) - PRODUCTION READY ✅

### Base URL: `/api/v1/auth`

#### Authentication Flow
All protected endpoints require JWT authentication via `Authorization: Bearer <token>` header.

#### Core Endpoints:

**POST `/register`**
```typescript
interface CreatorCreate {
  email: string;
  password: string;
  full_name: string;
  company_name?: string;
}

interface RegistrationResponse {
  creator: {
    id: string;
    email: string;
    full_name: string;
    company_name?: string;
    is_active: boolean;
    subscription_tier: string;
  };
  tokens: {
    access_token: string;
    refresh_token: string;
    token_type: "bearer";
    expires_in: number;
  };
  message: string;
}
```

**POST `/login`**
```typescript
interface LoginRequest {
  email: string;
  password: string;
  remember_me?: boolean;
}
// Returns same RegistrationResponse format
```

**POST `/refresh`**
```typescript
interface TokenRefreshRequest {
  refresh_token: string;
}

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
}
```

**GET `/me`** (Protected)
```typescript
interface CreatorResponse {
  id: string;
  email: string;
  full_name: string;
  company_name?: string;
  is_active: boolean;
  subscription_tier: string;
  created_at: string;
  updated_at: string;
}
```

**POST `/logout`** (Protected)
```typescript
// Optional body: { refresh_token?: string }
// Returns 204 No Content
```

#### Password Management:

**POST `/password/validate`**
```typescript
interface PasswordValidationRequest {
  password: string;
  personal_info?: Record<string, any>;
}

interface PasswordStrengthResponse {
  strength: "weak" | "moderate" | "strong";
  score: number; // 0-100
  is_valid: boolean;
  violations: string[];
  suggestions: string[];
  estimated_crack_time: string;
}
```

**POST `/password/reset/request`**
```typescript
interface PasswordResetRequest {
  email: string;
}
// Returns 202 Accepted regardless of email existence
```

**POST `/password/reset/confirm`**
```typescript
interface PasswordResetConfirm {
  token: string;
  new_password: string;
}
```

#### Advanced Features:

**POST `/tokens/revoke`** (Protected)
- Revokes current JWT token
- Returns 204 No Content

**POST `/keys/rotate`** (Protected, Admin only)
- Rotates JWT signing keys
- Requires admin role

#### GDPR Compliance:

**POST `/gdpr/data-deletion`** (Protected)
```typescript
interface DataDeletionRequest {
  deletion_type: "anonymization" | "soft_delete" | "hard_delete";
  reason: string;
  confirm_deletion: boolean;
}
```

**GET `/gdpr/data-export`** (Protected)
```typescript
interface DataExportResponse {
  export_id: string;
  creator_id: string;
  export_date: string;
  data: Record<string, any>;
}
```

#### Error Handling:
- 400: Validation errors, password policy violations
- 401: Invalid credentials, expired tokens
- 403: Forbidden (missing permissions)
- 409: Email already registered
- 423: Account locked due to failed attempts
- 429: Rate limiting exceeded

---

## 2. AI Engine Service (Port 8003) - PRODUCTION READY ✅

### Base URL: `/api/v1/ai`

#### Conversation Processing:

**POST `/conversations`**
```typescript
interface ConversationRequest {
  query: string; // 1-4000 chars
  creator_id: string;
  conversation_id: string;
  context_window?: number; // 1000-8000
}

interface ConversationResponse {
  response: string;
  conversation_id: string;
  confidence: number; // 0.0-1.0
  processing_time_ms: number;
  model_used: string;
  sources_count: number;
  sources: Array<{
    document_id: string;
    chunk_index: number;
    similarity_score: number;
    rank: number;
    content_preview: string;
    metadata: Record<string, any>;
  }>;
}
```

**GET `/conversations/{conversation_id}/context`**
```typescript
interface ContextResponse {
  conversation_id: string;
  messages: Array<{
    id: string;
    role: "user" | "assistant";
    content: string;
    created_at: string;
    processing_time_ms?: number;
    metadata?: Record<string, any>;
  }>;
  total_messages: number;
  summary?: Record<string, any>;
}
```

#### Document Processing:

**POST `/documents/process`** (Multipart form)
```typescript
// Form data:
// - file: File (PDF, DOC, DOCX, TXT, MD - max 10MB)
// - creator_id: string
// - document_id?: string (optional)

interface DocumentProcessResponse {
  document_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  total_chunks: number;
  processing_time_seconds: number;
  filename: string;
  error_message?: string;
  metadata: Record<string, any>;
}
```

**POST `/documents/search`**
```typescript
interface DocumentSearchRequest {
  query: string; // 1-1000 chars
  creator_id: string;
  limit?: number; // 1-20, default 5
  similarity_threshold?: number; // 0.0-1.0, default 0.7
}

interface DocumentSearchResponse {
  query: string;
  results: Array<{
    document_id: string;
    chunk_index: number;
    content: string;
    similarity_score: number;
    metadata: Record<string, any>;
  }>;
  total_results: number;
  processing_time_ms: number;
}
```

#### Model Management:

**GET `/models/status`**
```typescript
interface ModelsStatusResponse {
  embedding_model: {
    name: string;
    status: "available" | "not_available";
    loaded: boolean;
  };
  chat_model: {
    name: string;
    status: "available" | "not_available";  
    loaded: boolean;
  };
  all_models: Array<{
    name: string;
    size: number;
    modified_at: string;
    loaded: boolean;
  }>;
  server_status: string;
  timestamp: string;
}
```

**POST `/models/reload`**
- Forces model reload
- Returns model availability status

#### ChromaDB & Vector Operations:

**GET `/chromadb/health`**
**GET `/chromadb/stats`** 
**GET `/ollama/health`**
**POST `/ollama/test-embedding`**
**POST `/ollama/test-chat`**

#### Advanced Features:

**POST `/models/deploy`** (Model versioning)
**GET `/models/{model_name}/versions`**
**POST `/models/{model_name}/rollback`**
**GET `/models/{model_name}/active`**

#### Error Handling:
- 400: Invalid file type, file too large
- 413: Request entity too large
- 422: Document processing failed
- 500: Internal server error
- 503: Service unavailable (models not loaded)

---

## 3. Creator Hub Service (Port 8002) - FOUNDATION READY ⚠️

### Base URL: `/api/v1/creators`

#### Knowledge Management:

**POST `/knowledge/upload`** (Multipart form)
```typescript
// Form data:
// - file: File (PDF, DOCX, TXT, MD - max 10MB)
// - title: string
// - description?: string  
// - tags?: string (comma-separated)

interface KnowledgeDocument {
  id: string;
  creator_id: string;
  title: string;
  description?: string;
  filename: string;
  file_size: number;
  status: "pending" | "processing" | "completed" | "failed";
  chunk_count?: number;
  processing_time?: number;
  error_message?: string;
  embeddings_stored: boolean;
  metadata: {
    filename: string;
    file_size: number;
    document_type: "PDF" | "DOCX" | "TXT" | "MD";
    upload_timestamp: string;
    tags: string[];
    // ... other metadata
  };
  created_at: string;
  updated_at: string;
}
```

**GET `/knowledge/documents`**
```typescript
interface DocumentListResponse {
  documents: KnowledgeDocument[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
// Query params: page?, page_size?, status_filter?
```

**GET `/knowledge/documents/{doc_id}`**
**DELETE `/knowledge/documents/{doc_id}`**
**POST `/knowledge/documents/{doc_id}/reprocess`**
**GET `/knowledge/documents/{doc_id}/status`**

#### AI Engine Integration:

**POST `/knowledge/search`** (Form data)
```typescript
// Form data:
// - query: string
// - limit?: number (1-20, default 5)
// - similarity_threshold?: number (0.0-1.0, default 0.7)

interface SearchResults {
  search_results: {
    query: string;
    results: Array<{
      document_id: string;
      chunk_index: number;
      content: string;
      similarity_score: number;
      metadata: Record<string, any>;
    }>;
    total_results: number;
    processing_time_ms: number;
  };
}
```

**POST `/knowledge/knowledge-context`** (Form data)
```typescript
// Same as search but returns enhanced context for AI processing
interface KnowledgeContext {
  knowledge_context: {
    knowledge_chunks: Array<{
      content: string;
      source: string;
      relevance_score: number;
    }>;
    total_chunks: number;
    query: string;
  };
}
```

#### Personality System (PHASE 2):

**POST `/knowledge/personality/analyze`**
```typescript
interface PersonalityAnalysisRequest {
  creator_id: string;
  force_reanalysis?: boolean;
  include_documents?: boolean;
}

interface PersonalityAnalysisResponse {
  analysis_status: "completed" | "in_progress" | "failed";
  personality_profile?: {
    personality_summary: string;
    confidence_score: number;
    key_methodologies: string[];
    traits: Array<{
      dimension: string;
      trait_value: string;
      confidence_score: number;
    }>;
  };
  traits_discovered: number;
  documents_analyzed: number;
}
```

**POST `/knowledge/personality/generate-prompt`**
```typescript
interface PersonalizedPromptRequest {
  creator_id: string;
  context: string;
  user_query: string;
  message_template?: string;
}

interface PersonalizedPromptResponse {
  personalized_prompt: string;
  template_used: string;
  confidence_score: number;
  personality_factors: string[];
}
```

**POST `/knowledge/personality/monitor-consistency`**
```typescript
interface ConsistencyMonitoringRequest {
  creator_id: string;
  ai_response: string;
  original_query: string;
  context: string;
}

interface ConsistencyMonitoringResponse {
  overall_score: number;
  is_consistent: boolean;
  detailed_scores: Record<string, number>;
  recommendations: string[];
}
```

#### Enhanced Knowledge Context:

**POST `/knowledge/knowledge-context/enhanced`** (Form data)
```typescript
// Same as knowledge-context but includes personality info
interface EnhancedContext {
  enhanced_context: {
    knowledge_chunks: any[];
    personality_info?: {
      personality_summary: string;
      key_methodologies: string[];
      confidence_score: number;
      dominant_traits: Array<{
        dimension: string;
        value: string;
        confidence: number;
      }>;
    };
    personality_prompt?: {
      personalized_prompt: string;
      template_used: string;
      confidence_score: number;
    };
  };
}
```

#### Visual Program Builder (PHASE 3):

**POST `/programs/`** (Form data)
```typescript
interface ProgramDefinition {
  program_id: string;
  creator_id: string;
  title: string;
  description: string;
  version: string;
  status: "draft" | "published" | "archived";
  personality_config: {
    enabled: boolean;
    enhance_content: boolean;
    enforce_consistency: boolean;
    adaptation_level: string;
  };
  execution_config: {
    strategy: "sequential" | "parallel" | "conditional";
    parallel_limit: number;
    timeout_seconds: number;
    retry_failed_steps: boolean;
    max_retries: number;
  };
  analytics_config: {
    enabled: boolean;
    track_performance: boolean;
    track_user_journey: boolean;
    store_debug_info: boolean;
    real_time_insights: boolean;
  };
  steps: ProgramStep[];
  created_at: string;
  updated_at: string;
}
```

**GET `/programs/`** - List programs with filters
**GET `/programs/{program_id}`** - Get program details
**PUT `/programs/{program_id}`** - Update program
**DELETE `/programs/{program_id}`** - Delete program

#### Program Steps:

**POST `/programs/{program_id}/steps`** (Form data)
```typescript
interface ProgramStep {
  step_id: string;
  program_id: string;
  step_type: "trigger" | "action" | "condition" | "data_collection" | "notification" | "delay";
  name: string;
  description: string;
  order_index: number;
  trigger_config: {
    trigger_type: "time_based" | "event_based" | "user_action" | "condition_based";
    // ... trigger-specific config
  };
  action_config: {
    action_type: "send_message" | "update_data" | "call_api" | "run_analysis";
    // ... action-specific config
  };
  enabled: boolean;
  created_at: string;
  updated_at: string;
}
```

**GET `/programs/{program_id}/steps`**
**PUT `/programs/{program_id}/steps/{step_id}`**
**DELETE `/programs/{program_id}/steps/{step_id}`**

#### Program Execution:

**POST `/programs/{program_id}/execute`** (Form data)
```typescript
interface ProgramExecutionResult {
  execution_id: string;
  program_id: string;
  execution_status: "running" | "completed" | "failed" | "cancelled";
  steps_completed: number;
  total_steps: number;
  start_time: string;
  end_time?: string;
  execution_time_ms: number;
  results: Record<string, any>;
  error_message?: string;
}
```

**GET `/programs/{program_id}/executions`** - Execution history
**POST `/programs/{program_id}/validate`** - Validate program
**POST `/programs/{program_id}/test-conditions`** - Test conditions

#### Analytics & Debugging:

**GET `/programs/{program_id}/analytics`**
**POST `/programs/{program_id}/insights`**
**GET `/programs/{program_id}/debug/sessions`**
**GET `/programs/{program_id}/debug/sessions/{session_id}`**

---

## 4. Channel Service (Port 8004) - DEMO READY ✅

### Base URL: `/api/v1`

#### Channel Management:

**GET `/channels`**
```typescript
interface ChannelListResponse {
  channels: ChannelConfiguration[];
  total: number;
}
```

**GET `/channels/{channel_id}/health`**
```typescript
interface ChannelHealthResponse {
  status: "healthy" | "unhealthy";
  channel_id: string;
  checks?: Record<string, string>;
}
```

#### Messaging:

**POST `/channels/{channel_id}/messages`**
```typescript
interface OutboundMessage {
  content: string;
  recipient: string;
  message_type?: "text" | "media" | "template";
  metadata?: Record<string, any>;
}

interface MessageResponse {
  message_id: string;
  status: "sent" | "delivered" | "failed";
  timestamp: string;
}
```

#### Webhooks:

**POST `/webhooks/whatsapp/{channel_id}`**
**POST `/webhooks/telegram/{channel_id}`**
- Process incoming messages from external platforms
- Query param: creator_id

#### Web Widget:

**WebSocket `/ws/widget/{channel_id}`**
```typescript
// Query params: creator_id?, session_id?, user_name?

interface WebSocketMessage {
  type: "user_message" | "ai_response" | "status" | "error";
  content?: string;
  conversation_id?: string;
  user_identifier?: string;
  timestamp?: string;
}

interface WebSocketResponse {
  type: "ai_response" | "status" | "error";
  content?: string;
  conversation_id?: string;
  confidence?: number;
  processing_time_ms?: number;
  model_used?: string;
  sources_count?: number;
}
```

**GET `/widget/{channel_id}/embed`** - Get HTML embed code
**GET `/widget-demo`** - Widget demonstration page
**GET `/widget.js`** - Widget JavaScript client

#### Connection Management:

**GET `/connections`**
```typescript
interface ConnectionStatus {
  active_websocket_connections: number;
  sessions: string[];
}
```

---

## Frontend API Client Configuration

### Environment Variables
```typescript
// services/frontend-service/.env.local
AUTH_SERVICE_URL=http://localhost:8001
CREATOR_HUB_SERVICE_URL=http://localhost:8002  
AI_ENGINE_SERVICE_URL=http://localhost:8003
CHANNEL_SERVICE_URL=http://localhost:8004
```

### Next.js Rewrites (next.config.ts)
```typescript
async rewrites() {
  return [
    {
      source: '/api/auth/:path*',
      destination: `${process.env.AUTH_SERVICE_URL || 'http://localhost:8001'}/api/v1/auth/:path*`,
    },
    {
      source: '/api/creators/:path*', 
      destination: `${process.env.CREATOR_HUB_SERVICE_URL || 'http://localhost:8002'}/api/v1/creators/:path*`,
    },
    {
      source: '/api/ai/:path*',
      destination: `${process.env.AI_ENGINE_SERVICE_URL || 'http://localhost:8003'}/api/v1/:path*`,
    },
    {
      source: '/api/channels/:path*',
      destination: `${process.env.CHANNEL_SERVICE_URL || 'http://localhost:8004'}/api/v1/:path*`,
    },
  ];
}
```

### API Client Implementation

The existing `src/lib/apiClient.ts` should handle:

1. **Authentication**: Automatic JWT token management with refresh
2. **Multi-tenant**: Creator ID isolation for all requests  
3. **Error Handling**: Proper HTTP status code handling
4. **Type Safety**: TypeScript interfaces for all endpoints
5. **Request/Response Interceptors**: Logging, error formatting

### Key Integration Points

1. **Authentication Flow**: 
   - Login → Store tokens → Auto-refresh → Logout
   - Protected routes require valid JWT

2. **Creator Isolation**:
   - All API calls include creator_id 
   - Multi-tenant database queries use RLS

3. **File Uploads**:
   - Document upload to Creator Hub Service
   - Automatic processing via AI Engine
   - Real-time status updates

4. **Real-time Features**:
   - WebSocket connections for chat testing
   - Live document processing status
   - Program execution monitoring

5. **Error Boundaries**:
   - Service unavailability fallbacks
   - Graceful degradation for demo mode
   - User-friendly error messages

---

## Testing Strategy

### Development Environment Access Codes:
- `dev2025`
- `coaching-ai-dev` 
- `visual-program-builder`

### Service Health Checks:
- GET `/health` - Basic service status
- GET `/ready` - Dependency validation

### Rate Limiting:
- Registration: 3 attempts/hour per IP
- Login: 5 attempts/15 minutes per IP  
- Password reset: 3 requests/hour per IP

### File Upload Limits:
- Max file size: 10MB
- Supported types: PDF, DOC, DOCX, TXT, MD
- Automatic virus scanning (production)

This integration guide ensures the frontend testing interface can seamlessly connect to all backend services while maintaining security, performance, and reliability standards.