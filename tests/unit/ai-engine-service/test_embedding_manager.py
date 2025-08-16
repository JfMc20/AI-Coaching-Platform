"""
Tests for Embedding Manager and Search Cache.
Tests advanced caching, search optimization, and query canonicalization.
"""

import pytest
import asyncio
import hashlib
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

try:
    from services.ai_engine_service.app.embedding_manager import (
        EmbeddingManager, SearchCache, QueryCanonicalizer, SearchCacheKey,
        CachedSearchResult, EmbeddingError
    )
except ImportError:
    pytest.skip("Embedding manager components not available", allow_module_level=True)


class TestQueryCanonicalizer:
    """Test query canonicalization functionality."""

    def test_canonicalize_simple_query(self):
        """Test canonicalizing a simple query."""
        query = "  How to Improve PRODUCTIVITY?  "
        canonical = QueryCanonicalizer.canonicalize_query(query)
        
        assert canonical == "how to improve productivity?"
        assert canonical.strip() == canonical  # No leading/trailing whitespace
        assert "  " not in canonical  # No multiple spaces

    def test_canonicalize_unicode_query(self):
        """Test canonicalizing query with unicode characters."""
        query = "Cómo mejorar la productividad? 你好"
        canonical = QueryCanonicalizer.canonicalize_query(query)
        
        assert "cómo" in canonical
        assert "你好" in canonical
        assert canonical == canonical.lower()

    def test_canonicalize_whitespace_normalization(self):
        """Test whitespace normalization in queries."""
        query = "How\n\tto   improve\r\n  productivity"
        canonical = QueryCanonicalizer.canonicalize_query(query)
        
        assert canonical == "how to improve productivity"
        assert "\n" not in canonical
        assert "\t" not in canonical
        assert "\r" not in canonical

    def test_generate_query_hash(self):
        """Test query hash generation."""
        query = "test query"
        hash1 = QueryCanonicalizer.generate_query_hash(query)
        hash2 = QueryCanonicalizer.generate_query_hash(query)
        
        assert hash1 == hash2  # Should be deterministic
        assert len(hash1) == 32  # Should be 32 characters
        assert isinstance(hash1, str)

    def test_generate_query_hash_different_queries(self):
        """Test that different queries generate different hashes."""
        hash1 = QueryCanonicalizer.generate_query_hash("query one")
        hash2 = QueryCanonicalizer.generate_query_hash("query two")
        
        assert hash1 != hash2

    def test_generate_filters_hash(self):
        """Test filters hash generation."""
        filters1 = {"type": "coaching", "date": "2023-01-01"}
        filters2 = {"date": "2023-01-01", "type": "coaching"}  # Different order
        
        hash1 = QueryCanonicalizer.generate_filters_hash(filters1)
        hash2 = QueryCanonicalizer.generate_filters_hash(filters2)
        
        assert hash1 == hash2  # Should be same despite different order
        assert len(hash1) == 16  # Should be 16 characters

    def test_generate_filters_hash_empty(self):
        """Test filters hash generation with empty filters."""
        empty_hash = QueryCanonicalizer.generate_filters_hash({})
        
        assert len(empty_hash) == 16
        assert isinstance(empty_hash, str)


class TestSearchCacheKey:
    """Test search cache key functionality."""

    def test_search_cache_key_creation(self):
        """Test creating search cache key."""
        key = SearchCacheKey(
            creator_id="creator_123",
            query_hash="abcd1234",
            model_version="v1.0",
            filters_hash="efgh5678"
        )
        
        assert key.creator_id == "creator_123"
        assert key.query_hash == "abcd1234"
        assert key.model_version == "v1.0"
        assert key.filters_hash == "efgh5678"

    def test_search_cache_key_to_string(self):
        """Test converting search cache key to string."""
        key = SearchCacheKey(
            creator_id="creator_123",
            query_hash="abcd1234",
            model_version="v1.0",
            filters_hash="efgh5678"
        )
        
        key_string = key.to_string()
        expected = "search:creator_123:abcd1234:v1.0:efgh5678"
        
        assert key_string == expected


class TestCachedSearchResult:
    """Test cached search result functionality."""

    def test_cached_search_result_creation(self):
        """Test creating cached search result."""
        results = [{"document_id": "doc_1", "content": "test"}]
        
        cached_result = CachedSearchResult(
            results=results,
            query="test query",
            timestamp=datetime.utcnow(),
            model_version="v1.0",
            filters={},
            hit_count=0
        )
        
        assert cached_result.results == results
        assert cached_result.query == "test query"
        assert cached_result.hit_count == 0


