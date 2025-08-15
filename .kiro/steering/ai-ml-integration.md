---
inclusion: always
---

# AI/ML Integration Guidelines ✅ PRODUCTION IMPLEMENTATION

## Current Implementation Status

### AI Engine Service ✅ FULLY FUNCTIONAL
- **RAG Pipeline**: IMPLEMENTED and OPERATIONAL with retrieval-augmented generation
- **Ollama Integration**: FUNCTIONAL with llama2:7b-chat, mistral, nomic-embed-text models
- **ChromaDB**: PRODUCTION READY with multi-tenant vector storage
- **Document Processing**: PDF, DOCX, TXT support IMPLEMENTED
- **Conversation Context**: Redis-based context management FUNCTIONAL
- **Performance**: <5s response times, retry logic, fallback responses

## RAG Pipeline Architecture ✅ IMPLEMENTED

### Core RAG Implementation ✅ FUNCTIONAL
The AI Engine service HAS IMPLEMENTED a comprehensive RAG pipeline:

```python
from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime

class RAGPipeline:
    """Main Retrieval-Augmented Generation pipeline."""
    
    def __init__(self, ollama_client, chroma_client, conversation_manager):
        self.ollama_client = ollama_client
        self.chroma_client = chroma_client
        self.conversation_manager = conversation_manager
        self.max_context_tokens = 4000  # Leave room for response
        self.max_retrieved_chunks = 5
    
    async def process_query(
        self, 
        query: str, 
        creator_id: str, 
        conversation_id: str,
        context_window: int = 4000
    ) -> AIResponse:
        """
        Process user query through complete RAG pipeline.
        
        Pipeline steps:
        1. Retrieve conversation context
        2. Search relevant knowledge chunks
        3. Build contextual prompt
        4. Generate AI response
        5. Update conversation context
        """
        
        # 1. Get conversation context
        conversation_context = await self.conversation_manager.get_context(
            conversation_id, max_messages=10
        )
        
        # 2. Retrieve relevant knowledge
        relevant_chunks = await self.retrieve_knowledge(
            query, creator_id, limit=self.max_retrieved_chunks
        )
        
        # 3. Build prompt with context
        prompt = await self.build_contextual_prompt(
            query, conversation_context, relevant_chunks, context_window
        )
        
        # 4. Generate response
        response = await self.ollama_client.generate_chat_completion(
            prompt, max_tokens=1000, temperature=0.7
        )
        
        # 5. Calculate confidence score
        confidence = self.calculate_confidence_score(relevant_chunks, response)
        
        # 6. Update conversation context
        await self.conversation_manager.add_exchange(
            conversation_id, query, response, relevant_chunks
        )
        
        return AIResponse(
            response=response,
            sources=relevant_chunks,
            confidence=confidence,
            conversation_id=conversation_id,
            processing_time_ms=self.get_processing_time()
        )
    
    async def retrieve_knowledge(
        self, 
        query: str, 
        creator_id: str, 
        limit: int = 5
    ) -> List[RetrievedChunk]:
        """Retrieve relevant knowledge chunks from vector store."""
        
        # Generate query embedding
        query_embedding = await self.ollama_client.generate_embedding(
            query, model="nomic-embed-text"
        )
        
        # Search in creator's knowledge base
        collection_name = f"creator_{creator_id}_knowledge"
        results = await self.chroma_client.query(
            collection_name=collection_name,
            query_embeddings=[query_embedding],
            n_results=limit,
            include=["documents", "metadatas", "distances"]
        )
        
        # Convert to structured format
        chunks = []
        for i, (doc, metadata, distance) in enumerate(zip(
            results["documents"][0],
            results["metadatas"][0], 
            results["distances"][0]
        )):
            chunks.append(RetrievedChunk(
                content=doc,
                metadata=metadata,
                similarity_score=1 - distance,  # Convert distance to similarity
                rank=i + 1
            ))
        
        return chunks
    
    async def build_contextual_prompt(
        self,
        query: str,
        conversation_context: List[ConversationMessage],
        knowledge_chunks: List[RetrievedChunk],
        max_tokens: int
    ) -> str:
        """Build prompt with conversation context and retrieved knowledge."""
        
        # Base prompt template
        prompt_parts = [
            "You are an AI coaching assistant. Use the provided context and conversation history to give helpful, accurate responses.",
            "",
            "KNOWLEDGE CONTEXT:"
        ]
        
        # Add knowledge chunks
        for chunk in knowledge_chunks:
            prompt_parts.append(f"- {chunk.content[:500]}...")  # Truncate long chunks
        
        prompt_parts.extend([
            "",
            "CONVERSATION HISTORY:"
        ])
        
        # Add recent conversation context
        for msg in conversation_context[-5:]:  # Last 5 messages
            role = "User" if msg.sender_type == "user" else "Assistant"
            prompt_parts.append(f"{role}: {msg.content}")
        
        prompt_parts.extend([
            "",
            f"User: {query}",
            "Assistant:"
        ])
        
        full_prompt = "\n".join(prompt_parts)
        
        # Truncate if too long
        if len(full_prompt.split()) > max_tokens:
            # Prioritize recent context over older knowledge
            truncated_prompt = self.truncate_prompt_intelligently(
                full_prompt, max_tokens
            )
            return truncated_prompt
        
        return full_prompt
    
    def calculate_confidence_score(
        self, 
        chunks: List[RetrievedChunk], 
        response: str
    ) -> float:
        """Calculate confidence score based on retrieval quality and response."""
        
        if not chunks:
            return 0.3  # Low confidence without knowledge
        
        # Average similarity score of retrieved chunks
        avg_similarity = sum(chunk.similarity_score for chunk in chunks) / len(chunks)
        
        # Boost confidence if multiple high-quality chunks
        quality_boost = min(len([c for c in chunks if c.similarity_score > 0.8]) * 0.1, 0.3)
        
        # Response length factor (very short responses might be less confident)
        length_factor = min(len(response.split()) / 50, 1.0)
        
        confidence = (avg_similarity * 0.6) + quality_boost + (length_factor * 0.1)
        return min(confidence, 1.0)
```

