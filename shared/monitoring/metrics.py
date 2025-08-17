"""
Prometheus Metrics Collection for ML Models

Implements comprehensive metrics collection for SLA compliance, performance monitoring,
and cost tracking with privacy protection.
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from prometheus_client import (
    Counter, Histogram, Gauge, CollectorRegistry, 
    generate_latest
)


logger = logging.getLogger(__name__)


class OperationType(str, Enum):
    """ML operation types for metrics categorization"""
    EMBEDDING = "embedding"
    CHAT = "chat"
    SEARCH = "search"
    DOCUMENT_PROCESSING = "document_processing"
    MODEL_INFERENCE = "model_inference"
    CONVERSATION = "conversation"


class ErrorType(str, Enum):
    """Error types for categorization"""
    INPUT_VALIDATION = "input_validation"
    MODEL_ERROR = "model_error"
    TIMEOUT = "timeout"
    OOM = "out_of_memory"
    API_ERROR = "api_error"
    INFRASTRUCTURE = "infrastructure"


@dataclass
class ModelMetrics:
    """Container for model-specific metrics"""
    model_name: str
    requests_total: int = 0
    errors_total: int = 0
    latency_p50: float = 0.0
    latency_p95: float = 0.0
    latency_p99: float = 0.0
    tokens_processed: int = 0
    cost_total: float = 0.0


class MetricsCollector:
    """
    Comprehensive metrics collector for ML operations
    
    Collects performance, error, and business metrics while maintaining
    privacy protection and GDPR compliance.
    """
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or CollectorRegistry()
        self._setup_metrics()
    
    def _setup_metrics(self):
        """Setup all Prometheus metrics"""
        
        # === Performance Metrics ===
        
        # Request latency histogram with SLA targets
        self.request_latency = Histogram(
            'ml_request_duration_seconds',
            'Request latency for ML operations',
            ['operation_type', 'model_name', 'creator_id'],
            buckets=[0.1, 0.5, 1.0, 3.0, 5.0, 10.0, 30.0, 60.0],
            registry=self.registry
        )
        
        # Request rate counter
        self.requests_total = Counter(
            'ml_requests_total',
            'Total number of ML requests',
            ['operation_type', 'model_name', 'status', 'creator_id'],
            registry=self.registry
        )
        
        # Token usage counter for cost tracking
        self.tokens_processed = Counter(
            'ml_tokens_processed_total',
            'Total tokens processed by model',
            ['operation_type', 'model_name', 'creator_id'],
            registry=self.registry
        )
        
        # === Error Metrics ===
        
        # Error rate counter with categorization
        self.errors_total = Counter(
            'ml_errors_total',
            'Total number of ML operation errors',
            ['operation_type', 'model_name', 'error_type', 'creator_id'],
            registry=self.registry
        )
        
        # Model timeout rate
        self.timeouts_total = Counter(
            'ml_timeouts_total',
            'Total number of model timeouts',
            ['operation_type', 'model_name', 'creator_id'],
            registry=self.registry
        )
        
        # === Resource Metrics ===
        
        # Resource utilization gauges
        self.cpu_usage = Gauge(
            'ml_cpu_usage_percent',
            'CPU usage percentage for ML operations',
            ['service', 'model_name'],
            registry=self.registry
        )
        
        self.memory_usage = Gauge(
            'ml_memory_usage_bytes',
            'Memory usage in bytes for ML operations',
            ['service', 'model_name'],
            registry=self.registry
        )
        
        self.gpu_usage = Gauge(
            'ml_gpu_usage_percent',
            'GPU usage percentage for ML operations',
            ['service', 'model_name'],
            registry=self.registry
        )
        
        # Queue depth for load monitoring
        self.queue_depth = Gauge(
            'ml_queue_depth',
            'Current queue depth for ML operations',
            ['operation_type', 'service'],
            registry=self.registry
        )
        
        # === Business Metrics ===
        
        # Cost tracking
        self.cost_total = Counter(
            'ml_cost_total_usd',
            'Total cost in USD for ML operations',
            ['operation_type', 'model_name', 'creator_id'],
            registry=self.registry
        )
        
        # Model availability gauge
        self.model_availability = Gauge(
            'ml_model_availability',
            'Model availability (1=available, 0=unavailable)',
            ['model_name', 'service'],
            registry=self.registry
        )
        
        # === Privacy-Safe Input Metrics ===
        
        # Input length distribution (no content stored)
        self.input_length = Histogram(
            'ml_input_length_chars',
            'Distribution of input length in characters',
            ['operation_type', 'creator_id'],
            buckets=[10, 50, 100, 500, 1000, 5000, 10000, 50000],
            registry=self.registry
        )
        
        # Content type distribution (classification only)
        self.content_type = Counter(
            'ml_content_type_total',
            'Distribution of content types (question, command, etc)',
            ['content_type', 'operation_type', 'creator_id'],
            registry=self.registry
        )
        
        # === SLA Compliance Metrics ===
        
        # SLA violation counter
        self.sla_violations = Counter(
            'ml_sla_violations_total',
            'Total SLA violations by type',
            ['violation_type', 'severity', 'service'],
            registry=self.registry
        )
    
    def record_request(
        self,
        operation_type: OperationType,
        model_name: str,
        duration_seconds: float,
        creator_id: str,
        status: str = "success",
        tokens: Optional[int] = None,
        cost: Optional[float] = None,
        input_length: Optional[int] = None,
        content_type: Optional[str] = None
    ):
        """
        Record a completed ML request with all relevant metrics
        
        Args:
            operation_type: Type of ML operation
            model_name: Name of the model used
            duration_seconds: Request duration in seconds
            creator_id: Creator ID for multi-tenancy
            status: Request status (success, error, timeout)
            tokens: Number of tokens processed
            cost: Cost of the request in USD
            input_length: Length of input in characters (privacy-safe)
            content_type: Classified content type (privacy-safe)
        """
        try:
            # Record latency
            self.request_latency.labels(
                operation_type=operation_type.value,
                model_name=model_name,
                creator_id=creator_id
            ).observe(duration_seconds)
            
            # Record request count
            self.requests_total.labels(
                operation_type=operation_type.value,
                model_name=model_name,
                status=status,
                creator_id=creator_id
            ).inc()
            
            # Record tokens if provided
            if tokens:
                self.tokens_processed.labels(
                    operation_type=operation_type.value,
                    model_name=model_name,
                    creator_id=creator_id
                ).inc(tokens)
            
            # Record cost if provided
            if cost:
                self.cost_total.labels(
                    operation_type=operation_type.value,
                    model_name=model_name,
                    creator_id=creator_id
                ).inc(cost)
            
            # Record input length (privacy-safe)
            if input_length:
                self.input_length.labels(
                    operation_type=operation_type.value,
                    creator_id=creator_id
                ).observe(input_length)
            
            # Record content type (privacy-safe classification)
            if content_type:
                self.content_type.labels(
                    content_type=content_type,
                    operation_type=operation_type.value,
                    creator_id=creator_id
                ).inc()
            
            # Check for SLA violations
            self._check_sla_violations(operation_type, duration_seconds, status)
            
        except Exception as e:
            logger.error(f"Failed to record metrics: {e}")
    
    def record_error(
        self,
        operation_type: OperationType,
        model_name: str,
        error_type: ErrorType,
        creator_id: str,
        duration_seconds: Optional[float] = None
    ):
        """
        Record an ML operation error
        
        Args:
            operation_type: Type of ML operation
            model_name: Name of the model
            error_type: Type of error that occurred
            creator_id: Creator ID for multi-tenancy
            duration_seconds: Duration before error occurred
        """
        try:
            # Record general error
            self.errors_total.labels(
                operation_type=operation_type.value,
                model_name=model_name,
                error_type=error_type.value,
                creator_id=creator_id
            ).inc()
            
            # Record timeout specifically
            if error_type == ErrorType.TIMEOUT:
                self.timeouts_total.labels(
                    operation_type=operation_type.value,
                    model_name=model_name,
                    creator_id=creator_id
                ).inc()
            
            # Record as failed request
            if duration_seconds:
                self.record_request(
                    operation_type=operation_type,
                    model_name=model_name,
                    duration_seconds=duration_seconds,
                    creator_id=creator_id,
                    status="error"
                )
            
        except Exception as e:
            logger.error(f"Failed to record error metrics: {e}")
    
    def record_ml_operation_start(self, ml_metrics: 'MLMetrics'):
        """
        Record the start of an ML operation
        
        Args:
            ml_metrics: ML metrics data container
        """
        try:
            # Import time at the top would be better, but for now:
            import time
            # Just store the start time for now - actual recording happens on completion
            ml_metrics.start_time = time.time()
            logger.debug(f"ML operation started: {ml_metrics.operation_type} for model {ml_metrics.model_name}")
        except Exception as e:
            logger.error(f"Failed to record ML operation start: {e}")
    
    def record_ml_operation_success(
        self,
        ml_metrics: 'MLMetrics',
        duration_ms: float,
        sources_count: int = 0
    ):
        """
        Record successful completion of an ML operation
        
        Args:
            ml_metrics: ML metrics data container
            duration_ms: Duration in milliseconds
            sources_count: Number of sources/results
        """
        try:
            duration_seconds = duration_ms / 1000.0
            self.record_request(
                operation_type=ml_metrics.operation_type,
                model_name=ml_metrics.model_name,
                duration_seconds=duration_seconds,
                creator_id=ml_metrics.creator_id,
                status="success",
                tokens=ml_metrics.token_count,
                input_length=ml_metrics.input_length
            )
        except Exception as e:
            logger.error(f"Failed to record ML operation success: {e}")
    
    def record_resource_usage(
        self,
        service: str,
        model_name: str,
        cpu_percent: Optional[float] = None,
        memory_bytes: Optional[float] = None,
        gpu_percent: Optional[float] = None
    ):
        """
        Record resource usage metrics
        
        Args:
            service: Service name (ai-engine, ollama, chromadb)
            model_name: Model name
            cpu_percent: CPU usage percentage
            memory_bytes: Memory usage in bytes
            gpu_percent: GPU usage percentage
        """
        try:
            if cpu_percent is not None:
                self.cpu_usage.labels(
                    service=service,
                    model_name=model_name
                ).set(cpu_percent)
            
            if memory_bytes is not None:
                self.memory_usage.labels(
                    service=service,
                    model_name=model_name
                ).set(memory_bytes)
            
            if gpu_percent is not None:
                self.gpu_usage.labels(
                    service=service,
                    model_name=model_name
                ).set(gpu_percent)
                
        except Exception as e:
            logger.error(f"Failed to record resource metrics: {e}")
    
    def set_model_availability(self, model_name: str, service: str, available: bool):
        """
        Set model availability status
        
        Args:
            model_name: Name of the model
            service: Service hosting the model
            available: Whether model is available
        """
        try:
            self.model_availability.labels(
                model_name=model_name,
                service=service
            ).set(1 if available else 0)
            
        except Exception as e:
            logger.error(f"Failed to set model availability: {e}")
    
    def set_queue_depth(self, operation_type: OperationType, service: str, depth: int):
        """
        Set current queue depth for load monitoring
        
        Args:
            operation_type: Type of operation in queue
            service: Service name
            depth: Current queue depth
        """
        try:
            self.queue_depth.labels(
                operation_type=operation_type.value,
                service=service
            ).set(depth)
            
        except Exception as e:
            logger.error(f"Failed to set queue depth: {e}")
    
    def _check_sla_violations(
        self,
        operation_type: OperationType,
        duration_seconds: float,
        status: str
    ):
        """
        Check for SLA violations and record them
        
        Args:
            operation_type: Type of ML operation
            duration_seconds: Request duration
            status: Request status
        """
        try:
            # Define SLA targets based on operation type
            sla_targets = {
                OperationType.EMBEDDING: 1.0,  # 1 second
                OperationType.CHAT: 3.0,       # 3 seconds
                OperationType.SEARCH: 0.5,     # 0.5 seconds
                OperationType.DOCUMENT_PROCESSING: 10.0,  # 10 seconds
                OperationType.MODEL_INFERENCE: 5.0       # 5 seconds
            }
            
            target = sla_targets.get(operation_type, 5.0)
            
            # Check latency SLA
            if duration_seconds > target:
                self.sla_violations.labels(
                    violation_type="latency",
                    severity="p2" if duration_seconds > target * 2 else "p3",
                    service="ai-engine"
                ).inc()
            
            # Check error rate SLA
            if status == "error":
                self.sla_violations.labels(
                    violation_type="error_rate",
                    severity="p2",
                    service="ai-engine"
                ).inc()
                
        except Exception as e:
            logger.error(f"Failed to check SLA violations: {e}")
    
    def get_metrics(self) -> str:
        """
        Get all metrics in Prometheus format
        
        Returns:
            Metrics in Prometheus exposition format
        """
        return generate_latest(self.registry)
    
    def get_model_summary(self, model_name: str) -> ModelMetrics:
        """
        Get summary metrics for a specific model
        
        Args:
            model_name: Name of the model
            
        Returns:
            ModelMetrics object with aggregated data
        """
        # This would typically query a time-series database
        # For now, return a placeholder implementation
        return ModelMetrics(model_name=model_name)


class PerformanceMetrics:
    """Helper class for performance-specific metrics"""
    
    def __init__(self, collector: MetricsCollector):
        self.collector = collector
    
    def record_latency_percentiles(
        self,
        operation_type: OperationType,
        model_name: str,
        p50: float,
        p95: float,
        p99: float
    ):
        """Record latency percentiles for SLA monitoring"""
        # These would typically be calculated from histogram data
        # Implementation depends on your metrics backend
    
    def check_sla_compliance(self) -> Dict[str, bool]:
        """
        Check current SLA compliance status
        
        Returns:
            Dictionary of SLA compliance by metric
        """
        # Implementation would check current metrics against SLA targets
        return {
            "latency_p95": True,
            "error_rate": True,
            "availability": True
        }


class ErrorMetrics:
    """Helper class for error-specific metrics"""
    
    def __init__(self, collector: MetricsCollector):
        self.collector = collector
    
    def get_error_rate(
        self,
        operation_type: OperationType,
        time_window_minutes: int = 5
    ) -> float:
        """
        Calculate current error rate for an operation type
        
        Args:
            operation_type: Type of operation
            time_window_minutes: Time window for calculation
            
        Returns:
            Error rate as percentage
        """
        # Implementation would query metrics backend
        return 0.0
    
    def get_top_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top error types by frequency
        
        Args:
            limit: Number of top errors to return
            
        Returns:
            List of error information dictionaries
        """
        # Implementation would query metrics backend
        return []