class TestSearchCache:
    """Test search cache functionality."""

    @pytest.fixture
    def search_cache(self):
        """Create search cache with mocked cache manager."""
        mock_cache_manager = Mock()
        mock_cache_manager.redis = AsyncMock()
        return SearchCache(cache_manager=mock_cache_manager)

    async def test_cache_search_results(self, search_cache):
        """Test caching search results."""
        search_cache.cache_manager.redis.set.return_value = True
        
        results = [{"document_id": "doc_1", "content": "test content"}]
        
        success = await search_cache.cache_search_results(
            creator_id="creator_123",
            query="test query",
            model_version="v1.0",
            filters={},
            results=results
        )
        
        assert success is True
        search_cache.cache_manager.redis.set.assert_called_once()

    async def test_get_cached_search_results_hit(self, search_cache):
        """Test getting cached search results - cache hit."""
        cached_data = {
            "results": [{"document_id": "doc_1"}],
            "query": "test query",
            "timestamp": datetime.utcnow().isoformat(),
            "model_version": "v1.0",
            "filters": {},
            "hit_count": 0
        }
        
        search_cache.cache_manager.redis.get.return_value = cached_data
        search_cache.cache_manager.redis.set.return_value = True
        
        result = await search_cache.get_cached_search_results(
            creator_id="creator_123",
            query="test query",
            model_version="v1.0",
            filters={}
        )
        
        assert result is not None
        assert isinstance(result, CachedSearchResult)
        assert len(result.results) == 1
        assert result.hit_count == 1  # Should be incremented

    async def test_get_cached_search_results_miss(self, search_cache):
        """Test getting cached search results - cache miss."""
        search_cache.cache_manager.redis.get.return_value = None
        
        result = await search_cache.get_cached_search_results(
            creator_id="creator_123",
            query="test query",
            model_version="v1.0",
            filters={}
        )
        
        assert result is None

    async def test_invalidate_search_cache_targeted(self, search_cache):
        """Test targeted cache invalidation for specific document."""
        # Mock cache keys
        search_cache.cache_manager.redis.get_keys_pattern.return_value = [
            "search:creator_123:hash1:v1.0:filters1",
            "search:creator_123:hash2:v1.0:filters2"
        ]
        
        # Mock cached data with document
        cached_data_with_doc = {
            "results": [{"document_id": "doc_to_delete"}]
        }
        cached_data_without_doc = {
            "results": [{"document_id": "other_doc"}]
        }
        
        search_cache.cache_manager.redis.get.side_effect = [
            cached_data_with_doc,
            cached_data_without_doc
        ]
        search_cache.cache_manager.redis.delete.return_value = True
        
        invalidated_count = await search_cache.invalidate_search_cache(
            creator_id="creator_123",
            document_id="doc_to_delete"
        )
        
        assert invalidated_count == 1
        search_cache.cache_manager.redis.delete.assert_called_once()

    async def test_invalidate_search_cache_full(self, search_cache):
        """Test full cache invalidation for creator."""
        search_cache.cache_manager.redis.get_keys_pattern.return_value = [
            "search:creator_123:hash1:v1.0:filters1",
            "search:creator_123:hash2:v1.0:filters2"
        ]
        search_cache.cache_manager.redis.delete.return_value = True
        
        invalidated_count = await search_cache.invalidate_search_cache(
            creator_id="creator_123"
        )
        
        assert invalidated_count == 2
        assert search_cache.cache_manager.redis.delete.call_count == 2

    async def test_build_search_cache_key(self, search_cache):
        """Test building structured search cache key."""
        key = search_cache._build_search_cache_key(
            creator_id="creator_123",
            query="Test Query",
            model_version="v1.0",
            filters={"type": "coaching"}
        )
        
        assert isinstance(key, SearchCacheKey)
        assert key.creator_id == "creator_123"
        assert len(key.query_hash) == 32
        assert key.model_version == "v1.0"
        assert len(key.filters_hash) == 16

    async def test_track_popular_query(self, search_cache):
        """Test tracking popular queries."""
        search_cache.cache_manager.redis.increment.return_value = 6  # Above threshold
        search_cache.cache_manager.redis.expire.return_value = True
        search_cache.cache_manager.redis.set.return_value = True
        
        await search_cache._track_popular_query("creator_123", "popular query")
        
        search_cache.cache_manager.redis.increment.assert_called_once()
        search_cache.cache_manager.redis.set.assert_called_once()  # Should store query text

    async def test_get_popular_queries(self, search_cache):
        """Test getting popular queries."""
        search_cache.cache_manager.redis.get_keys_pattern.return_value = [
            "popular_query:hash1",
            "popular_query:hash2"
        ]
        
        # Mock query counts and texts
        search_cache.cache_manager.redis.get.side_effect = [
            "10",  # Count for hash1
            "popular query 1",  # Text for hash1
            "8",   # Count for hash2
            "popular query 2"   # Text for hash2
        ]
        
        popular_queries = await search_cache._get_popular_queries("creator_123")
        
        assert len(popular_queries) == 2
        assert popular_queries[0]["count"] == 10  # Should be sorted by count
        assert popular_queries[1]["count"] == 8


