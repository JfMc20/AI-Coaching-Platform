"""
OpenTelemetry Distributed Tracing for ML Operations

Implements comprehensive tracing for AI Engine, Ollama, and ChromaDB services
with correlation ID tracking and span instrumentation for performance monitoring.
"""

import uuid
import time
import logging
import inspect
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from functools import wraps
from contextlib import asynccontextmanager

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.propagate import inject, extract
from opentelemetry.trace import Status, StatusCode

from shared.config.env_constants import get_env_value

logger = logging.getLogger(__name__)


@dataclass
class TraceContext:
    """Context information for distributed tracing"""
    correlation_id: str
    creator_id: str
    operation_type: str
    model_name: Optional[str] = None
    request_id: Optional[str] = None
    start_time: float = 0.0


class MLTracer:
    """ML Operations tracer with privacy protection"""
    
    def __init__(self):
        self.tracer_provider = None
        self.tracer = None
        self._setup_tracing()
    
    def _setup_tracing(self):
        """Setup OpenTelemetry tracing configuration"""
        try:
            # Configure tracer provider
            self.tracer_provider = TracerProvider()
            trace.set_tracer_provider(self.tracer_provider)
            
            # Setup Jaeger exporter if configured
            jaeger_endpoint = get_env_value("JAEGER_ENDPOINT", "http://localhost:14268/api/traces")
            if jaeger_endpoint and get_env_value("ENABLE_TRACING", "false").lower() == "true":
                jaeger_exporter = JaegerExporter(
                    endpoint=jaeger_endpoint,
                    collector_endpoint=jaeger_endpoint,
                )
                span_processor = BatchSpanProcessor(jaeger_exporter)
                self.tracer_provider.add_span_processor(span_processor)
                logger.info(f"Jaeger tracing enabled: {jaeger_endpoint}")
            
            # Get tracer instance
            self.tracer = trace.get_tracer(__name__)
            
            # Auto-instrument HTTP and Redis
            HTTPXClientInstrumentor().instrument()
            RedisInstrumentor().instrument()
            
        except Exception as e:
            logger.error(f"Failed to setup tracing: {e}")
            # Create noop tracer as fallback
            self.tracer = trace.NoOpTracer()


# Global tracer instance
_ml_tracer = MLTracer()


def get_tracer() -> trace.Tracer:
    """Get the configured ML operations tracer"""
    return _ml_tracer.tracer


def create_correlation_id() -> str:
    """Create a unique correlation ID for request tracking"""
    return f"ml_{uuid.uuid4().hex[:16]}"


