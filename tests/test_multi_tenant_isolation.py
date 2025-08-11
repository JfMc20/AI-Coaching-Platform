"""
Tests for multi-tenant data isolation
Verifies zero data leakage between tenants using Row Level Security (RLS)
"""

import pytest
import asyncio
import asyncpg
import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from shared.models.database import Base, Creator, UserSession, KnowledgeDocument, WidgetConfig, Conversation, Message


# Test database configuration
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", 
    "postgresql+asyncpg://postgres:postgres@localhost:5432/test_mvp_coaching"
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for testing"""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session


@pytest.fixture
async def test_creators(db_session: AsyncSession):
    """Create test creators for isolation testing"""
    creator1 = Creator(
        email="creator1@test.com",
        password_hash="hashed_password_1",
        full_name="Creator One",
        company_name="Company One"
    )
    
    creator2 = Creator(
        email="creator2@test.com", 
        password_hash="hashed_password_2",
        full_name="Creator Two",
        company_name="Company Two"
    )
    
    db_session.add(creator1)
    db_session.add(creator2)
    await db_session.commit()
    await db_session.refresh(creator1)
    await db_session.refresh(creator2)
    
    return creator1, creator2


@pytest.fixture
async def raw_connection():
    """Create raw asyncpg connection for RLS testing"""
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        user="postgres",
        password="postgres",
        database="test_mvp_coaching"
    )
    
    yield conn
    
    await conn.close()


class TestMultiTenantIsolation:
    """Test multi-tenant data isolation"""
    
    async def test_creator_isolation_with_rls(self, raw_connection, test_creators):
        """Test that creators can only see their own data with RLS"""
        creator1, creator2 = test_creators
        
        # Set current creator context for creator1
        await raw_connection.execute(
            "SET app.current_creator_id = $1", str(creator1.id)
        )
        
        # Creator1 should only see their own record
        result = await raw_connection.fetch("SELECT * FROM auth.creators")
        assert len(result) == 1
        assert result[0]['email'] == creator1.email
        
        # Switch context to creator2
        await raw_connection.execute(
            "SET app.current_creator_id = $1", str(creator2.id)
        )
        
        # Creator2 should only see their own record
        result = await raw_connection.fetch("SELECT * FROM auth.creators")
        assert len(result) == 1
        assert result[0]['email'] == creator2.email
    
    async def test_user_sessions_isolation(self, raw_connection, test_creators):
        """Test user sessions isolation between tenants"""
        creator1, creator2 = test_creators
        
        # Create user sessions for both creators
        await raw_connection.execute("""
            INSERT INTO auth.user_sessions (session_id, creator_id, channel)
            VALUES ($1, $2, 'web_widget'), ($3, $4, 'web_widget')
        """, "session1", creator1.id, "session2", creator2.id)
        
        # Set context to creator1
        await raw_connection.execute(
            "SET app.current_creator_id = $1", str(creator1.id)
        )
        
        # Creator1 should only see their session
        result = await raw_connection.fetch("SELECT * FROM auth.user_sessions")
        assert len(result) == 1
        assert result[0]['session_id'] == "session1"
        assert result[0]['creator_id'] == creator1.id
        
        # Switch to creator2
        await raw_connection.execute(
            "SET app.current_creator_id = $1", str(creator2.id)
        )
        
        # Creator2 should only see their session
        result = await raw_connection.fetch("SELECT * FROM auth.user_sessions")
        assert len(result) == 1
        assert result[0]['session_id'] == "session2"
        assert result[0]['creator_id'] == creator2.id
    
    async def test_knowledge_documents_isolation(self, raw_connection, test_creators):
        """Test knowledge documents isolation between tenants"""
        creator1, creator2 = test_creators
        
        # Create documents for both creators
        await raw_connection.execute("""
            INSERT INTO content.knowledge_documents (creator_id, document_id, filename, status)
            VALUES ($1, 'doc1', 'creator1_doc.pdf', 'completed'),
                   ($2, 'doc2', 'creator2_doc.pdf', 'completed')
        """, creator1.id, creator2.id)
        
        # Set context to creator1
        await raw_connection.execute(
            "SET app.current_creator_id = $1", str(creator1.id)
        )
        
        # Creator1 should only see their document
        result = await raw_connection.fetch("SELECT * FROM content.knowledge_documents")
        assert len(result) == 1
        assert result[0]['document_id'] == "doc1"
        assert result[0]['creator_id'] == creator1.id
        
        # Switch to creator2
        await raw_connection.execute(
            "SET app.current_creator_id = $1", str(creator2.id)
        )
        
        # Creator2 should only see their document
        result = await raw_connection.fetch("SELECT * FROM content.knowledge_documents")
        assert len(result) == 1
        assert result[0]['document_id'] == "doc2"
        assert result[0]['creator_id'] == creator2.id
    
    async def test_widget_configs_isolation(self, raw_connection, test_creators):
        """Test widget configurations isolation between tenants"""
        creator1, creator2 = test_creators
        
        # Create widget configs for both creators
        await raw_connection.execute("""
            INSERT INTO content.widget_configs (creator_id, widget_id, is_active, theme, behavior)
            VALUES ($1, 'widget1', true, '{}', '{}'),
                   ($2, 'widget2', true, '{}', '{}')
        """, creator1.id, creator2.id)
        
        # Set context to creator1
        await raw_connection.execute(
            "SET app.current_creator_id = $1", str(creator1.id)
        )
        
        # Creator1 should only see their widget
        result = await raw_connection.fetch("SELECT * FROM content.widget_configs")
        assert len(result) == 1
        assert result[0]['widget_id'] == "widget1"
        assert result[0]['creator_id'] == creator1.id
        
        # Switch to creator2
        await raw_connection.execute(
            "SET app.current_creator_id = $1", str(creator2.id)
        )
        
        # Creator2 should only see their widget
        result = await raw_connection.fetch("SELECT * FROM content.widget_configs")
        assert len(result) == 1
        assert result[0]['widget_id'] == "widget2"
        assert result[0]['creator_id'] == creator2.id
    
    async def test_conversations_and_messages_isolation(self, raw_connection, test_creators):
        """Test conversations and messages isolation between tenants"""
        creator1, creator2 = test_creators
        
        # Create user sessions first
        session1_result = await raw_connection.fetchrow("""
            INSERT INTO auth.user_sessions (session_id, creator_id, channel)
            VALUES ('conv_session1', $1, 'web_widget')
            RETURNING id
        """, creator1.id)
        
        session2_result = await raw_connection.fetchrow("""
            INSERT INTO auth.user_sessions (session_id, creator_id, channel)
            VALUES ('conv_session2', $1, 'web_widget')
            RETURNING id
        """, creator2.id)
        
        session1_id = session1_result['id']
        session2_id = session2_result['id']
        
        # Create conversations
        conv1_result = await raw_connection.fetchrow("""
            INSERT INTO conversations.conversations (creator_id, session_id, title, message_count)
            VALUES ($1, $2, 'Conversation 1', 1)
            RETURNING id
        """, creator1.id, session1_id)
        
        conv2_result = await raw_connection.fetchrow("""
            INSERT INTO conversations.conversations (creator_id, session_id, title, message_count)
            VALUES ($1, $2, 'Conversation 2', 1)
            RETURNING id
        """, creator2.id, session2_id)
        
        conv1_id = conv1_result['id']
        conv2_id = conv2_result['id']
        
        # Create messages
        await raw_connection.execute("""
            INSERT INTO conversations.messages (creator_id, conversation_id, role, content)
            VALUES ($1, $2, 'user', 'Message from creator 1'),
                   ($3, $4, 'user', 'Message from creator 2')
        """, creator1.id, conv1_id, creator2.id, conv2_id)
        
        # Test conversations isolation
        await raw_connection.execute(
            "SET app.current_creator_id = $1", str(creator1.id)
        )
        
        conv_result = await raw_connection.fetch("SELECT * FROM conversations.conversations")
        assert len(conv_result) == 1
        assert conv_result[0]['title'] == "Conversation 1"
        
        msg_result = await raw_connection.fetch("SELECT * FROM conversations.messages")
        assert len(msg_result) == 1
        assert msg_result[0]['content'] == "Message from creator 1"
        
        # Switch to creator2
        await raw_connection.execute(
            "SET app.current_creator_id = $1", str(creator2.id)
        )
        
        conv_result = await raw_connection.fetch("SELECT * FROM conversations.conversations")
        assert len(conv_result) == 1
        assert conv_result[0]['title'] == "Conversation 2"
        
        msg_result = await raw_connection.fetch("SELECT * FROM conversations.messages")
        assert len(msg_result) == 1
        assert msg_result[0]['content'] == "Message from creator 2"
    
    async def test_cross_tenant_data_access_blocked(self, raw_connection, test_creators):
        """Test that attempts to access cross-tenant data are blocked"""
        creator1, creator2 = test_creators
        
        # Create data for creator2
        await raw_connection.execute("""
            INSERT INTO content.knowledge_documents (creator_id, document_id, filename, status)
            VALUES ($1, 'secret_doc', 'secret.pdf', 'completed')
        """, creator2.id)
        
        # Set context to creator1
        await raw_connection.execute(
            "SET app.current_creator_id = $1", str(creator1.id)
        )
        
        # Creator1 should not be able to see creator2's document
        result = await raw_connection.fetch("""
            SELECT * FROM content.knowledge_documents 
            WHERE document_id = 'secret_doc'
        """)
        assert len(result) == 0
        
        # Creator1 should not be able to update creator2's document
        rows_affected = await raw_connection.execute("""
            UPDATE content.knowledge_documents 
            SET status = 'failed' 
            WHERE document_id = 'secret_doc'
        """)
        # Should return "UPDATE 0" meaning no rows were affected
        assert "UPDATE 0" in rows_affected
        
        # Creator1 should not be able to delete creator2's document
        rows_affected = await raw_connection.execute("""
            DELETE FROM content.knowledge_documents 
            WHERE document_id = 'secret_doc'
        """)
        assert "DELETE 0" in rows_affected
    
    async def test_rls_policies_are_active(self, raw_connection):
        """Test that RLS policies are actually enabled and active"""
        
        # Check that RLS is enabled on all tables
        tables_with_rls = await raw_connection.fetch("""
            SELECT schemaname, tablename, rowsecurity 
            FROM pg_tables 
            WHERE schemaname IN ('auth', 'content', 'conversations')
            AND rowsecurity = true
        """)
        
        expected_tables = {
            ('auth', 'creators'),
            ('auth', 'user_sessions'),
            ('content', 'knowledge_documents'),
            ('content', 'widget_configs'),
            ('conversations', 'conversations'),
            ('conversations', 'messages')
        }
        
        actual_tables = {(row['schemaname'], row['tablename']) for row in tables_with_rls}
        
        assert actual_tables == expected_tables, f"RLS not enabled on all tables. Missing: {expected_tables - actual_tables}"
        
        # Check that policies exist
        policies = await raw_connection.fetch("""
            SELECT schemaname, tablename, policyname 
            FROM pg_policies 
            WHERE schemaname IN ('auth', 'content', 'conversations')
        """)
        
        policy_names = {row['policyname'] for row in policies}
        expected_policies = {
            'creator_isolation_policy',
            'user_sessions_isolation_policy',
            'knowledge_documents_isolation_policy',
            'widget_configs_isolation_policy',
            'conversations_isolation_policy',
            'messages_isolation_policy'
        }
        
        assert expected_policies.issubset(policy_names), f"Missing policies: {expected_policies - policy_names}"
    
    async def test_performance_with_large_dataset(self, raw_connection, test_creators):
        """Test that RLS doesn't significantly impact performance with larger datasets"""
        creator1, creator2 = test_creators
        
        # Create a larger dataset (100 documents per creator)
        documents_data = []
        for i in range(100):
            documents_data.extend([
                (creator1.id, f"doc1_{i}", f"document1_{i}.pdf", "completed"),
                (creator2.id, f"doc2_{i}", f"document2_{i}.pdf", "completed")
            ])
        
        # Batch insert
        await raw_connection.executemany("""
            INSERT INTO content.knowledge_documents (creator_id, document_id, filename, status)
            VALUES ($1, $2, $3, $4)
        """, documents_data)
        
        # Set context to creator1
        await raw_connection.execute(
            "SET app.current_creator_id = $1", str(creator1.id)
        )
        
        # Query should still be fast and return only creator1's documents
        import time
        start_time = time.time()
        
        result = await raw_connection.fetch("SELECT * FROM content.knowledge_documents")
        
        end_time = time.time()
        query_time = end_time - start_time
        
        # Should return exactly 100 documents for creator1
        assert len(result) == 100
        
        # All documents should belong to creator1
        for row in result:
            assert row['creator_id'] == creator1.id
            assert row['document_id'].startswith('doc1_')
        
        # Query should complete in reasonable time (less than 1 second for this dataset)
        assert query_time < 1.0, f"Query took too long: {query_time} seconds"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])