# Global metrics collector instance
_metrics_collector = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


@dataclass
class MLMetrics:
    """ML operation metrics data container"""
    operation_type: OperationType
    model_name: str
    creator_id: str
    input_length: Optional[int] = None
    output_length: Optional[int] = None
    token_count: Optional[int] = None
    start_time: Optional[float] = None


class MLMetricsUtils:
    """Convenience class for ML-specific metrics recording"""
    
    @staticmethod
    def record_embedding_request(
        model_name: str,
        creator_id: str,
        duration_seconds: float,
        input_length: int,
        tokens_processed: int,
        status: str = "success"
    ):
        """Record an embedding generation request"""
        collector = get_metrics_collector()
        collector.record_request(
            operation_type=OperationType.EMBEDDING,
            model_name=model_name,
            duration_seconds=duration_seconds,
            creator_id=creator_id,
            status=status,
            tokens=tokens_processed,
            input_length=input_length
        )
    
    @staticmethod
    def record_chat_request(
        model_name: str,
        creator_id: str,
        duration_seconds: float,
        input_length: int,
        output_length: int,
        status: str = "success",
        content_type: str = "question"
    ):
        """Record a chat completion request"""
        collector = get_metrics_collector()
        collector.record_request(
            operation_type=OperationType.CHAT,
            model_name=model_name,
            duration_seconds=duration_seconds,
            creator_id=creator_id,
            status=status,
            tokens=input_length + output_length,
            input_length=input_length,
            content_type=content_type
        )
    
    @staticmethod
    def record_search_request(
        creator_id: str,
        duration_seconds: float,
        query_length: int,
        results_count: int,
        status: str = "success"
    ):
        """Record a vector search request"""
        collector = get_metrics_collector()
        collector.record_request(
            operation_type=OperationType.SEARCH,
            model_name="chromadb",
            duration_seconds=duration_seconds,
            creator_id=creator_id,
            status=status,
            input_length=query_length
        )