"""Seed development data

Revision ID: 002
Revises: 001
Create Date: 2024-12-09 12:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Insert seed data for development"""
    
    # Insert sample creators for development
    # Password hash for "password123" using bcrypt
    password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6hsxq5S/kS'
    
    op.execute(f'''
        INSERT INTO auth.creators (email, password_hash, full_name, company_name, subscription_tier) VALUES
        ('demo@example.com', '{password_hash}', 'Demo Creator', 'Demo Company', 'free'),
        ('test@example.com', '{password_hash}', 'Test Creator', 'Test Company', 'free'),
        ('premium@example.com', '{password_hash}', 'Premium Creator', 'Premium Company', 'premium')
        ON CONFLICT (email) DO NOTHING
    ''')
    
    # Get creator IDs for further seed data
    demo_creator_result = op.get_bind().execute(
        sa.text("SELECT id FROM auth.creators WHERE email = 'demo@example.com'")
    ).fetchone()
    
    test_creator_result = op.get_bind().execute(
        sa.text("SELECT id FROM auth.creators WHERE email = 'test@example.com'")
    ).fetchone()
    
    if demo_creator_result and test_creator_result:
        demo_creator_id = demo_creator_result[0]
        test_creator_id = test_creator_result[0]
        
        # Insert sample user sessions
        op.execute(f'''
            INSERT INTO auth.user_sessions (session_id, creator_id, channel, metadata) VALUES
            ('demo-session-001', '{demo_creator_id}', 'web_widget', '{{"ip": "127.0.0.1", "user_agent": "Demo Browser"}}'),
            ('demo-session-002', '{demo_creator_id}', 'web_widget', '{{"ip": "127.0.0.1", "user_agent": "Demo Browser"}}'),
            ('test-session-001', '{test_creator_id}', 'web_widget', '{{"ip": "127.0.0.1", "user_agent": "Test Browser"}}')
            ON CONFLICT (session_id) DO NOTHING
        ''')
        
        # Insert sample widget configurations
        op.execute(f'''
            INSERT INTO content.widget_configs (creator_id, widget_id, is_active, theme, behavior, allowed_domains, rate_limit_per_minute) VALUES
            ('{demo_creator_id}', 'demo-widget-001', true, 
             '{{"primary_color": "#007bff", "secondary_color": "#6c757d", "background_color": "#ffffff", "text_color": "#212529", "border_radius": 8}}',
             '{{"auto_open": false, "greeting_message": "¡Hola! ¿En qué puedo ayudarte?", "placeholder_text": "Escribe tu mensaje...", "show_typing_indicator": true, "response_delay_ms": 1000}}',
             ARRAY['localhost', 'demo.example.com'], 20),
            ('{test_creator_id}', 'test-widget-001', true,
             '{{"primary_color": "#28a745", "secondary_color": "#6c757d", "background_color": "#ffffff", "text_color": "#212529", "border_radius": 12}}',
             '{{"auto_open": true, "greeting_message": "Welcome! How can I help you today?", "placeholder_text": "Type your message...", "show_typing_indicator": true, "response_delay_ms": 500}}',
             ARRAY['localhost', 'test.example.com'], 15)
        ''')
        
        # Insert sample knowledge documents
        op.execute(f'''
            INSERT INTO content.knowledge_documents (creator_id, document_id, filename, file_path, file_size, mime_type, status, total_chunks, metadata) VALUES
            ('{demo_creator_id}', 'demo-doc-001', 'demo-guide.pdf', '/uploads/demo-guide.pdf', 1024000, 'application/pdf', 'completed', 5, 
             '{{"title": "Demo Guide", "pages": 10, "language": "es"}}'),
            ('{demo_creator_id}', 'demo-doc-002', 'faq.txt', '/uploads/faq.txt', 5120, 'text/plain', 'completed', 2,
             '{{"title": "Frequently Asked Questions", "language": "es"}}'),
            ('{test_creator_id}', 'test-doc-001', 'test-manual.docx', '/uploads/test-manual.docx', 2048000, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'completed', 8,
             '{{"title": "Test Manual", "pages": 15, "language": "en"}}')
        ''')
        
        # Get session IDs for conversations
        demo_session_result = op.get_bind().execute(
            sa.text("SELECT id FROM auth.user_sessions WHERE session_id = 'demo-session-001'")
        ).fetchone()
        
        test_session_result = op.get_bind().execute(
            sa.text("SELECT id FROM auth.user_sessions WHERE session_id = 'test-session-001'")
        ).fetchone()
        
        if demo_session_result and test_session_result:
            demo_session_id = demo_session_result[0]
            test_session_id = test_session_result[0]
            
            # Insert sample conversations
            op.execute(f'''
                INSERT INTO conversations.conversations (creator_id, session_id, title, channel, message_count, metadata) VALUES
                ('{demo_creator_id}', '{demo_session_id}', 'Consulta sobre servicios', 'web_widget', 4,
                 '{{"topic": "services", "satisfaction": "high"}}'),
                ('{test_creator_id}', '{test_session_id}', 'Technical Support', 'web_widget', 6,
                 '{{"topic": "technical", "satisfaction": "medium"}}')
            ''')
            
            # Get conversation IDs for messages
            demo_conv_result = op.get_bind().execute(
                sa.text(f"SELECT id FROM conversations.conversations WHERE creator_id = '{demo_creator_id}' AND title = 'Consulta sobre servicios'")
            ).fetchone()
            
            test_conv_result = op.get_bind().execute(
                sa.text(f"SELECT id FROM conversations.conversations WHERE creator_id = '{test_creator_id}' AND title = 'Technical Support'")
            ).fetchone()
            
            if demo_conv_result and test_conv_result:
                demo_conv_id = demo_conv_result[0]
                test_conv_id = test_conv_result[0]
                
                # Insert sample messages
                op.execute(f'''
                    INSERT INTO conversations.messages (creator_id, conversation_id, role, content, processing_time_ms) VALUES
                    ('{demo_creator_id}', '{demo_conv_id}', 'user', '¿Qué servicios ofrecen?', null),
                    ('{demo_creator_id}', '{demo_conv_id}', 'assistant', 'Ofrecemos servicios de coaching personalizado, consultoría empresarial y desarrollo de habilidades. ¿Te interesa algún área específica?', 1500),
                    ('{demo_creator_id}', '{demo_conv_id}', 'user', 'Me interesa el coaching personalizado', null),
                    ('{demo_creator_id}', '{demo_conv_id}', 'assistant', 'Excelente elección. Nuestro coaching personalizado incluye sesiones individuales, planes de desarrollo y seguimiento continuo. ¿Te gustaría agendar una consulta inicial?', 1200),
                    
                    ('{test_creator_id}', '{test_conv_id}', 'user', 'I am having trouble with the login system', null),
                    ('{test_creator_id}', '{test_conv_id}', 'assistant', 'I can help you with login issues. Can you tell me what specific error message you are seeing?', 800),
                    ('{test_creator_id}', '{test_conv_id}', 'user', 'It says "Invalid credentials" but I am sure my password is correct', null),
                    ('{test_creator_id}', '{test_conv_id}', 'assistant', 'This could be due to several reasons. Let me guide you through some troubleshooting steps. First, please try resetting your password using the "Forgot Password" link.', 1100),
                    ('{test_creator_id}', '{test_conv_id}', 'user', 'I tried that but did not receive the email', null),
                    ('{test_creator_id}', '{test_conv_id}', 'assistant', 'Please check your spam folder. If you still do not see the email, I can escalate this to our technical team. Can you provide your registered email address?', 900)
                ''')


def downgrade() -> None:
    """Remove seed data"""
    
    # Delete in reverse order due to foreign key constraints
    op.execute("DELETE FROM conversations.messages WHERE creator_id IN (SELECT id FROM auth.creators WHERE email IN ('demo@example.com', 'test@example.com', 'premium@example.com'))")
    op.execute("DELETE FROM conversations.conversations WHERE creator_id IN (SELECT id FROM auth.creators WHERE email IN ('demo@example.com', 'test@example.com', 'premium@example.com'))")
    op.execute("DELETE FROM content.knowledge_documents WHERE creator_id IN (SELECT id FROM auth.creators WHERE email IN ('demo@example.com', 'test@example.com', 'premium@example.com'))")
    op.execute("DELETE FROM content.widget_configs WHERE creator_id IN (SELECT id FROM auth.creators WHERE email IN ('demo@example.com', 'test@example.com', 'premium@example.com'))")
    op.execute("DELETE FROM auth.user_sessions WHERE creator_id IN (SELECT id FROM auth.creators WHERE email IN ('demo@example.com', 'test@example.com', 'premium@example.com'))")
    op.execute("DELETE FROM auth.creators WHERE email IN ('demo@example.com', 'test@example.com', 'premium@example.com')")