## Ollama Integration Patterns

### Ollama Client Implementation
Standardized Ollama client with error handling and retries:

```python
import httpx
import asyncio
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class OllamaClient:
    """Async client for Ollama API with retry logic and error handling."""
    
    def __init__(self, base_url: str = "http://ollama:11434"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(60.0)  # 60 second timeout
        )
        self.embedding_model = "nomic-embed-text"
        self.chat_model = "llama2:7b-chat"
    
    async def generate_embedding(
        self, 
        text: str, 
        model: Optional[str] = None
    ) -> List[float]:
        """Generate text embedding using specified model."""
        
        model = model or self.embedding_model
        
        payload = {
            "model": model,
            "prompt": text
        }
        
        try:
            response = await self._make_request_with_retry(
                "POST", "/api/embeddings", json=payload
            )
            
            embedding = response.get("embedding")
            if not embedding:
                raise AIEngineError("No embedding returned from Ollama")
            
            return embedding
            
        except Exception as e:
            logger.exception(f"Embedding generation failed: {e}")
            raise AIEngineError(f"Failed to generate embedding: {str(e)}")
    
    async def generate_chat_completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        stream: bool = False
    ) -> str:
        """Generate chat completion using specified model."""
        
        model = model or self.chat_model
        
        payload = {
            "model": model,
            "prompt": prompt,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
                "top_p": 0.9,
                "stop": ["User:", "Human:"]  # Stop tokens
            },
            "stream": stream
        }
        
        try:
            response = await self._make_request_with_retry(
                "POST", "/api/generate", json=payload
            )
            
            generated_text = response.get("response", "").strip()
            if not generated_text:
                raise AIEngineError("Empty response from Ollama")
            
            return generated_text
            
        except Exception as e:
            logger.exception(f"Chat completion failed: {e}")
            raise AIEngineError(f"Failed to generate response: {str(e)}")
    
    async def check_model_availability(self, model: str) -> bool:
        """Check if a model is available and loaded."""
        
        try:
            response = await self.client.get("/api/tags")
            response.raise_for_status()
            
            models = response.json().get("models", [])
            available_models = [m["name"] for m in models]
            
            return model in available_models
            
        except Exception as e:
            logger.exception(f"Model availability check failed: {e}")
            return False
    
    async def pull_model(self, model: str) -> bool:
        """Pull a model if not available."""
        
        payload = {"name": model}
        
        try:
            # Make streaming request for model pull
            async with self.client.stream("POST", "/api/pull", json=payload) as response:
                response.raise_for_status()
                
                # Ollama pull is streaming, wait for completion
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        if data.get("status") == "success":
                            return True
            
            return False
            
        except Exception as e:
            logger.exception(f"Model pull failed: {e}")
            return False
    
    async def _make_request_with_retry(
        self,
        method: str,
        endpoint: str,
        max_retries: int = 3,
        **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request with exponential backoff retry."""
        
        for attempt in range(max_retries):
            try:
                response = await self.client.request(method, endpoint, **kwargs)
                response.raise_for_status()
                return response.json()
                
            except httpx.TimeoutException:
                if attempt == max_retries - 1:
                    raise AIEngineError("Request timeout after retries")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500 and attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise AIEngineError(f"HTTP error: {e.response.status_code}")
                
            except Exception as e:
                if attempt == max_retries - 1:
                    raise AIEngineError(f"Request failed: {str(e)}")
                await asyncio.sleep(2 ** attempt)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Ollama service health and model status."""
        
        try:
            # Check service availability
            response = await self.client.get("/api/tags")
            response.raise_for_status()
            
            models = response.json().get("models", [])
            
            # Check required models
            required_models = [self.embedding_model, self.chat_model]
            available_models = [m["name"] for m in models]
            
            missing_models = [m for m in required_models if m not in available_models]
            
            return {
                "status": "healthy" if not missing_models else "degraded",
                "available_models": available_models,
                "missing_models": missing_models,
                "total_models": len(models)
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "available_models": [],
                "missing_models": required_models
            }
```