class TestEmbeddingManager:
    """Test embedding manager functionality."""

    @pytest.fixture
    def embedding_manager(self):
        """Create embedding manager with mocked dependencies."""
        manager = EmbeddingManager()
        manager.ollama_manager = AsyncMock()
        manager.chromadb_manager = AsyncMock()
        manager.cache_manager = AsyncMock()
        manager.search_cache = Mock()
        return manager

    async def test_generate_embeddings_batch_no_cache(self, embedding_manager):
        """Test generating embeddings without cache."""
        texts = ["First text", "Second text"]
        
        # Mock Ollama response
        mock_response = Mock()
        mock_response.embeddings = [
            [0.1, 0.2, 0.3] * 128,  # First embedding
            [0.4, 0.5, 0.6] * 128   # Second embedding
        ]
        embedding_manager.ollama_manager.generate_embeddings.return_value = mock_response
        
        embeddings = await embedding_manager.generate_embeddings_batch(
            texts=texts,
            creator_id="creator_123",
            use_cache=False
        )
        
        assert len(embeddings) == 2
        assert len(embeddings[0]) == 384
        assert len(embeddings[1]) == 384

    async def test_generate_embeddings_batch_with_cache_hit(self, embedding_manager):
        """Test generating embeddings with cache hit."""
        texts = ["Cached text"]
        cached_embedding = [0.1, 0.2, 0.3] * 128
        
        # Mock cache hit
        with patch.object(embedding_manager, '_get_cached_embedding', return_value=cached_embedding):
            embeddings = await embedding_manager.generate_embeddings_batch(
                texts=texts,
                creator_id="creator_123",
                use_cache=True
            )
        
        assert len(embeddings) == 1
        assert embeddings[0] == cached_embedding
        # Ollama should not be called
        embedding_manager.ollama_manager.generate_embeddings.assert_not_called()

    async def test_generate_embeddings_batch_with_cache_miss(self, embedding_manager):
        """Test generating embeddings with cache miss."""
        texts = ["New text"]
        
        # Mock cache miss
        with patch.object(embedding_manager, '_get_cached_embedding', return_value=None):
            with patch.object(embedding_manager, '_cache_embedding', return_value=True):
                # Mock Ollama response
                mock_response = Mock()
                mock_response.embeddings = [[0.1, 0.2, 0.3] * 128]
                embedding_manager.ollama_manager.generate_embeddings.return_value = mock_response
                
                embeddings = await embedding_manager.generate_embeddings_batch(
                    texts=texts,
                    creator_id="creator_123",
                    use_cache=True
                )
        
        assert len(embeddings) == 1
        embedding_manager.ollama_manager.generate_embeddings.assert_called_once()

    async def test_search_similar_documents_with_cache_hit(self, embedding_manager):
        """Test searching documents with cache hit."""
        cached_results = [
            {"document_id": "doc_1", "similarity_score": 0.85}
        ]
        
        mock_cached_result = CachedSearchResult(
            results=cached_results,
            query="test query",
            timestamp=datetime.utcnow(),
            model_version="v1.0",
            filters={},
            hit_count=1
        )
        
        embedding_manager.search_cache.get_cached_search_results.return_value = mock_cached_result
        
        results = await embedding_manager.search_similar_documents(
            query="test query",
            creator_id="creator_123",
            limit=5,
            similarity_threshold=0.7,
            use_cache=True
        )
        
        assert len(results) == 1
        assert results[0]["document_id"] == "doc_1"
        # ChromaDB should not be called
        embedding_manager.chromadb_manager.query_embeddings.assert_not_called()

    async def test_search_similar_documents_with_cache_miss(self, embedding_manager):
        """Test searching documents with cache miss."""
        # Mock cache miss
        embedding_manager.search_cache.get_cached_search_results.return_value = None
        embedding_manager.search_cache.cache_search_results.return_value = True
        
        # Mock embedding generation
        with patch.object(embedding_manager, 'generate_embeddings_batch') as mock_gen:
            mock_gen.return_value = [[0.1, 0.2, 0.3] * 128]
            
            # Mock ChromaDB search
            mock_search_results = {
                "documents": [["Document content"]],
                "metadatas": [[{"document_id": "doc_1", "chunk_index": 0}]],
                "distances": [[0.15]]  # 0.85 similarity
            }
            embedding_manager.chromadb_manager.query_embeddings.return_value = mock_search_results
            
            results = await embedding_manager.search_similar_documents(
                query="test query",
                creator_id="creator_123",
                limit=5,
                similarity_threshold=0.7,
                use_cache=True
            )
        
        assert len(results) == 1
        assert results[0]["document_id"] == "doc_1"
        assert results[0]["similarity_score"] == 0.85
        embedding_manager.chromadb_manager.query_embeddings.assert_called_once()

    async def test_search_similar_documents_filter_by_threshold(self, embedding_manager):
        """Test filtering search results by similarity threshold."""
        embedding_manager.search_cache.get_cached_search_results.return_value = None
        
        with patch.object(embedding_manager, 'generate_embeddings_batch') as mock_gen:
            mock_gen.return_value = [[0.1, 0.2, 0.3] * 128]
            
            # Mock ChromaDB search with mixed similarity scores
            mock_search_results = {
                "documents": [["High similarity doc", "Low similarity doc"]],
                "metadatas": [[
                    {"document_id": "doc_1", "chunk_index": 0},
                    {"document_id": "doc_2", "chunk_index": 0}
                ]],
                "distances": [[0.15, 0.6]]  # 0.85 and 0.4 similarity
            }
            embedding_manager.chromadb_manager.query_embeddings.return_value = mock_search_results
            
            results = await embedding_manager.search_similar_documents(
                query="test query",
                creator_id="creator_123",
                limit=5,
                similarity_threshold=0.7,  # Should filter out 0.4 similarity
                use_cache=False
            )
        
        assert len(results) == 1  # Only high similarity doc
        assert results[0]["document_id"] == "doc_1"
        assert results[0]["similarity_score"] == 0.85

    async def test_invalidate_document_cache(self, embedding_manager):
        """Test invalidating document cache."""
        embedding_manager.search_cache.invalidate_search_cache.return_value = 3
        embedding_manager.cache_manager.redis.delete.return_value = True
        
        success = await embedding_manager.invalidate_document_cache(
            creator_id="creator_123",
            document_id="doc_to_delete"
        )
        
        assert success is True
        embedding_manager.search_cache.invalidate_search_cache.assert_called_once_with(
            "creator_123", "doc_to_delete"
        )

    async def test_get_embedding_stats(self, embedding_manager):
        """Test getting embedding statistics."""
        # Mock ChromaDB stats
        mock_chromadb_stats = Mock()
        mock_chromadb_stats.collection_name = "test_collection"
        mock_chromadb_stats.total_embeddings = 1000
        mock_chromadb_stats.document_count = 50
        mock_chromadb_stats.last_updated = datetime.utcnow()
        
        embedding_manager.chromadb_manager.get_collection_stats.return_value = mock_chromadb_stats
        
        # Mock cache keys
        embedding_manager.cache_manager.redis.get_keys_pattern.return_value = [
            "embedding:hash1",
            "search:hash2",
            "other:hash3"
        ]
        
        stats = await embedding_manager.get_embedding_stats("creator_123")
        
        assert "chromadb_stats" in stats
        assert "cache_stats" in stats
        assert stats["chromadb_stats"]["total_embeddings"] == 1000
        assert stats["cache_stats"]["total_cache_keys"] == 3
        assert stats["cache_stats"]["embedding_cache_keys"] == 1
        assert stats["cache_stats"]["search_cache_keys"] == 1

    async def test_get_cached_embedding(self, embedding_manager):
        """Test getting cached embedding."""
        cached_embedding = [0.1, 0.2, 0.3] * 128
        embedding_manager.cache_manager.redis.get.return_value = cached_embedding
        
        result = await embedding_manager._get_cached_embedding("creator_123", "test text")
        
        assert result == cached_embedding
        
        # Verify cache key generation
        expected_hash = hashlib.sha256("test text".encode('utf-8')).hexdigest()[:32]
        expected_key = f"embedding:{expected_hash}"
        
        embedding_manager.cache_manager.redis.get.assert_called_once_with(
            "creator_123", expected_key
        )

    async def test_cache_embedding(self, embedding_manager):
        """Test caching embedding."""
        embedding = [0.1, 0.2, 0.3] * 128
        embedding_manager.cache_manager.redis.set.return_value = True
        
        success = await embedding_manager._cache_embedding("creator_123", "test text", embedding)
        
        assert success is True
        
        # Verify cache key generation and TTL
        expected_hash = hashlib.sha256("test text".encode('utf-8')).hexdigest()[:32]
        expected_key = f"embedding:{expected_hash}"
        
        embedding_manager.cache_manager.redis.set.assert_called_once_with(
            "creator_123", expected_key, embedding, embedding_manager.search_cache.embedding_cache_ttl
        )

    async def test_generate_embeddings_batch_timeout(self, embedding_manager):
        """Test embedding generation timeout handling."""
        texts = ["Test text"]
        
        # Mock timeout
        embedding_manager.ollama_manager.generate_embeddings.side_effect = asyncio.TimeoutError()
        
        with pytest.raises(EmbeddingError, match="timed out"):
            await embedding_manager.generate_embeddings_batch(
                texts=texts,
                creator_id="creator_123",
                use_cache=False
            )

    async def test_search_similar_documents_error_handling(self, embedding_manager):
        """Test error handling in document search."""
        embedding_manager.search_cache.get_cached_search_results.return_value = None
        
        with patch.object(embedding_manager, 'generate_embeddings_batch') as mock_gen:
            mock_gen.side_effect = Exception("Embedding generation failed")
            
            with pytest.raises(EmbeddingError):
                await embedding_manager.search_similar_documents(
                    query="test query",
                    creator_id="creator_123",
                    use_cache=False
                )


