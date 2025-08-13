"""
Ollama Manager for AI Engine Service
Handles LLM and embedding model interactions with error handling and fallbacks.

This module uses centralized environment configuration from shared.config.env_constants
for all environment variable access and default values.
"""

import os
import logging
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass
from contextlib import asynccontextmanager

from shared.config.settings import get_ai_engine_config
from shared.config.env_constants import (
    OLLAMA_URL,
    EMBEDDING_MODEL,
    CHAT_MODEL,
    get_env_value
)
from shared.exceptions.base import BaseServiceException

logger = logging.getLogger(__name__)


class OllamaError(BaseServiceException):
    """Ollama specific errors"""
    pass


class OllamaConnectionError(OllamaError):
    """Ollama connection errors"""
    pass


class OllamaModelError(OllamaError):
    """Ollama model management errors"""
    pass


@dataclass
class ModelInfo:
    """Model information structure"""
    name: str
    size: Optional[str] = None
    digest: Optional[str] = None
    modified_at: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    loaded: bool = False


@dataclass
class EmbeddingResponse:
    """Embedding generation response"""
    embeddings: List[List[float]]
    model: str
    processing_time_ms: float
    token_count: Optional[int] = None


@dataclass
class ChatResponse:
    """Chat completion response"""
    response: str
    model: str
    processing_time_ms: float
    context: Optional[List[int]] = None
    done: bool = True


