# Microservices Architecture

## Service Overview

```
📦 Multi-Channel AI Coaching Platform
├── 🔐 auth-service (8001)          # JWT + RBAC + GDPR + Multi-tenant ✅ Production Ready
├── 🎨 creator-hub-service (8002)   # Content management + Program builder ⚠️ Foundation Ready
├── 🤖 ai-engine-service (8003)     # RAG pipeline + Ollama + ChromaDB ✅ Production Ready
├── 📡 channel-service (8004)       # WebSocket + Multi-channel + Web Widget ✅ Demo Ready
├── 🔧 testing-service (8005)       # Visual debugging + AI training 🚧 Future Implementation
├── 🌐 nginx (80/443)               # API Gateway + Load balancer ✅ Configured
└── 📊 Infrastructure Services      # PostgreSQL + Redis + ChromaDB + Ollama ✅ Optimized
```

## Service Details

### Auth Service (Port 8001) - ✅ Production Ready
- **Purpose**: JWT authentication, RBAC, GDPR compliance, multi-tenancy
- **Status**: Complete implementation with 85%+ test coverage
- **Key Features**:
  - JWT RS256 with refresh token rotation
  - Role-Based Access Control (RBAC)
  - Argon2 password hashing
  - Rate limiting and brute force protection
  - GDPR compliance (data export/deletion)

### Creator Hub Service (Port 8002) - ⚠️ Foundation Ready
- **Purpose**: Content management, program builder, analytics dashboard
- **Status**: Basic structure exists, needs content management features
- **Planned Features**:
  - Knowledge base management
  - Visual program builder using React Flow
  - Analytics dashboard
  - Multi-channel configuration

### AI Engine Service (Port 8003) - ✅ Production Ready
- **Purpose**: RAG pipeline, Ollama integration, ChromaDB vector storage
- **Status**: Full implementation with optimized performance
- **Key Features**:
  - <5s response times with confidence scoring
  - Optimized Ollama with llama3.2:1b + nomic-embed-text
  - Multi-tenant ChromaDB collections
  - Document processing (PDF, DOCX, TXT)
  - Conversation context management

### Channel Service (Port 8004) - ✅ Demo Ready
- **Purpose**: WebSocket communication, multi-channel messaging, web widgets
- **Status**: Foundation with web widget implementation
- **Key Features**:
  - WebSocket infrastructure with Redis scaling
  - Multi-channel abstraction layer
  - WhatsApp Business API handler architecture
  - Telegram Bot API handler
  - Embeddable web widget

### Testing Service (Port 8005) - 🚧 Future Implementation
- **Purpose**: Visual debugging, AI training, performance monitoring
- **Status**: Planned for Q1 2025
- **Planned Features**:
  - Creator personality trainer
  - Proactive engine simulator
  - Program flow debugger
  - Multi-channel orchestrator

## Infrastructure Services

### API Gateway (Nginx)
- **Ports**: 80/443
- **Features**: Load balancing, rate limiting, CORS configuration
- **SSL**: TLS 1.3 termination

### Database Layer
- **PostgreSQL 15**: Multi-tenant RLS policies, async SQLAlchemy
- **Redis 7**: Tenant-isolated caching, sessions, rate limiting
- **ChromaDB**: Vector storage with creator-specific collections

### AI/ML Stack
- **Ollama**: Local LLM serving (llama3.2, nomic-embed-text)
- **Models**: Optimized for 8GB RAM systems (1.8GB usage)
- **Performance**: <3.3s embeddings, <10.3s chat responses