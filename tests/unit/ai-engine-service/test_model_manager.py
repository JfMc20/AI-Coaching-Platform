"""
Unit tests for Model Manager - Versioning and Rollback System
Tests model deployment strategies, rollback capabilities, and version management
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta

# Test data
SAMPLE_MODEL_VERSIONS = [
    {
        "model_name": "llama2:7b-chat",
        "version": "1.0.0",
        "status": "healthy",
        "deployment_time": datetime.utcnow() - timedelta(days=30),
        "performance_metrics": {
            "error_rate": 0.02,
            "latency_p95": 2500,
            "availability": 0.998
        }
    },
    {
        "model_name": "llama2:7b-chat", 
        "version": "1.1.0",
        "status": "healthy",
        "deployment_time": datetime.utcnow() - timedelta(days=7),
        "performance_metrics": {
            "error_rate": 0.015,
            "latency_p95": 2200,
            "availability": 0.999
        }
    }
]


class TestModelManager:
    """Test model management functionality"""
    
    @pytest.fixture
    async def mock_dependencies(self):
        """Setup mocked dependencies for model manager tests"""
        with patch('services.ai_engine_service.app.model_manager.get_cache_manager') as mock_cache, \
             patch('services.ai_engine_service.app.model_manager.get_metrics_collector') as mock_metrics, \
             patch('services.ai_engine_service.app.model_manager.get_alert_manager') as mock_alerts, \
             patch('services.ai_engine_service.app.model_manager.get_ollama_manager') as mock_ollama:
            
            # Mock cache manager
            cache_manager = AsyncMock()
            cache_manager.get.return_value = None
            cache_manager.set.return_value = True
            mock_cache.return_value = cache_manager
            
            # Mock metrics collector
            metrics_collector = Mock()
            mock_metrics.return_value = metrics_collector
            
            # Mock alert manager
            alert_manager = AsyncMock()
            alert_manager.create_alert.return_value = True
            mock_alerts.return_value = alert_manager
            
            # Mock Ollama manager
            ollama_manager = AsyncMock()
            ollama_manager.health_check.return_value = {
                "status": "healthy",
                "embedding_model": {"available": True},
                "chat_model": {"available": True}
            }
            ollama_manager.generate_embedding.return_value = [0.1] * 384
            ollama_manager.generate_chat_completion.return_value = "Test response"
            mock_ollama.return_value = ollama_manager
            
            yield {
                "cache": cache_manager,
                "metrics": metrics_collector,
                "alerts": alert_manager,
                "ollama": ollama_manager
            }
    
    async def test_model_manager_initialization(self, mock_dependencies):
        """Test model manager can be initialized"""
        try:
            from services.ai_engine_service.app.model_manager import ModelManager
            
            manager = ModelManager()
            assert manager is not None
            assert manager.rollback_thresholds is not None
            assert "error_rate" in manager.rollback_thresholds
            assert "latency_p95" in manager.rollback_thresholds
            assert "availability" in manager.rollback_thresholds
            
        except ImportError:
            pytest.skip("ModelManager not available")
    
    async def test_version_format_validation(self, mock_dependencies):
        """Test semantic version format validation"""
        try:
            from services.ai_engine_service.app.model_manager import ModelManager
            
            manager = ModelManager()
            
            # Test valid versions
            valid_versions = ["1.0.0", "2.1.3", "10.20.30", "1.0.0-beta", "2.1.0-alpha.1"]
            for version in valid_versions:
                is_valid = await manager._validate_version_format(version)
                assert is_valid, f"Version {version} should be valid"
            
            # Test invalid versions
            invalid_versions = ["1.0", "v1.0.0", "1.0.0.0", "invalid", ""]
            for version in invalid_versions:
                is_valid = await manager._validate_version_format(version)
                assert not is_valid, f"Version {version} should be invalid"
            
        except ImportError:
            pytest.skip("ModelManager not available")
    
    async def test_canary_deployment_success(self, mock_dependencies):
        """Test successful canary deployment"""
        try:
            from services.ai_engine_service.app.model_manager import ModelManager, DeploymentStrategy
            
            manager = ModelManager()
            
            # Mock successful metrics at each stage
            mock_dependencies["cache"].get.side_effect = [
                "1.0.0",  # Current version
                None,     # No cached metrics
                None,     # No cached metrics
                None      # No cached metrics
            ]
            
            # Mock performance metrics collection to return good metrics
            with patch.object(manager, '_collect_performance_metrics') as mock_collect:
                mock_collect.return_value = {
                    "error_rate": 0.01,      # Below 5% threshold
                    "latency_p95": 2000,     # Below 5000ms threshold
                    "availability": 0.999    # Above 99.5% threshold
                }
                
                with patch.object(manager, '_configure_traffic_split') as mock_traffic, \
                     patch.object(manager, '_set_active_version') as mock_set_active:
                    
                    # Test canary deployment
                    success = await manager.deploy_model_version(
                        model_name="llama2:7b-chat",
                        version="1.2.0",
                        strategy=DeploymentStrategy.CANARY
                    )
                    
                    assert success, "Canary deployment should succeed with good metrics"
                    
                    # Verify traffic split was called for each canary stage
                    assert mock_traffic.call_count >= 3  # 5%, 25%, 100%
                    
                    # Verify active version was set
                    mock_set_active.assert_called_once_with("llama2:7b-chat", "1.2.0")
            
        except ImportError:
            pytest.skip("ModelManager not available")
    
    async def test_canary_deployment_rollback(self, mock_dependencies):
        """Test canary deployment with automatic rollback"""
        try:
            from services.ai_engine_service.app.model_manager import ModelManager, DeploymentStrategy
            
            manager = ModelManager()
            
            # Mock current version
            mock_dependencies["cache"].get.side_effect = [
                "1.0.0",  # Current version
                None,     # No cached metrics
            ]
            
            # Mock performance metrics to trigger rollback
            with patch.object(manager, '_collect_performance_metrics') as mock_collect:
                mock_collect.return_value = {
                    "error_rate": 0.08,      # Above 5% threshold - should trigger rollback
                    "latency_p95": 2000,
                    "availability": 0.999
                }
                
                with patch.object(manager, '_configure_traffic_split') as mock_traffic, \
                     patch.object(manager, '_rollback_to_previous_version') as mock_rollback:
                    
                    mock_rollback.return_value = True
                    
                    # Test canary deployment with rollback
                    success = await manager.deploy_model_version(
                        model_name="llama2:7b-chat",
                        version="1.2.0",
                        strategy=DeploymentStrategy.CANARY
                    )
                    
                    assert not success, "Canary deployment should fail and rollback"
                # Verify rollback was triggered
                    mock_rollback.assert_called_once_with("llama2:7b-chat", "1.0.0")
            
        except ImportError:
            pytest.skip("ModelManager not available")
    
    async def test_blue_green_deployment(self, mock_dependencies):
        """Test blue-green deployment strategy"""
        try:
            from services.ai_engine_service.app.model_manager import ModelManager, DeploymentStrategy
            
            manager = ModelManager()
            
            with patch.object(manager, '_validate_model_health') as mock_health, \
                 patch.object(manager, '_run_smoke_tests') as mock_smoke, \
                 patch.object(manager, '_collect_performance_metrics') as mock_collect, \
                 patch.object(manager, '_configure_traffic_split') as mock_traffic, \
                 patch.object(manager, '_set_active_version') as mock_set_active:
                
                # Mock successful validation and tests
                mock_health.return_value = True
                mock_smoke.return_value = True
                mock_collect.return_value = {
                    "error_rate": 0.01,
                    "latency_p95": 2000,
                    "availability": 0.999
                }
                
                # Test blue-green deployment
                success = await manager.deploy_model_version(
                    model_name="llama2:7b-chat",
                    version="1.2.0",
                    strategy=DeploymentStrategy.BLUE_GREEN
                )
                
                assert success, "Blue-green deployment should succeed"
                
                # Verify validation steps
                mock_health.assert_called_once()
                mock_smoke.assert_called_once()
                
                # Verify immediate traffic switch
                mock_traffic.assert_called_with("llama2:7b-chat", "1.2.0", 100)
                mock_set_active.assert_called_once()
            
        except ImportError:
            pytest.skip("ModelManager not available")
    
    async def test_rollback_threshold_evaluation(self, mock_dependencies):
        """Test rollback threshold evaluation logic"""
        try:
            from services.ai_engine_service.app.model_manager import ModelManager
            
            manager = ModelManager()
            
            # Test metrics within thresholds
            good_metrics = {
                "error_rate": 0.02,      # Below 5%
                "latency_p95": 3000,     # Below 5000ms
                "availability": 0.998    # Above 99.5%
            }
            
            should_rollback = await manager._should_rollback(good_metrics, manager.rollback_thresholds)
            assert not should_rollback, "Should not rollback with good metrics"
            
            # Test metrics exceeding error rate threshold
            bad_error_metrics = {
                "error_rate": 0.08,      # Above 5%
                "latency_p95": 3000,
                "availability": 0.998
            }
            
            should_rollback = await manager._should_rollback(bad_error_metrics, manager.rollback_thresholds)
            assert should_rollback, "Should rollback with high error rate"
            
            # Test metrics exceeding latency threshold
            bad_latency_metrics = {
                "error_rate": 0.02,
                "latency_p95": 6000,     # Above 5000ms
                "availability": 0.998
            }
            
            should_rollback = await manager._should_rollback(bad_latency_metrics, manager.rollback_thresholds)
            assert should_rollback, "Should rollback with high latency"
            
            # Test metrics below availability threshold
            bad_availability_metrics = {
                "error_rate": 0.02,
                "latency_p95": 3000,
                "availability": 0.990    # Below 99.5%
            }
            
            should_rollback = await manager._should_rollback(bad_availability_metrics, manager.rollback_thresholds)
            assert should_rollback, "Should rollback with low availability"
            
        except ImportError:
            pytest.skip("ModelManager not available")
    
    async def test_smoke_tests(self, mock_dependencies):
        """Test model smoke tests"""
        try:
            from services.ai_engine_service.app.model_manager import ModelManager
            
            manager = ModelManager()
            
            # Test embedding model smoke test
            smoke_passed = await manager._run_smoke_tests("embedding", "1.0.0")
            assert smoke_passed, "Embedding model smoke test should pass"
            
            # Verify embedding generation was called
            mock_dependencies["ollama"].generate_embedding.assert_called_once()
            
            # Test chat model smoke test
            smoke_passed = await manager._run_smoke_tests("chat", "1.0.0")
            assert smoke_passed, "Chat model smoke test should pass"
            
            # Verify chat completion was called
            mock_dependencies["ollama"].generate_chat_completion.assert_called_once()
            
        except ImportError:
            pytest.skip("ModelManager not available")
    
    async def test_model_health_validation(self, mock_dependencies):
        """Test model health validation"""
        try:
            from services.ai_engine_service.app.model_manager import ModelManager
            
            manager = ModelManager()
            
            # Test healthy embedding model
            is_healthy = await manager._validate_model_health("embedding", "1.0.0")
            assert is_healthy, "Healthy embedding model should pass validation"
            
            # Test healthy chat model
            is_healthy = await manager._validate_model_health("chat", "1.0.0")
            assert is_healthy, "Healthy chat model should pass validation"
            
            # Test unhealthy model
            mock_dependencies["ollama"].health_check.return_value = {
                "embedding_model": {"available": False},
                "chat_model": {"available": False}
            }
            
            is_healthy = await manager._validate_model_health("embedding", "1.0.0")
            assert not is_healthy, "Unhealthy model should fail validation"
            
        except ImportError:
            pytest.skip("ModelManager not available")
    
    async def test_rollback_functionality(self, mock_dependencies):
        """Test model rollback functionality"""
        try:
            from services.ai_engine_service.app.model_manager import ModelManager
            
            manager = ModelManager()
            
            with patch.object(manager, '_configure_traffic_split') as mock_traffic, \
                 patch.object(manager, '_set_active_version') as mock_set_active:
                
                # Test successful rollback
                success = await manager._rollback_to_previous_version(
                    model_name="llama2:7b-chat",
                    previous_version="1.0.0"
                )
                
                assert success, "Rollback should succeed"
                
                # Verify traffic was switched back
                mock_traffic.assert_called_once_with("llama2:7b-chat", "1.0.0", 100)
                
                # Verify active version was set
                mock_set_active.assert_called_once_with("llama2:7b-chat", "1.0.0")
                
                # Verify alert was created
                mock_dependencies["alerts"].create_alert.assert_called_once()
                
                # Test rollback without previous version
                success = await manager._rollback_to_previous_version(
                    model_name="llama2:7b-chat",
                    previous_version=None
                )
                
                assert not success, "Rollback should fail without previous version"
            
        except ImportError:
            pytest.skip("ModelManager not available")
    
    async def test_concurrent_deployments(self, mock_dependencies):
        """Test handling of concurrent model deployments"""
        try:
            from services.ai_engine_service.app.model_manager import ModelManager, DeploymentStrategy
            
            manager = ModelManager()
            
            with patch.object(manager, '_validate_model_health') as mock_health, \
                 patch.object(manager, '_collect_performance_metrics') as mock_collect, \
                 patch.object(manager, '_configure_traffic_split') as mock_traffic, \
                 patch.object(manager, '_set_active_version') as mock_set_active:
                
                mock_health.return_value = True
                mock_collect.return_value = {
                    "error_rate": 0.01,
                    "latency_p95": 2000,
                    "availability": 0.999
                }
                
                # Test concurrent deployments of different models
                tasks = [
                    manager.deploy_model_version("embedding", "1.1.0", DeploymentStrategy.IMMEDIATE),
                    manager.deploy_model_version("chat", "1.1.0", DeploymentStrategy.IMMEDIATE)
                ]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Verify both deployments completed
                successful_results = [r for r in results if not isinstance(r, Exception)]
                assert len(successful_results) == 2, "Both deployments should succeed"
                
                for result in successful_results:
                    assert result is True, "Each deployment should return success"
            
        except ImportError:
            pytest.skip("ModelManager not available")
    
    async def test_custom_rollback_thresholds(self, mock_dependencies):
        """Test deployment with custom rollback thresholds"""
        try:
            from services.ai_engine_service.app.model_manager import ModelManager, DeploymentStrategy
            
            manager = ModelManager()
            
            # Custom thresholds - more strict
            custom_thresholds = {
                "error_rate": 0.01,      # 1% instead of 5%
                "latency_p95": 3000,     # 3s instead of 5s
                "availability": 0.999    # 99.9% instead of 99.5%
            }
            
            with patch.object(manager, '_collect_performance_metrics') as mock_collect:
                # Metrics that would pass default thresholds but fail custom ones
                mock_collect.return_value = {
                    "error_rate": 0.02,      # Above custom 1% threshold
                    "latency_p95": 2500,
                    "availability": 0.998
                }
                
                with patch.object(manager, '_rollback_to_previous_version') as mock_rollback:
                    mock_rollback.return_value = True
                    
                    # Test deployment with custom thresholds
                    success = await manager.deploy_model_version(
                        model_name="llama2:7b-chat",
                        version="1.2.0",
                        strategy=DeploymentStrategy.CANARY,
                        rollback_thresholds=custom_thresholds
                    )
                    
                    assert not success, "Deployment should fail with strict custom thresholds"
                    mock_rollback.assert_called_once()
            
        except ImportError:
            pytest.skip("ModelManager not available")


class TestModelManagerIntegration:
    """Integration tests for model manager with real dependencies"""
    
    async def test_model_manager_factory(self):
        """Test model manager factory function"""
        try:
            from services.ai_engine_service.app.model_manager import get_model_manager
            
            # Test singleton behavior
            manager1 = get_model_manager()
            manager2 = get_model_manager()
            
            assert manager1 is manager2, "Model manager should be singleton"
            assert manager1 is not None
            
        except ImportError:
            pytest.skip("ModelManager not available")
    
    async def test_version_storage_and_retrieval(self):
        """Test model version storage and retrieval"""
        try:
            from services.ai_engine_service.app.model_manager import ModelManager, ModelVersion, ModelStatus, DeploymentStrategy
            from datetime import datetime
            
            manager = ModelManager()
            
            # Create test model version
            model_version = ModelVersion(
                model_name="test_model",
                version="1.0.0",
                deployment_time=datetime.utcnow(),
                status=ModelStatus.HEALTHY,
                performance_metrics={"error_rate": 0.01},
                rollback_threshold={"error_rate": 0.05},
                deployment_strategy=DeploymentStrategy.CANARY
            )
            
            # Test version storage
            await manager._store_model_version(model_version)
            
            # Test active version management
            await manager._set_active_version("test_model", "1.0.0")
            active_version = await manager._get_active_version("test_model")
            
            assert active_version == "1.0.0", "Active version should be retrievable"
            
        except ImportError:
            pytest.skip("ModelManager not available")


if __name__ == "__main__":
    # Run model manager tests
    pytest.main([__file__, "-v", "--tb=short"])