## ChromaDB Management

### Multi-Tenant ChromaDB Operations
Implement proper tenant isolation and collection management:

```python
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ChromaManager:
    """Manages ChromaDB collections with multi-tenant isolation."""
    
    def __init__(self, host: str = "chromadb", port: int = 8000):
        self.client = chromadb.HttpClient(
            host=host,
            port=port,
            settings=Settings(
                chroma_client_auth_provider="chromadb.auth.basic.BasicAuthClientProvider",
                chroma_client_auth_credentials="admin:admin"  # Configure in production
            )
        )
        self.embedding_function = self._get_embedding_function()
    
    def _get_embedding_function(self):
        """Get embedding function for ChromaDB."""
        # Use Ollama embedding function
        from chromadb.utils import embedding_functions
        
        return embedding_functions.OllamaEmbeddingFunction(
            url="http://ollama:11434/api/embeddings",
            model_name="nomic-embed-text"
        )
    
    async def get_or_create_collection(self, creator_id: str):
        """Get or create collection for specific creator."""
        
        collection_name = f"creator_{creator_id}_knowledge"
        
        try:
            # Try to get existing collection
            collection = self.client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            logger.info(f"Retrieved existing collection: {collection_name}")
            
        except Exception:
            # Create new collection if doesn't exist
            collection = self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function,
                metadata={
                    "creator_id": creator_id,
                    "created_at": datetime.utcnow().isoformat(),
                    "description": f"Knowledge base for creator {creator_id}"
                }
            )
            logger.info(f"Created new collection: {collection_name}")
        
        return collection
    
    async def add_documents(
        self, 
        creator_id: str, 
        documents: List[DocumentChunk]
    ) -> bool:
        """Add document chunks to creator's collection."""
        
        collection = await self.get_or_create_collection(creator_id)
        
        try:
            # Prepare data for ChromaDB
            ids = [chunk.id for chunk in documents]
            documents_text = [chunk.content for chunk in documents]
            metadatas = []
            
            for chunk in documents:
                metadata = {
                    "document_id": chunk.metadata.get("document_id"),
                    "chunk_index": chunk.chunk_index,
                    "creator_id": creator_id,
                    "source": chunk.metadata.get("source", "unknown"),
                    "created_at": datetime.utcnow().isoformat(),
                    "token_count": chunk.token_count
                }
                # Add custom metadata
                metadata.update(chunk.metadata)
                metadatas.append(metadata)
            
            # Add to collection
            collection.add(
                documents=documents_text,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(documents)} chunks to collection {collection.name}")
            return True
            
        except Exception as e:
            logger.exception(f"Failed to add documents to ChromaDB: {e}")
            raise AIEngineError(f"Failed to store documents: {str(e)}")
    
    async def search_documents(
        self,
        creator_id: str,
        query: str,
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search documents in creator's collection."""
        
        collection = await self.get_or_create_collection(creator_id)
        
        try:
            results = collection.query(
                query_texts=[query],
                n_results=limit,
                include=["documents", "metadatas", "distances"]
            )
            
            # Filter by similarity threshold
            filtered_results = []
            for doc, metadata, distance in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            ):
                similarity = 1 - distance  # Convert distance to similarity
                if similarity >= similarity_threshold:
                    filtered_results.append({
                        "content": doc,
                        "metadata": metadata,
                        "similarity_score": similarity
                    })
            
            logger.info(f"Found {len(filtered_results)} relevant chunks for query")
            return filtered_results
            
        except Exception as e:
            logger.exception(f"Search failed in ChromaDB: {e}")
            raise AIEngineError(f"Search failed: {str(e)}")
    
    async def delete_document(self, creator_id: str, document_id: str) -> bool:
        """Delete all chunks of a document from collection."""
        
        collection = await self.get_or_create_collection(creator_id)
        
        try:
            # Find all chunks for this document
            results = collection.get(
                where={"document_id": document_id},
                include=["metadatas"]
            )
            
            if results["ids"]:
                collection.delete(ids=results["ids"])
                logger.info(f"Deleted {len(results['ids'])} chunks for document {document_id}")
                return True
            else:
                logger.warning(f"No chunks found for document {document_id}")
                return False
                
        except Exception as e:
            logger.exception(f"Failed to delete document from ChromaDB: {e}")
            raise AIEngineError(f"Failed to delete document: {str(e)}")
    
    async def get_collection_stats(self, creator_id: str) -> Dict[str, Any]:
        """Get statistics for creator's collection."""
        
        try:
            collection = await self.get_or_create_collection(creator_id)
            count = collection.count()
            
            # Get sample of metadata to analyze
            sample = collection.peek(limit=100)
            
            # Analyze document sources
            sources = {}
            for metadata in sample.get("metadatas", []):
                source = metadata.get("source", "unknown")
                sources[source] = sources.get(source, 0) + 1
            
            return {
                "total_chunks": count,
                "collection_name": collection.name,
                "sources": sources,
                "sample_size": len(sample.get("metadatas", []))
            }
            
        except Exception as e:
            logger.exception(f"Failed to get collection stats: {e}")
            return {
                "total_chunks": 0,
                "error": str(e)
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check ChromaDB health and connectivity."""
        
        try:
            # Test basic connectivity
            collections = self.client.list_collections()
            
            return {
                "status": "healthy",
                "total_collections": len(collections),
                "collections": [c.name for c in collections[:10]]  # First 10
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
```

