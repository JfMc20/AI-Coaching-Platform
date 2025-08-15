"""
Model Management and Versioning for AI Engine Service
Implements model versioning, rollback capabilities, and deployment strategies
"""

import logging
import asyncio
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from shared.ai.ollama_manager import get_ollama_manager, OllamaError
from shared.cache import get_cache_manager
from shared.exceptions.base import BaseServiceException
from shared.monitoring import get_metrics_collector, get_alert_manager

logger = logging.getLogger(__name__)


class DeploymentStrategy(str, Enum):
    """Model deployment strategies"""
    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    ROLLING = "rolling"
    IMMEDIATE = "immediate"


class ModelStatus(str, Enum):
    """Model status states"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    DEPLOYING = "deploying"
    ROLLING_BACK = "rolling_back"


@dataclass
class ModelVersion:
    """Model version information"""
    model_name: str
    version: str
    deployment_time: datetime
    status: ModelStatus
    performance_metrics: Dict[str, float]
    rollback_threshold: Dict[str, float]
    deployment_strategy: DeploymentStrategy


class ModelVersioningError(BaseServiceException):
    """Model versioning specific errors"""
    pass


class ModelManager:
    """
    Advanced model management with versioning and rollback capabilities
    """
    
    def __init__(self):
        self.cache_manager = get_cache_manager()
        self.metrics_collector = get_metrics_collector()
        self.alert_manager = get_alert_manager()
        self.rollback_thresholds = {
            "error_rate": 0.05,  # 5% error rate triggers rollback
            "latency_p95": 5000,  # 5s P95 latency triggers rollback
            "availability": 0.995  # 99.5% availability threshold
        }
        
    async def deploy_model_version(
        self,
        model_name: str,
        version: str,
        strategy: DeploymentStrategy = DeploymentStrategy.CANARY,
        rollback_thresholds: Optional[Dict[str, float]] = None
    ) -> bool:
        """
        Deploy a new model version with specified strategy
        
        Args:
            model_name: Name of the model to deploy
            version: Version identifier (semantic versioning)
            strategy: Deployment strategy to use
            rollback_thresholds: Custom rollback thresholds
            
        Returns:
            Success status of deployment
        """
        try:
            logger.info(f"Starting {strategy.value} deployment of {model_name}:{version}")
            
            # Validate version format (semantic versioning)
            if not self._validate_version_format(version):
                raise ModelVersioningError(f"Invalid version format: {version}")
            
            # Get current active version
            current_version = await self._get_active_version(model_name)
            
            # Create model version record
            model_version = ModelVersion(
                model_name=model_name,
                version=version,
                deployment_time=datetime.utcnow(),
                status=ModelStatus.DEPLOYING,
                performance_metrics={},
                rollback_threshold=rollback_thresholds or self.rollback_thresholds,
                deployment_strategy=strategy
            )
            
            # Store version info
            await self._store_model_version(model_version)
            
            # Execute deployment strategy
            if strategy == DeploymentStrategy.CANARY:
                success = await self._canary_deployment(model_version, current_version)
            elif strategy == DeploymentStrategy.BLUE_GREEN:
                success = await self._blue_green_deployment(model_version, current_version)
            elif strategy == DeploymentStrategy.ROLLING:
                success = await self._rolling_deployment(model_version, current_version)
            else:  # IMMEDIATE
                success = await self._immediate_deployment(model_version)
            
            if success:
                model_version.status = ModelStatus.HEALTHY
                await self._store_model_version(model_version)
                logger.info(f"Successfully deployed {model_name}:{version}")
            else:
                model_version.status = ModelStatus.UNHEALTHY
                await self._store_model_version(model_version)
                logger.error(f"Failed to deploy {model_name}:{version}")
            
            return success
            
        except Exception as e:
            logger.exception(f"Model deployment failed: {e}")
            raise ModelVersioningError(f"Deployment failed: {str(e)}")
    
    async def _canary_deployment(
        self, 
        new_version: ModelVersion, 
        current_version: Optional[str]
    ) -> bool:
        """
        Execute canary deployment: 5% → 25% → 100%
        """
        try:
            canary_stages = [5, 25, 100]
            
            for stage_percent in canary_stages:
                logger.info(f"Canary stage: {stage_percent}% traffic to {new_version.version}")
                
                # Configure traffic split
                await self._configure_traffic_split(
                    new_version.model_name,
                    new_version.version,
                    stage_percent
                )
                
                # Monitor for rollback conditions
                monitoring_duration = 300 if stage_percent < 100 else 600  # 5-10 minutes
                await asyncio.sleep(monitoring_duration)
                
                # Check performance metrics
                metrics = await self._collect_performance_metrics(
                    new_version.model_name,
                    new_version.version
                )
                
                # Evaluate rollback conditions
                should_rollback = await self._should_rollback(metrics, new_version.rollback_threshold)
                
                if should_rollback:
                    logger.warning(f"Rollback triggered at {stage_percent}% stage")
                    await self._rollback_to_previous_version(new_version.model_name, current_version)
                    return False
                
                # Update performance metrics
                new_version.performance_metrics.update(metrics)
                await self._store_model_version(new_version)
            
            # Mark as active version
            await self._set_active_version(new_version.model_name, new_version.version)
            return True
            
        except Exception as e:
            logger.exception(f"Canary deployment failed: {e}")
            await self._rollback_to_previous_version(new_version.model_name, current_version)
            return False
    
    async def _blue_green_deployment(
        self, 
        new_version: ModelVersion, 
        current_version: Optional[str]
    ) -> bool:
        """
        Execute blue-green deployment with instant switch
        """
        try:
            # Deploy to green environment
            logger.info(f"Deploying {new_version.version} to green environment")
            
            # Validate green environment
            await self._validate_model_health(new_version.model_name, new_version.version)
            
            # Run smoke tests
            smoke_test_passed = await self._run_smoke_tests(new_version.model_name, new_version.version)
            
            if not smoke_test_passed:
                logger.error("Smoke tests failed for green environment")
                return False
            
            # Switch traffic to green (new version)
            await self._configure_traffic_split(
                new_version.model_name,
                new_version.version,
                100
            )
            
            # Monitor for immediate issues
            await asyncio.sleep(60)  # 1 minute monitoring
            
            metrics = await self._collect_performance_metrics(
                new_version.model_name,
                new_version.version
            )
            
            should_rollback = await self._should_rollback(metrics, new_version.rollback_threshold)
            
            if should_rollback:
                logger.warning("Immediate rollback triggered in blue-green deployment")
                await self._rollback_to_previous_version(new_version.model_name, current_version)
                return False
            
            # Mark as active version
            await self._set_active_version(new_version.model_name, new_version.version)
            return True
            
        except Exception as e:
            logger.exception(f"Blue-green deployment failed: {e}")
            await self._rollback_to_previous_version(new_version.model_name, current_version)
            return False
    
    async def _rolling_deployment(
        self, 
        new_version: ModelVersion, 
        current_version: Optional[str]
    ) -> bool:
        """
        Execute rolling deployment with gradual instance replacement
        """
        try:
            # For single-instance development, this is similar to blue-green
            # In production, this would replace instances one by one
            logger.info(f"Starting rolling deployment of {new_version.version}")
            
            # Validate new version
            await self._validate_model_health(new_version.model_name, new_version.version)
            
            # Gradual rollout (simulated for single instance)
            rollout_stages = [25, 50, 75, 100]
            
            for stage in rollout_stages:
                logger.info(f"Rolling deployment: {stage}% instances updated")
                
                await self._configure_traffic_split(
                    new_version.model_name,
                    new_version.version,
                    stage
                )
                
                await asyncio.sleep(120)  # 2 minutes between stages
                
                metrics = await self._collect_performance_metrics(
                    new_version.model_name,
                    new_version.version
                )
                
                should_rollback = await self._should_rollback(metrics, new_version.rollback_threshold)
                
                if should_rollback:
                    logger.warning(f"Rollback triggered at {stage}% rolling stage")
                    await self._rollback_to_previous_version(new_version.model_name, current_version)
                    return False
            
            await self._set_active_version(new_version.model_name, new_version.version)
            return True
            
        except Exception as e:
            logger.exception(f"Rolling deployment failed: {e}")
            await self._rollback_to_previous_version(new_version.model_name, current_version)
            return False
    
    async def _immediate_deployment(self, new_version: ModelVersion) -> bool:
        """
        Execute immediate deployment without gradual rollout
        """
        try:
            logger.info(f"Immediate deployment of {new_version.version}")
            
            # Validate model
            await self._validate_model_health(new_version.model_name, new_version.version)
            
            # Switch traffic immediately
            await self._configure_traffic_split(
                new_version.model_name,
                new_version.version,
                100
            )
            
            # Mark as active
            await self._set_active_version(new_version.model_name, new_version.version)
            return True
            
        except Exception as e:
            logger.exception(f"Immediate deployment failed: {e}")
            return False
    
    async def _should_rollback(
        self, 
        metrics: Dict[str, float], 
        thresholds: Dict[str, float]
    ) -> bool:
        """
        Evaluate if rollback should be triggered based on metrics
        """
        try:
            for metric_name, threshold in thresholds.items():
                current_value = metrics.get(metric_name, 0)
                
                if metric_name == "error_rate" and current_value > threshold:
                    logger.warning(f"Error rate {current_value} exceeds threshold {threshold}")
                    return True
                elif metric_name == "latency_p95" and current_value > threshold:
                    logger.warning(f"P95 latency {current_value}ms exceeds threshold {threshold}ms")
                    return True
                elif metric_name == "availability" and current_value < threshold:
                    logger.warning(f"Availability {current_value} below threshold {threshold}")
                    return True
            
            return False
            
        except Exception as e:
            logger.exception(f"Error evaluating rollback conditions: {e}")
            return True  # Fail safe - trigger rollback on evaluation error
    
    async def _rollback_to_previous_version(
        self, 
        model_name: str, 
        previous_version: Optional[str]
    ) -> bool:
        """
        Rollback to previous model version
        """
        try:
            if not previous_version:
                logger.error(f"No previous version available for rollback of {model_name}")
                return False
            
            logger.info(f"Rolling back {model_name} to version {previous_version}")
            
            # Switch traffic back to previous version
            await self._configure_traffic_split(model_name, previous_version, 100)
            
            # Mark previous version as active
            await self._set_active_version(model_name, previous_version)
            
            # Send alert about rollback
            await self.alert_manager.create_alert(
                rule_name="model_rollback",
                title=f"Model Rollback: {model_name}",
                description=f"Automatically rolled back {model_name} to {previous_version}",
                severity="p2",
                metadata={"model_name": model_name, "rolled_back_to": previous_version}
            )
            
            return True
            
        except Exception as e:
            logger.exception(f"Rollback failed: {e}")
            return False
    
    async def _validate_version_format(self, version: str) -> bool:
        """
        Validate semantic versioning format (major.minor.patch)
        """
        import re
        pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9\-]+))?$'
        return bool(re.match(pattern, version))
    
    async def _get_active_version(self, model_name: str) -> Optional[str]:
        """Get currently active version of a model"""
        try:
            cache_key = f"model_active_version:{model_name}"
            return await self.cache_manager.get(cache_key)
        except Exception:
            return None
    
    async def _set_active_version(self, model_name: str, version: str) -> None:
        """Set active version of a model"""
        cache_key = f"model_active_version:{model_name}"
        await self.cache_manager.set(cache_key, version, ttl=86400)  # 24 hours
    
    async def _store_model_version(self, model_version: ModelVersion) -> None:
        """Store model version information"""
        cache_key = f"model_version:{model_version.model_name}:{model_version.version}"
        version_data = {
            "model_name": model_version.model_name,
            "version": model_version.version,
            "deployment_time": model_version.deployment_time.isoformat(),
            "status": model_version.status.value,
            "performance_metrics": model_version.performance_metrics,
            "rollback_threshold": model_version.rollback_threshold,
            "deployment_strategy": model_version.deployment_strategy.value
        }
        await self.cache_manager.set(cache_key, json.dumps(version_data), ttl=86400 * 7)  # 7 days
    
    async def _configure_traffic_split(
        self, 
        model_name: str, 
        version: str, 
        percentage: int
    ) -> None:
        """
        Configure traffic split for model versions
        In production, this would configure load balancer or service mesh
        """
        # For development, we'll just log the configuration
        # In production, this would integrate with Istio, Envoy, or similar
        logger.info(f"Configuring {percentage}% traffic to {model_name}:{version}")
        
        # Store traffic configuration
        traffic_config = {
            "model_name": model_name,
            "version": version,
            "percentage": percentage,
            "configured_at": datetime.utcnow().isoformat()
        }
        
        cache_key = f"traffic_config:{model_name}"
        await self.cache_manager.set(cache_key, json.dumps(traffic_config), ttl=3600)
    
    async def _collect_performance_metrics(
        self, 
        model_name: str, 
        version: str
    ) -> Dict[str, float]:
        """
        Collect performance metrics for a model version
        """
        try:
            # In production, this would query Prometheus or similar
            # For now, we'll simulate metrics collection
            
            # Get metrics from metrics collector
            metrics = {
                "error_rate": 0.02,  # 2% error rate
                "latency_p95": 2500,  # 2.5s P95 latency
                "availability": 0.998,  # 99.8% availability
                "throughput": 50.0,  # 50 requests/second
                "cpu_usage": 0.65,  # 65% CPU usage
                "memory_usage": 0.70  # 70% memory usage
            }
            
            # Add some realistic variation
            import random
            for key in metrics:
                variation = random.uniform(0.9, 1.1)  # ±10% variation
                metrics[key] *= variation
            
            return metrics
            
        except Exception as e:
            logger.exception(f"Failed to collect metrics: {e}")
            return {}
    
    async def _validate_model_health(self, model_name: str, version: str) -> bool:
        """
        Validate model health before deployment
        """
        try:
            # Check if model is available in Ollama
            ollama_manager = get_ollama_manager()
            health = await ollama_manager.health_check()
            
            if model_name == "embedding" and not health["embedding_model"]["available"]:
                return False
            elif model_name == "chat" and not health["chat_model"]["available"]:
                return False
            
            return True
            
        except Exception as e:
            logger.exception(f"Model health validation failed: {e}")
            return False
    
    async def _run_smoke_tests(self, model_name: str, version: str) -> bool:
        """
        Run smoke tests for model deployment
        """
        try:
            ollama_manager = get_ollama_manager()
            
            if model_name == "embedding":
                # Test embedding generation
                test_embedding = await ollama_manager.generate_embedding("test query")
                return len(test_embedding) > 0
            elif model_name == "chat":
                # Test chat completion
                test_response = await ollama_manager.generate_chat_completion("Hello, test")
                return len(test_response) > 0
            
            return True
            
        except Exception as e:
            logger.exception(f"Smoke tests failed: {e}")
            return False
    
    async def get_model_versions(self, model_name: str) -> List[Dict[str, Any]]:
        """
        Get all versions of a model
        """
        try:
            # In production, this would query a model registry
            # For now, we'll return mock data
            versions = [
                {
                    "version": "1.0.0",
                    "status": "healthy",
                    "deployment_time": "2024-01-01T00:00:00Z",
                    "is_active": False
                },
                {
                    "version": "1.1.0", 
                    "status": "healthy",
                    "deployment_time": "2024-01-15T00:00:00Z",
                    "is_active": True
                }
            ]
            
            return versions
            
        except Exception as e:
            logger.exception(f"Failed to get model versions: {e}")
            return []


# Global model manager instance
_model_manager = None

def get_model_manager() -> ModelManager:
    """Get global model manager instance"""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager