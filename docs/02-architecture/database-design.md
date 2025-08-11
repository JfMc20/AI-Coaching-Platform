# Database Design

## Overview

The database design follows a multi-tenant architecture supporting thousands of creators and millions of end users. The schema is optimized for performance, scalability, and data integrity while maintaining flexibility for future feature additions.

## Database Schema

### Core Entities

#### Creators Table
```sql
CREATE TABLE creators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    company_name VARCHAR(255),
    subscription_tier VARCHAR(50) NOT NULL DEFAULT 'basic',
    subscription_status VARCHAR(50) NOT NULL DEFAULT 'active',
    subscription_expires_at TIMESTAMP WITH TIME ZONE,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    stripe_customer_id VARCHAR(255),
    onboarding_completed BOOLEAN DEFAULT false
);

CREATE INDEX idx_creators_email ON creators(email);
CREATE INDEX idx_creators_subscription ON creators(subscription_tier, subscription_status);
CREATE INDEX idx_creators_active ON creators(is_active) WHERE is_active = true;
```

#### Users Table (End Users)
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID NOT NULL REFERENCES creators(id) ON DELETE CASCADE,
    external_id VARCHAR(255), -- Channel-specific user ID
    channel VARCHAR(50) NOT NULL, -- 'web', 'whatsapp', 'telegram', 'mobile'
    profile_data JSONB DEFAULT '{}',
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    timezone VARCHAR(50) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'en'
);

CREATE INDEX idx_users_creator ON users(creator_id);
CREATE INDEX idx_users_channel ON users(channel);
CREATE INDEX idx_users_external ON users(external_id, channel);
CREATE INDEX idx_users_active ON users(creator_id, is_active) WHERE is_active = true;
```

### Knowledge Management

#### Knowledge Bases Table
```sql
CREATE TABLE knowledge_bases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID NOT NULL REFERENCES creators(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    document_count INTEGER DEFAULT 0,
    total_size_bytes BIGINT DEFAULT 0
);

CREATE INDEX idx_knowledge_bases_creator ON knowledge_bases(creator_id);
CREATE INDEX idx_knowledge_bases_active ON knowledge_bases(creator_id, is_active) WHERE is_active = true;
```

#### Documents Table
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_base_id UUID NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    file_path VARCHAR(1000),
    file_type VARCHAR(50),
    file_size_bytes BIGINT,
    metadata JSONB DEFAULT '{}',
    processing_status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    chunk_count INTEGER DEFAULT 0,
    embedding_status VARCHAR(50) DEFAULT 'pending'
);

CREATE INDEX idx_documents_knowledge_base ON documents(knowledge_base_id);
CREATE INDEX idx_documents_status ON documents(processing_status);
CREATE INDEX idx_documents_embedding ON documents(embedding_status);
CREATE INDEX idx_documents_created ON documents(created_at DESC);
```

#### Document Chunks Table
```sql
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding_id VARCHAR(255), -- Reference to ChromaDB
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_chunks_document ON document_chunks(document_id);
CREATE INDEX idx_chunks_embedding ON document_chunks(embedding_id);
CREATE UNIQUE INDEX idx_chunks_unique ON document_chunks(document_id, chunk_index);
```

### Program Management

#### Programs Table
```sql
CREATE TABLE programs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID NOT NULL REFERENCES creators(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    flow_definition JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'draft',
    version INTEGER DEFAULT 1,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    published_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    enrollment_count INTEGER DEFAULT 0
);

CREATE INDEX idx_programs_creator ON programs(creator_id);
CREATE INDEX idx_programs_status ON programs(status);
CREATE INDEX idx_programs_active ON programs(creator_id, is_active) WHERE is_active = true;
```

#### Program Enrollments Table
```sql
CREATE TABLE program_enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    program_id UUID NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'active',
    progress JSONB DEFAULT '{}',
    current_step VARCHAR(255),
    enrolled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_enrollments_program ON program_enrollments(program_id);
CREATE INDEX idx_enrollments_user ON program_enrollments(user_id);
CREATE INDEX idx_enrollments_status ON program_enrollments(status);
CREATE UNIQUE INDEX idx_enrollments_unique ON program_enrollments(program_id, user_id);
```

