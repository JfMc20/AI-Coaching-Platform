-- Initialize database for MVP Coaching AI Platform
-- This script sets up the basic database structure

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable Row Level Security
ALTER DATABASE mvp_coaching SET row_security = on;

-- Create schemas for better organization
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS content;
CREATE SCHEMA IF NOT EXISTS conversations;
CREATE SCHEMA IF NOT EXISTS analytics;

-- Grant permissions
GRANT USAGE ON SCHEMA auth TO postgres;
GRANT USAGE ON SCHEMA content TO postgres;
GRANT USAGE ON SCHEMA conversations TO postgres;
GRANT USAGE ON SCHEMA analytics TO postgres;

-- Create basic tables (detailed schema will be handled by Alembic migrations)

-- Creators table (in auth schema)
CREATE TABLE IF NOT EXISTS auth.creators (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    company_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    subscription_tier VARCHAR(50) DEFAULT 'free',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Enable RLS on creators table
ALTER TABLE auth.creators ENABLE ROW LEVEL SECURITY;

-- Create RLS policy for creators (creators can only see their own data)
CREATE POLICY creator_isolation_policy ON auth.creators
    FOR ALL
    TO postgres
    USING (id = current_setting('app.current_creator_id', true)::uuid);

-- User sessions table (for anonymous widget users)
CREATE TABLE IF NOT EXISTS auth.user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    creator_id UUID NOT NULL REFERENCES auth.creators(id) ON DELETE CASCADE,
    channel VARCHAR(50) DEFAULT 'web_widget',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Enable RLS on user_sessions
ALTER TABLE auth.user_sessions ENABLE ROW LEVEL SECURITY;

-- Create RLS policy for user_sessions
CREATE POLICY user_sessions_isolation_policy ON auth.user_sessions
    FOR ALL
    TO postgres
    USING (creator_id = current_setting('app.current_creator_id', true)::uuid);

-- Knowledge documents table (in content schema)
CREATE TABLE IF NOT EXISTS content.knowledge_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    creator_id UUID NOT NULL REFERENCES auth.creators(id) ON DELETE CASCADE,
    document_id VARCHAR(255) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500),
    file_size BIGINT,
    mime_type VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending',
    total_chunks INTEGER DEFAULT 0,
    processing_time_seconds FLOAT,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(creator_id, document_id)
);

-- Enable RLS on knowledge_documents
ALTER TABLE content.knowledge_documents ENABLE ROW LEVEL SECURITY;

-- Create RLS policy for knowledge_documents
CREATE POLICY knowledge_documents_isolation_policy ON content.knowledge_documents
    FOR ALL
    TO postgres
    USING (creator_id = current_setting('app.current_creator_id', true)::uuid);

-- Widget configurations table (in content schema)
CREATE TABLE IF NOT EXISTS content.widget_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    creator_id UUID NOT NULL REFERENCES auth.creators(id) ON DELETE CASCADE,
    widget_id VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    theme JSONB DEFAULT '{}',
    behavior JSONB DEFAULT '{}',
    allowed_domains TEXT[],
    rate_limit_per_minute INTEGER DEFAULT 10,
    embed_code TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(creator_id, widget_id)
);

-- Enable RLS on widget_configs
ALTER TABLE content.widget_configs ENABLE ROW LEVEL SECURITY;

-- Create RLS policy for widget_configs
CREATE POLICY widget_configs_isolation_policy ON content.widget_configs
    FOR ALL
    TO postgres
    USING (creator_id = current_setting('app.current_creator_id', true)::uuid);

-- Conversations table (in conversations schema)
CREATE TABLE IF NOT EXISTS conversations.conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    creator_id UUID NOT NULL REFERENCES auth.creators(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES auth.user_sessions(id) ON DELETE CASCADE,
    title VARCHAR(255),
    channel VARCHAR(50) DEFAULT 'web_widget',
    is_active BOOLEAN DEFAULT true,
    message_count INTEGER DEFAULT 0,
    last_message_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Enable RLS on conversations
ALTER TABLE conversations.conversations ENABLE ROW LEVEL SECURITY;

-- Create RLS policy for conversations
CREATE POLICY conversations_isolation_policy ON conversations.conversations
    FOR ALL
    TO postgres
    USING (creator_id = current_setting('app.current_creator_id', true)::uuid);

-- Messages table (in conversations schema)
CREATE TABLE IF NOT EXISTS conversations.messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    creator_id UUID NOT NULL REFERENCES auth.creators(id) ON DELETE CASCADE,
    conversation_id UUID NOT NULL REFERENCES conversations.conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Enable RLS on messages
ALTER TABLE conversations.messages ENABLE ROW LEVEL SECURITY;

-- Create RLS policy for messages
CREATE POLICY messages_isolation_policy ON conversations.messages
    FOR ALL
    TO postgres
    USING (creator_id = current_setting('app.current_creator_id', true)::uuid);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_creators_email ON auth.creators(email);
CREATE INDEX IF NOT EXISTS idx_user_sessions_creator_id ON auth.user_sessions(creator_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_session_id ON auth.user_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_creator_id ON content.knowledge_documents(creator_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_status ON content.knowledge_documents(creator_id, status);
CREATE INDEX IF NOT EXISTS idx_widget_configs_creator_id ON content.widget_configs(creator_id);
CREATE INDEX IF NOT EXISTS idx_conversations_creator_id ON conversations.conversations(creator_id);
CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations.conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_creator_id ON conversations.messages(creator_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON conversations.messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON conversations.messages(creator_id, created_at);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_creators_updated_at BEFORE UPDATE ON auth.creators FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_sessions_updated_at BEFORE UPDATE ON auth.user_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_knowledge_documents_updated_at BEFORE UPDATE ON content.knowledge_documents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_widget_configs_updated_at BEFORE UPDATE ON content.widget_configs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations.conversations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data for development
INSERT INTO auth.creators (email, password_hash, full_name, company_name) VALUES
('demo@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6hsxq5S/kS', 'Demo Creator', 'Demo Company'),
('test@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6hsxq5S/kS', 'Test Creator', 'Test Company')
ON CONFLICT (email) DO NOTHING;