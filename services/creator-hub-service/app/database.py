"""
Creator Hub Service Database Layer
Implements multi-tenant database operations for creator management
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import text, select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from shared.models.database import Creator
from .ai_client import get_ai_client, DocumentProcessResponse

# Database manager and session handling
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from shared.config.env_constants import get_env_value, DATABASE_URL
from typing import AsyncGenerator

# Database setup (similar to auth service pattern)
database_url = get_env_value(DATABASE_URL, fallback=True)
engine = create_async_engine(database_url, echo=False)
async_session = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def set_tenant_context(creator_id: str, db: AsyncSession):
    """Set tenant context for Row Level Security policies"""
    try:
        await db.execute(
            text("SELECT set_config('app.current_creator_id', :creator_id, true)"),
            {"creator_id": creator_id}
        )
    except Exception as e:
        logger.error(f"Failed to set tenant context: {e}")
        raise
from shared.exceptions.base import DatabaseError, NotFoundError
from .models import (
    CreatorProfile, CreatorProfileUpdate, CreatorStatus,
    KnowledgeDocument, DocumentMetadata, DocumentStatus, DocumentType,
    DashboardMetrics, ConversationSummary, ConversationStatus,
    WidgetConfiguration, WidgetSettings
)

logger = logging.getLogger(__name__)


# ==================== CREATOR PROFILE OPERATIONS ====================

class CreatorProfileService:
    """Service for creator profile management"""
    
    @staticmethod
    async def get_creator_profile(creator_id: str, session: AsyncSession) -> Optional[CreatorProfile]:
        """Get creator profile by ID"""
        try:
            # Set tenant context
            await session.execute(
                text("SET app.current_creator_id = :creator_id"),
                {"creator_id": creator_id}
            )
            
            # Query for creator profile (stored in creators table)
            result = await session.execute(
                select(Creator).where(Creator.id == creator_id)
            )
            creator = result.scalar_one_or_none()
            
            if not creator:
                return None
            
            # Convert to CreatorProfile model
            return CreatorProfile(
                id=str(creator.id),
                creator_id=creator_id,
                email=creator.email,
                display_name=creator.full_name or creator.email.split('@')[0],
                bio=creator.metadata.get('bio') if creator.metadata else None,
                avatar_url=creator.metadata.get('avatar_url') if creator.metadata else None,
                website_url=creator.metadata.get('website_url') if creator.metadata else None,
                status=CreatorStatus.ACTIVE,  # Default status
                coaching_categories=creator.metadata.get('coaching_categories', []) if creator.metadata else [],
                experience_years=creator.metadata.get('experience_years') if creator.metadata else None,
                certifications=creator.metadata.get('certifications', []) if creator.metadata else [],
                timezone=creator.metadata.get('timezone', 'UTC') if creator.metadata else 'UTC',
                language=creator.metadata.get('language', 'en') if creator.metadata else 'en',
                onboarding_completed=creator.metadata.get('onboarding_completed', False) if creator.metadata else False,
                created_at=creator.created_at,
                updated_at=creator.updated_at
            )
            
        except Exception as e:
            logger.error(f"Failed to get creator profile {creator_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve creator profile: {str(e)}")
    
    @staticmethod
    async def update_creator_profile(
        creator_id: str, 
        profile_data: CreatorProfileUpdate, 
        session: AsyncSession
    ) -> CreatorProfile:
        """Update creator profile"""
        try:
            # Set tenant context
            await session.execute(
                text("SET app.current_creator_id = :creator_id"),
                {"creator_id": creator_id}
            )
            
            # Prepare update data
            update_fields = {}
            metadata_updates = {}
            
            if profile_data.display_name is not None:
                update_fields["full_name"] = profile_data.display_name
            
            # Update metadata fields
            metadata_fields = [
                'bio', 'avatar_url', 'website_url', 'coaching_categories',
                'experience_years', 'certifications', 'timezone', 'language'
            ]
            
            for field in metadata_fields:
                value = getattr(profile_data, field, None)
                if value is not None:
                    metadata_updates[field] = value
            
            # Update creator record
            if update_fields or metadata_updates:
                update_stmt = update(Creator).where(Creator.id == creator_id)
                
                if update_fields:
                    update_stmt = update_stmt.values(**update_fields)
                
                if metadata_updates:
                    # Merge with existing metadata
                    update_stmt = update_stmt.values(
                        metadata=func.jsonb_set(
                            Creator.metadata,
                            '{}',
                            text(f"'{metadata_updates}'::jsonb"),
                            True
                        ),
                        updated_at=datetime.utcnow()
                    )
                
                await session.execute(update_stmt)
                await session.commit()
            
            # Return updated profile
            return await CreatorProfileService.get_creator_profile(creator_id, session)
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to update creator profile {creator_id}: {str(e)}")
            raise DatabaseError(f"Failed to update creator profile: {str(e)}")


# ==================== KNOWLEDGE BASE OPERATIONS ====================

class KnowledgeBaseService:
    """Service for knowledge base document management"""
    
    @staticmethod
    async def create_document(
        creator_id: str,
        title: str,
        description: Optional[str],
        metadata: DocumentMetadata,
        session: AsyncSession
    ) -> KnowledgeDocument:
        """Create a new knowledge document record"""
        try:
            # Set tenant context
            await session.execute(
                text("SET app.current_creator_id = :creator_id"),
                {"creator_id": creator_id}
            )
            
            document_id = str(uuid4())
            
            # Create document record (stored in a documents table - simplified for MVP)
            document_data = {
                "id": document_id,
                "creator_id": creator_id,
                "title": title,
                "description": description,
                "metadata": metadata.dict(),
                "status": DocumentStatus.UPLOADING,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Insert into documents table (assuming it exists)
            insert_stmt = text("""
                INSERT INTO documents (id, creator_id, title, description, metadata, status, created_at, updated_at)
                VALUES (:id, :creator_id, :title, :description, :metadata, :status, :created_at, :updated_at)
            """)
            
            await session.execute(insert_stmt, document_data)
            await session.commit()
            
            return KnowledgeDocument(
                id=document_id,
                creator_id=creator_id,
                title=title,
                description=description,
                metadata=metadata,
                status=DocumentStatus.UPLOADING,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to create document for creator {creator_id}: {str(e)}")
            raise DatabaseError(f"Failed to create document: {str(e)}")
    
    @staticmethod
    async def list_documents(
        creator_id: str,
        session: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[DocumentStatus] = None
    ) -> Dict[str, Any]:
        """List creator's documents with pagination"""
        try:
            # Set tenant context
            await session.execute(
                text("SET app.current_creator_id = :creator_id"),
                {"creator_id": creator_id}
            )
            
            # Build query
            base_query = """
                SELECT id, creator_id, title, description, metadata, status, 
                       chunk_count, processing_time, error_message, file_path,
                       embeddings_stored, created_at, updated_at
                FROM documents 
                WHERE creator_id = :creator_id
            """
            
            params = {"creator_id": creator_id}
            
            if status_filter:
                base_query += " AND status = :status"
                params["status"] = status_filter
            
            # Count total
            count_query = f"SELECT COUNT(*) FROM ({base_query}) as subq"
            count_result = await session.execute(text(count_query), params)
            total_count = count_result.scalar()
            
            # Get paginated results
            offset = (page - 1) * page_size
            base_query += f" ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
            params.update({"limit": page_size, "offset": offset})
            
            result = await session.execute(text(base_query), params)
            documents = []
            
            for row in result:
                doc_data = dict(row._mapping)
                documents.append(KnowledgeDocument(**doc_data))
            
            return {
                "documents": documents,
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "has_next": offset + page_size < total_count
            }
            
        except Exception as e:
            logger.error(f"Failed to list documents for creator {creator_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve documents: {str(e)}")
    
    @staticmethod
    async def update_document_status(
        creator_id: str,
        document_id: str,
        status: DocumentStatus,
        session: AsyncSession,
        chunk_count: Optional[int] = None,
        processing_time: Optional[float] = None,
        error_message: Optional[str] = None
    ) -> Optional[KnowledgeDocument]:
        """Update document processing status"""
        try:
            # Set tenant context
            await session.execute(
                text("SET app.current_creator_id = :creator_id"),
                {"creator_id": creator_id}
            )
            
            update_data = {
                "document_id": document_id,
                "creator_id": creator_id,
                "status": status,
                "updated_at": datetime.utcnow()
            }
            
            update_fields = ["status = :status", "updated_at = :updated_at"]
            
            if chunk_count is not None:
                update_data["chunk_count"] = chunk_count
                update_fields.append("chunk_count = :chunk_count")
            
            if processing_time is not None:
                update_data["processing_time"] = processing_time
                update_fields.append("processing_time = :processing_time")
            
            if error_message is not None:
                update_data["error_message"] = error_message
                update_fields.append("error_message = :error_message")
            
            if status == DocumentStatus.COMPLETED:
                update_data["embeddings_stored"] = True
                update_fields.append("embeddings_stored = :embeddings_stored")
            
            update_query = f"""
                UPDATE documents 
                SET {', '.join(update_fields)}
                WHERE id = :document_id AND creator_id = :creator_id
            """
            
            result = await session.execute(text(update_query), update_data)
            await session.commit()
            
            if result.rowcount == 0:
                return None
            
            # Return updated document
            return await KnowledgeBaseService.get_document(creator_id, document_id, session)
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to update document {document_id}: {str(e)}")
            raise DatabaseError(f"Failed to update document: {str(e)}")
    
    @staticmethod
    async def get_document(
        creator_id: str,
        document_id: str,
        session: AsyncSession
    ) -> Optional[KnowledgeDocument]:
        """Get document by ID"""
        try:
            # Set tenant context
            await session.execute(
                text("SET app.current_creator_id = :creator_id"),
                {"creator_id": creator_id}
            )
            
            query = text("""
                SELECT id, creator_id, title, description, metadata, status,
                       chunk_count, processing_time, error_message, file_path,
                       embeddings_stored, created_at, updated_at
                FROM documents 
                WHERE id = :document_id AND creator_id = :creator_id
            """)
            
            result = await session.execute(query, {
                "document_id": document_id,
                "creator_id": creator_id
            })
            
            row = result.first()
            if not row:
                return None
            
            doc_data = dict(row._mapping)
            return KnowledgeDocument(**doc_data)
            
        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve document: {str(e)}")
    
    @staticmethod
    async def delete_document(
        creator_id: str,
        document_id: str,
        session: AsyncSession
    ) -> bool:
        """Delete document and associated embeddings"""
        try:
            # Set tenant context
            await session.execute(
                text("SET app.current_creator_id = :creator_id"),
                {"creator_id": creator_id}
            )
            
            # Delete document record
            delete_query = text("""
                DELETE FROM documents 
                WHERE id = :document_id AND creator_id = :creator_id
            """)
            
            result = await session.execute(delete_query, {
                "document_id": document_id,
                "creator_id": creator_id
            })
            
            await session.commit()
            return result.rowcount > 0
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to delete document {document_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete document: {str(e)}")
    
    # ==================== PHASE 1: AI ENGINE INTEGRATION ====================
    
    @staticmethod
    async def process_document_with_ai_engine(
        creator_id: str,
        document_id: str,
        filename: str,
        file_content: bytes,
        session: AsyncSession,
        auth_token: Optional[str] = None
    ) -> DocumentProcessResponse:
        """
        Process document through AI Engine for real embedding generation
        
        Args:
            creator_id: Creator ID for tenant isolation
            document_id: Document ID to update
            filename: Original filename
            file_content: Document content as bytes
            session: Database session
            auth_token: Optional authentication token
            
        Returns:
            DocumentProcessResponse from AI Engine
        """
        try:
            # Set tenant context
            await set_tenant_context(creator_id, session)
            
            # Update document status to processing
            await KnowledgeBaseService.update_document_status(
                creator_id=creator_id,
                document_id=document_id,
                status=DocumentStatus.PROCESSING,
                session=session
            )
            
            # Get AI Engine client
            ai_client = get_ai_client()
            
            # Process document through AI Engine
            logger.info(f"Processing document {document_id} through AI Engine for creator {creator_id}")
            
            ai_response = await ai_client.process_document(
                creator_id=creator_id,
                filename=filename,
                file_content=file_content,
                document_id=document_id,
                auth_token=auth_token
            )
            
            # Update document with AI Engine results
            await KnowledgeBaseService.update_document_status(
                creator_id=creator_id,
                document_id=document_id,
                status=DocumentStatus.COMPLETED,
                chunk_count=ai_response.total_chunks,
                processing_time=ai_response.processing_time_seconds,
                session=session
            )
            
            logger.info(f"Document {document_id} processed successfully: {ai_response.total_chunks} chunks created")
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Failed to process document {document_id} with AI Engine: {str(e)}")
            
            # Update document status to failed
            await KnowledgeBaseService.update_document_status(
                creator_id=creator_id,
                document_id=document_id,
                status=DocumentStatus.FAILED,
                error_message=str(e),
                session=session
            )
            
            raise DatabaseError(f"Failed to process document with AI Engine: {str(e)}")
    
    @staticmethod
    async def sync_embeddings_to_chromadb(
        creator_id: str,
        document_id: str,
        session: AsyncSession,
        auth_token: Optional[str] = None
    ) -> bool:
        """
        Synchronize document embeddings to ChromaDB through AI Engine
        
        Args:
            creator_id: Creator ID for tenant isolation
            document_id: Document ID to sync
            session: Database session
            auth_token: Optional authentication token
            
        Returns:
            True if sync successful, False otherwise
        """
        try:
            # Set tenant context
            await set_tenant_context(creator_id, session)
            
            # Get document details
            document = await KnowledgeBaseService.get_document(creator_id, document_id, session)
            if not document:
                raise NotFoundError(f"Document {document_id} not found")
            
            # Check if document is processed
            if document.status != DocumentStatus.COMPLETED:
                logger.warning(f"Document {document_id} is not in COMPLETED status, current: {document.status}")
                return False
            
            # AI Engine automatically stores embeddings in ChromaDB during processing
            # This function exists for future manual sync needs or reprocessing
            logger.info(f"Embeddings for document {document_id} are already synced via AI Engine processing")
            
            # Update embeddings_stored flag
            update_stmt = text("""
                UPDATE documents 
                SET embeddings_stored = true, updated_at = :updated_at
                WHERE id = :document_id AND creator_id = :creator_id
            """)
            
            await session.execute(update_stmt, {
                "document_id": document_id,
                "creator_id": creator_id,
                "updated_at": datetime.utcnow()
            })
            
            await session.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync embeddings for document {document_id}: {str(e)}")
            await session.rollback()
            return False
    
    @staticmethod
    async def get_creator_knowledge_context(
        creator_id: str,
        query: str,
        limit: int = 10,
        similarity_threshold: float = 0.7,
        session: AsyncSession,
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get knowledge context for creator query from processed documents
        
        Args:
            creator_id: Creator ID for context
            query: Query to get context for
            limit: Maximum number of context chunks
            similarity_threshold: Minimum similarity score
            session: Database session
            auth_token: Optional authentication token
            
        Returns:
            Dictionary with creator knowledge context
        """
        try:
            # Set tenant context
            await set_tenant_context(creator_id, session)
            
            # Get AI Engine client
            ai_client = get_ai_client()
            
            # Search creator's documents for relevant context
            context = await ai_client.get_creator_knowledge_context(
                creator_id=creator_id,
                query=query,
                limit=limit,
                auth_token=auth_token
            )
            
            # Add document metadata from our database
            if context.get("knowledge_chunks"):
                # Get document titles and metadata
                document_ids = list(set(chunk["source_document"] for chunk in context["knowledge_chunks"]))
                
                if document_ids:
                    docs_query = text("""
                        SELECT id, title, metadata->>'filename' as filename
                        FROM documents 
                        WHERE id = ANY(:document_ids) AND creator_id = :creator_id
                    """)
                    
                    docs_result = await session.execute(docs_query, {
                        "document_ids": document_ids,
                        "creator_id": creator_id
                    })
                    
                    docs_info = {row.id: {"title": row.title, "filename": row.filename} 
                                for row in docs_result.fetchall()}
                    
                    # Enrich chunks with document info
                    for chunk in context["knowledge_chunks"]:
                        doc_id = chunk["source_document"]
                        if doc_id in docs_info:
                            chunk["document_title"] = docs_info[doc_id]["title"]
                            chunk["document_filename"] = docs_info[doc_id]["filename"]
            
            logger.info(f"Retrieved {len(context.get('knowledge_chunks', []))} knowledge chunks for creator {creator_id}")
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to get creator knowledge context: {str(e)}")
            return {
                "creator_id": creator_id,
                "query": query,
                "knowledge_chunks": [],
                "total_chunks": 0,
                "error": str(e)
            }
    
    @staticmethod
    async def search_creator_documents(
        creator_id: str,
        query: str,
        limit: int = 5,
        similarity_threshold: float = 0.7,
        session: AsyncSession,
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search creator's documents using semantic similarity
        
        Args:
            creator_id: Creator ID for search scope
            query: Search query
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score
            session: Database session
            auth_token: Optional authentication token
            
        Returns:
            Dictionary with search results
        """
        try:
            # Set tenant context
            await set_tenant_context(creator_id, session)
            
            # Get AI Engine client
            ai_client = get_ai_client()
            
            # Search documents via AI Engine
            search_response = await ai_client.search_documents(
                query=query,
                creator_id=creator_id,
                limit=limit,
                similarity_threshold=similarity_threshold,
                auth_token=auth_token
            )
            
            logger.info(f"Found {search_response.total_results} search results for creator {creator_id}")
            
            return {
                "query": search_response.query,
                "results": [
                    {
                        "document_id": result.document_id,
                        "chunk_index": result.chunk_index,
                        "content": result.content,
                        "similarity_score": result.similarity_score,
                        "metadata": result.metadata
                    }
                    for result in search_response.results
                ],
                "total_results": search_response.total_results,
                "search_time_ms": search_response.search_time_ms
            }
            
        except Exception as e:
            logger.error(f"Failed to search creator documents: {str(e)}")
            return {
                "query": query,
                "results": [],
                "total_results": 0,
                "error": str(e)
            }


# ==================== ANALYTICS OPERATIONS ====================

class AnalyticsService:
    """Service for creator analytics and dashboard metrics"""
    
    @staticmethod
    async def get_dashboard_metrics(
        creator_id: str,
        session: AsyncSession,
        period_days: int = 30
    ) -> DashboardMetrics:
        """Get dashboard metrics for creator"""
        try:
            # Set tenant context
            await session.execute(
                text("SET app.current_creator_id = :creator_id"),
                {"creator_id": creator_id}
            )
            
            period_start = datetime.utcnow() - timedelta(days=period_days)
            period_end = datetime.utcnow()
            
            # Get document metrics
            doc_metrics_query = text("""
                SELECT 
                    COUNT(*) as total_documents,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as documents_processed,
                    SUM(COALESCE(chunk_count, 0)) as total_knowledge_chunks
                FROM documents 
                WHERE creator_id = :creator_id
            """)
            
            doc_result = await session.execute(doc_metrics_query, {"creator_id": creator_id})
            doc_row = doc_result.first()
            
            # For MVP, use mock data for conversation metrics
            # In production, these would come from actual conversation tables
            conversation_metrics = {
                "total_conversations": 25,
                "active_conversations": 8,
                "messages_today": 42,
                "avg_response_time": 2.3,
                "active_users_7d": 15,
                "active_users_30d": 47,
                "user_satisfaction_score": 4.2
            }
            
            return DashboardMetrics(
                id=str(uuid4()),
                creator_id=creator_id,
                total_conversations=conversation_metrics["total_conversations"],
                active_conversations=conversation_metrics["active_conversations"],
                messages_today=conversation_metrics["messages_today"],
                total_documents=doc_row.total_documents or 0,
                documents_processed=doc_row.documents_processed or 0,
                total_knowledge_chunks=doc_row.total_knowledge_chunks or 0,
                avg_response_time=conversation_metrics["avg_response_time"],
                user_satisfaction_score=conversation_metrics["user_satisfaction_score"],
                active_users_7d=conversation_metrics["active_users_7d"],
                active_users_30d=conversation_metrics["active_users_30d"],
                period_start=period_start,
                period_end=period_end,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Failed to get dashboard metrics for creator {creator_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve dashboard metrics: {str(e)}")


# ==================== WIDGET CONFIGURATION OPERATIONS ====================

class WidgetConfigService:
    """Service for widget configuration management"""
    
    @staticmethod
    async def get_widget_config(
        creator_id: str,
        session: AsyncSession
    ) -> Optional[WidgetConfiguration]:
        """Get creator's widget configuration"""
        try:
            # Set tenant context
            await session.execute(
                text("SET app.current_creator_id = :creator_id"),
                {"creator_id": creator_id}
            )
            
            # For MVP, return default configuration
            # In production, this would be stored in a widget_configurations table
            return WidgetConfiguration(
                id=str(uuid4()),
                creator_id=creator_id,
                name="Default Widget",
                description="Default widget configuration",
                is_active=True,
                settings=WidgetSettings(),
                welcome_message="Hello! How can I help you today?",
                placeholder_text="Type your message...",
                enable_file_upload=True,
                enable_voice_input=False,
                allowed_domains=[],
                rate_limit_messages=10,
                track_analytics=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Failed to get widget config for creator {creator_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve widget configuration: {str(e)}")
    
    @staticmethod
    async def update_widget_config(
        creator_id: str,
        config_data: Dict[str, Any],
        session: AsyncSession
    ) -> WidgetConfiguration:
        """Update widget configuration"""
        try:
            # Set tenant context
            await session.execute(
                text("SET app.current_creator_id = :creator_id"),
                {"creator_id": creator_id}
            )
            
            # For MVP, return updated configuration
            # In production, this would update the widget_configurations table
            current_config = await WidgetConfigService.get_widget_config(creator_id, session)
            
            # Update fields if provided
            for key, value in config_data.items():
                if hasattr(current_config, key):
                    setattr(current_config, key, value)
            
            current_config.updated_at = datetime.utcnow()
            return current_config
            
        except Exception as e:
            logger.error(f"Failed to update widget config for creator {creator_id}: {str(e)}")
            raise DatabaseError(f"Failed to update widget configuration: {str(e)}")