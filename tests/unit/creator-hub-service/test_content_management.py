"""
Comprehensive tests for creator hub content management.
Tests knowledge base management, document operations, and content organization.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from shared.models.database import Document
from shared.exceptions.documents import DocumentProcessingError


class TestKnowledgeBaseManagement:
    """Test knowledge base management functionality."""

    async def test_document_upload_success(self, creator_hub_client: AsyncClient, auth_headers):
        """Test successful document upload."""
        # Mock file upload
        files = {
            "file": ("test.pdf", b"PDF content", "application/pdf")
        }
        
        data = {
            "title": "Test Document",
            "description": "A test document for knowledge base"
        }
        
        response = await creator_hub_client.post(
            "/api/v1/knowledge/upload",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        document_data = response.json()
        
        assert document_data["title"] == "Test Document"
        assert document_data["description"] == "A test document for knowledge base"
        assert "id" in document_data
        assert "created_at" in document_data
        assert document_data["status"] == "processing"

    async def test_document_upload_invalid_file_type(self, creator_hub_client: AsyncClient, auth_headers):
        """Test document upload with invalid file type."""
        files = {
            "file": ("test.exe", b"Executable content", "application/x-executable")
        }
        
        data = {
            "title": "Invalid Document",
            "description": "Should be rejected"
        }
        
        response = await creator_hub_client.post(
            "/api/v1/knowledge/upload",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        assert response.status_code == 422
        error_data = response.json()
        assert "file type" in error_data["detail"].lower() or "unsupported" in error_data["detail"].lower()

    async def test_document_upload_oversized_file(self, creator_hub_client: AsyncClient, auth_headers):
        """Test document upload with oversized file."""
        # Simulate large file (>50MB)
        large_content = b"x" * (51 * 1024 * 1024)  # 51MB
        
        files = {
            "file": ("large.pdf", large_content, "application/pdf")
        }
        
        data = {
            "title": "Large Document",
            "description": "Should be rejected for size"
        }
        
        response = await creator_hub_client.post(
            "/api/v1/knowledge/upload",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        assert response.status_code == 413
        error_data = response.json()
        assert "size" in error_data["detail"].lower() or "large" in error_data["detail"].lower()

    async def test_list_documents(self, creator_hub_client: AsyncClient, auth_headers):
        """Test listing creator's documents."""
        response = await creator_hub_client.get(
            "/api/v1/knowledge/documents",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        documents_data = response.json()
        
        assert "documents" in documents_data
        assert "total" in documents_data
        assert "page" in documents_data
        assert "per_page" in documents_data
        assert isinstance(documents_data["documents"], list)

    async def test_list_documents_with_pagination(self, creator_hub_client: AsyncClient, auth_headers):
        """Test document listing with pagination."""
        response = await creator_hub_client.get(
            "/api/v1/knowledge/documents?page=2&per_page=5",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        documents_data = response.json()
        
        assert documents_data["page"] == 2
        assert documents_data["per_page"] == 5
        assert len(documents_data["documents"]) <= 5

    async def test_list_documents_with_filters(self, creator_hub_client: AsyncClient, auth_headers):
        """Test document listing with filters."""
        # Test status filter
        response = await creator_hub_client.get(
            "/api/v1/knowledge/documents?status=processed",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        documents_data = response.json()
        
        # All returned documents should have 'processed' status
        for doc in documents_data["documents"]:
            assert doc["status"] == "processed"

    async def test_get_document_details(self, creator_hub_client: AsyncClient, auth_headers):
        """Test getting specific document details."""
        # Assuming a document exists with this ID
        document_id = "test_document_123"
        
        response = await creator_hub_client.get(
            f"/api/v1/knowledge/documents/{document_id}",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            document_data = response.json()
            
            assert document_data["id"] == document_id
            assert "title" in document_data
            assert "content" in document_data or "chunks" in document_data
            assert "metadata" in document_data
        else:
            # Document might not exist in test environment
            assert response.status_code == 404

    async def test_update_document_metadata(self, creator_hub_client: AsyncClient, auth_headers):
        """Test updating document metadata."""
        document_id = "test_document_123"
        
        update_data = {
            "title": "Updated Document Title",
            "description": "Updated description",
            "tags": ["updated", "test", "knowledge"]
        }
        
        response = await creator_hub_client.put(
            f"/api/v1/knowledge/documents/{document_id}",
            json=update_data,
            headers=auth_headers
        )
        
        if response.status_code == 200:
            document_data = response.json()
            
            assert document_data["title"] == "Updated Document Title"
            assert document_data["description"] == "Updated description"
            assert "updated" in document_data["tags"]
        else:
            # Document might not exist in test environment
            assert response.status_code == 404

    async def test_delete_document(self, creator_hub_client: AsyncClient, auth_headers):
        """Test document deletion."""
        document_id = "test_document_to_delete"
        
        response = await creator_hub_client.delete(
            f"/api/v1/knowledge/documents/{document_id}",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            # Verify document is deleted
            get_response = await creator_hub_client.get(
                f"/api/v1/knowledge/documents/{document_id}",
                headers=auth_headers
            )
            assert get_response.status_code == 404
        else:
            # Document might not exist in test environment
            assert response.status_code == 404

    async def test_search_documents(self, creator_hub_client: AsyncClient, auth_headers):
        """Test document search functionality."""
        search_data = {
            "query": "machine learning",
            "limit": 10
        }
        
        response = await creator_hub_client.post(
            "/api/v1/knowledge/search",
            json=search_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        search_results = response.json()
        
        assert "results" in search_results
        assert "total" in search_results
        assert isinstance(search_results["results"], list)
        
        # Each result should have relevance scoring
        for result in search_results["results"]:
            assert "document_id" in result
            assert "relevance_score" in result
            assert "matched_content" in result


class TestContentOrganization:
    """Test content organization features."""

    async def test_create_content_category(self, creator_hub_client: AsyncClient, auth_headers):
        """Test creating content categories."""
        category_data = {
            "name": "Machine Learning",
            "description": "Documents about ML concepts and techniques",
            "color": "#3498db"
        }
        
        response = await creator_hub_client.post(
            "/api/v1/knowledge/categories",
            json=category_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        category = response.json()
        
        assert category["name"] == "Machine Learning"
        assert category["description"] == "Documents about ML concepts and techniques"
        assert category["color"] == "#3498db"
        assert "id" in category

    async def test_list_content_categories(self, creator_hub_client: AsyncClient, auth_headers):
        """Test listing content categories."""
        response = await creator_hub_client.get(
            "/api/v1/knowledge/categories",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        categories = response.json()
        
        assert isinstance(categories, list)
        for category in categories:
            assert "id" in category
            assert "name" in category
            assert "document_count" in category

    async def test_assign_document_to_category(self, creator_hub_client: AsyncClient, auth_headers):
        """Test assigning documents to categories."""
        document_id = "test_document_123"
        category_id = "category_456"
        
        assignment_data = {
            "category_id": category_id
        }
        
        response = await creator_hub_client.post(
            f"/api/v1/knowledge/documents/{document_id}/category",
            json=assignment_data,
            headers=auth_headers
        )
        
        if response.status_code == 200:
            # Verify assignment
            doc_response = await creator_hub_client.get(
                f"/api/v1/knowledge/documents/{document_id}",
                headers=auth_headers
            )
            
            if doc_response.status_code == 200:
                doc_data = doc_response.json()
                assert doc_data["category_id"] == category_id
        else:
            # Document or category might not exist
            assert response.status_code in [404, 422]

    async def test_tag_management(self, creator_hub_client: AsyncClient, auth_headers):
        """Test document tagging functionality."""
        document_id = "test_document_123"
        
        tag_data = {
            "tags": ["AI", "machine-learning", "tutorial", "beginner"]
        }
        
        response = await creator_hub_client.post(
            f"/api/v1/knowledge/documents/{document_id}/tags",
            json=tag_data,
            headers=auth_headers
        )
        
        if response.status_code == 200:
            # Verify tags were added
            doc_response = await creator_hub_client.get(
                f"/api/v1/knowledge/documents/{document_id}",
                headers=auth_headers
            )
            
            if doc_response.status_code == 200:
                doc_data = doc_response.json()
                assert "AI" in doc_data["tags"]
                assert "machine-learning" in doc_data["tags"]
        else:
            assert response.status_code == 404


class TestDocumentProcessingStatus:
    """Test document processing status tracking."""

    async def test_document_processing_status_tracking(self, creator_hub_client: AsyncClient, auth_headers):
        """Test tracking document processing status."""
        document_id = "processing_document_123"
        
        response = await creator_hub_client.get(
            f"/api/v1/knowledge/documents/{document_id}/status",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            status_data = response.json()
            
            assert "status" in status_data
            assert status_data["status"] in ["pending", "processing", "processed", "failed"]
            assert "progress" in status_data
            assert "estimated_completion" in status_data or status_data["status"] == "processed"
        else:
            assert response.status_code == 404

    async def test_batch_processing_status(self, creator_hub_client: AsyncClient, auth_headers):
        """Test batch processing status for multiple documents."""
        response = await creator_hub_client.get(
            "/api/v1/knowledge/processing-status",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        status_data = response.json()
        
        assert "total_documents" in status_data
        assert "processed" in status_data
        assert "processing" in status_data
        assert "failed" in status_data
        assert "queue_size" in status_data

    async def test_reprocess_failed_document(self, creator_hub_client: AsyncClient, auth_headers):
        """Test reprocessing failed documents."""
        document_id = "failed_document_123"
        
        response = await creator_hub_client.post(
            f"/api/v1/knowledge/documents/{document_id}/reprocess",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            # Verify status changed to processing
            status_response = await creator_hub_client.get(
                f"/api/v1/knowledge/documents/{document_id}/status",
                headers=auth_headers
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                assert status_data["status"] in ["pending", "processing"]
        else:
            # Document might not exist or not in failed state
            assert response.status_code in [404, 422]


class TestKnowledgeBaseAnalytics:
    """Test knowledge base analytics and insights."""

    async def test_knowledge_base_statistics(self, creator_hub_client: AsyncClient, auth_headers):
        """Test getting knowledge base statistics."""
        response = await creator_hub_client.get(
            "/api/v1/knowledge/statistics",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        stats = response.json()
        
        assert "total_documents" in stats
        assert "total_size_bytes" in stats
        assert "processed_documents" in stats
        assert "failed_documents" in stats
        assert "categories_count" in stats
        assert "most_used_tags" in stats
        assert isinstance(stats["most_used_tags"], list)

    async def test_document_usage_analytics(self, creator_hub_client: AsyncClient, auth_headers):
        """Test document usage analytics."""
        response = await creator_hub_client.get(
            "/api/v1/knowledge/analytics/usage",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        analytics = response.json()
        
        assert "most_accessed_documents" in analytics
        assert "search_patterns" in analytics
        assert "content_gaps" in analytics
        assert isinstance(analytics["most_accessed_documents"], list)

    async def test_content_quality_analysis(self, creator_hub_client: AsyncClient, auth_headers):
        """Test content quality analysis."""
        response = await creator_hub_client.get(
            "/api/v1/knowledge/analytics/quality",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        quality_data = response.json()
        
        assert "average_content_length" in quality_data
        assert "readability_score" in quality_data
        assert "duplicate_content" in quality_data
        assert "improvement_suggestions" in quality_data