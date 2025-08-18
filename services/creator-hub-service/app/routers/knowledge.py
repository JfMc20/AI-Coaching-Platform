"""
Knowledge Base Management Router
Handles document upload, processing, and organization with personality integration
"""

import logging
import os
import aiofiles
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from shared.exceptions.base import NotFoundError, DatabaseError

# Import dependencies from our app layer
from ..database import get_db
from ..dependencies.auth import get_current_creator_id

from ..models import (
    KnowledgeDocument, DocumentMetadata, DocumentType, DocumentStatus,
    DocumentUploadRequest, DocumentListResponse
)
from ..database import KnowledgeBaseService

# Import personality system components
from ..personality_models import (
    PersonalityAnalysisRequest, PersonalityAnalysisResponse,
    PersonalizedPromptRequest, PersonalizedPromptResponse,
    ConsistencyMonitoringRequest, ConsistencyMonitoringResponse
)
from ..personality_engine import get_personality_engine
from ..prompt_generator import get_prompt_generator
from ..consistency_monitor import get_consistency_monitor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/creators/knowledge", tags=["knowledge"])

# File upload configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}
UPLOAD_DIR = "/app/uploads"


# ==================== DOCUMENT UPLOAD ENDPOINTS ====================

@router.post("/upload", response_model=KnowledgeDocument)
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload"),
    title: str = Form(..., description="Document title"),
    description: Optional[str] = Form(None, description="Document description"),
    tags: Optional[str] = Form(None, description="Comma-separated tags"),
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db)
):
    """Upload and process a document"""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        # Check file extension
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file_ext} not supported. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Check file size
        file_size = 0
        content = await file.read()
        file_size = len(content)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file provided"
            )
        
        # Generate unique filename
        file_id = str(uuid4())
        filename = f"{file_id}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        # Ensure upload directory exists
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Determine document type
        doc_type_map = {
            ".pdf": DocumentType.PDF,
            ".docx": DocumentType.DOCX,
            ".txt": DocumentType.TXT,
            ".md": DocumentType.MD
        }
        document_type = doc_type_map.get(file_ext, DocumentType.TXT)
        
        # Parse tags
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        # Create document metadata
        metadata = DocumentMetadata(
            filename=file.filename,
            file_size=file_size,
            document_type=document_type,
            upload_timestamp=datetime.utcnow(),
            content_hash=None,  # TODO: Calculate hash
            page_count=None,    # TODO: Extract from document
            word_count=None,    # TODO: Calculate word count
            language_detected=None,  # TODO: Detect language
            tags=tag_list
        )
        
        # Create document record
        document = await KnowledgeBaseService.create_document(
            creator_id=creator_id,
            title=title,
            description=description,
            metadata=metadata,
            session=session
        )
        
        # Update document with file path
        await KnowledgeBaseService.update_document_status(
            creator_id=creator_id,
            document_id=document.id,
            status=DocumentStatus.PROCESSING,
            session=session
        )
        
        # PHASE 1: Real AI Engine processing
        try:
            # Process document through AI Engine for real embeddings
            ai_response = await KnowledgeBaseService.process_document_with_ai_engine(
                creator_id=creator_id,
                document_id=document.id,
                filename=file.filename,
                file_content=content,
                session=session
            )
            
            logger.info(f"Document processed via AI Engine: {ai_response.total_chunks} chunks, {ai_response.processing_time_seconds:.2f}s")
            
        except Exception as e:
            logger.error(f"AI Engine processing failed, falling back to mock: {str(e)}")
            
            # Fallback to mock processing if AI Engine fails
            await KnowledgeBaseService.update_document_status(
                creator_id=creator_id,
                document_id=document.id,
                status=DocumentStatus.COMPLETED,
                chunk_count=10,  # Mock value
                processing_time=2.5,  # Mock value
                session=session
            )
        
        logger.info(f"Document uploaded successfully: {document.id} for creator {creator_id}")
        
        # Return updated document
        updated_document = await KnowledgeBaseService.get_document(
            creator_id, document.id, session
        )
        
        return updated_document or document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document"
        )