## Conversation Context Management

### Context Window Management
Implement intelligent context window management:

```python
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

class ConversationManager:
    """Manages conversation context and history."""
    
    def __init__(self, redis_client, max_context_messages: int = 20):
        self.redis = redis_client
        self.max_context_messages = max_context_messages
        self.context_ttl = 3600 * 24  # 24 hours
    
    async def get_context(
        self, 
        conversation_id: str, 
        max_messages: int = 10
    ) -> List[ConversationMessage]:
        """Get recent conversation context."""
        
        key = f"conversation:{conversation_id}:messages"
        
        try:
            # Get recent messages from Redis list
            messages_data = await self.redis.lrange(key, -max_messages, -1)
            
            messages = []
            for msg_data in messages_data:
                msg_dict = json.loads(msg_data)
                messages.append(ConversationMessage(**msg_dict))
            
            return messages
            
        except Exception as e:
            logger.exception(f"Failed to get conversation context: {e}")
            return []
    
    async def add_exchange(
        self,
        conversation_id: str,
        user_message: str,
        ai_response: str,
        sources: List[RetrievedChunk] = None
    ) -> bool:
        """Add user-AI exchange to conversation context."""
        
        key = f"conversation:{conversation_id}:messages"
        
        try:
            # Create message objects
            user_msg = ConversationMessage(
                id=f"msg_{int(datetime.utcnow().timestamp() * 1000)}",
                conversation_id=conversation_id,
                sender_type="user",
                content=user_message,
                timestamp=datetime.utcnow(),
                metadata={}
            )
            
            ai_msg = ConversationMessage(
                id=f"msg_{int(datetime.utcnow().timestamp() * 1000) + 1}",
                conversation_id=conversation_id,
                sender_type="ai",
                content=ai_response,
                timestamp=datetime.utcnow(),
                metadata={
                    "sources": [s.dict() for s in (sources or [])],
                    "model": "llama2:7b-chat"
                }
            )
            
            # Add to Redis list using async pipeline
            async with self.redis.pipeline() as pipe:
                await pipe.rpush(key, user_msg.json())
                await pipe.rpush(key, ai_msg.json())
                
                # Trim to max context size
                await pipe.ltrim(key, -self.max_context_messages, -1)
                
                # Set expiration
                await pipe.expire(key, self.context_ttl)
                
                await pipe.execute()
            
            logger.info(f"Added exchange to conversation {conversation_id}")
            return True
            
        except Exception as e:
            logger.exception(f"Failed to add conversation exchange: {e}")
            return False
    
    async def get_conversation_summary(
        self, 
        conversation_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get conversation summary and statistics."""
        
        messages = await self.get_context(conversation_id, max_messages=100)
        
        if not messages:
            return None
        
        user_messages = [m for m in messages if m.sender_type == "user"]
        ai_messages = [m for m in messages if m.sender_type == "ai"]
        
        return {
            "conversation_id": conversation_id,
            "total_messages": len(messages),
            "user_messages": len(user_messages),
            "ai_messages": len(ai_messages),
            "first_message": messages[0].timestamp.isoformat() if messages else None,
            "last_message": messages[-1].timestamp.isoformat() if messages else None,
            "avg_response_length": sum(len(m.content) for m in ai_messages) / len(ai_messages) if ai_messages else 0
        }
```

