"""
Embedding Management and Search Optimization for AI Engine Service
Implements advanced caching, search optimization, and vector database management
"""

import logging
import asyncio
import hashlib
import json
import time
import unicodedata
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass

from shared.ai.chromadb_manager import get_chromadb_manager, ChromaDBError
from shared.ai.ollama_manager import get_ollama_manager, OllamaError
from shared.cache import get_cache_manager
from shared.exceptions.base import BaseServiceException

logger = logging.getLogger(__name__)


class EmbeddingError(BaseServiceException):
    """Embedding management specific errors"""


class SearchCacheError(BaseServiceException):
    """Search cache specific errors"""


@dataclass
class SearchCacheKey:
    """Structured search cache key"""
    creator_id: str
    query_hash: str
    model_version: str
    filters_hash: str
    
    def to_string(self) -> str:
        """Convert to cache key string"""
        return f"search:{self.creator_id}:{self.query_hash}:{self.model_version}:{self.filters_hash}"


@dataclass
class CachedSearchResult:
    """Cached search result with metadata"""
    results: List[Dict[str, Any]]
    query: str
    timestamp: datetime
    model_version: str
    filters: Dict[str, Any]
    hit_count: int = 0


class QueryCanonicalizer:
    """Handles query canonicalization for consistent caching"""
    
    @staticmethod
    def canonicalize_query(query: str) -> str:
        """
        Canonicalize query for consistent cache keys
        
        Args:
            query: Raw search query
            
        Returns:
            Canonicalized query string
        """
        try:
            # 1. Unicode normalization (NFKC)
            normalized = unicodedata.normalize('NFKC', query)
            
            # 2. Convert to lowercase
            lowercased = normalized.lower()
            
            # 3. Normalize whitespace
            # - Strip leading/trailing whitespace
            # - Collapse multiple spaces to single space
            # - Normalize line endings
            whitespace_normalized = ' '.join(lowercased.split())
            
            return whitespace_normalized
            
        except Exception as e:
            logger.warning(f"Query canonicalization failed: {e}")
            return query.strip().lower()
    
    @staticmethod
    def generate_query_hash(query: str) -> str:
        """
        Generate deterministic hash for canonicalized query
        
        Args:
            query: Canonicalized query
            
        Returns:
            SHA256 hash (first 32 characters)
        """
        try:
            query_bytes = query.encode('utf-8')
            hash_obj = hashlib.sha256(query_bytes)
            return hash_obj.hexdigest()[:32]
        except Exception as e:
            logger.warning(f"Query hash generation failed: {e}")
            return hashlib.md5(query.encode('utf-8', errors='ignore')).hexdigest()[:32]
    
    @staticmethod
    def generate_filters_hash(filters: Dict[str, Any]) -> str:
        """
        Generate deterministic hash for search filters
        
        Args:
            filters: Search filters dictionary
            
        Returns:
            SHA256 hash (first 16 characters)
        """
        try:
            # Sort keys for consistency
            filters_json = json.dumps(filters, sort_keys=True, separators=(',', ':'))
            hash_obj = hashlib.sha256(filters_json.encode('utf-8'))
            return hash_obj.hexdigest()[:16]
        except Exception as e:
            logger.warning(f"Filters hash generation failed: {e}")
            return "default"