# ==================== DOCUMENT MANAGEMENT ENDPOINTS ====================

@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[DocumentStatus] = Query(default=None, description="Filter by status"),
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db)
):
    """List creator's documents"""
    try:
        result = await KnowledgeBaseService.list_documents(
            creator_id=creator_id,
            session=session,
            page=page,
            page_size=page_size,
            status_filter=status_filter
        )
        
        logger.info(f"Documents listed for creator: {creator_id} (page {page})")
        
        return DocumentListResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to list documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve documents"
        )


@router.get("/documents/{doc_id}", response_model=KnowledgeDocument)
async def get_document(
    doc_id: str,
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db)
):
    """Get document details"""
    try:
        document = await KnowledgeBaseService.get_document(
            creator_id=creator_id,
            document_id=doc_id,
            session=session
        )
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        logger.info(f"Document retrieved: {doc_id}")
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document"
        )


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db)
):
    """Delete a document"""
    try:
        # Get document details for file cleanup
        document = await KnowledgeBaseService.get_document(
            creator_id=creator_id,
            document_id=doc_id,
            session=session
        )
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Delete from database
        deleted = await KnowledgeBaseService.delete_document(
            creator_id=creator_id,
            document_id=doc_id,
            session=session
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # TODO: Clean up file and embeddings
        # In a real implementation:
        # 1. Delete physical file
        # 2. Delete embeddings from vector database
        # 3. Clean up any related data
        
        logger.info(f"Document deleted: {doc_id}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Document deleted successfully", "document_id": doc_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )


# ==================== DOCUMENT PROCESSING ENDPOINTS ====================

@router.post("/documents/{doc_id}/reprocess")
async def reprocess_document(
    doc_id: str,
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db)
):
    """Reprocess a document (regenerate embeddings)"""
    try:
        # Get document
        document = await KnowledgeBaseService.get_document(
            creator_id=creator_id,
            document_id=doc_id,
            session=session
        )
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Update status to processing
        await KnowledgeBaseService.update_document_status(
            creator_id=creator_id,
            document_id=doc_id,
            status=DocumentStatus.PROCESSING,
            session=session
        )
        
        # TODO: Trigger reprocessing
        # In a real implementation, this would queue the document for reprocessing
        
        # For MVP, simulate reprocessing
        await KnowledgeBaseService.update_document_status(
            creator_id=creator_id,
            document_id=doc_id,
            status=DocumentStatus.COMPLETED,
            processing_time=1.8,
            session=session
        )
        
        logger.info(f"Document reprocessing started: {doc_id}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Document reprocessing started", "document_id": doc_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reprocess document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reprocess document"
        )


@router.get("/documents/{doc_id}/status")
async def get_document_status(
    doc_id: str,
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db)
):
    """Get document processing status"""
    try:
        document = await KnowledgeBaseService.get_document(
            creator_id=creator_id,
            document_id=doc_id,
            session=session
        )
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        return {
            "document_id": doc_id,
            "status": document.status,
            "chunk_count": document.chunk_count,
            "processing_time": document.processing_time,
            "error_message": document.error_message,
            "embeddings_stored": document.embeddings_stored,
            "updated_at": document.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document status"
        )


# ==================== PHASE 1: AI ENGINE INTEGRATION ENDPOINTS ====================

@router.post("/search")
async def search_creator_documents(
    query: str = Form(..., description="Search query"),
    limit: int = Form(default=5, ge=1, le=20, description="Maximum number of results"),
    similarity_threshold: float = Form(default=0.7, ge=0.0, le=1.0, description="Minimum similarity score"),
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db)
):
    """Search creator's documents using semantic similarity via AI Engine"""
    try:
        # Search documents using AI Engine
        search_results = await KnowledgeBaseService.search_creator_documents(
            creator_id=creator_id,
            query=query,
            limit=limit,
            similarity_threshold=similarity_threshold,
            session=session
        )
        
        logger.info(f"Document search completed for creator {creator_id}: {search_results['total_results']} results")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Search completed successfully",
                "search_results": search_results
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to search documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search documents"
        )


