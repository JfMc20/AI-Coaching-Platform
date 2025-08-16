"""
Automated Health Checks and Model Monitoring

Implements synthetic request monitoring, model availability checks,
and automated health validation for ML services.
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

import httpx
from .metrics import get_metrics_collector, OperationType

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class CheckType(str, Enum):
    """Types of health checks"""
    AVAILABILITY = "availability"
    LATENCY = "latency"
    ACCURACY = "accuracy"
    RESOURCE = "resource"
    SYNTHETIC = "synthetic"


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    check_name: str
    check_type: CheckType
    status: HealthStatus
    timestamp: datetime
    duration_ms: float
    details: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    recovery_suggestions: List[str] = field(default_factory=list)


@dataclass
class SyntheticRequest:
    """Synthetic request for model testing"""
    operation_type: OperationType
    input_text: str
    expected_output_pattern: Optional[str] = None
    max_latency_ms: float = 5000
    model_name: Optional[str] = None
    creator_id: str = "health_check"


class ModelHealthChecker:
    """
    Comprehensive health checker for ML models and services
    """
    
    def __init__(self):
        self.metrics_collector = get_metrics_collector()
        self._setup_synthetic_requests()
        self._health_history = {}
    
    def _setup_synthetic_requests(self):
        """Setup synthetic requests for different operations"""
        self.synthetic_requests = [
            # Embedding generation test
            SyntheticRequest(
                operation_type=OperationType.EMBEDDING,
                input_text="This is a test document for embedding generation",
                max_latency_ms=3000
            ),
            
            # Chat completion test
            SyntheticRequest(
                operation_type=OperationType.CHAT,
                input_text="Hello, how are you today?",
                expected_output_pattern=r".+",  # Any non-empty response
                max_latency_ms=5000
            ),
            
            # Search test
            SyntheticRequest(
                operation_type=OperationType.SEARCH,
                input_text="productivity tips",
                max_latency_ms=1000
            ),
            
            # Document processing test
            SyntheticRequest(
                operation_type=OperationType.DOCUMENT_PROCESSING,
                input_text="# Test Document\n\nThis is a test document for processing validation.",
                max_latency_ms=10000
            )
        ]
    
    async def check_service_availability(self, service_url: str, service_name: str) -> HealthCheckResult:
        """
        Check if a service is available and responding
        
        Args:
            service_url: URL of the service to check
            service_name: Name of the service
            
        Returns:
            HealthCheckResult with availability status
        """
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{service_url}/health")
                duration_ms = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    try:
                        health_data = response.json()
                        return HealthCheckResult(
                            check_name=f"{service_name}_availability",
                            check_type=CheckType.AVAILABILITY,
                            status=HealthStatus.HEALTHY,
                            timestamp=datetime.utcnow(),
                            duration_ms=duration_ms,
                            details={
                                "status_code": response.status_code,
                                "response_data": health_data,
                                "service_url": service_url
                            }
                        )
                    except Exception:
                        # Service responded but not with valid JSON
                        return HealthCheckResult(
                            check_name=f"{service_name}_availability",
                            check_type=CheckType.AVAILABILITY,
                            status=HealthStatus.DEGRADED,
                            timestamp=datetime.utcnow(),
                            duration_ms=duration_ms,
                            details={"status_code": response.status_code},
                            error_message="Service responded but not with valid health data"
                        )
                else:
                    return HealthCheckResult(
                        check_name=f"{service_name}_availability",
                        check_type=CheckType.AVAILABILITY,
                        status=HealthStatus.UNHEALTHY,
                        timestamp=datetime.utcnow(),
                        duration_ms=duration_ms,
                        details={"status_code": response.status_code},
                        error_message=f"Service returned status code {response.status_code}"
                    )
                    
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                check_name=f"{service_name}_availability",
                check_type=CheckType.AVAILABILITY,
                status=HealthStatus.UNHEALTHY,
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms,
                error_message=str(e),
                recovery_suggestions=[
                    f"Check if {service_name} service is running",
                    f"Verify network connectivity to {service_url}",
                    "Check service logs for errors"
                ]
            )
    
    async def check_model_latency(self, model_name: str, operation_type: OperationType) -> HealthCheckResult:
        """
        Check model response latency
        
        Args:
            model_name: Name of the model to check
            operation_type: Type of operation to test
            
        Returns:
            HealthCheckResult with latency status
        """
        # Find appropriate synthetic request
        synthetic_request = next(
            (req for req in self.synthetic_requests if req.operation_type == operation_type),
            None
        )
        
        if not synthetic_request:
            return HealthCheckResult(
                check_name=f"{model_name}_latency",
                check_type=CheckType.LATENCY,
                status=HealthStatus.UNKNOWN,
                timestamp=datetime.utcnow(),
                duration_ms=0,
                error_message=f"No synthetic request defined for {operation_type}"
            )
        
        start_time = time.time()
        
        try:
            # Execute synthetic request (this would call actual ML service)
            await self._execute_synthetic_request(synthetic_request, model_name)
            duration_ms = (time.time() - start_time) * 1000
            
            # Check if latency is within acceptable range
            if duration_ms <= synthetic_request.max_latency_ms:
                status = HealthStatus.HEALTHY
            elif duration_ms <= synthetic_request.max_latency_ms * 1.5:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY
            
            return HealthCheckResult(
                check_name=f"{model_name}_latency",
                check_type=CheckType.LATENCY,
                status=status,
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms,
                details={
                    "operation_type": operation_type.value,
                    "max_allowed_ms": synthetic_request.max_latency_ms,
                    "actual_ms": duration_ms,
                    "performance_ratio": duration_ms / synthetic_request.max_latency_ms
                }
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                check_name=f"{model_name}_latency",
                check_type=CheckType.LATENCY,
                status=HealthStatus.UNHEALTHY,
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms,
                error_message=str(e),
                recovery_suggestions=[
                    f"Check {model_name} model availability",
                    "Review model resource allocation",
                    "Check for model loading issues"
                ]
            )
    
    async def _execute_synthetic_request(self, request: SyntheticRequest, model_name: str) -> Any:
        """
        Execute a synthetic request against ML service
        
        Args:
            request: Synthetic request to execute
            model_name: Name of model to use
            
        Returns:
            Response from ML service
        """
        # This would make actual calls to your ML services
        # Implementation depends on your service APIs
        
        if request.operation_type == OperationType.EMBEDDING:
            return await self._test_embedding_generation(request.input_text, model_name)
        elif request.operation_type == OperationType.CHAT:
            return await self._test_chat_completion(request.input_text, model_name)
        elif request.operation_type == OperationType.SEARCH:
            return await self._test_vector_search(request.input_text)
        elif request.operation_type == OperationType.DOCUMENT_PROCESSING:
            return await self._test_document_processing(request.input_text)
        else:
            raise ValueError(f"Unsupported operation type: {request.operation_type}")
    
    async def _test_embedding_generation(self, text: str, model_name: str) -> List[float]:
        """Test embedding generation"""
        # Mock implementation - replace with actual service call
        await asyncio.sleep(0.1)  # Simulate processing time
        return [0.1] * 384  # Mock embedding vector
    
    async def _test_chat_completion(self, text: str, model_name: str) -> str:
        """Test chat completion"""
        # Mock implementation - replace with actual service call
        await asyncio.sleep(0.5)  # Simulate processing time
        return "This is a test response from the health check system."
    
    async def _test_vector_search(self, query: str) -> List[Dict[str, Any]]:
        """Test vector search"""
        # Mock implementation - replace with actual service call
        await asyncio.sleep(0.1)  # Simulate processing time
        return [{"content": "test result", "score": 0.9}]
    
    async def _test_document_processing(self, content: str) -> Dict[str, Any]:
        """Test document processing"""
        # Mock implementation - replace with actual service call
        await asyncio.sleep(1.0)  # Simulate processing time
        return {"chunks": 1, "status": "processed"}
    
    async def check_resource_usage(self, service_name: str) -> HealthCheckResult:
        """
        Check resource usage for a service
        
        Args:
            service_name: Name of service to check
            
        Returns:
            HealthCheckResult with resource status
        """
        start_time = time.time()
        
        try:
            # This would typically query system metrics
            # Mock implementation
            cpu_percent = 45.0  # Mock CPU usage
            memory_percent = 60.0  # Mock memory usage
            gpu_percent = 30.0  # Mock GPU usage
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Determine status based on resource usage
            if cpu_percent > 90 or memory_percent > 90 or gpu_percent > 90:
                status = HealthStatus.UNHEALTHY
            elif cpu_percent > 75 or memory_percent > 75 or gpu_percent > 75:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.HEALTHY
            
            return HealthCheckResult(
                check_name=f"{service_name}_resources",
                check_type=CheckType.RESOURCE,
                status=status,
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "gpu_percent": gpu_percent,
                    "service": service_name
                }
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                check_name=f"{service_name}_resources",
                check_type=CheckType.RESOURCE,
                status=HealthStatus.UNKNOWN,
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms,
                error_message=str(e)
            )
    
    async def run_comprehensive_health_check(self) -> Dict[str, HealthCheckResult]:
        """
        Run comprehensive health check on all ML services
        
        Returns:
            Dictionary of health check results
        """
        results = {}
        
        # Service availability checks
        services = [
            ("http://localhost:8003", "ai-engine"),
            ("http://localhost:11434", "ollama"),
            ("http://localhost:8000", "chromadb")
        ]
        
        for service_url, service_name in services:
            result = await self.check_service_availability(service_url, service_name)
            results[f"{service_name}_availability"] = result
        
        # Model latency checks
        models = [
            ("llama2:7b-chat", OperationType.CHAT),
            ("nomic-embed-text", OperationType.EMBEDDING)
        ]
        
        for model_name, operation_type in models:
            result = await self.check_model_latency(model_name, operation_type)
            results[f"{model_name}_latency"] = result
        
        # Resource usage checks
        for _, service_name in services:
            result = await self.check_resource_usage(service_name)
            results[f"{service_name}_resources"] = result
        
        # Update health history
        self._update_health_history(results)
        
        return results
    
    def _update_health_history(self, results: Dict[str, HealthCheckResult]):
        """Update health check history"""
        timestamp = datetime.utcnow()
        
        for check_name, result in results.items():
            if check_name not in self._health_history:
                self._health_history[check_name] = []
            
            self._health_history[check_name].append({
                'timestamp': timestamp,
                'status': result.status.value,
                'duration_ms': result.duration_ms
            })
            
            # Keep only last 100 results per check
            if len(self._health_history[check_name]) > 100:
                self._health_history[check_name] = self._health_history[check_name][-100:]
    
    def get_health_summary(self) -> Dict[str, Any]:
        """
        Get overall health summary
        
        Returns:
            Health summary with aggregated status
        """
        if not self._health_history:
            return {"overall_status": "unknown", "checks": 0}
        
        recent_checks = {}
        current_time = datetime.utcnow()
        
        # Get most recent status for each check
        for check_name, history in self._health_history.items():
            if history:
                latest = history[-1]
                # Only consider checks from last 5 minutes
                if current_time - latest['timestamp'] < timedelta(minutes=5):
                    recent_checks[check_name] = latest['status']
        
        if not recent_checks:
            return {"overall_status": "unknown", "checks": 0}
        
        # Determine overall status
        statuses = list(recent_checks.values())
        
        if any(status == "unhealthy" for status in statuses):
            overall_status = "unhealthy"
        elif any(status == "degraded" for status in statuses):
            overall_status = "degraded"
        elif all(status == "healthy" for status in statuses):
            overall_status = "healthy"
        else:
            overall_status = "unknown"
        
        return {
            "overall_status": overall_status,
            "checks": len(recent_checks),
            "healthy": sum(1 for s in statuses if s == "healthy"),
            "degraded": sum(1 for s in statuses if s == "degraded"),
            "unhealthy": sum(1 for s in statuses if s == "unhealthy"),
            "last_check": max(
                latest['timestamp'] for latest in 
                [history[-1] for history in self._health_history.values() if history]
            ).isoformat() if self._health_history else None
        }


class SyntheticRequestRunner:
    """
    Automated runner for synthetic requests
    """
    
    def __init__(self, health_checker: ModelHealthChecker):
        self.health_checker = health_checker
        self.running = False
        self._task = None
    
    async def start_monitoring(self, interval_minutes: int = 5):
        """
        Start continuous monitoring with synthetic requests
        
        Args:
            interval_minutes: Interval between monitoring runs
        """
        if self.running:
            logger.warning("Synthetic monitoring already running")
            return
        
        self.running = True
        self._task = asyncio.create_task(self._monitoring_loop(interval_minutes))
        logger.info(f"Started synthetic monitoring with {interval_minutes}min interval")
    
    async def stop_monitoring(self):
        """Stop continuous monitoring"""
        if not self.running:
            return
        
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped synthetic monitoring")
    
    async def _monitoring_loop(self, interval_minutes: int):
        """Main monitoring loop"""
        while self.running:
            try:
                logger.info("Running synthetic health checks...")
                results = await self.health_checker.run_comprehensive_health_check()
                
                # Log results
                healthy_count = sum(1 for r in results.values() if r.status == HealthStatus.HEALTHY)
                total_count = len(results)
                
                logger.info(f"Health check completed: {healthy_count}/{total_count} checks healthy")
                
                # Sleep until next check
                await asyncio.sleep(interval_minutes * 60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying


# Global health checker instance
_health_checker = None


def get_health_checker() -> ModelHealthChecker:
    """Get the global health checker instance"""
    global _health_checker
    if _health_checker is None:
        _health_checker = ModelHealthChecker()
    return _health_checker