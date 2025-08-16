"""
Knowledge Base Management Router
Handles document upload, processing, and organization
"""

import logging
import os
import aiofiles
from typing import List, Optional
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.database import get_tenant_session
from shared.security.auth import get_current_creator_id
from shared.exceptions.base import NotFoundError, DatabaseError

from ..models import (
    KnowledgeDocument, DocumentMetadata, DocumentType, DocumentStatus,
    DocumentUploadRequest, DocumentListResponse
)
from ..database import KnowledgeBaseService

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
    session: AsyncSession = Depends(get_tenant_session)
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
        
        # TODO: Trigger background processing
        # In a real implementation, this would:
        # 1. Extract text from the document
        # 2. Chunk the content
        # 3. Generate embeddings
        # 4. Store in vector database
        # 5. Update status to COMPLETED
        
        # For MVP, simulate successful processing
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
    session: AsyncSession = Depends(get_tenant_session)
):
    """List creator's documents"""
    try:
        result = await KnowledgeBaseService.list_documents(
            creator_id=creator_id,
            page=page,
            page_size=page_size,
            status_filter=status_filter,
            session=session
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
    session: AsyncSession = Depends(get_tenant_session)
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
    session: AsyncSession = Depends(get_tenant_session)
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
    session: AsyncSession = Depends(get_tenant_session)
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
    session: AsyncSession = Depends(get_tenant_session)
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