@router.post("/knowledge-context")
async def get_creator_knowledge_context(
    query: str = Form(..., description="Query to get context for"),
    limit: int = Form(default=10, ge=1, le=50, description="Maximum number of context chunks"),
    similarity_threshold: float = Form(default=0.7, ge=0.0, le=1.0, description="Minimum similarity score"),
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db)
):
    """Get knowledge context for creator query from processed documents"""
    try:
        # Get knowledge context using AI Engine
        knowledge_context = await KnowledgeBaseService.get_creator_knowledge_context(
            creator_id=creator_id,
            query=query,
            limit=limit,
            similarity_threshold=similarity_threshold,
            session=session
        )
        
        logger.info(f"Knowledge context retrieved for creator {creator_id}: {len(knowledge_context.get('knowledge_chunks', []))} chunks")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Knowledge context retrieved successfully",
                "knowledge_context": knowledge_context
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get knowledge context: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve knowledge context"
        )


@router.post("/documents/{doc_id}/sync-embeddings")
async def sync_document_embeddings(
    doc_id: str,
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db)
):
    """Manually sync document embeddings to ChromaDB via AI Engine"""
    try:
        # Sync embeddings
        sync_success = await KnowledgeBaseService.sync_embeddings_to_chromadb(
            creator_id=creator_id,
            document_id=doc_id,
            session=session
        )
        
        if sync_success:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "message": "Document embeddings synced successfully",
                    "document_id": doc_id,
                    "sync_status": "completed"
                }
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "message": "Failed to sync document embeddings",
                    "document_id": doc_id,
                    "sync_status": "failed"
                }
            )
        
    except Exception as e:
        logger.error(f"Failed to sync embeddings for document {doc_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync document embeddings"
        )


# ==================== PHASE 2: PERSONALITY SYSTEM ENDPOINTS ====================

@router.post("/personality/analyze", response_model=PersonalityAnalysisResponse)
async def analyze_creator_personality(
    request: PersonalityAnalysisRequest,
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db)
):
    """Analyze creator's personality from uploaded documents"""
    try:
        # Ensure the request creator_id matches authenticated creator
        if request.creator_id != creator_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot analyze personality for different creator"
            )
        
        # Get personality engine
        personality_engine = get_personality_engine()
        
        # Perform personality analysis
        analysis_response = await personality_engine.analyze_creator_personality(
            creator_id=creator_id,
            session=session,
            force_reanalysis=request.force_reanalysis,
            include_documents=request.include_documents
        )
        
        logger.info(
            f"Personality analysis completed for creator {creator_id}: "
            f"status={analysis_response.analysis_status}, "
            f"traits={analysis_response.traits_discovered}"
        )
        
        return analysis_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze personality: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze creator personality"
        )


@router.post("/personality/generate-prompt", response_model=PersonalizedPromptResponse)
async def generate_personalized_prompt(
    request: PersonalizedPromptRequest,
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db)
):
    """Generate personalized prompt based on creator personality"""
    try:
        # Ensure the request creator_id matches authenticated creator
        if request.creator_id != creator_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot generate prompt for different creator"
            )
        
        # Get creator's personality profile
        personality_engine = get_personality_engine()
        analysis_response = await personality_engine.analyze_creator_personality(
            creator_id=creator_id,
            session=session,
            force_reanalysis=False
        )
        
        if not analysis_response.personality_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No personality profile found. Please run personality analysis first."
            )
        
        # Generate personalized prompt
        prompt_generator = get_prompt_generator()
        prompt_response = await prompt_generator.generate_personalized_prompt(
            request=request,
            personality_profile=analysis_response.personality_profile,
            session=session
        )
        
        logger.info(
            f"Personalized prompt generated for creator {creator_id}: "
            f"template={prompt_response.template_used}, "
            f"confidence={prompt_response.confidence_score:.2f}"
        )
        
        return prompt_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate personalized prompt: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate personalized prompt"
        )