def trace_ml_operation(
    operation_name: str,
    operation_type: str = "ml_operation",
    include_input_length: bool = True,
    include_model_info: bool = True
):
    """
    Decorator for tracing ML operations with privacy protection
    
    Args:
        operation_name: Name of the operation (e.g., "embedding_generation")
        operation_type: Type of operation (e.g., "embedding", "chat", "search")
        include_input_length: Whether to include input length in span
        include_model_info: Whether to include model information in span
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer()
            correlation_id = kwargs.get('correlation_id') or create_correlation_id()
            
            with tracer.start_as_current_span(operation_name) as span:
                try:
                    # Add basic span attributes (privacy-safe)
                    span.set_attribute("operation.type", operation_type)
                    span.set_attribute("correlation.id", correlation_id)
                    span.set_attribute("service.name", "ai-engine")
                    
                    # Add creator ID if available (for multi-tenancy)
                    creator_id = kwargs.get('creator_id')
                    if creator_id:
                        span.set_attribute("tenant.creator_id", creator_id)
                    
                    # Add input length (privacy-safe metadata)
                    if include_input_length:
                        input_text = kwargs.get('text') or kwargs.get('query') or kwargs.get('input_text')
                        if input_text:
                            span.set_attribute("input.length", len(input_text))
                            span.set_attribute("input.type", type(input_text).__name__)
                    
                    # Add model information
                    if include_model_info:
                        model = kwargs.get('model') or kwargs.get('model_name')
                        if model:
                            span.set_attribute("model.name", model)
                    
                    # Record start time
                    start_time = time.time()
                    span.set_attribute("operation.start_time", start_time)
                    
                    # Execute function
                    result = await func(*args, **kwargs)
                    
                    # Record success metrics
                    duration = time.time() - start_time
                    span.set_attribute("operation.duration", duration)
                    span.set_attribute("operation.status", "success")
                    
                    # Add result metadata (privacy-safe)
                    if hasattr(result, '__len__'):
                        span.set_attribute("result.length", len(result))
                    
                    span.set_status(Status(StatusCode.OK))
                    return result
                    
                except Exception as e:
                    # Record error information
                    duration = time.time() - start_time
                    span.set_attribute("operation.duration", duration)
                    span.set_attribute("operation.status", "error")
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e)[:200])  # Truncate for privacy
                    
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer()
            correlation_id = kwargs.get('correlation_id') or create_correlation_id()
            
            with tracer.start_as_current_span(operation_name) as span:
                try:
                    # Similar implementation for sync functions
                    span.set_attribute("operation.type", operation_type)
                    span.set_attribute("correlation.id", correlation_id)
                    
                    start_time = time.time()
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    span.set_attribute("operation.duration", duration)
                    span.set_attribute("operation.status", "success")
                    span.set_status(Status(StatusCode.OK))
                    
                    return result
                    
                except Exception as e:
                    duration = time.time() - start_time
                    span.set_attribute("operation.duration", duration)
                    span.set_attribute("operation.status", "error")
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e)[:200])
                    
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise
        
        # Return appropriate wrapper based on function type
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


@asynccontextmanager
async def trace_ml_request(
    operation_name: str,
    context: TraceContext,
    tags: Optional[Dict[str, Any]] = None
):
    """
    Async context manager for tracing ML requests with full context
    
    Args:
        operation_name: Name of the operation
        context: Trace context information
        tags: Additional tags to add to span
    """
    tracer = get_tracer()
    
    with tracer.start_as_current_span(operation_name) as span:
        try:
            # Set context attributes
            span.set_attribute("correlation.id", context.correlation_id)
            span.set_attribute("tenant.creator_id", context.creator_id)
            span.set_attribute("operation.type", context.operation_type)
            
            if context.model_name:
                span.set_attribute("model.name", context.model_name)
            
            if context.request_id:
                span.set_attribute("request.id", context.request_id)
            
            # Add custom tags
            if tags:
                for key, value in tags.items():
                    if isinstance(value, (str, int, float, bool)):
                        span.set_attribute(f"custom.{key}", value)
            
            # Record start time
            context.start_time = time.time()
            span.set_attribute("operation.start_time", context.start_time)
            
            yield span
            
            # Record success
            duration = time.time() - context.start_time
            span.set_attribute("operation.duration", duration)
            span.set_attribute("operation.status", "success")
            span.set_status(Status(StatusCode.OK))
            
        except Exception as e:
            # Record error
            duration = time.time() - context.start_time
            span.set_attribute("operation.duration", duration)
            span.set_attribute("operation.status", "error")
            span.set_attribute("error.type", type(e).__name__)
            span.set_attribute("error.message", str(e)[:200])
            
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise


def inject_trace_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """
    Inject trace context into HTTP headers for propagation
    
    Args:
        headers: Existing headers dictionary
        
    Returns:
        Headers with trace context injected
    """
    inject(headers)
    return headers


def extract_trace_context(headers: Dict[str, str]) -> Optional[trace.Context]:
    """
    Extract trace context from HTTP headers
    
    Args:
        headers: HTTP headers dictionary
        
    Returns:
        Extracted trace context or None
    """
    try:
        return extract(headers)
    except Exception as e:
        logger.warning(f"Failed to extract trace context: {e}")
        return None


class SpanLogger:
    """Helper for adding structured logs to spans"""
    
    @staticmethod
    def log_ml_metrics(
        span: trace.Span,
        latency_ms: float,
        tokens_processed: Optional[int] = None,
        model_version: Optional[str] = None,
        cache_hit: bool = False
    ):
        """Log ML-specific metrics to span"""
        span.set_attribute("metrics.latency_ms", latency_ms)
        span.set_attribute("metrics.cache_hit", cache_hit)
        
        if tokens_processed:
            span.set_attribute("metrics.tokens_processed", tokens_processed)
        
        if model_version:
            span.set_attribute("model.version", model_version)
    
    @staticmethod
    def log_error_details(
        span: trace.Span,
        error: Exception,
        error_code: Optional[str] = None,
        retry_count: int = 0
    ):
        """Log error details to span"""
        span.set_attribute("error.type", type(error).__name__)
        span.set_attribute("error.message", str(error)[:200])
        span.set_attribute("error.retry_count", retry_count)
        
        if error_code:
            span.set_attribute("error.code", error_code)
    
    @staticmethod
    def log_resource_usage(
        span: trace.Span,
        cpu_percent: Optional[float] = None,
        memory_mb: Optional[float] = None,
        gpu_percent: Optional[float] = None
    ):
        """Log resource usage to span"""
        if cpu_percent is not None:
            span.set_attribute("resources.cpu_percent", cpu_percent)
        
        if memory_mb is not None:
            span.set_attribute("resources.memory_mb", memory_mb)
        
        if gpu_percent is not None:
            span.set_attribute("resources.gpu_percent", gpu_percent)


# Convenience function for quick span creation
def start_ml_span(
    operation_name: str,
    correlation_id: Optional[str] = None,
    creator_id: Optional[str] = None,
    model_name: Optional[str] = None
) -> trace.Span:
    """
    Start a new ML operation span with standard attributes
    
    Args:
        operation_name: Name of the operation
        correlation_id: Correlation ID for request tracking
        creator_id: Creator ID for multi-tenancy
        model_name: Model name for ML operations
        
    Returns:
        Started span
    """
    tracer = get_tracer()
    span = tracer.start_span(operation_name)
    
    if correlation_id:
        span.set_attribute("correlation.id", correlation_id)
    
    if creator_id:
        span.set_attribute("tenant.creator_id", creator_id)
    
    if model_name:
        span.set_attribute("model.name", model_name)
    
    return span