### Conversation Management

#### Conversations Table
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    channel VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    context JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_message_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    message_count INTEGER DEFAULT 0,
    escalated_to_human BOOLEAN DEFAULT false,
    escalated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_conversations_user ON conversations(user_id);
CREATE INDEX idx_conversations_channel ON conversations(channel);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_updated ON conversations(updated_at DESC);
```

#### Messages Table
```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_type VARCHAR(50) NOT NULL, -- 'user', 'ai', 'creator'
    sender_id UUID,
    content TEXT NOT NULL,
    message_type VARCHAR(50) DEFAULT 'text',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    delivered_at TIMESTAMP WITH TIME ZONE,
    read_at TIMESTAMP WITH TIME ZONE,
    response_time_ms INTEGER,
    ai_confidence DECIMAL(3,2)
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_created ON messages(created_at DESC);
CREATE INDEX idx_messages_sender ON messages(sender_type, sender_id);
```

### User Profiling and Analytics

#### User Profiles Table
```sql
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    profile_data JSONB NOT NULL DEFAULT '{}',
    interests JSONB DEFAULT '[]',
    goals JSONB DEFAULT '[]',
    preferences JSONB DEFAULT '{}',
    behavior_patterns JSONB DEFAULT '{}',
    engagement_score DECIMAL(5,2) DEFAULT 0.0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_profiles_user ON user_profiles(user_id);
CREATE INDEX idx_profiles_engagement ON user_profiles(engagement_score DESC);
CREATE UNIQUE INDEX idx_profiles_unique ON user_profiles(user_id);
```

#### User Interactions Table
```sql
CREATE TABLE user_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    interaction_type VARCHAR(100) NOT NULL,
    interaction_data JSONB DEFAULT '{}',
    channel VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_id UUID,
    program_id UUID REFERENCES programs(id),
    message_id UUID REFERENCES messages(id)
);

CREATE INDEX idx_interactions_user ON user_interactions(user_id);
CREATE INDEX idx_interactions_type ON user_interactions(interaction_type);
CREATE INDEX idx_interactions_created ON user_interactions(created_at DESC);
CREATE INDEX idx_interactions_session ON user_interactions(session_id);
```

### Gamification System

#### Badges Table
```sql
CREATE TABLE badges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID NOT NULL REFERENCES creators(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    criteria JSONB NOT NULL,
    design JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    awarded_count INTEGER DEFAULT 0
);

CREATE INDEX idx_badges_creator ON badges(creator_id);
CREATE INDEX idx_badges_active ON badges(creator_id, is_active) WHERE is_active = true;
```

#### User Badges Table
```sql
CREATE TABLE user_badges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    badge_id UUID NOT NULL REFERENCES badges(id) ON DELETE CASCADE,
    earned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    criteria_met JSONB DEFAULT '{}',
    notified BOOLEAN DEFAULT false
);

CREATE INDEX idx_user_badges_user ON user_badges(user_id);
CREATE INDEX idx_user_badges_badge ON user_badges(badge_id);
CREATE INDEX idx_user_badges_earned ON user_badges(earned_at DESC);
CREATE UNIQUE INDEX idx_user_badges_unique ON user_badges(user_id, badge_id);
```

#### Achievements Table
```sql
CREATE TABLE achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    achievement_type VARCHAR(100) NOT NULL,
    achievement_data JSONB DEFAULT '{}',
    points INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    program_id UUID REFERENCES programs(id)
);

CREATE INDEX idx_achievements_user ON achievements(user_id);
CREATE INDEX idx_achievements_type ON achievements(achievement_type);
CREATE INDEX idx_achievements_created ON achievements(created_at DESC);
```

### Analytics and Metrics

#### Engagement Metrics Table
```sql
CREATE TABLE engagement_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID NOT NULL REFERENCES creators(id) ON DELETE CASCADE,
    metric_type VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,2) NOT NULL,
    dimensions JSONB DEFAULT '{}',
    date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_metrics_creator ON engagement_metrics(creator_id);
