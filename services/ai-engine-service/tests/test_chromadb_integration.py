"""
Integration tests for ChromaDB multi-tenant functionality
Tests scalability, metadata filtering, and tenant isolation
"""

import pytest
import asyncio
import uuid
from typing import List, Dict, Any
from datetime import datetime

from shared.ai.chromadb_manager import ChromaDBManager, ChromaDBError, EmbeddingMetadata


class TestChromaDBIntegration:
    """Test ChromaDB multi-tenant integration"""
    
    @pytest.fixture
    async def chromadb_manager(self):
        """Create ChromaDB manager for testing"""
        manager = ChromaDBManager(
            chromadb_url="http://localhost:8000",
            shard_count=5,  # Smaller shard count for testing
            max_connections=5
        )
        yield manager
        await manager.close()
    
    @pytest.fixture
    def sample_embeddings(self) -> List[List[float]]:
        """Generate sample embeddings for testing"""
        return [
            [0.1, 0.2, 0.3, 0.4, 0.5] * 20,  # 100-dimensional embedding
            [0.2, 0.3, 0.4, 0.5, 0.6] * 20,
            [0.3, 0.4, 0.5, 0.6, 0.7] * 20
        ]
    
    @pytest.fixture
    def sample_documents(self) -> List[str]:
        """Generate sample documents for testing"""
        return [
            "This is the first test document about AI and machine learning.",
            "The second document discusses natural language processing techniques.",
            "Finally, the third document covers computer vision applications."
        ]
    
    @pytest.fixture
    def sample_metadatas(self) -> List[Dict[str, Any]]:
        """Generate sample metadata for testing"""
        return [
            {
                "document_type": "article",
                "source_file": "test1.pdf",
                "page_number": 1,
                "section": "introduction",
                "token_count": 15
            },
            {
                "document_type": "article", 
                "source_file": "test2.pdf",
                "page_number": 2,
                "section": "methodology",
                "token_count": 12
            },
            {
                "document_type": "article",
                "source_file": "test3.pdf", 
                "page_number": 3,
                "section": "conclusion",
                "token_count": 13
            }
        ]
    
    @pytest.mark.asyncio
    async def test_health_check(self, chromadb_manager):
        """Test ChromaDB health check"""
        health = await chromadb_manager.health_check()
        
        assert health["status"] == "healthy"
        assert "url" in health
        assert "collections_count" in health
        assert "shard_count" in health
        assert health["shard_count"] == 5
        assert "timestamp" in health
    
    @pytest.mark.asyncio
    async def test_shard_name_generation(self, chromadb_manager):
        """Test consistent shard name generation"""
        creator_id = "test-creator-123"
        
        # Should generate same shard name consistently
        shard1 = chromadb_manager._get_shard_name(creator_id)
        shard2 = chromadb_manager._get_shard_name(creator_id)
        
        assert shard1 == shard2
        assert shard1.startswith("knowledge_shard_")
        assert shard1.endswith(str(hash(creator_id) % 5))
    
    @pytest.mark.asyncio
    async def test_collection_creation(self, chromadb_manager):
        """Test collection creation and caching"""
        creator_id = f"test-creator-{uuid.uuid4()}"
        
        # First call should create collection
        collection1 = await chromadb_manager.get_or_create_collection(creator_id)
        assert collection1 is not None
        
        # Second call should return cached collection
        collection2 = await chromadb_manager.get_or_create_collection(creator_id)
        assert collection1.name == collection2.name
    
    @pytest.mark.asyncio
    async def test_add_embeddings(
        self, 
        chromadb_manager, 
        sample_embeddings, 
        sample_documents, 
        sample_metadatas
    ):
        """Test adding embeddings with metadata filtering"""
        creator_id = f"test-creator-{uuid.uuid4()}"
        document_id = f"test-doc-{uuid.uuid4()}"
        
        # Add embeddings
        ids = await chromadb_manager.add_embeddings(
            creator_id=creator_id,
            document_id=document_id,
            embeddings=sample_embeddings,
            documents=sample_documents,
            metadatas=sample_metadatas
        )
        
        assert len(ids) == 3
        assert all(creator_id in id_str for id_str in ids)
        assert all(document_id in id_str for id_str in ids)
    
    @pytest.mark.asyncio
    async def test_query_embeddings_with_tenant_isolation(
        self,
        chromadb_manager,
        sample_embeddings,
        sample_documents,
        sample_metadatas
    ):
        """Test querying embeddings with proper tenant isolation"""
        creator1_id = f"test-creator-1-{uuid.uuid4()}"
        creator2_id = f"test-creator-2-{uuid.uuid4()}"
        document_id = f"test-doc-{uuid.uuid4()}"
        
        # Add embeddings for creator 1
        await chromadb_manager.add_embeddings(
            creator_id=creator1_id,
            document_id=document_id,
            embeddings=sample_embeddings,
            documents=sample_documents,
            metadatas=sample_metadatas
        )
        
        # Add embeddings for creator 2
        await chromadb_manager.add_embeddings(
            creator_id=creator2_id,
            document_id=document_id,
            embeddings=sample_embeddings,
            documents=sample_documents,
            metadatas=sample_metadatas
        )
        
        # Query for creator 1 - should only return creator 1's data
        results1 = await chromadb_manager.query_embeddings(
            creator_id=creator1_id,
            query_embeddings=[sample_embeddings[0]],
            n_results=10
        )
        
        # Verify tenant isolation
        assert len(results1["ids"][0]) > 0
        for metadata in results1["metadatas"][0]:
            assert metadata["creator_id"] == creator1_id
        
        # Query for creator 2 - should only return creator 2's data
        results2 = await chromadb_manager.query_embeddings(
            creator_id=creator2_id,
            query_embeddings=[sample_embeddings[0]],
            n_results=10
        )
        
        # Verify tenant isolation
        assert len(results2["ids"][0]) > 0
        for metadata in results2["metadatas"][0]:
            assert metadata["creator_id"] == creator2_id
        
        # Verify no cross-tenant data leakage
        creator1_ids = set(results1["ids"][0])
        creator2_ids = set(results2["ids"][0])
        assert creator1_ids.isdisjoint(creator2_ids)
    
    @pytest.mark.asyncio
    async def test_delete_document_embeddings(
        self,
        chromadb_manager,
        sample_embeddings,
        sample_documents,
        sample_metadatas
    ):
        """Test deleting document embeddings"""
        creator_id = f"test-creator-{uuid.uuid4()}"
        document_id = f"test-doc-{uuid.uuid4()}"
        
        # Add embeddings
        await chromadb_manager.add_embeddings(
            creator_id=creator_id,
            document_id=document_id,
            embeddings=sample_embeddings,
            documents=sample_documents,
            metadatas=sample_metadatas
        )
        
        # Verify embeddings exist
        results_before = await chromadb_manager.query_embeddings(
            creator_id=creator_id,
            query_embeddings=[sample_embeddings[0]],
            n_results=10
        )
        assert len(results_before["ids"][0]) == 3
        
        # Delete embeddings
        deleted_count = await chromadb_manager.delete_document_embeddings(
            creator_id=creator_id,
            document_id=document_id
        )
        assert deleted_count == 3
        
        # Verify embeddings are deleted
        results_after = await chromadb_manager.query_embeddings(
            creator_id=creator_id,
            query_embeddings=[sample_embeddings[0]],
            n_results=10
        )
        assert len(results_after["ids"][0]) == 0
    
    @pytest.mark.asyncio
    async def test_collection_stats(
        self,
        chromadb_manager,
        sample_embeddings,
        sample_documents,
        sample_metadatas
    ):
        """Test collection statistics generation"""
        creator_id = f"test-creator-{uuid.uuid4()}"
        document_id = f"test-doc-{uuid.uuid4()}"
        
        # Add embeddings
        await chromadb_manager.add_embeddings(
            creator_id=creator_id,
            document_id=document_id,
            embeddings=sample_embeddings,
            documents=sample_documents,
            metadatas=sample_metadatas
        )
        
        # Get stats
        stats = await chromadb_manager.get_collection_stats(creator_id)
        
        assert stats.collection_name.startswith("knowledge_shard_")
        assert stats.document_count >= 1
        assert stats.total_embeddings >= 3
        assert stats.creators_count >= 1
        assert stats.avg_embeddings_per_creator > 0
        assert isinstance(stats.last_updated, datetime)
    
    @pytest.mark.asyncio
    async def test_scalability_with_multiple_creators(
        self,
        chromadb_manager,
        sample_embeddings,
        sample_documents,
        sample_metadatas
    ):
        """Test scalability with multiple creators (simulates 1000+ creators)"""
        num_creators = 50  # Reduced for test performance
        creators = [f"test-creator-{i}-{uuid.uuid4()}" for i in range(num_creators)]
        
        # Add embeddings for multiple creators concurrently
        tasks = []
        for i, creator_id in enumerate(creators):
            document_id = f"test-doc-{i}-{uuid.uuid4()}"
            task = chromadb_manager.add_embeddings(
                creator_id=creator_id,
                document_id=document_id,
                embeddings=sample_embeddings,
                documents=sample_documents,
                metadatas=sample_metadatas
            )
            tasks.append(task)
        
        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all succeeded
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == num_creators
        
        # Verify shard distribution
        shard_distribution = {}
        for creator_id in creators:
            shard_name = chromadb_manager._get_shard_name(creator_id)
            shard_distribution[shard_name] = shard_distribution.get(shard_name, 0) + 1
        
        # Should distribute across multiple shards
        assert len(shard_distribution) > 1
        print(f"Shard distribution: {shard_distribution}")
    
    @pytest.mark.asyncio
    async def test_metadata_filtering(
        self,
        chromadb_manager,
        sample_embeddings,
        sample_documents,
        sample_metadatas
    ):
        """Test advanced metadata filtering"""
        creator_id = f"test-creator-{uuid.uuid4()}"
        document_id = f"test-doc-{uuid.uuid4()}"
        
        # Add embeddings with different metadata
        modified_metadatas = [
            {**meta, "document_type": "article", "page_number": i + 1}
            for i, meta in enumerate(sample_metadatas)
        ]
        
        await chromadb_manager.add_embeddings(
            creator_id=creator_id,
            document_id=document_id,
            embeddings=sample_embeddings,
            documents=sample_documents,
            metadatas=modified_metadatas
        )
        
        # Query with metadata filter
        results = await chromadb_manager.query_embeddings(
            creator_id=creator_id,
            query_embeddings=[sample_embeddings[0]],
            n_results=10,
            where={"page_number": {"$gte": 2}}  # Page 2 and above
        )
        
        # Should return only documents with page_number >= 2
        assert len(results["ids"][0]) == 2
        for metadata in results["metadatas"][0]:
            assert metadata["page_number"] >= 2
    
    @pytest.mark.asyncio
    async def test_error_handling(self, chromadb_manager):
        """Test error handling for invalid operations"""
        creator_id = f"test-creator-{uuid.uuid4()}"
        
        # Test empty embeddings
        with pytest.raises(ValueError, match="embeddings.*cannot be empty"):
            await chromadb_manager.add_embeddings(
                creator_id=creator_id,
                document_id="test-doc",
                embeddings=[],
                documents=[],
                metadatas=[]
            )
        
        # Test mismatched lengths
        with pytest.raises(ValueError, match="must have same length"):
            await chromadb_manager.add_embeddings(
                creator_id=creator_id,
                document_id="test-doc",
                embeddings=[[0.1, 0.2]],
                documents=["doc1", "doc2"],  # Different length
                metadatas=[{"key": "value"}]
            )
    
    @pytest.mark.asyncio
    async def test_connection_pool_management(self, chromadb_manager):
        """Test connection pool limits and management"""
        creator_ids = [f"test-creator-{i}-{uuid.uuid4()}" for i in range(10)]
        
        # Create many concurrent operations to test connection pooling
        tasks = [
            chromadb_manager.get_or_create_collection(creator_id)
            for creator_id in creator_ids
        ]
        
        # Should handle concurrent operations within connection limits
        collections = await asyncio.gather(*tasks)
        assert len(collections) == 10
        assert all(collection is not None for collection in collections)


@pytest.mark.asyncio
async def test_chromadb_manager_singleton():
    """Test ChromaDB manager singleton pattern"""
    from shared.ai.chromadb_manager import get_chromadb_manager, close_chromadb_manager
    
    # Get manager instances
    manager1 = get_chromadb_manager()
    manager2 = get_chromadb_manager()
    
    # Should be same instance
    assert manager1 is manager2
    
    # Cleanup
    await close_chromadb_manager()
    
    # After cleanup, should create new instance
    manager3 = get_chromadb_manager()
    assert manager3 is not manager1
    
    await close_chromadb_manager()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])