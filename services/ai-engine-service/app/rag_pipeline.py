"""
RAG Pipeline Implementation for AI Engine Service
Implements Retrieval-Augmented Generation with conversation context management
"""

import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from collections import deque
from functools import lru_cache

from shared.ai.chromadb_manager import get_chromadb_manager
from shared.ai.ollama_manager import get_ollama_manager
from shared.models.conversations import Message, MessageRole
from shared.exceptions.base import BaseServiceException
from shared.monitoring import (
    trace_ml_operation, get_metrics_collector, create_correlation_id,
    OperationType, MLMetrics
)

# Import the new embedding manager
from .embedding_manager import get_embedding_manager, EmbeddingError

logger = logging.getLogger(__name__)


# Centralized serialization helpers for consistent message handling
def serialize_message(message: Message) -> Dict[str, Any]:
    """
    Serialize a Message object to a dictionary with proper datetime handling
    
    Args:
        message: Message object to serialize
        
    Returns:
        Dictionary with ISO string datetime fields
    """
    message_dict = message.model_dump()
    
    # Convert datetime fields to ISO strings
    if message_dict.get('created_at'):
        message_dict['created_at'] = message.created_at.isoformat()
    if message_dict.get('updated_at'):
        message_dict['updated_at'] = message.updated_at.isoformat()
    
    return message_dict


def deserialize_message(message_data: Dict[str, Any]) -> Message:
    """
    Deserialize a dictionary to a Message object with proper datetime parsing
    
    Args:
        message_data: Dictionary with message data
        
    Returns:
        Message object with parsed datetime fields
        
    Raises:
        ValueError: If message data is invalid
    """
    # Parse datetime fields from ISO strings
    if isinstance(message_data.get('created_at'), str):
        message_data['created_at'] = datetime.fromisoformat(message_data['created_at'].replace('Z', '+00:00'))
    if isinstance(message_data.get('updated_at'), str):
        message_data['updated_at'] = datetime.fromisoformat(message_data['updated_at'].replace('Z', '+00:00'))
    
    return Message(**message_data)


def generate_message_id() -> str:
    """
    Generate a unique message ID using UUID to avoid collisions
    
    Returns:
        Unique message ID string
    """
    return f"msg_{uuid.uuid4().hex}"


class RAGError(BaseServiceException):
    """RAG pipeline specific errors"""


class ConversationError(BaseServiceException):
    """Conversation management errors"""


@dataclass
class RetrievedChunk:
    """Retrieved document chunk with similarity score"""
    content: str
    metadata: Dict[str, Any]
    similarity_score: float
    rank: int
    document_id: str
    chunk_index: int


@dataclass
class AIResponse:
    """AI response with context and metadata"""
    response: str
    sources: List[RetrievedChunk]
    confidence: float
    conversation_id: str
    processing_time_ms: float
    model_used: str
    token_count: Optional[int] = None
    context_used: Optional[List[Message]] = None


