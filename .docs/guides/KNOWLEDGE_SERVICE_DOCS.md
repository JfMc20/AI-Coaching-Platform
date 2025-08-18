# Creator Hub Knowledge Service - Complete Documentation

## 📋 Overview

The Knowledge Service is a critical component of the Creator Hub that manages document processing, knowledge base management, and semantic search through AI Engine integration. This service enables creators to upload their expertise and methodology documents which are then processed into embeddings for the AI digital twin.

## 🏗️ Architecture

```
Creator Hub Knowledge Service
├── 📄 Document Upload & Management
├── 🤖 AI Engine Integration (PHASE 1)
├── 🔍 Semantic Search & Retrieval
├── 🧠 Knowledge Context Generation
├── 🔄 ChromaDB Synchronization
└── 📊 Document Analytics
```

## 🔧 Core Components

### 1. AI Engine Client (`ai_client.py`)
**Purpose**: HTTP client for communicating with AI Engine Service

#### Key Classes:
- `AIEngineClient`: Main client class
- `DocumentProcessRequest/Response`: Document processing models
- `DocumentSearchRequest/Response`: Search operation models
- `ConversationRequest/Response`: Conversation processing models

#### Main Methods:
```python
async def process_document(creator_id, filename, file_content, document_id, auth_token)
async def search_documents(query, creator_id, limit, similarity_threshold, auth_token)
async def get_creator_knowledge_context(creator_id, query, limit, auth_token)
async def process_conversation_with_knowledge(message, creator_id, conversation_id, auth_token)
async def health_check()
```

### 2. Database Service (`database.py`)
**Purpose**: Data access layer with AI Engine integration

#### KnowledgeBaseService Methods:

##### Original Methods:
- `create_document()` - Create document record
- `list_documents()` - List creator's documents with pagination
- `get_document()` - Get document by ID
- `delete_document()` - Delete document and cleanup
- `update_document_status()` - Update processing status

##### PHASE 1: AI Engine Integration Methods:
- `process_document_with_ai_engine()` - Real document processing
- `sync_embeddings_to_chromadb()` - ChromaDB synchronization
- `get_creator_knowledge_context()` - Knowledge context retrieval
- `search_creator_documents()` - Semantic document search

### 3. API Endpoints (`routers/knowledge.py`)
**Purpose**: REST API endpoints for knowledge management

## 📚 API Endpoints Documentation

### Document Management Endpoints

#### `POST /api/v1/creators/knowledge/upload`
Upload and process a document for knowledge extraction.

**Request:**
```http
POST /api/v1/creators/knowledge/upload
Content-Type: multipart/form-data
Authorization: Bearer <token>

file: <binary file data>
title: "Document Title"
description: "Optional description"
tags: "tag1,tag2,tag3"
```

**Response:**
```json
{
  "id": "doc_uuid",
  "creator_id": "creator_uuid",
  "title": "Document Title", 
  "status": "COMPLETED",
  "chunk_count": 15,
  "processing_time": 3.2,
  "embeddings_stored": true,
  "metadata": {
    "filename": "document.pdf",
    "file_size": 1024000,
    "document_type": "PDF"
  }
}
```

**Processing Flow:**
1. File validation (type, size)
2. Save to upload directory
3. Create database record
4. **PHASE 1**: Process through AI Engine for real embeddings
5. Update status and return results
6. **Fallback**: Mock processing if AI Engine fails

#### `GET /api/v1/creators/knowledge/documents`
List creator's documents with pagination and filtering.

**Query Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)
- `status_filter`: Filter by DocumentStatus

**Response:**
```json
{
  "documents": [...],
  "total_count": 50,
  "page": 1,
  "page_size": 20,
  "has_next": true
}
```

#### `GET /api/v1/creators/knowledge/documents/{doc_id}`
Get detailed document information.

#### `DELETE /api/v1/creators/knowledge/documents/{doc_id}`
Delete document and cleanup associated data.

#### `POST /api/v1/creators/knowledge/documents/{doc_id}/reprocess`
Reprocess document to regenerate embeddings.

#### `GET /api/v1/creators/knowledge/documents/{doc_id}/status`
Get document processing status and metrics.

### PHASE 1: AI Engine Integration Endpoints

#### `POST /api/v1/creators/knowledge/search`
Search creator's documents using semantic similarity.

**Request:**
```http
POST /api/v1/creators/knowledge/search
Content-Type: application/x-www-form-urlencoded

query=coaching techniques for entrepreneurs
limit=5
similarity_threshold=0.7
```

**Response:**
```json
{
  "message": "Search completed successfully",
  "search_results": {
    "query": "coaching techniques for entrepreneurs",
    "results": [
      {
        "document_id": "doc_uuid",
        "chunk_index": 3,
        "content": "Relevant content chunk...",
        "similarity_score": 0.89,
        "metadata": {}
      }
    ],
    "total_results": 5,
    "search_time_ms": 45.2
  }
}
```

#### `POST /api/v1/creators/knowledge/knowledge-context`
Get knowledge context for creator query from processed documents.

**Request:**
```http
POST /api/v1/creators/knowledge/knowledge-context
Content-Type: application/x-www-form-urlencoded

query=how to help clients with goal setting
limit=10
similarity_threshold=0.7
```