class OllamaManager:
    """
    Ollama client manager for LLM and embedding operations.
    
    Handles model loading, health checks, and API interactions with proper
    error handling and connection management. Uses centralized environment
    configuration from shared.config.env_constants for all settings.
    """
    
    def __init__(
        self,
        ollama_url: Optional[str] = None,
        embedding_model: Optional[str] = None,
        chat_model: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3
    ):
        """
        Initialize Ollama manager.
        
        Uses centralized environment configuration with automatic fallback to
        environment-specific defaults when config loading fails.
        
        Args:
            ollama_url: Ollama server URL (defaults to config then centralized defaults)
            embedding_model: Embedding model name (defaults to config then centralized defaults)
            chat_model: Chat model name (defaults to config then centralized defaults)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
        """
        try:
            self.config = get_ai_engine_config()
        except Exception as e:
            logger.warning(
                f"Failed to load AI engine config: {str(e)}. "
                f"Using centralized environment defaults."
            )
            self.config = None
        
        # Configuration with centralized fallbacks
        # Priority: 1. Passed parameter, 2. Config from get_ai_engine_config, 3. Centralized defaults
        self.ollama_url = (
            ollama_url or
            (self.config.ollama_url if self.config else None) or
            get_env_value(OLLAMA_URL, fallback=True)
        )
        self.embedding_model = (
            embedding_model or
            (self.config.embedding_model if self.config else None) or
            get_env_value(EMBEDDING_MODEL, fallback=True)
        )
        self.chat_model = (
            chat_model or
            (self.config.chat_model if self.config else None) or
            get_env_value(CHAT_MODEL, fallback=True)
        )
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Remove trailing slash from URL if URL is not None
        if self.ollama_url:
            self.ollama_url = self.ollama_url.rstrip('/')
        
        # Session management
        self._session: Optional[aiohttp.ClientSession] = None
        self._models_cache: Dict[str, ModelInfo] = {}
        self._cache_ttl = 300  # 5 minutes cache TTL
        self._last_cache_update: Optional[datetime] = None
        
        logger.info(
            f"Ollama Manager initialized - "
            f"url: {self.ollama_url}, "
            f"embedding_model: {self.embedding_model}, "
            f"chat_model: {self.chat_model}, "
            f"timeout: {timeout}s"
        )
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers={"Content-Type": "application/json"}
            )
        return self._session
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> Union[Dict[str, Any], aiohttp.ClientResponse]:
        """
        Make HTTP request to Ollama API with retry logic
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            data: Request payload
            stream: Whether to return streaming response
            
        Returns:
            Response data or streaming response
            
        Raises:
            OllamaConnectionError: If connection fails
            OllamaError: If API request fails
        """
        url = f"{self.ollama_url}{endpoint}"
        session = await self._get_session()
        
        for attempt in range(self.max_retries + 1):
            try:
                async with session.request(method, url, json=data) as response:
                    if stream:
                        return response
                    
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        raise OllamaError(
                            f"Ollama API error {response.status}: {error_text}"
                        )
                        
            except aiohttp.ClientError as e:
                if attempt == self.max_retries:
                    logger.error(f"Ollama connection failed after {self.max_retries + 1} attempts: {str(e)}")
                    raise OllamaConnectionError(f"Failed to connect to Ollama: {str(e)}") from e
                
                # Exponential backoff
                wait_time = 2 ** attempt
                logger.warning(f"Ollama request failed (attempt {attempt + 1}), retrying in {wait_time}s: {str(e)}")
                await asyncio.sleep(wait_time)
            
            except Exception as e:
                logger.error(f"Unexpected error in Ollama request: {str(e)}")
                raise OllamaError(f"Unexpected error: {str(e)}") from e
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Ollama server
        
        Returns:
            Health status dictionary
            
        Raises:
            OllamaConnectionError: If health check fails
        """
        try:
            # Test basic connectivity
            response = await self._make_request("GET", "/api/tags")
            
            # Check if required models are available
            available_models = [model["name"] for model in response.get("models", [])]
            
            # Check if models are available (exact match or starts with)
            embedding_model_available = any(
                model == self.embedding_model or 
                model.startswith(self.embedding_model + ":") or
                model.startswith(self.embedding_model + "-")
                for model in available_models
            )
            chat_model_available = any(
                model == self.chat_model or
                model.startswith(self.chat_model + ":") or
                model.startswith(self.chat_model + "-")
                for model in available_models
            )
            
            return {
                "status": "healthy",
                "url": self.ollama_url,
                "models_count": len(available_models),
                "embedding_model": {
                    "name": self.embedding_model,
                    "available": embedding_model_available
                },
                "chat_model": {
                    "name": self.chat_model,
                    "available": chat_model_available
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Ollama health check failed: {str(e)}"
            logger.error(error_msg)
            raise OllamaConnectionError(error_msg) from e
    
    async def list_models(self, force_refresh: bool = False) -> List[ModelInfo]:
        """
        List available models with caching
        
        Args:
            force_refresh: Force refresh of models cache
            
        Returns:
            List of available models
            
        Raises:
            OllamaError: If listing models fails
        """
        # Check cache
        if (not force_refresh and 
            self._models_cache and 
            self._last_cache_update and
            (datetime.utcnow() - self._last_cache_update).seconds < self._cache_ttl):
            return list(self._models_cache.values())
        
        try:
            response = await self._make_request("GET", "/api/tags")
            models = []
            
            for model_data in response.get("models", []):
                model_info = ModelInfo(
                    name=model_data.get("name", ""),
                    size=model_data.get("size"),
                    digest=model_data.get("digest"),
                    modified_at=model_data.get("modified_at"),
                    details=model_data.get("details"),
                    loaded=True  # Assume loaded if listed
                )
                models.append(model_info)
                self._models_cache[model_info.name] = model_info
            
            self._last_cache_update = datetime.utcnow()
            logger.info(f"Retrieved {len(models)} models from Ollama")
            
            return models
            
        except Exception as e:
            error_msg = f"Failed to list Ollama models: {str(e)}"
            logger.error(error_msg)
            raise OllamaError(error_msg) from e
    
    async def pull_model(self, model_name: str) -> bool:
        """
        Pull/download a model from Ollama registry
        
        Args:
            model_name: Name of model to pull
            
        Returns:
            True if successful
            
        Raises:
            OllamaModelError: If model pull fails
        """
        try:
            logger.info(f"Pulling model {model_name} from Ollama registry...")
            
            data = {"name": model_name}
            response = await self._make_request("POST", "/api/pull", data=data, stream=True)
            
            # Handle streaming response
            if isinstance(response, aiohttp.ClientResponse):
                async for line in response.content:
                    if line:
                        # Parse progress updates (optional)
                        try:
                            import json
                            progress = json.loads(line.decode())
                            if progress.get("status"):
                                logger.debug(f"Pull progress: {progress['status']}")
                        except:
                            pass
            
            # Invalidate cache to refresh model list
            self._models_cache.clear()
            self._last_cache_update = None
            
            logger.info(f"Successfully pulled model {model_name}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to pull model {model_name}: {str(e)}"
            logger.error(error_msg)
            raise OllamaModelError(error_msg) from e
    
    async def generate_embeddings(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> EmbeddingResponse:
        """
        Generate embeddings for text inputs
        
        Args:
            texts: List of texts to embed
            model: Model name (defaults to configured embedding model)
            
        Returns:
            Embedding response with vectors
            
        Raises:
            OllamaModelError: If embedding generation fails
        """
        if not texts:
            raise ValueError("texts cannot be empty")
        
        model_name = model or self.embedding_model
        start_time = datetime.utcnow()
        
        try:
            # Generate embeddings for each text
            embeddings = []
            total_tokens = 0
            
            for text in texts:
                data = {
                    "model": model_name,
                    "prompt": text
                }
                
                response = await self._make_request("POST", "/api/embeddings", data=data)
                
                if "embedding" not in response:
                    raise OllamaModelError(f"No embedding in response: {response}")
                
                embeddings.append(response["embedding"])
                
                # Estimate token count (rough approximation)
                total_tokens += len(text.split())
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.debug(
                f"Generated {len(embeddings)} embeddings using {model_name} "
                f"in {processing_time:.2f}ms"
            )
            
            return EmbeddingResponse(
                embeddings=embeddings,
                model=model_name,
                processing_time_ms=processing_time,
                token_count=total_tokens
            )
            
        except Exception as e:
            error_msg = f"Failed to generate embeddings with {model_name}: {str(e)}"
            logger.error(error_msg)
            raise OllamaModelError(error_msg) from e
    
    async def generate_chat_response(
        self,
        prompt: str,
        model: Optional[str] = None,
        context: Optional[List[int]] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> ChatResponse:
        """
        Generate chat completion response
        
        Args:
            prompt: User prompt/message
            model: Model name (defaults to configured chat model)
            context: Previous conversation context
            system_prompt: System prompt for behavior
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Chat response
            
        Raises:
            OllamaModelError: If chat generation fails
        """
        if not prompt.strip():
            raise ValueError("prompt cannot be empty")
        
        model_name = model or self.chat_model
        start_time = datetime.utcnow()
        
        try:
            # Build request data
            data = {
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature
                }
            }
            
            if context:
                data["context"] = context
            
            if system_prompt:
                data["system"] = system_prompt
            
            if max_tokens:
                data["options"]["num_predict"] = max_tokens
            
            response = await self._make_request("POST", "/api/generate", data=data)
            
            if "response" not in response:
                raise OllamaModelError(f"No response in chat completion: {response}")
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.debug(
                f"Generated chat response using {model_name} "
                f"in {processing_time:.2f}ms"
            )
            
            return ChatResponse(
                response=response["response"],
                model=model_name,
                processing_time_ms=processing_time,
                context=response.get("context"),
                done=response.get("done", True)
            )
            
        except Exception as e:
            error_msg = f"Failed to generate chat response with {model_name}: {str(e)}"
            logger.error(error_msg)
            raise OllamaModelError(error_msg) from e
    
    async def ensure_models_available(self) -> Dict[str, bool]:
        """
        Ensure required models are available, pull if necessary
        
        Returns:
            Dictionary with model availability status
            
        Raises:
            OllamaModelError: If models cannot be made available
        """
        try:
            models = await self.list_models(force_refresh=True)
            available_models = [model.name for model in models]
            
            results = {}
            
            # Check embedding model
            embedding_available = any(
                self.embedding_model in model for model in available_models
            )
            
            if not embedding_available:
                logger.info(f"Pulling embedding model: {self.embedding_model}")
                await self.pull_model(self.embedding_model)
                embedding_available = True
            
            results["embedding_model"] = embedding_available
            
            # Check chat model
            chat_available = any(
                self.chat_model in model for model in available_models
            )
            
            if not chat_available:
                logger.info(f"Pulling chat model: {self.chat_model}")
                await self.pull_model(self.chat_model)
                chat_available = True
            
            results["chat_model"] = chat_available
            
            return results
            
        except Exception as e:
            error_msg = f"Failed to ensure models availability: {str(e)}"
            logger.error(error_msg)
            raise OllamaModelError(error_msg) from e
    
    async def close(self):
        """Close aiohttp session and cleanup resources"""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("Ollama manager session closed")
        
        self._models_cache.clear()
        self._last_cache_update = None


# Global instance (initialized lazily)
_ollama_manager: Optional[OllamaManager] = None


def get_ollama_manager() -> OllamaManager:
    """Get global Ollama manager instance (lazy initialization)"""
    global _ollama_manager
    if _ollama_manager is None:
        _ollama_manager = OllamaManager()
    return _ollama_manager


async def close_ollama_manager():
    """Close global Ollama manager"""
    global _ollama_manager
    if _ollama_manager is not None:
        await _ollama_manager.close()
        _ollama_manager = None