class ConversationManager:
    """Manages conversation context and history using Redis"""
    
    def __init__(self, cache_manager=None, max_context_messages: int = 20):
        """
        Initialize conversation manager
        
        Args:
            cache_manager: Cache manager for context storage
            max_context_messages: Maximum messages to keep in context
        """
        # Import here to avoid circular imports
        from shared.cache import get_cache_manager
        
        self.cache_manager = cache_manager or get_cache_manager()
        self.max_context_messages = max_context_messages
        self.context_ttl = 3600 * 24  # 24 hours
        
        # In-memory fallback with bounded LRU cache (max 1000 conversations)
        self._memory_cache = lru_cache(maxsize=1000)(self._get_conversation_from_memory)
        
        # Internal storage for LRU cache
        self._conversation_storage: Dict[str, List[Message]] = {}
        
        logger.info(f"ConversationManager initialized with max_context_messages={max_context_messages}")
    
    def _get_conversation_from_memory(self, conversation_id: str) -> List[Message]:
        """Helper method for LRU cache to get conversation from memory"""
        return self._conversation_storage.get(conversation_id, [])
    
    async def get_context(
        self, 
        conversation_id: str, 
        max_messages: int = 10,
        creator_id: str = "system"
    ) -> List[Message]:
        """
        Get recent conversation context
        
        Args:
            conversation_id: Conversation identifier
            max_messages: Maximum messages to retrieve
            creator_id: Creator ID for tenant isolation
            
        Returns:
            List of recent messages
        """
        try:
            # Try cache first
            cache_key = f"conversation:{conversation_id}:messages"
            cached_messages = await self.cache_manager.redis.get(creator_id, cache_key)
            
            if cached_messages and isinstance(cached_messages, list):
                messages = []
                for msg_data in cached_messages[-max_messages:]:
                    try:
                        # Use centralized deserialization
                        message = deserialize_message(msg_data)
                        messages.append(message)
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Failed to deserialize message data: {e}")
                        continue
                
                return messages
            else:
                # Fallback to bounded memory cache
                cached_messages = self._memory_cache(conversation_id)
                return cached_messages[-max_messages:] if cached_messages else []
                
        except Exception as e:
            logger.error(f"Failed to get conversation context: {e}")
            # Return empty context on error
            return []
    
    @trace_ml_operation("conversation_add_exchange", operation_type=OperationType.CONVERSATION)
    async def add_exchange(
        self,
        conversation_id: str,
        user_message: str,
        ai_response: str,
        creator_id: str = "system",
        sources: List[RetrievedChunk] = None,
        processing_time_ms: float = 0,
        model_used: str = "unknown"
    ) -> bool:
        """
        Add user-AI exchange to conversation context
        
        Args:
            conversation_id: Conversation identifier
            user_message: User's message
            ai_response: AI's response
            creator_id: Creator ID for tenant isolation
            sources: Retrieved sources used for response
            processing_time_ms: Time taken to generate response
            model_used: Model used for generation
            
        Returns:
            True if successful
        """
        try:
            # Track conversation metrics
            metrics_collector = get_metrics_collector()
            start_time = datetime.utcnow()
            timestamp = datetime.utcnow()
            
            conv_metrics = MLMetrics(
                operation_type=OperationType.CONVERSATION,
                input_length=len(user_message),
                output_length=len(ai_response),
                model_name=model_used,
                creator_id=creator_id
            )
            metrics_collector.record_ml_operation_start(conv_metrics)
            
            # Create user message with UUID
            user_msg = Message(
                id=generate_message_id(),
                creator_id=creator_id,
                conversation_id=conversation_id,
                role=MessageRole.USER,
                content=user_message,
                created_at=timestamp,
                metadata={}
            )
            
            # Create AI message with UUID
            ai_msg = Message(
                id=generate_message_id(),
                creator_id=creator_id,
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT,
                content=ai_response,
                created_at=timestamp,
                processing_time_ms=int(processing_time_ms),
                metadata={
                    "sources": [
                        {
                            "document_id": s.document_id,
                            "chunk_index": s.chunk_index,
                            "similarity_score": s.similarity_score,
                            "content_preview": s.content[:100] + "..." if len(s.content) > 100 else s.content
                        }
                        for s in (sources or [])
                    ],
                    "model_used": model_used,
                    "processing_time_ms": processing_time_ms
                }
            )
            
            # Get current messages from cache
            cache_key = f"conversation:{conversation_id}:messages"
            current_messages = await self.cache_manager.redis.get(creator_id, cache_key) or []
            
            # Add new messages using centralized serialization
            new_messages = current_messages + [serialize_message(user_msg), serialize_message(ai_msg)]
            
            # Trim to max context size
            if len(new_messages) > self.max_context_messages:
                new_messages = new_messages[-self.max_context_messages:]
            
            # Store back in cache
            await self.cache_manager.redis.set(
                creator_id, 
                cache_key, 
                new_messages, 
                self.context_ttl
            )
            
            # Also update bounded memory cache as fallback
            if conversation_id not in self._conversation_storage:
                self._conversation_storage[conversation_id] = []
            
            self._conversation_storage[conversation_id].extend([user_msg, ai_msg])
            
            # Trim memory cache to max context size
            if len(self._conversation_storage[conversation_id]) > self.max_context_messages:
                self._conversation_storage[conversation_id] = self._conversation_storage[conversation_id][-self.max_context_messages:]
            
            # Clear LRU cache for this conversation to force refresh
            self._memory_cache.cache_clear()
            
            # Record successful conversation update
            operation_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            metrics_collector.record_ml_operation_success(
                conv_metrics, operation_time, len(sources or [])
            )
            
            logger.debug(f"Added exchange to conversation {conversation_id}")
            return True
            
        except Exception as e:
            # Record conversation error
            operation_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            metrics_collector.record_ml_operation_error(
                conv_metrics, operation_time, str(e)
            )
            
            logger.error(f"Failed to add conversation exchange: {e}")
            return False
    
    async def get_conversation_summary(
        self, 
        conversation_id: str,
        creator_id: str = "system"
    ) -> Optional[Dict[str, Any]]:
        """
        Get conversation summary and statistics
        
        Args:
            conversation_id: Conversation identifier
            creator_id: Creator ID for tenant isolation
            
        Returns:
            Conversation summary or None if not found
        """
        try:
            messages = await self.get_context(conversation_id, max_messages=100, creator_id=creator_id)
            
            if not messages:
                return None
            
            user_messages = [m for m in messages if m.role == MessageRole.USER]
            ai_messages = [m for m in messages if m.role == MessageRole.ASSISTANT]
            
            # Calculate average response time
            response_times = [
                m.processing_time_ms for m in ai_messages 
                if m.processing_time_ms is not None
            ]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            return {
                "conversation_id": conversation_id,
                "total_messages": len(messages),
                "user_messages": len(user_messages),
                "ai_messages": len(ai_messages),
                "first_message": messages[0].created_at.isoformat() if messages else None,
                "last_message": messages[-1].created_at.isoformat() if messages else None,
                "avg_response_time_ms": avg_response_time,
                "avg_response_length": sum(len(m.content) for m in ai_messages) / len(ai_messages) if ai_messages else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get conversation summary: {e}")
            return None


class RAGPipeline:
    """
    Main Retrieval-Augmented Generation pipeline
    
    Implements complete RAG workflow:
    1. Retrieve conversation context
    2. Search relevant knowledge chunks
    3. Build contextual prompt
    4. Generate AI response
    5. Update conversation context
    """
    
    def __init__(
        self,
        chromadb_manager=None,
        ollama_manager=None,
        conversation_manager=None,
        embedding_manager=None,
        max_context_tokens: int = 4000,
        max_retrieved_chunks: int = 5,
        similarity_threshold: float = 0.7
    ):
        """
        Initialize RAG pipeline
        
        Args:
            chromadb_manager: ChromaDB manager instance
            ollama_manager: Ollama manager instance
            conversation_manager: Conversation manager instance
            embedding_manager: Embedding manager instance
            max_context_tokens: Maximum tokens for context window
            max_retrieved_chunks: Maximum chunks to retrieve
            similarity_threshold: Minimum similarity score for chunks
        """
        self.chromadb_manager = chromadb_manager or get_chromadb_manager()
        self.ollama_manager = ollama_manager or get_ollama_manager()
        self.conversation_manager = conversation_manager or ConversationManager()
        self.embedding_manager = embedding_manager or get_embedding_manager()
        
        self.max_context_tokens = max_context_tokens
        self.max_retrieved_chunks = max_retrieved_chunks
        self.similarity_threshold = similarity_threshold
        
        # Performance tracking with bounded deque (max 1000 entries)
        self._processing_times: deque = deque(maxlen=1000)
        
        logger.info(
            f"RAG Pipeline initialized - "
            f"max_context_tokens: {max_context_tokens}, "
            f"max_retrieved_chunks: {max_retrieved_chunks}, "
            f"similarity_threshold: {similarity_threshold}"
        )
    
    @trace_ml_operation("rag_process_query", operation_type=OperationType.CHAT)
    async def process_query(
        self, 
        query: str, 
        creator_id: str, 
        conversation_id: str,
        context_window: int = None
    ) -> AIResponse:
        """
        Process user query through complete RAG pipeline
        
        Args:
            query: User's query/message
            creator_id: Creator identifier for tenant isolation
            conversation_id: Conversation identifier
            context_window: Override default context window size
            
        Returns:
            AI response with sources and metadata
            
        Raises:
            RAGError: If processing fails
        """
        start_time = datetime.utcnow()
        context_window = context_window or self.max_context_tokens
        
        # Get metrics collector for tracking
        metrics_collector = get_metrics_collector()
        correlation_id = create_correlation_id()
        
        try:
            logger.info(f"Processing query for creator {creator_id}, conversation {conversation_id} [correlation_id: {correlation_id}]")
            
            # Track query start metrics
            ml_metrics = MLMetrics(
                operation_type=OperationType.CHAT,
                input_length=len(query),
                model_name="llama2:7b-chat",
                creator_id=creator_id
            )
            metrics_collector.record_ml_operation_start(ml_metrics)
            
            # 1. Get conversation context
            conversation_context = await self.conversation_manager.get_context(
                conversation_id, max_messages=10, creator_id=creator_id
            )
            
            # 2. Retrieve relevant knowledge
            relevant_chunks = await self.retrieve_knowledge(
                query, creator_id, limit=self.max_retrieved_chunks
            )
            
            # 3. Build contextual prompt
            prompt = await self.build_contextual_prompt(
                query, conversation_context, relevant_chunks, context_window
            )
            
            # 4. Generate response
            chat_response = await self.ollama_manager.generate_chat_response(
                prompt=prompt,
                temperature=0.7,
                max_tokens=1000
            )
            
            # 5. Calculate confidence score
            confidence = self.calculate_confidence_score(relevant_chunks, chat_response.response)
            
            # 6. Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self._processing_times.append(processing_time)
            
            # Record successful completion metrics
            ml_metrics.output_length = len(chat_response.response)
            ml_metrics.token_count = chat_response.total_duration or 0  # Use duration as proxy
            metrics_collector.record_ml_operation_success(
                ml_metrics, processing_time, len(relevant_chunks)
            )
            
            # 7. Create response object
            ai_response = AIResponse(
                response=chat_response.response,
                sources=relevant_chunks,
                confidence=confidence,
                conversation_id=conversation_id,
                processing_time_ms=processing_time,
                model_used=chat_response.model,
                token_count=None,  # TODO: Implement token counting
                context_used=conversation_context
            )
            
            # 8. Update conversation context
            await self.conversation_manager.add_exchange(
                conversation_id=conversation_id,
                user_message=query,
                ai_response=chat_response.response,
                creator_id=creator_id,
                sources=relevant_chunks,
                processing_time_ms=processing_time,
                model_used=chat_response.model
            )
            
            logger.info(
                f"Query processed successfully - "
                f"processing_time: {processing_time:.2f}ms, "
                f"confidence: {confidence:.2f}, "
                f"sources: {len(relevant_chunks)}"
            )
            
            return ai_response
            
        except Exception as e:
            # Record error metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            metrics_collector.record_ml_operation_error(
                ml_metrics, processing_time, str(e)
            )
            
            error_msg = f"RAG pipeline processing failed: {str(e)}"
            logger.error(error_msg)
            raise RAGError(error_msg) from e
    
    @trace_ml_operation("rag_retrieve_knowledge", operation_type=OperationType.SEARCH)
    async def retrieve_knowledge(
        self, 
        query: str, 
        creator_id: str, 
        limit: int = 5
    ) -> List[RetrievedChunk]:
        """
        Retrieve relevant knowledge chunks from vector store using optimized search
        
        Args:
            query: Search query
            creator_id: Creator identifier for tenant isolation
            limit: Maximum chunks to retrieve
            
        Returns:
            List of retrieved chunks with similarity scores
            
        Raises:
            RAGError: If retrieval fails
        """
        try:
            # Track search metrics
            metrics_collector = get_metrics_collector()
            start_time = datetime.utcnow()
            
            search_metrics = MLMetrics(
                operation_type=OperationType.SEARCH,
                input_length=len(query),
                model_name="nomic-embed-text",
                creator_id=creator_id
            )
            metrics_collector.record_ml_operation_start(search_metrics)
            
            # Use the optimized embedding manager for search
            search_results = await self.embedding_manager.search_similar_documents(
                query=query,
                creator_id=creator_id,
                limit=limit,
                similarity_threshold=self.similarity_threshold,
                use_cache=True
            )
            
            # Convert to RetrievedChunk format
            chunks = []
            for result in search_results:
                chunk = RetrievedChunk(
                    content=result["content"],
                    metadata=result["metadata"],
                    similarity_score=result["similarity_score"],
                    rank=result["rank"],
                    document_id=result["document_id"],
                    chunk_index=result["chunk_index"]
                )
                chunks.append(chunk)
            
            # Record successful search metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            search_metrics.output_length = len(chunks)
            metrics_collector.record_ml_operation_success(
                search_metrics, processing_time, len(chunks)
            )
            
            logger.debug(f"Retrieved {len(chunks)} relevant chunks for query using optimized search")
            return chunks
            
        except EmbeddingError as e:
            # Record search error metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            metrics_collector.record_ml_operation_error(
                search_metrics, processing_time, str(e)
            )
            
            error_msg = f"Optimized knowledge retrieval failed: {str(e)}"
            logger.error(error_msg)
            raise RAGError(error_msg) from e
        except Exception as e:
            # Record unexpected error metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            metrics_collector.record_ml_operation_error(
                search_metrics, processing_time, str(e)
            )
            
            error_msg = f"Unexpected error in knowledge retrieval: {str(e)}"
            logger.error(error_msg)
            raise RAGError(error_msg) from e
    
    async def build_contextual_prompt(
        self,
        query: str,
        conversation_context: List[Message],
        knowledge_chunks: List[RetrievedChunk],
        max_tokens: int
    ) -> str:
        """
        Build prompt with conversation context and retrieved knowledge
        
        Args:
            query: User's query
            conversation_context: Recent conversation messages
            knowledge_chunks: Retrieved knowledge chunks
            max_tokens: Maximum tokens for prompt
            
        Returns:
            Formatted prompt string
        """
        try:
            # Base prompt template
            prompt_parts = [
                "You are an AI coaching assistant. Use the provided context and conversation history to give helpful, accurate responses.",
                "Be conversational, supportive, and focus on actionable advice.",
                "",
                "KNOWLEDGE CONTEXT:"
            ]
            
            # Add knowledge chunks
            if knowledge_chunks:
                for i, chunk in enumerate(knowledge_chunks[:3]):  # Limit to top 3 chunks
                    # Truncate long chunks
                    content = chunk.content[:500] + "..." if len(chunk.content) > 500 else chunk.content
                    prompt_parts.append(f"[Source {i+1}] {content}")
            else:
                prompt_parts.append("No specific knowledge found for this query.")
            
            prompt_parts.extend([
                "",
                "CONVERSATION HISTORY:"
            ])
            
            # Add recent conversation context
            if conversation_context:
                for msg in conversation_context[-5:]:  # Last 5 messages
                    role = "User" if msg.role == MessageRole.USER else "Assistant"
                    # Truncate long messages
                    content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
                    prompt_parts.append(f"{role}: {content}")
            else:
                prompt_parts.append("This is the start of the conversation.")
            
            prompt_parts.extend([
                "",
                f"User: {query}",
                "Assistant:"
            ])
            
            full_prompt = "\n".join(prompt_parts)
            
            # Truncate if too long (rough token estimation: 1 token ≈ 4 characters)
            estimated_tokens = len(full_prompt) // 4
            if estimated_tokens > max_tokens:
                # Prioritize recent context over older knowledge
                truncated_prompt = self.truncate_prompt_intelligently(
                    full_prompt, max_tokens
                )
                return truncated_prompt
            
            return full_prompt
            
        except Exception as e:
            logger.error(f"Failed to build contextual prompt: {e}")
            # Return basic prompt on error
            return f"User: {query}\nAssistant:"
    
    def truncate_prompt_intelligently(
        self, 
        prompt: str, 
        max_tokens: int
    ) -> str:
        """
        Intelligently truncate prompt to fit within token limit
        
        Args:
            prompt: Full prompt text
            max_tokens: Maximum allowed tokens
            
        Returns:
            Truncated prompt
        """
        try:
            # Rough token estimation: 1 token ≈ 4 characters
            max_chars = max_tokens * 4
            
            if len(prompt) <= max_chars:
                return prompt
            
            # Split into sections
            sections = prompt.split("\n\n")
            
            # Always keep the user query and assistant prompt
            essential_parts = []
            for section in reversed(sections):
                if "User:" in section or "Assistant:" in section:
                    essential_parts.insert(0, section)
                    if len(essential_parts) >= 2:  # User query + Assistant prompt
                        break
            
            # Add conversation history if space allows
            remaining_chars = max_chars - sum(len(part) for part in essential_parts)
            
            for section in reversed(sections):
                if "CONVERSATION HISTORY:" in section or any(
                    role in section for role in ["User:", "Assistant:"]
                ):
                    if len(section) <= remaining_chars:
                        essential_parts.insert(-1, section)
                        remaining_chars -= len(section)
            
            # Add knowledge context if space allows
            remaining_chars = max_chars - sum(len(part) for part in essential_parts)
            
            for section in sections:
                if "KNOWLEDGE CONTEXT:" in section or "[Source" in section:
                    if len(section) <= remaining_chars:
                        essential_parts.insert(-2, section)
                        remaining_chars -= len(section)
                        break
            
            truncated = "\n\n".join(essential_parts)
            
            # Final truncation if still too long
            if len(truncated) > max_chars:
                truncated = truncated[:max_chars-3] + "..."
            
            return truncated
            
        except Exception as e:
            logger.error(f"Failed to truncate prompt: {e}")
            # Return simple truncation
            max_chars = max_tokens * 4
            return prompt[:max_chars-3] + "..." if len(prompt) > max_chars else prompt
    
    def calculate_confidence_score(
        self, 
        chunks: List[RetrievedChunk], 
        response: str
    ) -> float:
        """
        Calculate confidence score based on retrieval quality and response
        
        Args:
            chunks: Retrieved knowledge chunks
            response: Generated response
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        try:
            if not chunks:
                return 0.3  # Low confidence without knowledge
            
            # Average similarity score of retrieved chunks
            avg_similarity = sum(chunk.similarity_score for chunk in chunks) / len(chunks)
            
            # Boost confidence if multiple high-quality chunks
            high_quality_chunks = len([c for c in chunks if c.similarity_score > 0.8])
            quality_boost = min(high_quality_chunks * 0.1, 0.3)
            
            # Response length factor (very short responses might be less confident)
            response_words = len(response.split())
            length_factor = min(response_words / 50, 1.0)
            
            # Combine factors
            confidence = (avg_similarity * 0.6) + quality_boost + (length_factor * 0.1)
            
            # Ensure confidence is between 0.0 and 1.0
            return max(0.0, min(confidence, 1.0))
            
        except Exception as e:
            logger.error(f"Failed to calculate confidence score: {e}")
            return 0.5  # Default confidence on error
    
    async def get_pipeline_stats(self) -> Dict[str, Any]:
        """
        Get pipeline performance statistics
        
        Returns:
            Performance statistics dictionary
        """
        try:
            if not self._processing_times:
                return {
                    "total_queries": 0,
                    "avg_processing_time_ms": 0,
                    "min_processing_time_ms": 0,
                    "max_processing_time_ms": 0,
                    "p95_processing_time_ms": 0,
                    "recent_queries": 0
                }
            
            processing_times = sorted(self._processing_times)
            total_queries = len(processing_times)
            
            return {
                "total_queries": total_queries,
                "avg_processing_time_ms": sum(processing_times) / total_queries,
                "min_processing_time_ms": min(processing_times),
                "max_processing_time_ms": max(processing_times),
                "p95_processing_time_ms": processing_times[int(total_queries * 0.95)] if total_queries > 0 else 0,
                "recent_queries": total_queries  # All queries in bounded deque are recent
            }
            
        except Exception as e:
            logger.error(f"Failed to get pipeline stats: {e}")
            return {"error": str(e)}


# Global RAG pipeline instance (initialized lazily)
_rag_pipeline: Optional[RAGPipeline] = None


def get_rag_pipeline() -> RAGPipeline:
    """Get global RAG pipeline instance (lazy initialization)"""
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline


async def close_rag_pipeline():
    """Close global RAG pipeline"""
    global _rag_pipeline
    if _rag_pipeline is not None:
        # RAG pipeline doesn't need explicit cleanup
        _rag_pipeline = None