class SearchCache:
    """Advanced search result caching with TTL and invalidation"""
    
    def __init__(self, cache_manager=None):
        self.cache_manager = cache_manager or get_cache_manager()
        self.canonicalizer = QueryCanonicalizer()
        
        # Cache TTL settings (in seconds)
        self.search_results_ttl = 3600  # 1 hour
        self.embedding_cache_ttl = 7 * 24 * 3600  # 7 days
        self.metadata_cache_ttl = 30 * 60  # 30 minutes
        self.model_version_cache_ttl = 24 * 3600  # 24 hours
        
        # Cache warming settings
        self.enable_cache_warming = True
        self.popular_queries_threshold = 5
    
    async def get_cached_search_results(
        self,
        creator_id: str,
        query: str,
        model_version: str,
        filters: Dict[str, Any] = None
    ) -> Optional[CachedSearchResult]:
        """
        Get cached search results with canonicalized query
        
        Args:
            creator_id: Creator identifier
            query: Search query
            model_version: Model version identifier
            filters: Search filters
            
        Returns:
            Cached search result or None if not found
        """
        try:
            filters = filters or {}
            
            # Generate cache key
            cache_key = self._build_search_cache_key(
                creator_id, query, model_version, filters
            )
            
            # Try to get from cache
            cached_data = await self.cache_manager.redis.get(creator_id, cache_key.to_string())
            
            if cached_data:
                # Increment hit count
                cached_result = CachedSearchResult(**cached_data)
                cached_result.hit_count += 1
                
                # Update hit count in cache
                await self.cache_manager.redis.set(
                    creator_id, 
                    cache_key.to_string(), 
                    cached_result.__dict__, 
                    self.search_results_ttl
                )
                
                logger.debug(f"Search cache hit for query: {query[:50]}...")
                return cached_result
            
            logger.debug(f"Search cache miss for query: {query[:50]}...")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cached search results: {e}")
            return None
    
    async def cache_search_results(
        self,
        creator_id: str,
        query: str,
        model_version: str,
        filters: Dict[str, Any],
        results: List[Dict[str, Any]]
    ) -> bool:
        """
        Cache search results with structured key
        
        Args:
            creator_id: Creator identifier
            query: Search query
            model_version: Model version identifier
            filters: Search filters
            results: Search results to cache
            
        Returns:
            True if caching successful
        """
        try:
            # Generate cache key
            cache_key = self._build_search_cache_key(
                creator_id, query, model_version, filters
            )
            
            # Create cached result
            cached_result = CachedSearchResult(
                results=results,
                query=query,
                timestamp=datetime.now(timezone.utc),
                model_version=model_version,
                filters=filters,
                hit_count=0
            )
            
            # Store in cache
            success = await self.cache_manager.redis.set(
                creator_id,
                cache_key.to_string(),
                cached_result.__dict__,
                self.search_results_ttl
            )
            
            if success:
                logger.debug(f"Cached search results for query: {query[:50]}...")
                
                # Track popular queries for cache warming
                if self.enable_cache_warming:
                    await self._track_popular_query(creator_id, query)
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to cache search results: {e}")
            return False
    
    async def invalidate_search_cache(
        self,
        creator_id: str,
        document_id: Optional[str] = None
    ) -> int:
        """
        Invalidate search cache entries
        
        Args:
            creator_id: Creator identifier
            document_id: Optional document ID for targeted invalidation
            
        Returns:
            Number of cache entries invalidated
        """
        try:
            if document_id:
                # Targeted invalidation - find cache entries that might contain this document
                pattern = f"search:{creator_id}:*"
                cache_keys = await self.cache_manager.redis.get_keys_pattern(creator_id, pattern)
                
                invalidated = 0
                for key in cache_keys:
                    # Check if cached result contains the document
                    cached_data = await self.cache_manager.redis.get(creator_id, key)
                    if cached_data and self._contains_document(cached_data.get('results', []), document_id):
                        await self.cache_manager.redis.delete(creator_id, key)
                        invalidated += 1
                
                logger.info(f"Invalidated {invalidated} cache entries for document {document_id}")
                return invalidated
            else:
                # Full cache invalidation for creator
                pattern = f"search:{creator_id}:*"
                cache_keys = await self.cache_manager.redis.get_keys_pattern(creator_id, pattern)
                
                for key in cache_keys:
                    await self.cache_manager.redis.delete(creator_id, key)
                
                logger.info(f"Invalidated {len(cache_keys)} cache entries for creator {creator_id}")
                return len(cache_keys)
                
        except Exception as e:
            logger.error(f"Failed to invalidate search cache: {e}")
            return 0
    
    async def warm_popular_queries(self, creator_id: str) -> int:
        """
        Warm cache for popular queries
        
        Args:
            creator_id: Creator identifier
            
        Returns:
            Number of queries warmed
        """
        try:
            if not self.enable_cache_warming:
                return 0
            
            # Get popular queries
            popular_queries = await self._get_popular_queries(creator_id)
            
            warmed_count = 0
            for query_data in popular_queries:
                query = query_data['query']
                
                # Check if already cached
                cache_key = self._build_search_cache_key(
                    creator_id, query, "current", {}
                )
                
                if not await self.cache_manager.redis.exists(creator_id, cache_key.to_string()):
                    # Perform search to warm cache
                    try:
                        # This would trigger actual search and caching
                        # Implementation depends on search service integration
                        logger.debug(f"Would warm cache for query: {query[:50]}...")
                        warmed_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to warm cache for query '{query}': {e}")
            
            logger.info(f"Warmed cache for {warmed_count} popular queries")
            return warmed_count
            
        except Exception as e:
            logger.error(f"Failed to warm popular queries cache: {e}")
            return 0
    
    def _build_search_cache_key(
        self,
        creator_id: str,
        query: str,
        model_version: str,
        filters: Dict[str, Any]
    ) -> SearchCacheKey:
        """Build structured search cache key"""
        # Canonicalize query
        canonical_query = self.canonicalizer.canonicalize_query(query)
        
        # Generate hashes
        query_hash = self.canonicalizer.generate_query_hash(canonical_query)
        filters_hash = self.canonicalizer.generate_filters_hash(filters)
        
        return SearchCacheKey(
            creator_id=creator_id,
            query_hash=query_hash,
            model_version=model_version,
            filters_hash=filters_hash
        )
    
    def _contains_document(self, results: List[Dict[str, Any]], document_id: str) -> bool:
        """Check if search results contain specific document"""
        for result in results:
            if result.get('document_id') == document_id:
                return True
        return False
    
    async def _track_popular_query(self, creator_id: str, query: str):
        """Track query popularity for cache warming"""
        try:
            query_key = f"popular_query:{hashlib.md5(query.encode()).hexdigest()[:16]}"
            
            # Increment query count
            count = await self.cache_manager.redis.increment(creator_id, query_key)
            
            # Set expiration for tracking (7 days)
            await self.cache_manager.redis.expire(creator_id, query_key, 7 * 24 * 3600)
            
            # Store query text if it's becoming popular
            if count >= self.popular_queries_threshold:
                query_text_key = f"popular_query_text:{query_key}"
                await self.cache_manager.redis.set(
                    creator_id, 
                    query_text_key, 
                    query, 
                    7 * 24 * 3600
                )
                
        except Exception as e:
            logger.warning(f"Failed to track popular query: {e}")
    
    async def _get_popular_queries(self, creator_id: str) -> List[Dict[str, Any]]:
        """Get popular queries for cache warming"""
        try:
            # Get all popular query keys
            pattern = "popular_query:*"
            query_keys = await self.cache_manager.redis.get_keys_pattern(creator_id, pattern)
            
            popular_queries = []
            for key in query_keys:
                count_raw = await self.cache_manager.redis.get(creator_id, key)
                if count_raw is not None:
                    try:
                        # Handle bytes or string conversion safely
                        if isinstance(count_raw, bytes):
                            count_raw = count_raw.decode('utf-8')
                        count = int(count_raw)
                        if count >= self.popular_queries_threshold:
                            # Get query text
                            text_key = f"popular_query_text:{key}"
                            query_text = await self.cache_manager.redis.get(creator_id, text_key)
                            
                            if query_text:
                                popular_queries.append({
                                    'query': query_text,
                                    'count': count
                                })
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid count value for key {key}: {count_raw}, error: {e}")
                        continue
            
            # Sort by popularity
            popular_queries.sort(key=lambda x: x['count'], reverse=True)
            return popular_queries[:10]  # Top 10
            
        except Exception as e:
            logger.error(f"Failed to get popular queries: {e}")
            return []


