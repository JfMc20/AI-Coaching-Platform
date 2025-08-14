"""
ChromaDB Multi-Tenant Manager
Implements scalable metadata filtering strategy for 100,000+ creators

This module uses centralized environment configuration from shared.config.env_constants
for all ChromaDB-related settings, with fallback to environment-specific defaults.
"""

import hashlib
import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from contextlib import asynccontextmanager

# Conditional ChromaDB imports for development environment compatibility
try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.api.models.Collection import Collection
    from chromadb.api.types import Documents, Embeddings, Metadatas, IDs
    CHROMADB_AVAILABLE = True
except ImportError:
    # ChromaDB not available - create mock classes for development
    chromadb = None
    Settings = None
    Collection = None
    Documents = None
    Embeddings = None
    Metadatas = None
    IDs = None
    CHROMADB_AVAILABLE = False
    # Logger will be defined later, so we'll log this after logger initialization

from shared.config.settings import get_ai_engine_config
from shared.config.env_constants import (
    CHROMADB_URL,
    CHROMA_SHARD_COUNT,
    CHROMA_MAX_CONNECTIONS_PER_INSTANCE,
    get_env_value
)
from shared.exceptions.base import BaseServiceException

logger = logging.getLogger(__name__)

# Log ChromaDB availability after logger is initialized
if not CHROMADB_AVAILABLE:
    logger.warning("ChromaDB not available - using mock implementation for development")


class MockChromaDBClient:
    """Mock ChromaDB client for development environment"""
    
    def __init__(self, host: str, port: int, settings=None):
        self.host = host
        self.port = port
        self.settings = settings
        self._collections = {}
    
    def get_collection(self, name: str):
        if name not in self._collections:
            raise Exception(f"Collection {name} not found")
        return self._collections[name]
    
    def create_collection(self, name: str, metadata=None):
        collection = MockCollection(name, metadata)
        self._collections[name] = collection
        return collection
    
    def list_collections(self):
        return [MockCollectionInfo(name) for name in self._collections.keys()]
    
    def delete_collection(self, name: str):
        if name in self._collections:
            del self._collections[name]


class MockCollection:
    """Mock ChromaDB collection for development environment"""
    
    def __init__(self, name: str, metadata=None):
        self.name = name
        self.metadata = metadata or {}
        self._data = {
            "ids": [],
            "documents": [],
            "metadatas": [],
            "embeddings": []
        }
    
    def add(self, embeddings, documents, metadatas, ids):
        self._data["embeddings"].extend(embeddings)
        self._data["documents"].extend(documents)
        self._data["metadatas"].extend(metadatas)
        self._data["ids"].extend(ids)
    
    def query(self, query_embeddings, n_results=5, where=None, include=None):
        # Simple mock query - return first n_results
        include = include or ["documents", "metadatas", "distances"]
        
        # Filter by where clause if provided
        filtered_indices = []
        for i, metadata in enumerate(self._data["metadatas"]):
            if self._matches_where_clause(metadata, where):
                filtered_indices.append(i)
        
        # Limit results
        filtered_indices = filtered_indices[:n_results]
        
        result = {}
        if "documents" in include:
            result["documents"] = [[self._data["documents"][i] for i in filtered_indices]]
        if "metadatas" in include:
            result["metadatas"] = [[self._data["metadatas"][i] for i in filtered_indices]]
        if "distances" in include:
            # Mock distances - random values between 0.1 and 0.9
            import random
            result["distances"] = [[random.uniform(0.1, 0.9) for _ in filtered_indices]]
        if "ids" in include:
            result["ids"] = [[self._data["ids"][i] for i in filtered_indices]]
        
        return result
    
    def get(self, where=None, include=None):
        include = include or ["documents", "metadatas", "ids"]
        
        # Filter by where clause if provided
        filtered_indices = []
        for i, metadata in enumerate(self._data["metadatas"]):
            if self._matches_where_clause(metadata, where):
                filtered_indices.append(i)
        
        result = {}
        if "documents" in include:
            result["documents"] = [self._data["documents"][i] for i in filtered_indices]
        if "metadatas" in include:
            result["metadatas"] = [self._data["metadatas"][i] for i in filtered_indices]
        if "ids" in include:
            result["ids"] = [self._data["ids"][i] for i in filtered_indices]
        
        return result
    
    def delete(self, ids):
        # Remove items with matching IDs
        indices_to_remove = []
        for i, item_id in enumerate(self._data["ids"]):
            if item_id in ids:
                indices_to_remove.append(i)
        
        # Remove in reverse order to maintain indices
        for i in reversed(indices_to_remove):
            del self._data["ids"][i]
            del self._data["documents"][i]
            del self._data["metadatas"][i]
            del self._data["embeddings"][i]
    
    def _matches_where_clause(self, metadata, where):
        if not where:
            return True
        
        # Simple where clause matching
        if "$and" in where:
            return all(self._matches_where_clause(metadata, clause) for clause in where["$and"])
        
        for key, condition in where.items():
            if key.startswith("$"):
                continue
            
            if isinstance(condition, dict):
                if "$eq" in condition:
                    if metadata.get(key) != condition["$eq"]:
                        return False
            else:
                if metadata.get(key) != condition:
                    return False
        
        return True


