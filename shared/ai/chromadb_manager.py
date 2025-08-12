"""
ChromaDB Multi-Tenant Manager
Implements scalable metadata filtering strategy for 100,000+ creators
"""

import os
import hashlib
import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from contextlib import asynccontextmanager

import chromadb
from chromadb.config import Settings
from chromadb.api.models.Collection import Collection
from chromadb.api.types import Documents, Embeddings, Metadatas, IDs

from shared.config.settings import get_ai_engine_config
from shared.exceptions.base import BaseServiceException

logger = logging.getLogger(__name__)


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
        Initialize ChromaDB manager
        
        Args:
            chromadb_url: ChromaDB server URL (defaults to config)
            shard_count: Number of shards for collections (5-50, defaults to config)
            max_connections: Max connections per instance (defaults to config)
            health_check_timeout: Health check timeout in seconds
        """
        # Read configuration directly from environment variables as fallback
        import os
        
        try:
            self.config = get_ai_engine_config()
        except Exception as e:
            logger.warning(f"Failed to load AI engine config: {str(e)}")
            self.config = None
        
        # Configuration with fallbacks - read directly from env if config fails
        self.chromadb_url = (
            chromadb_url or 
            (self.config.chromadb_url if self.config else None) or
            os.getenv("CHROMADB_URL") or
            "http://localhost:8000"
        )
        self.shard_count = (
            shard_count or 
            (self.config.chroma_shard_count if self.config else None) or
            int(os.getenv("CHROMA_SHARD_COUNT", "10"))
        )
        self.max_connections = (
            max_connections or 
            (self.config.chroma_max_connections if self.config else None) or
            int(os.getenv("CHROMA_MAX_CONNECTIONS_PER_INSTANCE", "10"))
        )
        self.health_check_timeout = health_check_timeout or 5
        
        # Validate required configuration
        if not self.chromadb_url:
            logger.error(f"ChromaDB URL not found. chromadb_url={chromadb_url}, config.chromadb_url={getattr(self.config, 'chromadb_url', 'NOT_FOUND')}")
            raise ValueError("ChromaDB URL is required")
        
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
    
    def _get_client(self) -> chromadb.HttpClient:
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
                
                self._client = chromadb.HttpClient(
                    host=host,
                    port=port,
                    settings=Settings(
                        anonymized_telemetry=False
                    )
                )
                logger.info(f"ChromaDB client created for {host}:{port}")
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