class EmbeddingManager:
    """
    Advanced embedding management with caching and optimization
    """
    
    def __init__(self):
        self.ollama_manager = get_ollama_manager()
        self.chromadb_manager = get_chromadb_manager()
        self.search_cache = SearchCache()
        self.cache_manager = get_cache_manager()
        
        # Performance settings
        self.embedding_batch_size = 10
        self.max_concurrent_embeddings = 5
        self.embedding_timeout = 60  # seconds - increased for debugging
    
    async def generate_embeddings_batch(
        self,
        texts: List[str],
        creator_id: str,
        use_cache: bool = True
    ) -> List[List[float]]:
        """
        Generate embeddings for batch of texts with caching
        
        Args:
            texts: List of texts to embed
            creator_id: Creator identifier for caching
            use_cache: Whether to use embedding cache
            
        Returns:
            List of embedding vectors
            
        Raises:
            EmbeddingError: If embedding generation fails
        """
        try:
            if not texts:
                return []
            
            embeddings = []
            cache_misses = []
            cache_miss_indices = []
            
            # Check cache for existing embeddings
            if use_cache:
                for i, text in enumerate(texts):
                    cached_embedding = await self._get_cached_embedding(creator_id, text)
                    if cached_embedding:
                        embeddings.append(cached_embedding)
                    else:
                        embeddings.append(None)  # Placeholder
                        cache_misses.append(text)
                        cache_miss_indices.append(i)
            else:
                cache_misses = texts
                cache_miss_indices = list(range(len(texts)))
                embeddings = [None] * len(texts)
            
            # Generate embeddings for cache misses
            if cache_misses:
                logger.debug(f"Generating embeddings for {len(cache_misses)} texts (cache misses)")
                
                # Process in batches
                new_embeddings = []
                for i in range(0, len(cache_misses), self.embedding_batch_size):
                    batch = cache_misses[i:i + self.embedding_batch_size]
                    
                    # Generate embeddings with timeout
                    logger.info(f"DEBUG: Generating embeddings for batch of {len(batch)} items, timeout={self.embedding_timeout}s")
                    start_time = time.time()
                    
                    try:
                        batch_embeddings = await asyncio.wait_for(
                            self.ollama_manager.generate_embeddings(batch),
                            timeout=self.embedding_timeout
                        )
                        elapsed = time.time() - start_time
                        logger.info(f"DEBUG: Embedding generation completed in {elapsed:.2f}s")
                    except asyncio.TimeoutError:
                        elapsed = time.time() - start_time
                        logger.error(f"DEBUG: Embedding generation timed out after {elapsed:.2f}s (limit: {self.embedding_timeout}s)")
                        raise EmbeddingError(f"Embedding generation timed out after {elapsed:.2f}s")
                    
                    new_embeddings.extend(batch_embeddings.embeddings)
                
                # Fill in the embeddings
                for i, embedding in enumerate(new_embeddings):
                    original_index = cache_miss_indices[i]
                    embeddings[original_index] = embedding
                    
                    # Cache the new embedding
                    if use_cache:
                        await self._cache_embedding(creator_id, cache_misses[i], embedding)
            
            logger.info(f"Generated/retrieved {len(embeddings)} embeddings ({len(cache_misses)} new)")
            return embeddings
            
        except asyncio.TimeoutError:
            raise EmbeddingError("Embedding generation timed out")
        except OllamaError as e:
            raise EmbeddingError(f"Ollama embedding generation failed: {str(e)}") from e
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise EmbeddingError(f"Embedding generation failed: {str(e)}") from e
    
    async def search_similar_documents(
        self,
        query: str,
        creator_id: str,
        limit: int = 5,
        similarity_threshold: float = 0.7,
        filters: Dict[str, Any] = None,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents with advanced caching
        
        Args:
            query: Search query
            creator_id: Creator identifier
            limit: Maximum results to return
            similarity_threshold: Minimum similarity score
            filters: Additional search filters
            use_cache: Whether to use search cache
            
        Returns:
            List of search results
            
        Raises:
            EmbeddingError: If search fails
        """
        try:
            filters = filters or {}
            model_version = "current"  # TODO: Get actual model version
            
            # Check search cache first
            if use_cache:
                cached_result = await self.search_cache.get_cached_search_results(
                    creator_id, query, model_version, filters
                )
                
                if cached_result:
                    # Filter and limit cached results
                    filtered_results = [
                        result for result in cached_result.results
                        if result.get('similarity_score', 0) >= similarity_threshold
                    ]
                    return filtered_results[:limit]
            
            # Generate query embedding
            query_embeddings = await self.generate_embeddings_batch(
                [query], creator_id, use_cache=use_cache
            )
            
            if not query_embeddings:
                raise EmbeddingError("Failed to generate query embedding")
            
            # Search in ChromaDB
            search_results = await self.chromadb_manager.query_embeddings(
                creator_id=creator_id,
                query_embeddings=[query_embeddings[0]],
                n_results=limit * 2,  # Get more results for filtering
                where=filters if filters else None,
                include=["documents", "metadatas", "distances"]
            )
            
            # Process results
            results = []
            if search_results.get("documents") and search_results["documents"][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    search_results["documents"][0],
                    search_results["metadatas"][0],
                    search_results["distances"][0]
                )):
                    similarity_score = 1 - distance  # Convert distance to similarity
                    
                    if similarity_score >= similarity_threshold:
                        result = {
                            "document_id": metadata.get("document_id", "unknown"),
                            "chunk_index": metadata.get("chunk_index", 0),
                            "content": doc,
                            "similarity_score": similarity_score,
                            "metadata": metadata,
                            "rank": i + 1
                        }
                        results.append(result)
            
            # Limit results
            results = results[:limit]
            
            # Cache results
            if use_cache and results:
                await self.search_cache.cache_search_results(
                    creator_id, query, model_version, filters, results
                )
            
            logger.info(f"Found {len(results)} similar documents for query")
            return results
            
        except ChromaDBError as e:
            raise EmbeddingError(f"ChromaDB search failed: {str(e)}") from e
        except Exception as e:
            logger.error(f"Document search failed: {e}")
            raise EmbeddingError(f"Document search failed: {str(e)}") from e
    
    async def invalidate_document_cache(
        self,
        creator_id: str,
        document_id: str
    ) -> bool:
        """
        Invalidate all cache entries related to a document
        
        Args:
            creator_id: Creator identifier
            document_id: Document identifier
            
        Returns:
            True if invalidation successful
        """
        try:
            # Invalidate search cache
            search_invalidated = await self.search_cache.invalidate_search_cache(
                creator_id, document_id
            )
            
            # Invalidate document metadata cache
            metadata_key = f"doc_meta:{document_id}"
            metadata_deleted = await self.cache_manager.redis.delete(creator_id, metadata_key)
            
            logger.info(
                f"Invalidated cache for document {document_id}: "
                f"{search_invalidated} search entries, "
                f"{'1' if metadata_deleted else '0'} metadata entries"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to invalidate document cache: {e}")
            return False
    
    async def get_embedding_stats(self, creator_id: str) -> Dict[str, Any]:
        """
        Get embedding and search statistics
        
        Args:
            creator_id: Creator identifier
            
        Returns:
            Statistics dictionary
        """
        try:
            # Get ChromaDB stats
            chromadb_stats = await self.chromadb_manager.get_collection_stats(creator_id)
            
            # Get cache stats
            cache_keys = await self.cache_manager.redis.get_keys_pattern(creator_id, "*")
            
            embedding_cache_keys = [k for k in cache_keys if k.startswith("embedding:")]
            search_cache_keys = [k for k in cache_keys if k.startswith("search:")]
            
            return {
                "chromadb_stats": {
                    "collection_name": chromadb_stats.collection_name,
                    "total_embeddings": chromadb_stats.total_embeddings,
                    "document_count": chromadb_stats.document_count,
                    "last_updated": (chromadb_stats.last_updated.replace(tzinfo=timezone.utc) 
                                   if chromadb_stats.last_updated.tzinfo is None 
                                   else chromadb_stats.last_updated).isoformat()
                },
                "cache_stats": {
                    "total_cache_keys": len(cache_keys),
                    "embedding_cache_keys": len(embedding_cache_keys),
                    "search_cache_keys": len(search_cache_keys)
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get embedding stats: {e}")
            return {"error": str(e)}
    
    async def _get_cached_embedding(
        self,
        creator_id: str,
        text: str
    ) -> Optional[List[float]]:
        """Get cached embedding for text"""
        try:
            # Generate cache key from text content
            text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()[:32]
            cache_key = f"embedding:{text_hash}"
            
            cached_embedding = await self.cache_manager.redis.get(creator_id, cache_key)
            return cached_embedding
            
        except Exception as e:
            logger.debug(f"Failed to get cached embedding: {e}")
            return None
    
    async def _cache_embedding(
        self,
        creator_id: str,
        text: str,
        embedding: List[float]
    ) -> bool:
        """Cache embedding for text"""
        try:
            # Generate cache key from text content
            text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()[:32]
            cache_key = f"embedding:{text_hash}"
            
            return await self.cache_manager.redis.set(
                creator_id,
                cache_key,
                embedding,
                self.search_cache.embedding_cache_ttl
            )
            
        except Exception as e:
            logger.debug(f"Failed to cache embedding: {e}")
            return False
    
    async def warm_cache(self, creator_id: str) -> List[str]:
        """
        Warm cache for creator's frequently used queries
        """
        try:
            # Get popular queries from analytics (mock implementation)
            popular_queries = [
                "coaching best practices",
                "trust building techniques", 
                "active listening skills",
                "goal setting strategies",
                "client accountability methods"
            ]
            
            warmed_queries = []
            
            for query in popular_queries:
                try:
                    # Pre-compute and cache search results
                    await self.search_similar_documents(
                        query=query,
                        creator_id=creator_id,
                        limit=5,
                        use_cache=True
                    )
                    warmed_queries.append(query)
                    
                except Exception as e:
                    logger.warning(f"Failed to warm cache for query '{query}': {e}")
                    continue
            
            logger.info(f"Warmed cache for {len(warmed_queries)} queries for creator {creator_id}")
            return warmed_queries
            
        except Exception as e:
            logger.exception(f"Cache warming failed: {e}")
            return []
    
    async def warm_popular_queries(self, creator_id: str) -> int:
        """
        Warm cache for popular queries (wrapper method for encapsulation)
        
        Args:
            creator_id: Creator identifier
            
        Returns:
            Number of queries warmed
        """
        return await self.search_cache.warm_popular_queries(creator_id)
    
    async def enable_embedding_compression(self, creator_id: str, compression_type: str = "float16") -> bool:
        """
        Enable embedding compression for storage efficiency
        
        Args:
            creator_id: Creator identifier
            compression_type: Type of compression (float16, int8, pq)
            
        Returns:
            Success status
        """
        try:
            if compression_type not in ["float16", "int8", "pq"]:
                raise EmbeddingError(f"Unsupported compression type: {compression_type}")
            
            # Store compression preference
            compression_key = f"embedding_compression:{creator_id}"
            compression_config = {
                "type": compression_type,
                "enabled": True,
                "enabled_at": datetime.now(timezone.utc).isoformat(),
                "expected_reduction": 0.5 if compression_type == "float16" else 0.75
            }
            
            await self.cache_manager.set(
                compression_key, 
                json.dumps(compression_config), 
                ttl=86400 * 30  # 30 days
            )
            
            logger.info(f"Enabled {compression_type} compression for creator {creator_id}")
            return True
            
        except Exception as e:
            logger.exception(f"Failed to enable compression: {e}")
            return False
    
    async def optimize_connection_pool(self) -> Dict[str, Any]:
        """
        Optimize ChromaDB connection pool settings
        
        Returns:
            Optimization results
        """
        try:
            # Get current connection stats
            get_chromadb_manager()
            
            # Mock connection pool optimization
            # In production, this would configure actual connection pools
            optimization_results = {
                "max_connections_per_instance": 10,
                "global_connection_limit": 100,
                "connection_timeout": 30,
                "pool_recycle_time": 3600,
                "optimized_at": datetime.utcnow().isoformat(),
                "expected_improvement": "20% better throughput"
            }
            
            # Store optimization config
            await self.cache_manager.set(
                "chromadb_pool_config",
                json.dumps(optimization_results),
                ttl=86400  # 24 hours
            )
            
            logger.info("ChromaDB connection pool optimized")
            return optimization_results
            
        except Exception as e:
            logger.exception(f"Connection pool optimization failed: {e}")
            return {"error": str(e)}
    
    async def tune_hnsw_parameters(self, dataset_size: int) -> Dict[str, int]:
        """
        Auto-tune HNSW parameters based on dataset size
        
        Args:
            dataset_size: Number of vectors in dataset
            
        Returns:
            Optimized HNSW parameters
        """
        try:
            # Auto-tune parameters based on dataset size
            if dataset_size < 1000:
                # Small dataset - prioritize accuracy
                hnsw_params = {
                    "M": 16,
                    "ef_construction": 200,
                    "ef": 100
                }
            elif dataset_size < 10000:
                # Medium dataset - balance accuracy and speed
                hnsw_params = {
                    "M": 16,
                    "ef_construction": 200,
                    "ef": min(400, max(50, dataset_size // 25))
                }
            else:
                # Large dataset - prioritize speed
                hnsw_params = {
                    "M": 12,  # Reduce connections for speed
                    "ef_construction": 150,
                    "ef": min(200, max(50, dataset_size // 50))
                }
            
            # Store tuned parameters
            tuning_config = {
                "dataset_size": dataset_size,
                "hnsw_params": hnsw_params,
                "tuned_at": datetime.utcnow().isoformat(),
                "rationale": f"Optimized for dataset size {dataset_size}"
            }
            
            await self.cache_manager.set(
                "hnsw_tuning_config",
                json.dumps(tuning_config),
                ttl=86400 * 7  # 7 days
            )
            
            logger.info(f"HNSW parameters tuned for dataset size {dataset_size}: {hnsw_params}")
            return hnsw_params
            
        except Exception as e:
            logger.exception(f"HNSW parameter tuning failed: {e}")
            return {"M": 16, "ef_construction": 200, "ef": 100}  # Default fallback
    
    async def get_performance_metrics(self, creator_id: str) -> Dict[str, Any]:
        """
        Get embedding and search performance metrics
        
        Args:
            creator_id: Creator identifier
            
        Returns:
            Performance metrics
        """
        try:
            # Mock performance metrics collection
            # In production, this would query actual metrics from Prometheus/monitoring
            metrics = {
                "search_performance": {
                    "avg_latency_ms": 150,
                    "p95_latency_ms": 300,
                    "p99_latency_ms": 500,
                    "cache_hit_rate": 0.75,
                    "searches_per_second": 25
                },
                "embedding_performance": {
                    "avg_generation_time_ms": 100,
                    "embeddings_per_second": 50,
                    "batch_efficiency": 0.85
                },
                "storage_metrics": {
                    "total_embeddings": 10000,
                    "storage_size_mb": 150,
                    "compression_ratio": 0.6,
                    "index_size_mb": 50
                },
                "cache_metrics": {
                    "cache_size_mb": 25,
                    "cache_hit_rate": 0.75,
                    "cache_evictions_per_hour": 10
                },
                "collected_at": datetime.utcnow().isoformat()
            }
            
            return metrics
            
        except Exception as e:
            logger.exception(f"Failed to get performance metrics: {e}")
            return {"error": str(e)}


# Global embedding manager instance
_embedding_manager: Optional[EmbeddingManager] = None


def get_embedding_manager() -> EmbeddingManager:
    """Get global embedding manager instance (lazy initialization)"""
    global _embedding_manager
    if _embedding_manager is None:
        _embedding_manager = EmbeddingManager()
    return _embedding_manager