class MockCollectionInfo:
    """Mock collection info for development environment"""
    
    def __init__(self, name: str):
        self.name = name


class MockSettings:
    """Mock ChromaDB settings for development environment"""
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


# Use mock classes when ChromaDB is not available
if not CHROMADB_AVAILABLE:
    chromadb = type('MockChromaDB', (), {
        'HttpClient': MockChromaDBClient
    })()
    Settings = MockSettings
    Collection = MockCollection


class ChromaDBError(BaseServiceException):
    """ChromaDB specific errors"""
    pass


class ChromaDBConnectionError(ChromaDBError):
    """ChromaDB connection errors"""
    pass


class ChromaDBCollectionError(ChromaDBError):
    """ChromaDB collection management errors"""
    pass


@dataclass
class EmbeddingMetadata:
    """Standard metadata structure for embeddings"""
    creator_id: str
    document_id: str
    chunk_index: int
    created_at: str
    document_type: Optional[str] = None
    source_file: Optional[str] = None
    page_number: Optional[int] = None
    section: Optional[str] = None
    token_count: Optional[int] = None


@dataclass
class CollectionStats:
    """Collection statistics for monitoring"""
    collection_name: str
    document_count: int
    total_embeddings: int
    creators_count: int
    avg_embeddings_per_creator: float
    last_updated: datetime
    size_mb: Optional[float] = None


