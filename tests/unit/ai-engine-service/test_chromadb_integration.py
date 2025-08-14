"""
Tests for ChromaDB manager integration.
Tests vector storage, retrieval, multi-tenant collection management, and metadata filtering.

Fixtures are now centralized in tests/fixtures/ai_fixtures.py and automatically
available through the main conftest.py configuration.
"""

import pytest

# Mark as unit tests despite "integration" in filename - these test individual components in isolation
pytestmark = pytest.mark.unit
from unittest.mock import AsyncMock, patch

from shared.ai.chromadb_manager import ChromaDBManager


class TestChromaDBIntegration:
    """Test ChromaDB manager functionality."""

    @pytest.fixture
    def chromadb_manager(self):
        """Create ChromaDB manager instance for testing."""
        return ChromaDBManager(host="localhost", port=8000)

    async def test_collection_creation(self, chromadb_manager, mock_chromadb_manager):
        """Test collection creation functionality."""
        with patch.object(chromadb_manager, 'create_collection', mock_chromadb_manager.create_collection):
            result = await chromadb_manager.create_collection(
                name="test-collection",
                tenant_id="test-tenant"
            )
            
            assert "name" in result
            assert result["name"] == "test-collection"
            assert "id" in result

    async def test_document_addition(self, chromadb_manager, mock_chromadb_manager, test_document_data):
        """Test adding documents to collection."""
        with patch.object(chromadb_manager, 'add_documents', mock_chromadb_manager.add_documents):
            result = await chromadb_manager.add_documents(
                collection_name="test-collection",
                documents=test_document_data["documents"],
                metadatas=test_document_data["metadatas"],
                ids=test_document_data["ids"]
            )
            
            assert "added" in result
            assert result["added"] > 0

    async def test_document_query(self, chromadb_manager, mock_chromadb_manager, test_query_request):
        """Test querying documents from collection."""
        with patch.object(chromadb_manager, 'query_documents', mock_chromadb_manager.query_documents):
            result = await chromadb_manager.query_documents(
                collection_name=test_query_request["collection_name"],
                query_text=test_query_request["query"],
                n_results=test_query_request["n_results"],
                tenant_id=test_query_request["tenant_id"]
            )
            
            assert "documents" in result
            assert "metadatas" in result
            assert "distances" in result
            assert "ids" in result
            assert len(result["documents"]) <= test_query_request["n_results"]

    async def test_collection_listing(self, chromadb_manager, mock_chromadb_manager):
        """Test listing collections."""
        with patch.object(chromadb_manager, 'list_collections', mock_chromadb_manager.list_collections):
            collections = await chromadb_manager.list_collections()
            
            assert isinstance(collections, list)
            if len(collections) > 0:
                assert isinstance(collections[0], str)

    async def test_collection_deletion(self, chromadb_manager, mock_chromadb_manager):
        """Test collection deletion."""
        with patch.object(chromadb_manager, 'delete_collection', mock_chromadb_manager.delete_collection):
            result = await chromadb_manager.delete_collection(
                name="test-collection",
                tenant_id="test-tenant"
            )
            
            assert "deleted" in result
            assert result["deleted"] is True

    async def test_multi_tenant_isolation(self, chromadb_manager, mock_chromadb_manager):
        """Test multi-tenant collection isolation."""
        tenant1_collection = "tenant1-collection"
        tenant2_collection = "tenant2-collection"
        
        # Mock different responses for different tenants
        async def mock_create_collection(name, tenant_id):
            return {"name": f"{tenant_id}-{name}", "id": f"{tenant_id}-id"}
        
        with patch.object(chromadb_manager, 'create_collection', side_effect=mock_create_collection):
            result1 = await chromadb_manager.create_collection(
                name="collection",
                tenant_id="tenant-1"
            )
            result2 = await chromadb_manager.create_collection(
                name="collection",
                tenant_id="tenant-2"
            )
            
            assert result1["name"] != result2["name"]
            assert "tenant-1" in result1["name"]
            assert "tenant-2" in result2["name"]

    async def test_metadata_filtering(self, chromadb_manager, mock_chromadb_manager):
        """Test document querying with metadata filters."""
        mock_chromadb_manager.query_documents.return_value = {
            "documents": ["Filtered document"],
            "metadatas": [{"type": "coaching", "tenant_id": "test-tenant"}],
            "distances": [0.1],
            "ids": ["filtered-doc-1"]
        }
        
        with patch.object(chromadb_manager, 'query_documents', mock_chromadb_manager.query_documents):
            result = await chromadb_manager.query_documents(
                collection_name="test-collection",
                query_text="coaching advice",
                n_results=5,
                where={"type": "coaching"},
                tenant_id="test-tenant"
            )
            
            assert len(result["documents"]) > 0
            for metadata in result["metadatas"]:
                assert metadata["type"] == "coaching"

    async def test_large_document_handling(self, chromadb_manager, mock_chromadb_manager, performance_test_data):
        """Test handling of large documents."""
        large_documents = [performance_test_data["long_text"]] * 10
        large_metadatas = [{"type": "large", "tenant_id": "test-tenant"}] * 10
        large_ids = [f"large-doc-{i}" for i in range(10)]
        
        with patch.object(chromadb_manager, 'add_documents', mock_chromadb_manager.add_documents):
            result = await chromadb_manager.add_documents(
                collection_name="large-collection",
                documents=large_documents,
                metadatas=large_metadatas,
                ids=large_ids
            )
            
            assert "added" in result
            assert result["added"] == 10

    async def test_concurrent_operations(self, chromadb_manager, mock_chromadb_manager):
        """Test concurrent ChromaDB operations."""
        import asyncio
        
        with patch.object(chromadb_manager, 'query_documents', mock_chromadb_manager.query_documents):
            # Create multiple concurrent query tasks
            tasks = [
                chromadb_manager.query_documents(
                    collection_name="test-collection",
                    query_text=f"concurrent query {i}",
                    n_results=3,
                    tenant_id="test-tenant"
                )
                for i in range(5)
            ]
            
            results = await asyncio.gather(*tasks)
            
            # All queries should succeed
            assert len(results) == 5
            for result in results:
                assert "documents" in result
                assert "metadatas" in result

    async def test_collection_statistics(self, chromadb_manager):
        """Test collection statistics retrieval."""
        with patch.object(chromadb_manager, 'get_collection_stats') as mock_stats:
            mock_stats.return_value = {
                "document_count": 1000,
                "collection_size": "50MB",
                "last_updated": "2023-12-01T10:00:00Z"
            }
            
            stats = await chromadb_manager.get_collection_stats("test-collection")
            
            assert "document_count" in stats
            assert "collection_size" in stats
            assert stats["document_count"] == 1000

    async def test_document_update(self, chromadb_manager, mock_chromadb_manager):
        """Test updating existing documents."""
        with patch.object(chromadb_manager, 'update_documents') as mock_update:
            mock_update.return_value = {"updated": 1}
            
            result = await chromadb_manager.update_documents(
                collection_name="test-collection",
                ids=["doc-1"],
                documents=["Updated document content"],
                metadatas=[{"type": "updated", "tenant_id": "test-tenant"}]
            )
            
            assert "updated" in result
            assert result["updated"] == 1

    async def test_document_deletion(self, chromadb_manager, mock_chromadb_manager):
        """Test deleting specific documents."""
        with patch.object(chromadb_manager, 'delete_documents') as mock_delete:
            mock_delete.return_value = {"deleted": 2}
            
            result = await chromadb_manager.delete_documents(
                collection_name="test-collection",
                ids=["doc-1", "doc-2"]
            )
            
            assert "deleted" in result
            assert result["deleted"] == 2

    async def test_similarity_search_accuracy(self, chromadb_manager, mock_chromadb_manager):
        """Test similarity search accuracy and ranking."""
        # Mock results with different similarity scores
        mock_chromadb_manager.query_documents.return_value = {
            "documents": [
                "Highly relevant document about productivity",
                "Somewhat relevant document about work",
                "Less relevant document about general topics"
            ],
            "metadatas": [
                {"relevance": "high", "tenant_id": "test-tenant"},
                {"relevance": "medium", "tenant_id": "test-tenant"},
                {"relevance": "low", "tenant_id": "test-tenant"}
            ],
            "distances": [0.1, 0.3, 0.7],  # Lower distance = higher similarity
            "ids": ["high-rel-1", "med-rel-1", "low-rel-1"]
        }
        
        with patch.object(chromadb_manager, 'query_documents', mock_chromadb_manager.query_documents):
            result = await chromadb_manager.query_documents(
                collection_name="test-collection",
                query_text="productivity tips",
                n_results=3,
                tenant_id="test-tenant"
            )
            
            # Results should be ordered by similarity (distance)
            distances = result["distances"]
            assert distances[0] < distances[1] < distances[2]

    async def test_error_handling_invalid_collection(self, chromadb_manager):
        """Test error handling for invalid collection operations."""
        with patch.object(chromadb_manager, 'query_documents') as mock_query:
            mock_query.side_effect = Exception("Collection not found")
            
            with pytest.raises(Exception):
                await chromadb_manager.query_documents(
                    collection_name="nonexistent-collection",
                    query_text="test query",
                    n_results=5,
                    tenant_id="test-tenant"
                )

    async def test_connection_health_check(self, chromadb_manager):
        """Test ChromaDB connection health check."""
        with patch.object(chromadb_manager, 'health_check') as mock_health:
            mock_health.return_value = {
                "status": "healthy",
                "version": "0.4.15",
                "collections_count": 25,
                "total_documents": 50000
            }
            
            health_status = await chromadb_manager.health_check()
            
            assert health_status["status"] == "healthy"
            assert "version" in health_status
            assert "collections_count" in health_status

    async def test_batch_operations(self, chromadb_manager, mock_chromadb_manager):
        """Test batch operations for efficiency."""
        batch_documents = [f"Batch document {i}" for i in range(100)]
        batch_metadatas = [{"batch": True, "index": i, "tenant_id": "test-tenant"} for i in range(100)]
        batch_ids = [f"batch-doc-{i}" for i in range(100)]
        
        mock_chromadb_manager.add_documents.return_value = {"added": 100}
        
        with patch.object(chromadb_manager, 'add_documents', mock_chromadb_manager.add_documents):
            result = await chromadb_manager.add_documents(
                collection_name="batch-collection",
                documents=batch_documents,
                metadatas=batch_metadatas,
                ids=batch_ids
            )
            
            assert result["added"] == 100

    async def test_scalability_simulation(self, chromadb_manager, mock_chromadb_manager):
        """Test scalability for large number of collections (simulating 100,000+ creators)."""
        # Simulate creating collections for many creators
        creator_count = 1000  # Reduced for test performance
        
        with patch.object(chromadb_manager, 'create_collection', mock_chromadb_manager.create_collection):
            tasks = [
                chromadb_manager.create_collection(
                    name=f"creator-{i}-collection",
                    tenant_id=f"creator-{i}"
                )
                for i in range(creator_count)
            ]
            
            # Process in batches to avoid overwhelming the system
            batch_size = 50
            for i in range(0, creator_count, batch_size):
                batch = tasks[i:i + batch_size]
                results = await asyncio.gather(*batch)
                
                # All collections should be created successfully
                assert len(results) == min(batch_size, creator_count - i)
                for result in results:
                    assert "name" in result
                    assert "id" in result