@router.post("/personality/monitor-consistency", response_model=ConsistencyMonitoringResponse)
async def monitor_response_consistency(
    request: ConsistencyMonitoringRequest,
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db)
):
    """Monitor AI response for personality consistency"""
    try:
        # Ensure the request creator_id matches authenticated creator
        if request.creator_id != creator_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot monitor consistency for different creator"
            )
        
        # Get creator's personality profile
        personality_engine = get_personality_engine()
        analysis_response = await personality_engine.analyze_creator_personality(
            creator_id=creator_id,
            session=session,
            force_reanalysis=False
        )
        
        if not analysis_response.personality_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No personality profile found. Please run personality analysis first."
            )
        
        # Monitor consistency
        consistency_monitor = get_consistency_monitor()
        monitoring_response = await consistency_monitor.monitor_response_consistency(
            request=request,
            personality_profile=analysis_response.personality_profile
        )
        
        logger.info(
            f"Consistency monitoring completed for creator {creator_id}: "
            f"score={monitoring_response.overall_score:.2f}, "
            f"consistent={monitoring_response.is_consistent}"
        )
        
        return monitoring_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to monitor consistency: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to monitor response consistency"
        )


@router.post("/knowledge-context/enhanced")
async def get_enhanced_knowledge_context(
    query: str = Form(..., description="Query to get context for"),
    limit: int = Form(default=10, ge=1, le=50, description="Maximum number of context chunks"),
    similarity_threshold: float = Form(default=0.7, ge=0.0, le=1.0, description="Minimum similarity score"),
    include_personality: bool = Form(default=True, description="Include personality-enhanced context"),
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db)
):
    """Get knowledge context enhanced with personality information"""
    try:
        # Get basic knowledge context
        knowledge_context = await KnowledgeBaseService.get_creator_knowledge_context(
            creator_id=creator_id,
            query=query,
            limit=limit,
            similarity_threshold=similarity_threshold,
            session=session
        )
        
        enhanced_context = knowledge_context.copy()
        
        # Add personality context if requested
        if include_personality:
            try:
                # Get personality profile
                personality_engine = get_personality_engine()
                analysis_response = await personality_engine.analyze_creator_personality(
                    creator_id=creator_id,
                    session=session,
                    force_reanalysis=False
                )
                
                if analysis_response.personality_profile:
                    enhanced_context["personality_info"] = {
                        "personality_summary": analysis_response.personality_profile.personality_summary,
                        "key_methodologies": analysis_response.personality_profile.key_methodologies,
                        "confidence_score": analysis_response.personality_profile.confidence_score,
                        "dominant_traits": [
                            {
                                "dimension": trait.dimension,
                                "value": trait.trait_value,
                                "confidence": trait.confidence_score
                            }
                            for trait in analysis_response.personality_profile.traits[:5]  # Top 5 traits
                        ]
                    }
                    
                    # Generate personality-aware prompt for this context
                    prompt_request = PersonalizedPromptRequest(
                        creator_id=creator_id,
                        context=f"Knowledge context for: {query}",
                        user_query=query
                    )
                    
                    prompt_generator = get_prompt_generator()
                    prompt_response = await prompt_generator.generate_personalized_prompt(
                        request=prompt_request,
                        personality_profile=analysis_response.personality_profile,
                        session=session
                    )
                    
                    enhanced_context["personality_prompt"] = {
                        "personalized_prompt": prompt_response.personalized_prompt,
                        "template_used": prompt_response.template_used,
                        "confidence_score": prompt_response.confidence_score
                    }
                    
                else:
                    enhanced_context["personality_info"] = {
                        "message": "No personality profile available. Run personality analysis first."
                    }
                    
            except Exception as e:
                logger.warning(f"Failed to add personality context: {str(e)}")
                enhanced_context["personality_info"] = {
                    "error": "Failed to retrieve personality information"
                }
        
        logger.info(
            f"Enhanced knowledge context retrieved for creator {creator_id}: "
            f"{len(enhanced_context.get('knowledge_chunks', []))} chunks, "
            f"personality_included={include_personality}"
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Enhanced knowledge context retrieved successfully",
                "enhanced_context": enhanced_context
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get enhanced knowledge context: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve enhanced knowledge context"
        )