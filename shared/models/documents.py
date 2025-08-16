"""Document processing models"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from enum import Enum
from .base import TenantAwareEntity


class ProcessingStatus(str, Enum):
    """Document processing status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentChunk(BaseModel):
    """Individual document chunk with embedding"""
    id: str = Field(..., description="Unique chunk identifier")
    content: str = Field(..., description="Text content of the chunk")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk metadata (page, section, etc)")
    embedding_vector: Optional[List[float]] = Field(None, description="Vector embedding for semantic search")
    chunk_index: int = Field(..., ge=0, description="Index of chunk within document")
    token_count: int = Field(..., ge=0, description="Number of tokens in chunk")
    
    @validator('content')
    def validate_content_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Chunk content cannot be empty')
        return v.strip()


class ProcessingResult(TenantAwareEntity):
    """Result of document processing operation"""
    document_id: str = Field(..., description="Unique document identifier")
    status: ProcessingStatus = Field(..., description="Processing status")
    chunks: List[DocumentChunk] = Field(default_factory=list, description="Processed document chunks")
    total_chunks: int = Field(..., ge=0, description="Total number of chunks created")
    processing_time_seconds: float = Field(..., ge=0, description="Time taken to process document")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata")
    
    @validator('total_chunks')
    def validate_chunks_count(cls, v, values):
        if 'chunks' in values and len(values['chunks']) != v:
            raise ValueError('total_chunks must match actual chunks count')
        return v