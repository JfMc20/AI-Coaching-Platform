# Data Layer Architecture

## Database Design

### PostgreSQL 15 - Primary Database
- **Multi-tenant RLS policies** with automatic creator_id isolation
- **Async SQLAlchemy** with connection pooling and query optimization
- **Automated Alembic migrations** with version control
- **Connection pooling** optimized for async I/O operations

### Key Tables and Models
- **creators**: User/creator management with RBAC
- **documents**: Knowledge base with metadata and security
- **widget_configurations**: Multi-channel widget settings
- **conversations**: Chat history with context management
- **refresh_tokens**, **jwt_blacklist**: Security and session management
- **audit_logs**: Comprehensive auditing for compliance

### Row Level Security (RLS)
All tables implement automatic RLS policies that filter data by `creator_id`, ensuring complete tenant isolation:

```sql
-- Example RLS policy
CREATE POLICY creator_isolation ON documents
FOR ALL TO authenticated_users
USING (creator_id = current_setting('app.current_creator_id')::uuid);
```

## Caching Strategy

### Redis 7 - Multi-tenant Caching
- **Tenant-isolated caching** using database separation (DB 0-4)
- **Sessions and JWT blacklisting** for security
- **Rate limiting** with distributed counters
- **Message queues** for async processing
- **Connection pooling** with async patterns

### Cache Patterns
- **Cache-aside**: Manual cache management with TTL
- **Write-through**: Immediate cache updates on data changes
- **Cache stampede prevention**: Distributed locking mechanisms

## Vector Storage

### ChromaDB - AI Embeddings
- **Creator-specific collections**: `creator_{creator_id}_knowledge`
- **HNSW indexing** for efficient similarity search
- **Auto-scaling collections** based on document volume
- **768-dimension embeddings** using nomic-embed-text

### Data Processing Pipeline
1. **Document Upload**: PDF/DOCX/TXT processing
2. **Chunking**: 1000 token chunks with 200 token overlap
3. **Embedding Generation**: nomic-embed-text (274MB model)
4. **Vector Storage**: ChromaDB with metadata indexing
5. **Semantic Search**: Similarity-based retrieval with ranking

## Performance Optimization

### Connection Pooling
- **Async SQLAlchemy**: 10-50 connections per service
- **Redis**: Connection pool with health checks
- **ChromaDB**: HTTP client with timeout configuration

### Query Optimization
- **Database indexing**: Creator_id, timestamps, status fields
- **Query analysis**: <100ms target for p95
- **N+1 prevention**: Eager loading with SQLAlchemy
- **Caching**: Frequently accessed data with appropriate TTL

### Monitoring
- **Query performance**: Slow query logging and analysis
- **Connection health**: Pool utilization and timeout monitoring
- **Cache hit rates**: Redis statistics and optimization
- **Vector search**: ChromaDB performance metrics