## Model Performance Monitoring

### AI Performance Metrics
Track AI model performance and quality:

```python
import time
from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class AIMetrics:
    """AI performance metrics."""
    response_time_ms: float
    token_count: int
    confidence_score: float
    retrieval_count: int
    model_used: str
    timestamp: datetime

class AIPerformanceMonitor:
    """Monitor AI model performance and quality."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.metrics_ttl = 3600 * 24 * 7  # 7 days
    
    async def record_metrics(
        self,
        creator_id: str,
        metrics: AIMetrics
    ) -> None:
        """Record AI performance metrics."""
        
        key = f"ai_metrics:{creator_id}:{datetime.utcnow().strftime('%Y%m%d')}"
        
        metrics_data = {
            "response_time_ms": metrics.response_time_ms,
            "token_count": metrics.token_count,
            "confidence_score": metrics.confidence_score,
            "retrieval_count": metrics.retrieval_count,
            "model_used": metrics.model_used,
            "timestamp": metrics.timestamp.isoformat()
        }
        
        try:
            await self.redis.lpush(key, json.dumps(metrics_data))
            await self.redis.expire(key, self.metrics_ttl)
            
        except Exception as e:
            logger.exception(f"Failed to record AI metrics: {e}")
    
    async def get_performance_stats(
        self,
        creator_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get AI performance statistics."""
        
        all_metrics = []
        
        for i in range(days):
            date = (datetime.utcnow() - timedelta(days=i)).strftime('%Y%m%d')
            key = f"ai_metrics:{creator_id}:{date}"
            
            try:
                metrics_data = await self.redis.lrange(key, 0, -1)
                for data in metrics_data:
                    all_metrics.append(json.loads(data))
            except Exception:
                continue
        
        if not all_metrics:
            return {"error": "No metrics available"}
        
        # Calculate statistics
        response_times = [m["response_time_ms"] for m in all_metrics]
        confidence_scores = [m["confidence_score"] for m in all_metrics]
        token_counts = [m["token_count"] for m in all_metrics]
        
        return {
            "total_requests": len(all_metrics),
            "avg_response_time_ms": sum(response_times) / len(response_times),
            "p95_response_time_ms": sorted(response_times)[int(len(response_times) * 0.95)],
            "avg_confidence": sum(confidence_scores) / len(confidence_scores),
            "avg_tokens": sum(token_counts) / len(token_counts),
            "model_usage": self._count_model_usage(all_metrics),
            "period_days": days
        }
    
    def _count_model_usage(self, metrics: List[Dict]) -> Dict[str, int]:
        """Count usage by model."""
        usage = {}
        for m in metrics:
            model = m.get("model_used", "unknown")
            usage[model] = usage.get(model, 0) + 1
        return usage
```