CREATE INDEX idx_metrics_type ON engagement_metrics(metric_type);
CREATE INDEX idx_metrics_date ON engagement_metrics(date DESC);
CREATE UNIQUE INDEX idx_metrics_unique ON engagement_metrics(creator_id, metric_type, date, dimensions);
```

#### Program Analytics Table
```sql
CREATE TABLE program_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    program_id UUID NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
    metric_type VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,2) NOT NULL,
    date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_program_analytics_program ON program_analytics(program_id);
CREATE INDEX idx_program_analytics_type ON program_analytics(metric_type);
CREATE INDEX idx_program_analytics_date ON program_analytics(date DESC);
```

### Channel Management

#### Channels Table
```sql
CREATE TABLE channels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID NOT NULL REFERENCES creators(id) ON DELETE CASCADE,
    channel_type VARCHAR(50) NOT NULL, -- 'web', 'whatsapp', 'telegram', 'mobile'
    channel_name VARCHAR(255) NOT NULL,
    configuration JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity_at TIMESTAMP WITH TIME ZONE,
    user_count INTEGER DEFAULT 0
);

CREATE INDEX idx_channels_creator ON channels(creator_id);
CREATE INDEX idx_channels_type ON channels(channel_type);
CREATE INDEX idx_channels_status ON channels(status);
```

### Subscription and Billing

#### Subscriptions Table
```sql
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID NOT NULL REFERENCES creators(id) ON DELETE CASCADE,
    stripe_subscription_id VARCHAR(255) UNIQUE,
    plan_name VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    current_period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    current_period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    cancel_at_period_end BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_subscriptions_creator ON subscriptions(creator_id);