class TestEmbeddingManagerIntegration:
    """Integration tests for embedding manager."""

    async def test_end_to_end_search_flow(self):
        """Test end-to-end search flow with caching."""
        manager = EmbeddingManager()
        
        # Mock all dependencies
        with patch.object(manager, 'ollama_manager') as mock_ollama:
            with patch.object(manager, 'chromadb_manager') as mock_chromadb:
                with patch.object(manager, 'cache_manager') as mock_cache:
                    
                    # Setup search cache
                    manager.search_cache = SearchCache(cache_manager=mock_cache)
                    
                    # Mock cache miss (first search)
                    mock_cache.redis.get.return_value = None
                    mock_cache.redis.set.return_value = True
                    
                    # Mock embedding generation
                    mock_response = Mock()
                    mock_response.embeddings = [[0.1, 0.2, 0.3] * 128]
                    mock_ollama.generate_embeddings.return_value = mock_response
                    
                    # Mock ChromaDB search
                    mock_chromadb.query_embeddings.return_value = {
                        "documents": [["Test document"]],
                        "metadatas": [[{"document_id": "doc_1", "chunk_index": 0}]],
                        "distances": [[0.2]]  # 0.8 similarity
                    }
                    
                    # First search (cache miss)
                    results1 = await manager.search_similar_documents(
                        query="test query",
                        creator_id="creator_123",
                        use_cache=True
                    )
                    
                    assert len(results1) == 1
                    assert results1[0]["document_id"] == "doc_1"
                    
                    # Mock cache hit (second search)
                    cached_result = CachedSearchResult(
                        results=results1,
                        query="test query",
                        timestamp=datetime.utcnow(),
                        model_version="current",
                        filters={},
                        hit_count=0
                    )
                    manager.search_cache.get_cached_search_results = AsyncMock(return_value=cached_result)
                    
                    # Second search (cache hit)
                    results2 = await manager.search_similar_documents(
                        query="test query",
                        creator_id="creator_123",
                        use_cache=True
                    )
                    
                    assert results2 == results1
                    # ChromaDB should only be called once (first search)
                    assert mock_chromadb.query_embeddings.call_count == 1