class ChromaDBManager:
    """
    Multi-tenant ChromaDB manager using metadata filtering strategy
    
    Implements shared collections with creator_id filtering for scalability.
    Supports 100,000+ creators with configurable sharding.
    """
    
    def __init__(
        self,
        chromadb_url: Optional[str] = None,
        shard_count: Optional[int] = None,
        max_connections: Optional[int] = None,
        health_check_timeout: int = 5
    ):
        """
        Initialize ChromaDB manager using centralized configuration
        
        Configuration priority:
        1. Explicit parameters passed to __init__
        2. Values from get_ai_engine_config() if available
        3. Centralized environment variables/defaults via get_env_value()
        
        Args:
            chromadb_url: ChromaDB server URL (defaults to centralized config)
            shard_count: Number of shards for collections (5-50, defaults to centralized config)
            max_connections: Max connections per instance (defaults to centralized config)
            health_check_timeout: Health check timeout in seconds
        """
        # Try to load AI engine config
        try:
            self.config = get_ai_engine_config()
        except Exception as e:
            logger.warning(f"Failed to load AI engine config, using centralized defaults: {str(e)}")
            self.config = None
        
        # Configuration with centralized fallbacks
        # Priority: explicit param -> config object -> centralized env/defaults
        self.chromadb_url = (
            chromadb_url or
            (self.config.chromadb_url if self.config else None) or
            get_env_value(CHROMADB_URL, fallback=True)
        )
        
        # Get shard count with safe type conversion
        shard_count_value = (
            shard_count or
            (self.config.chroma_shard_count if self.config else None) or
            get_env_value(CHROMA_SHARD_COUNT, fallback=True)
        )
        self.shard_count = self._safe_int_conversion(shard_count_value, "shard_count", 10, min_val=5, max_val=50)
        
        # Get max connections with safe type conversion
        max_connections_value = (
            max_connections or
            (self.config.chroma_max_connections if self.config else None) or
            get_env_value(CHROMA_MAX_CONNECTIONS_PER_INSTANCE, fallback=True)
        )
        self.max_connections = self._safe_int_conversion(max_connections_value, "max_connections", 10, min_val=1)
        
        self.health_check_timeout = health_check_timeout or 5
        
        # Validate required configuration
        if not self.chromadb_url:
            logger.error(
                f"ChromaDB URL not configured. "
                f"Attempted sources: param={chromadb_url}, "
                f"config={getattr(self.config, 'chromadb_url', 'NOT_FOUND')}, "
                f"centralized={get_env_value(CHROMADB_URL, fallback=False)}"
            )
            raise ValueError(
                "ChromaDB URL is required. Please set it via parameter, "
                "AI engine config, or the CHROMADB_URL environment variable."
            )
        
        # Validate shard count
        if not 5 <= self.shard_count <= 50:
            raise ValueError(f"shard_count must be between 5 and 50, got {self.shard_count}")
        
        # Client and connection management
        self._client: Optional[chromadb.HttpClient] = None
        self._connection_pool_semaphore = asyncio.Semaphore(self.max_connections)
        self._collections_cache: Dict[str, Collection] = {}
        self._stats_cache: Dict[str, CollectionStats] = {}
        self._cache_ttl = timedelta(minutes=5)
        self._last_cache_update: Dict[str, datetime] = {}
        
        logger.info(
            f"ChromaDB Manager initialized - "
            f"url: {self.chromadb_url}, "
            f"shard_count: {self.shard_count}, "
            f"max_connections: {self.max_connections}"
        )
    
    def _safe_int_conversion(self, value: Any, field_name: str, default: int, min_val: int = None, max_val: int = None) -> int:
        """
        Safely convert a value to integer with validation and fallback.
        
        Args:
            value: The value to convert
            field_name: Name of the field for logging
            default: Default value to use on conversion failure
            min_val: Optional minimum value constraint
            max_val: Optional maximum value constraint
            
        Returns:
            int: The converted integer value or default
        """
        if value is None:
            return default
        
        try:
            converted = int(value)
            
            # Apply constraints
            if min_val is not None and converted < min_val:
                logger.warning(f"{field_name} value {converted} is below minimum {min_val}, using {min_val}")
                converted = min_val
            
            if max_val is not None and converted > max_val:
                logger.warning(f"{field_name} value {converted} is above maximum {max_val}, using {max_val}")
                converted = max_val
            
            return converted
            
        except (ValueError, TypeError) as e:
            logger.warning(
                f"Failed to convert {field_name} value '{value}' to integer: {e}. "
                f"Using default value {default}"
            )
            return default
    
    def _get_shard_name(self, creator_id: str) -> str:
        """
        Generate shard collection name using consistent hashing
        
        Args:
            creator_id: Creator identifier
            
        Returns:
            Shard collection name (e.g., "knowledge_shard_3")
        """
        # Use SHA256 for consistent hashing
        hash_value = int(hashlib.sha256(creator_id.encode()).hexdigest(), 16)
        shard_index = hash_value % self.shard_count
        return f"knowledge_shard_{shard_index}"
    
    def _get_client(self):
        """Get or create ChromaDB client"""
        if self._client is None:
            try:
                # Parse URL more safely
                if "://" in self.chromadb_url:
                    url_parts = self.chromadb_url.split("://")[1]
                else:
                    url_parts = self.chromadb_url
                
                if ":" in url_parts:
                    host = url_parts.split(":")[0]
                    port = int(url_parts.split(":")[-1])
                else:
                    host = url_parts
                    port = 8000  # Default ChromaDB port
                
                if CHROMADB_AVAILABLE:
                    self._client = chromadb.HttpClient(
                        host=host,
                        port=port,
                        settings=Settings(
                            anonymized_telemetry=False
                        )
                    )
                    logger.info(f"ChromaDB client created for {host}:{port}")
                else:
                    # Use mock client for development
                    self._client = MockChromaDBClient(
                        host=host,
                        port=port,
                        settings=MockSettings(anonymized_telemetry=False)
                    )
                    logger.info(f"Mock ChromaDB client created for development (target: {host}:{port})")
                    
            except Exception as e:
                logger.error(f"Failed to create ChromaDB client: {str(e)}")
                raise ChromaDBConnectionError(f"Failed to connect to ChromaDB: {str(e)}") from e
        
        return self._client
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check with timeout
        
        Returns:
            Health status dictionary
            
        Raises:
            ChromaDBConnectionError: If health check fails
        """
        try:
            # Test direct HTTP connection to ChromaDB instead of using client
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                heartbeat_url = f"{self.chromadb_url}/api/v1/heartbeat"
                async with session.get(heartbeat_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        heartbeat_data = await response.json()
                        
                        return {
                            "status": "healthy",
                            "url": self.chromadb_url,
                            "collections_count": "not_checked",  # Skip collection count to avoid client issues
                            "shard_count": self.shard_count,
                            "max_connections": self.max_connections,
                            "heartbeat": heartbeat_data,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    else:
                        raise ChromaDBConnectionError(f"ChromaDB returned status {response.status}")
            
        except Exception as e:
            error_msg = f"ChromaDB health check failed: {str(e)}"
            logger.error(error_msg)
            raise ChromaDBConnectionError(error_msg) from e
    
    async def get_or_create_collection(self, creator_id: str) -> Collection:
        """
        Get or create collection for creator using sharding strategy
        
        Args:
            creator_id: Creator identifier
            
        Returns:
            ChromaDB collection instance
            
        Raises:
            ChromaDBCollectionError: If collection operations fail
        """
        shard_name = self._get_shard_name(creator_id)
        
        # Check cache first
        if shard_name in self._collections_cache:
            cache_time = self._last_cache_update.get(shard_name)
            if cache_time and datetime.utcnow() - cache_time < self._cache_ttl:
                return self._collections_cache[shard_name]
        
        try:
            async with self._connection_pool_semaphore:
                client = self._get_client()
                
                # Try to get existing collection first
                try:
                    collection = client.get_collection(name=shard_name)
                    logger.debug(f"Retrieved existing collection: {shard_name}")
                except Exception:
                    # Collection doesn't exist, create it
                    collection = client.create_collection(
                        name=shard_name,
                        metadata={
                            "description": f"Knowledge base shard {shard_name.split('_')[-1]}",
                            "created_at": datetime.utcnow().isoformat(),
                            "shard_strategy": "metadata_filtering",
                            "max_creators_per_shard": self.shard_count * 1000  # Estimated capacity
                        }
                    )
                    logger.info(f"Created new collection: {shard_name}")
                
                # Update cache
                self._collections_cache[shard_name] = collection
                self._last_cache_update[shard_name] = datetime.utcnow()
                
                return collection
                
        except Exception as e:
            error_msg = f"Failed to get/create collection for creator {creator_id}: {str(e)}"
            logger.error(error_msg)
            raise ChromaDBCollectionError(error_msg) from e
    
    async def add_embeddings(
        self,
        creator_id: str,
        document_id: str,
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Add embeddings to creator's collection with metadata filtering
        
        Args:
            creator_id: Creator identifier
            document_id: Document identifier
            embeddings: List of embedding vectors
            documents: List of document chunks
            metadatas: List of metadata dictionaries
            ids: Optional list of IDs (auto-generated if not provided)
            
        Returns:
            List of generated/provided IDs
            
        Raises:
            ChromaDBCollectionError: If adding embeddings fails
        """
        if not embeddings or not documents or not metadatas:
            raise ValueError("embeddings, documents, and metadatas cannot be empty")
        
        if len(embeddings) != len(documents) != len(metadatas):
            raise ValueError("embeddings, documents, and metadatas must have same length")
        
        try:
            collection = await self.get_or_create_collection(creator_id)
            
            # Generate IDs if not provided
            if ids is None:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                ids = [
                    f"{creator_id}_{document_id}_{i}_{timestamp}"
                    for i in range(len(embeddings))
                ]
            
            # Ensure all metadata includes creator_id for filtering
            enhanced_metadatas = []
            for i, metadata in enumerate(metadatas):
                enhanced_metadata = {
                    **metadata,
                    "creator_id": creator_id,
                    "document_id": document_id,
                    "chunk_index": i,
                    "created_at": datetime.utcnow().isoformat()
                }
                enhanced_metadatas.append(enhanced_metadata)
            
            # Add to collection
            collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=enhanced_metadatas,
                ids=ids
            )
            
            logger.info(
                f"Added {len(embeddings)} embeddings for creator {creator_id}, "
                f"document {document_id} to collection {collection.name}"
            )
            
            # Invalidate stats cache
            if collection.name in self._stats_cache:
                del self._stats_cache[collection.name]
            
            return ids
            
        except Exception as e:
            error_msg = f"Failed to add embeddings for creator {creator_id}: {str(e)}"
            logger.error(error_msg)
            raise ChromaDBCollectionError(error_msg) from e
    
    async def query_embeddings(
        self,
        creator_id: str,
        query_embeddings: List[List[float]],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        include: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Query embeddings with creator isolation
        
        Args:
            creator_id: Creator identifier for filtering
            query_embeddings: Query embedding vectors
            n_results: Number of results to return
            where: Additional metadata filters
            include: Fields to include in results
            
        Returns:
            Query results dictionary
            
        Raises:
            ChromaDBCollectionError: If query fails
        """
        try:
            collection = await self.get_or_create_collection(creator_id)
            
            # Build where clause with creator_id filter
            creator_filter = {"creator_id": {"$eq": creator_id}}
            if where:
                # Combine filters using $and
                combined_filter = {"$and": [creator_filter, where]}
            else:
                combined_filter = creator_filter
            
            # Set default includes
            if include is None:
                include = ["documents", "metadatas", "distances"]
            
            # Perform query
            results = collection.query(
                query_embeddings=query_embeddings,
                n_results=n_results,
                where=combined_filter,
                include=include
            )
            
            logger.debug(
                f"Queried {len(query_embeddings)} embeddings for creator {creator_id}, "
                f"returned {len(results.get('ids', []))} results"
            )
            
            return results
            
        except Exception as e:
            error_msg = f"Failed to query embeddings for creator {creator_id}: {str(e)}"
            logger.error(error_msg)
            raise ChromaDBCollectionError(error_msg) from e
    
    async def delete_document_embeddings(
        self,
        creator_id: str,
        document_id: str
    ) -> int:
        """
        Delete all embeddings for a specific document
        
        Args:
            creator_id: Creator identifier
            document_id: Document identifier
            
        Returns:
            Number of embeddings deleted
            
        Raises:
            ChromaDBCollectionError: If deletion fails
        """
        try:
            collection = await self.get_or_create_collection(creator_id)
            
            # Query to find all embeddings for this document
            results = collection.get(
                where={
                    "$and": [
                        {"creator_id": {"$eq": creator_id}},
                        {"document_id": {"$eq": document_id}}
                    ]
                },
                include=["metadatas"]
            )
            
            if not results["ids"]:
                logger.info(f"No embeddings found for document {document_id}")
                return 0
            
            # Delete embeddings
            collection.delete(ids=results["ids"])
            
            deleted_count = len(results["ids"])
            logger.info(
                f"Deleted {deleted_count} embeddings for creator {creator_id}, "
                f"document {document_id}"
            )
            
            # Invalidate stats cache
            if collection.name in self._stats_cache:
                del self._stats_cache[collection.name]
            
            return deleted_count
            
        except Exception as e:
            error_msg = f"Failed to delete embeddings for document {document_id}: {str(e)}"
            logger.error(error_msg)
            raise ChromaDBCollectionError(error_msg) from e
    
    async def get_collection_stats(self, creator_id: str) -> CollectionStats:
        """
        Get statistics for creator's collection shard
        
        Args:
            creator_id: Creator identifier
            
        Returns:
            Collection statistics
            
        Raises:
            ChromaDBCollectionError: If stats retrieval fails
        """
        shard_name = self._get_shard_name(creator_id)
        
        # Check cache
        if shard_name in self._stats_cache:
            cache_time = self._last_cache_update.get(f"stats_{shard_name}")
            if cache_time and datetime.utcnow() - cache_time < self._cache_ttl:
                return self._stats_cache[shard_name]
        
        try:
            collection = await self.get_or_create_collection(creator_id)
            
            # Get all documents in collection
            results = collection.get(include=["metadatas"])
            
            if not results["metadatas"]:
                stats = CollectionStats(
                    collection_name=shard_name,
                    document_count=0,
                    total_embeddings=0,
                    creators_count=0,
                    avg_embeddings_per_creator=0.0,
                    last_updated=datetime.utcnow()
                )
            else:
                # Analyze metadata
                creators = set()
                documents = set()
                
                for metadata in results["metadatas"]:
                    if metadata.get("creator_id"):
                        creators.add(metadata["creator_id"])
                    if metadata.get("document_id"):
                        documents.add(metadata["document_id"])
                
                total_embeddings = len(results["metadatas"])
                creators_count = len(creators)
                avg_embeddings = total_embeddings / creators_count if creators_count > 0 else 0.0
                
                stats = CollectionStats(
                    collection_name=shard_name,
                    document_count=len(documents),
                    total_embeddings=total_embeddings,
                    creators_count=creators_count,
                    avg_embeddings_per_creator=avg_embeddings,
                    last_updated=datetime.utcnow()
                )
            
            # Update cache
            self._stats_cache[shard_name] = stats
            self._last_cache_update[f"stats_{shard_name}"] = datetime.utcnow()
            
            return stats
            
        except Exception as e:
            error_msg = f"Failed to get collection stats for creator {creator_id}: {str(e)}"
            logger.error(error_msg)
            raise ChromaDBCollectionError(error_msg) from e
    
    async def get_all_shards_stats(self) -> List[CollectionStats]:
        """
        Get statistics for all collection shards
        
        Returns:
            List of collection statistics for all shards
        """
        stats_list = []
        
        try:
            client = self._get_client()
            collections = client.list_collections()
            
            for collection_info in collections:
                if collection_info.name.startswith("knowledge_shard_"):
                    try:
                        collection = client.get_collection(collection_info.name)
                        results = collection.get(include=["metadatas"])
                        
                        if not results["metadatas"]:
                            stats = CollectionStats(
                                collection_name=collection_info.name,
                                document_count=0,
                                total_embeddings=0,
                                creators_count=0,
                                avg_embeddings_per_creator=0.0,
                                last_updated=datetime.utcnow()
                            )
                        else:
                            creators = set()
                            documents = set()
                            
                            for metadata in results["metadatas"]:
                                if metadata.get("creator_id"):
                                    creators.add(metadata["creator_id"])
                                if metadata.get("document_id"):
                                    documents.add(metadata["document_id"])
                            
                            total_embeddings = len(results["metadatas"])
                            creators_count = len(creators)
                            avg_embeddings = total_embeddings / creators_count if creators_count > 0 else 0.0
                            
                            stats = CollectionStats(
                                collection_name=collection_info.name,
                                document_count=len(documents),
                                total_embeddings=total_embeddings,
                                creators_count=creators_count,
                                avg_embeddings_per_creator=avg_embeddings,
                                last_updated=datetime.utcnow()
                            )
                        
                        stats_list.append(stats)
                        
                    except Exception as e:
                        logger.warning(f"Failed to get stats for collection {collection_info.name}: {str(e)}")
                        continue
            
            return stats_list
            
        except Exception as e:
            error_msg = f"Failed to get all shards stats: {str(e)}"
            logger.error(error_msg)
            raise ChromaDBCollectionError(error_msg) from e
    
    async def close(self):
        """Close ChromaDB client and cleanup resources"""
        if self._client:
            try:
                # ChromaDB client doesn't have explicit close method
                # Just clear references
                self._client = None
                self._collections_cache.clear()
                self._stats_cache.clear()
                self._last_cache_update.clear()
                logger.info("ChromaDB manager closed successfully")
            except Exception as e:
                logger.warning(f"Error closing ChromaDB manager: {str(e)}")
    
    @asynccontextmanager
    async def get_connection(self):
        """Context manager for connection pool management"""
        async with self._connection_pool_semaphore:
            try:
                yield self._get_client()
            except Exception as e:
                logger.error(f"Connection error: {str(e)}")
                raise


# Global instance (initialized lazily)
_chromadb_manager: Optional[ChromaDBManager] = None


def get_chromadb_manager() -> ChromaDBManager:
    """Get global ChromaDB manager instance (lazy initialization)"""
    global _chromadb_manager
    if _chromadb_manager is None:
        _chromadb_manager = ChromaDBManager()
    return _chromadb_manager


async def close_chromadb_manager():
    """Close global ChromaDB manager"""
    global _chromadb_manager
    if _chromadb_manager is not None:
        await _chromadb_manager.close()
        _chromadb_manager = None