**Response:**
```json
{
  "message": "Knowledge context retrieved successfully",
  "knowledge_context": {
    "creator_id": "creator_uuid",
    "query": "how to help clients with goal setting",
    "knowledge_chunks": [
      {
        "content": "Goal setting framework content...",
        "similarity": 0.92,
        "source_document": "doc_uuid",
        "chunk_index": 5,
        "document_title": "Coaching Methodology",
        "document_filename": "coaching_guide.pdf",
        "metadata": {}
      }
    ],
    "total_chunks": 8,
    "search_time_ms": 67.3
  }
}
```

#### `POST /api/v1/creators/knowledge/documents/{doc_id}/sync-embeddings`
Manually sync document embeddings to ChromaDB.

**Response:**
```json
{
  "message": "Document embeddings synced successfully",
  "document_id": "doc_uuid",
  "sync_status": "completed"
}
```

## 🔍 Data Models

### DocumentStatus Enum
```python
class DocumentStatus(str, Enum):
    UPLOADING = "uploading"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"
```

### DocumentType Enum
```python
class DocumentType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"
```

### KnowledgeDocument Model
```python
class KnowledgeDocument(TenantAwareEntity):
    title: str
    description: Optional[str]
    metadata: DocumentMetadata
    status: DocumentStatus
    chunk_count: Optional[int]
    processing_time: Optional[float]
    error_message: Optional[str]
    embeddings_stored: bool
```

### DocumentMetadata Model
```python
class DocumentMetadata(BaseModel):
    filename: str
    file_size: int
    document_type: DocumentType
    upload_timestamp: datetime
    content_hash: Optional[str]
    page_count: Optional[int]
    word_count: Optional[int]
    language_detected: Optional[str]
    tags: List[str]
```

## 🔐 Security & Multi-Tenancy

### Row Level Security (RLS)
All database operations use creator_id isolation:
```python
await session.execute(
    text("SET app.current_creator_id = :creator_id"),
    {"creator_id": creator_id}
)
```

### Authentication
All endpoints require valid JWT token:
```python
creator_id: str = Depends(get_current_creator_id)
```

### Data Isolation
- Documents are scoped to creator_id
- AI Engine operations include creator_id for tenant isolation
- ChromaDB collections are partitioned by creator

## 🚀 AI Engine Integration (PHASE 1)

### Processing Flow
1. **Document Upload** → Creator Hub receives file
2. **Database Record** → Create document entry with UPLOADING status
3. **AI Engine Processing** → Send to `/api/v1/ai/documents/process`
4. **Embedding Generation** → AI Engine processes and stores in ChromaDB
5. **Status Update** → Update document status to COMPLETED
6. **Fallback** → Mock processing if AI Engine fails

### Search Flow
1. **Query Input** → Creator searches their knowledge base
2. **AI Engine Search** → Call `/api/v1/ai/documents/search`
3. **Semantic Matching** → Vector similarity search in ChromaDB
4. **Results Enrichment** → Add document metadata from Creator Hub DB
5. **Response** → Return ranked results with context

### Knowledge Context Flow
1. **Context Request** → Get relevant knowledge for specific query
2. **Multi-Document Search** → Search across all creator's documents
3. **Context Compilation** → Combine relevant chunks with metadata
4. **Enhanced Response** → Include document titles, sources, confidence scores

## 📊 Configuration

### File Upload Limits
```python
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}
UPLOAD_DIR = "/app/uploads"
```

### AI Engine Settings
```python
AI_ENGINE_URL = "http://ai-engine-service:8003"
TIMEOUT = 60.0  # seconds for document processing
```

### Search Parameters
```python
DEFAULT_SEARCH_LIMIT = 5
MAX_SEARCH_LIMIT = 20
DEFAULT_SIMILARITY_THRESHOLD = 0.7
DEFAULT_CONTEXT_LIMIT = 10
MAX_CONTEXT_LIMIT = 50
```

## 🔄 Error Handling

### Graceful Degradation
- AI Engine failure → Fallback to mock processing
- ChromaDB unavailable → Log error, continue with metadata only
- Network timeout → Retry with exponential backoff

### Error Types
- `DocumentProcessingError`: File processing failures
- `DatabaseError`: Database operation failures  
- `NotFoundError`: Resource not found
- `ValidationError`: Input validation failures

## 📈 Monitoring & Logging

### Key Metrics
- Document processing time
- AI Engine response times
- Search query performance
- Error rates by endpoint
- Storage usage per creator

### Logging Levels
- **INFO**: Successful operations
- **WARNING**: Fallback activations
- **ERROR**: Processing failures
- **DEBUG**: Detailed operation traces

## 🔮 Future Enhancements (PHASE 2 & 3)

### PHASE 2: Creator Personality System
- Personality analysis from documents
- Dynamic prompt generation
- Consistency monitoring
- Personality injection into search results

### PHASE 3: Visual Program Builder
- Drag-and-drop knowledge flows
- Conditional logic based on document content
- Automated coaching sequences
- Knowledge-driven triggers

## 🧪 Testing & Validation

### Unit Tests
- Document processing workflows
- AI Engine client operations
- Database service methods
- API endpoint validation

### Integration Tests
- End-to-end document upload
- Search accuracy validation
- Multi-tenant isolation
- Error handling scenarios

### Performance Tests
- Large document processing
- Concurrent upload handling
- Search response times
- Memory usage optimization

---

This documentation covers the complete Knowledge Service implementation including the new PHASE 1 AI Engine integration features. The service is now production-ready for real document processing and semantic search capabilities.