CREATE INDEX idx_subscriptions_stripe ON subscriptions(stripe_subscription_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
```

#### Usage Tracking Table
```sql
CREATE TABLE usage_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID NOT NULL REFERENCES creators(id) ON DELETE CASCADE,
    usage_type VARCHAR(100) NOT NULL, -- 'ai_interactions', 'storage_gb', 'users'
    usage_value INTEGER NOT NULL,
    date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_usage_creator ON usage_tracking(creator_id);
CREATE INDEX idx_usage_type ON usage_tracking(usage_type);
CREATE INDEX idx_usage_date ON usage_tracking(date DESC);
CREATE UNIQUE INDEX idx_usage_unique ON usage_tracking(creator_id, usage_type, date);
```

## Data Relationships

### Entity Relationship Diagram
```
Creators (1) ──── (M) Knowledge_Bases (1) ──── (M) Documents (1) ──── (M) Document_Chunks
    │                                                                           │
    │                                                                           │
    ├── (M) Programs (1) ──── (M) Program_Enrollments ──── (M) Users ─────────┤
    │                                                          │                │
    │                                                          │                │
    ├── (M) Channels                                           │                │
    │                                                          │                │
    ├── (M) Badges (1) ──── (M) User_Badges ─────────────────┤                │
    │                                                          │                │
    ├── (M) Subscriptions                                      │                │
    │                                                          │                │
    └── (M) Engagement_Metrics                                 │                │
                                                               │                │
Users (1) ──── (M) Conversations (1) ──── (M) Messages       │                │
    │                                                          │                │
    ├── (1) User_Profiles                                      │                │
    │                                                          │                │
    ├── (M) User_Interactions ────────────────────────────────┤                │
    │                                                          │                │
    └── (M) Achievements ──────────────────────────────────────┘                │
                                                                                 │
ChromaDB Collections ────────────────────────────────────────────────────────┘
```

## Indexing Strategy

### Primary Indexes
- All primary keys use UUID with B-tree indexes
- Foreign key relationships have corresponding indexes
- Unique constraints where business logic requires

### Performance Indexes
```sql
-- Frequently queried combinations
CREATE INDEX idx_users_creator_active ON users(creator_id, is_active, last_active_at);
CREATE INDEX idx_messages_conversation_created ON messages(conversation_id, created_at DESC);
CREATE INDEX idx_interactions_user_type_created ON user_interactions(user_id, interaction_type, created_at DESC);

-- Analytics queries
CREATE INDEX idx_metrics_creator_date_type ON engagement_metrics(creator_id, date DESC, metric_type);
CREATE INDEX idx_usage_creator_date ON usage_tracking(creator_id, date DESC);

-- Search and filtering
CREATE INDEX idx_documents_content_search ON documents USING gin(to_tsvector('english', title || ' ' || content));
CREATE INDEX idx_programs_creator_status ON programs(creator_id, status, is_active);
```

### Partial Indexes
```sql
-- Only index active records
CREATE INDEX idx_active_users ON users(creator_id, last_active_at) WHERE is_active = true;
CREATE INDEX idx_active_conversations ON conversations(user_id, updated_at) WHERE status = 'active';
CREATE INDEX idx_pending_documents ON documents(knowledge_base_id, created_at) WHERE processing_status = 'pending';
```

## Data Partitioning Strategy

### Time-Based Partitioning
```sql
-- Partition large tables by date for better performance
CREATE TABLE user_interactions_2024_01 PARTITION OF user_interactions
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE messages_2024_01 PARTITION OF messages
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### Creator-Based Partitioning
```sql
-- Consider partitioning by creator_id for very large deployments
-- This would require careful planning and may not be necessary initially
```

## Data Retention Policies

### Automated Cleanup
```sql
-- Clean up old interaction data (keep 2 years)
DELETE FROM user_interactions 
WHERE created_at < NOW() - INTERVAL '2 years';

-- Archive old messages (keep 1 year active, archive older)
-- Implementation would move to archive tables rather than delete

-- Clean up processed document chunks for deleted documents
DELETE FROM document_chunks 
WHERE document_id NOT IN (SELECT id FROM documents);
```

### Backup Strategy
- **Daily Backups:** Full database backup with point-in-time recovery
- **Incremental Backups:** Transaction log backups every 15 minutes
- **Cross-Region Replication:** Disaster recovery in different geographic region
- **Retention:** Keep daily backups for 30 days, weekly for 1 year

## Performance Optimization

### Query Optimization
```sql
-- Use EXPLAIN ANALYZE to optimize slow queries
EXPLAIN ANALYZE SELECT * FROM users 
WHERE creator_id = $1 AND is_active = true 
ORDER BY last_active_at DESC LIMIT 50;

-- Optimize with proper indexes and query structure
```

### Connection Pooling
```python
# SQLAlchemy configuration for connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

### Read Replicas
- **Master-Slave Setup:** Write operations to master, read operations to replicas
- **Load Balancing:** Distribute read queries across multiple replicas
- **Lag Monitoring:** Ensure replica lag stays within acceptable limits

## Security Considerations

### Data Encryption
- **At Rest:** Database-level encryption for sensitive data
- **In Transit:** TLS 1.3 for all database connections
- **Application Level:** Additional encryption for PII data

### Access Control
```sql
-- Row Level Security for multi-tenant isolation
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_isolation ON users
    FOR ALL TO application_role
    USING (creator_id = current_setting('app.current_creator_id')::uuid);
```

### Audit Logging
```sql
-- Audit trail for sensitive operations
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name VARCHAR(100) NOT NULL,
    operation VARCHAR(10) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    user_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Migration Strategy

### Schema Versioning
```python
# Alembic migration example
def upgrade():
    op.add_column('users', sa.Column('timezone', sa.String(50), server_default='UTC'))
    op.create_index('idx_users_timezone', 'users', ['timezone'])

def downgrade():
    op.drop_index('idx_users_timezone')
    op.drop_column('users', 'timezone')
```

### Data Migration
- **Backward Compatibility:** Ensure new schema works with existing data
- **Gradual Migration:** Migrate data in batches to avoid downtime
- **Rollback Plan:** Always have a rollback strategy for failed migrations
- **Testing:** Thoroughly test migrations on staging environment