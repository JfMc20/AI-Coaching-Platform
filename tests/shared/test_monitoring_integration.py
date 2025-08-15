"""
Comprehensive Integration Tests for ML Monitoring System

Tests the complete monitoring infrastructure including:
- OpenTelemetry tracing
- Prometheus metrics collection  
- Privacy-preserving monitoring
- Health checks and alerting
- SLA monitoring
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from shared.monitoring import (
    get_tracer, trace_ml_operation, create_correlation_id,
    get_metrics_collector, MLMetrics, OperationType,
    PrivacyPreservingMonitor, PrivacyConfig,
    get_health_checker, get_alert_manager,
    ModelHealthChecker, SyntheticRequestRunner,
    AlertManager, SLAMonitor, HealthStatus, AlertSeverity
)


class TestMonitoringIntegration:
    """Integration tests for the complete monitoring system"""
    
    @pytest.fixture
    def privacy_config(self):
        """Privacy configuration for testing"""
        return PrivacyConfig(
            sampling_rate=0.1,  # 10% for testing
            retention_days=1,   # Short retention for testing
            enable_pii_detection=True,
            enable_differential_privacy=True
        )
    
    @pytest.fixture
    def privacy_monitor(self, privacy_config):
        """Privacy monitor instance for testing"""
        return PrivacyPreservingMonitor(privacy_config)
    
    @pytest.fixture
    def health_checker(self):
        """Health checker instance for testing"""
        return ModelHealthChecker()
    
    @pytest.fixture
    def alert_manager(self):
        """Alert manager instance for testing"""
        return AlertManager()
    
    def test_correlation_id_generation(self):
        """Test correlation ID generation"""
        correlation_id_1 = create_correlation_id()
        correlation_id_2 = create_correlation_id()
        
        assert correlation_id_1 != correlation_id_2
        assert len(correlation_id_1) > 0
        assert len(correlation_id_2) > 0
    
    def test_metrics_collector_initialization(self):
        """Test metrics collector initialization"""
        collector = get_metrics_collector()
        assert collector is not None
        
        # Test singleton behavior
        collector2 = get_metrics_collector()
        assert collector is collector2
    
    def test_ml_metrics_creation(self):
        """Test ML metrics data structure"""
        metrics = MLMetrics(
            operation_type=OperationType.CHAT,
            input_length=100,
            model_name="test-model",
            creator_id="test-creator"
        )
        
        assert metrics.operation_type == OperationType.CHAT
        assert metrics.input_length == 100
        assert metrics.model_name == "test-model"
        assert metrics.creator_id == "test-creator"
    
    def test_privacy_preserving_monitor_initialization(self, privacy_config):
        """Test privacy monitor initialization"""
        monitor = PrivacyPreservingMonitor(privacy_config)
        
        assert monitor.config.sampling_rate == 0.1
        assert monitor.config.retention_days == 1
        assert monitor.config.enable_pii_detection is True
    
    @pytest.mark.asyncio
    async def test_privacy_monitor_query_logging(self, privacy_monitor):
        """Test privacy-preserving query logging"""
        correlation_id = create_correlation_id()
        
        log_entry = await privacy_monitor.log_query(
            query="What is the weather today?",
            creator_id="test-user",
            correlation_id=correlation_id,
            consent_given=True
        )
        
        assert log_entry['event_type'] == 'query'
        assert log_entry['correlation_id'] == correlation_id
        assert 'creator_id_hash' in log_entry
        assert log_entry['input_length'] == len("What is the weather today?")
        assert log_entry['consent_given'] is True
    
    @pytest.mark.asyncio
    async def test_privacy_monitor_response_logging(self, privacy_monitor):
        """Test privacy-preserving response logging"""
        correlation_id = create_correlation_id()
        
        log_entry = await privacy_monitor.log_response(
            response="The weather is sunny today.",
            creator_id="test-user",
            correlation_id=correlation_id,
            model_used="test-model",
            processing_time_ms=500.0
        )
        
        assert log_entry['event_type'] == 'response'
        assert log_entry['model_used'] == 'test-model'
        assert log_entry['processing_time_ms'] == 500.0
        assert log_entry['output_length'] == len("The weather is sunny today.")
    
    def test_privacy_compliance_report(self, privacy_monitor):
        """Test privacy compliance report generation"""
        report = privacy_monitor.get_privacy_compliance_report()
        
        assert 'sampling_rate' in report
        assert 'retention_days' in report
        assert 'pii_detection_enabled' in report
        assert 'gdpr_compliant' in report
        assert report['gdpr_compliant'] is True
    
    @pytest.mark.asyncio
    async def test_health_checker_service_availability(self, health_checker):
        """Test service availability checking"""
        # Mock successful service response
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "healthy"}
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await health_checker.check_service_availability(
                "http://localhost:8003", "ai-engine"
            )
            
            assert result.status == HealthStatus.HEALTHY
            assert result.check_name == "ai-engine_availability"
            assert result.duration_ms > 0
    
    @pytest.mark.asyncio
    async def test_health_checker_model_latency(self, health_checker):
        """Test model latency checking"""
        # Test with mock synthetic request
        start_time = time.time()
        
        result = await health_checker.check_model_latency(
            "test-model", OperationType.CHAT
        )
        
        assert result.check_name == "test-model_latency"
        assert result.check_type.value == "latency"
        assert result.duration_ms >= 0
    
    @pytest.mark.asyncio
    async def test_health_checker_resource_usage(self, health_checker):
        """Test resource usage checking"""
        result = await health_checker.check_resource_usage("test-service")
        
        assert result.check_name == "test-service_resources"
        assert result.check_type.value == "resource"
        assert "cpu_percent" in result.details
        assert "memory_percent" in result.details
    
    def test_alert_manager_initialization(self, alert_manager):
        """Test alert manager initialization"""
        assert alert_manager.sla_monitor is not None
        assert len(alert_manager.alert_rules) > 0
        assert alert_manager.active_alerts == {}
    
    def test_sla_monitor_targets(self, alert_manager):
        """Test SLA monitor target configuration"""
        sla_monitor = alert_manager.sla_monitor
        
        # Check that SLA targets are properly configured
        assert "embedding" in sla_monitor.sla_targets
        assert "chat" in sla_monitor.sla_targets
        assert "search" in sla_monitor.sla_targets
        
        # Verify target values
        embedding_target = sla_monitor.sla_targets["embedding"]
        assert embedding_target.latency_p95_ms == 3000
        assert embedding_target.error_rate_percent == 5.0
    
    def test_sla_compliance_checking(self, alert_manager):
        """Test SLA compliance checking"""
        sla_monitor = alert_manager.sla_monitor
        
        compliance = sla_monitor.check_sla_compliance(OperationType.CHAT)
        
        assert "operation_type" in compliance
        assert "target" in compliance
        assert "current" in compliance
        assert "violations" in compliance
        assert "is_compliant" in compliance
    
    def test_sla_summary_generation(self, alert_manager):
        """Test SLA summary generation"""
        sla_monitor = alert_manager.sla_monitor
        
        summary = sla_monitor.get_sla_summary()
        
        assert "overall_compliance" in summary
        assert "operations" in summary
        assert "total_violations" in summary
        assert "critical_violations" in summary
    
    @pytest.mark.asyncio
    async def test_alert_rule_evaluation(self, alert_manager):
        """Test alert rule evaluation"""
        # This will evaluate rules with mock data
        new_alerts = await alert_manager.evaluate_alert_rules()
        
        # Should return list of alerts (may be empty with mock data)
        assert isinstance(new_alerts, list)
    
    def test_alert_acknowledgment(self, alert_manager):
        """Test alert acknowledgment"""
        # Create a mock alert first
        from shared.monitoring.alerting import Alert, AlertType, AlertStatus
        
        test_alert = Alert(
            id="test-alert-123",
            rule_name="test_rule",
            alert_type=AlertType.ERROR_RATE,
            severity=AlertSeverity.P2,
            title="Test Alert",
            description="Test alert for acknowledgment",
            timestamp=datetime.utcnow()
        )
        
        # Add to active alerts
        alert_manager.active_alerts[test_alert.id] = test_alert
        
        # Test acknowledgment
        success = alert_manager.acknowledge_alert(test_alert.id, "test-user")
        assert success is True
        assert test_alert.status == AlertStatus.ACKNOWLEDGED
        assert test_alert.acknowledged_at is not None
    
    def test_alert_resolution(self, alert_manager):
        """Test alert resolution"""
        from shared.monitoring.alerting import Alert, AlertType, AlertStatus
        
        test_alert = Alert(
            id="test-alert-456",
            rule_name="test_rule",
            alert_type=AlertType.LATENCY,
            severity=AlertSeverity.P3,
            title="Test Alert",
            description="Test alert for resolution",
            timestamp=datetime.utcnow()
        )
        
        # Add to active alerts
        alert_manager.active_alerts[test_alert.id] = test_alert
        
        # Test resolution
        success = alert_manager.resolve_alert(test_alert.id, "test-user")
        assert success is True
        assert test_alert.status == AlertStatus.RESOLVED
        assert test_alert.resolved_at is not None
        assert test_alert.id not in alert_manager.active_alerts
    
    def test_alert_summary_generation(self, alert_manager):
        """Test alert summary generation"""
        summary = alert_manager.get_alert_summary()
        
        assert "total_active" in summary
        assert "by_severity" in summary
        assert "by_type" in summary
        assert "oldest_alert" in summary
        assert "newest_alert" in summary
    
    @pytest.mark.asyncio
    async def test_synthetic_monitoring_runner(self, health_checker):
        """Test synthetic monitoring runner"""
        runner = SyntheticRequestRunner(health_checker)
        
        # Test that runner initializes correctly
        assert runner.health_checker is health_checker
        assert runner.running is False
        assert runner._task is None
    
    def test_tracer_initialization(self):
        """Test OpenTelemetry tracer initialization"""
        tracer = get_tracer()
        assert tracer is not None
        
        # Test singleton behavior
        tracer2 = get_tracer()
        assert tracer is tracer2
    
    @pytest.mark.asyncio
    async def test_trace_ml_operation_decorator(self):
        """Test ML operation tracing decorator"""
        
        @trace_ml_operation(operation_type=OperationType.CHAT)
        async def test_ml_function(input_text: str) -> str:
            await asyncio.sleep(0.1)  # Simulate processing
            return f"Processed: {input_text}"
        
        result = await test_ml_function("test input")
        assert result == "Processed: test input"
    
    def test_health_summary_generation(self, health_checker):
        """Test health summary generation"""
        summary = health_checker.get_health_summary()
        
        assert "overall_status" in summary
        assert "checks" in summary


class TestMonitoringPipelineIntegration:
    """Test complete monitoring pipeline integration"""
    
    @pytest.mark.asyncio
    async def test_complete_ml_operation_monitoring(self):
        """Test complete ML operation with full monitoring pipeline"""
        
        # Initialize monitoring components
        privacy_config = PrivacyConfig(sampling_rate=1.0)  # 100% sampling for test
        privacy_monitor = PrivacyPreservingMonitor(privacy_config)
        metrics_collector = get_metrics_collector()
        correlation_id = create_correlation_id()
        
        # Simulate ML operation start
        ml_metrics = MLMetrics(
            operation_type=OperationType.CHAT,
            input_length=50,
            model_name="test-model",
            creator_id="test-user"
        )
        
        start_time = time.time()
        metrics_collector.record_ml_operation_start(ml_metrics)
        
        # Log privacy-preserving query
        await privacy_monitor.log_query(
            query="Test query for monitoring",
            creator_id="test-user",
            correlation_id=correlation_id,
            consent_given=True
        )
        
        # Simulate processing
        await asyncio.sleep(0.1)
        
        # Record successful completion
        processing_time = (time.time() - start_time) * 1000
        ml_metrics.output_length = 75
        metrics_collector.record_ml_operation_success(
            ml_metrics, processing_time, 3
        )
        
        # Log privacy-preserving response
        await privacy_monitor.log_response(
            response="Test response from monitoring",
            creator_id="test-user",
            correlation_id=correlation_id,
            model_used="test-model",
            processing_time_ms=processing_time
        )
        
        # Verify monitoring completed without errors
        assert processing_time > 0
        assert ml_metrics.output_length == 75
    
    @pytest.mark.asyncio
    async def test_monitoring_error_handling(self):
        """Test monitoring system error handling"""
        
        privacy_monitor = PrivacyPreservingMonitor()
        metrics_collector = get_metrics_collector()
        
        # Test with invalid inputs
        ml_metrics = MLMetrics(
            operation_type=OperationType.EMBEDDING,
            input_length=0,
            model_name="",
            creator_id=""
        )
        
        # Should handle gracefully without raising exceptions
        metrics_collector.record_ml_operation_start(ml_metrics)
        metrics_collector.record_ml_operation_error(ml_metrics, 100, "Test error")
        
        # Test privacy monitor with edge cases
        log_entry = await privacy_monitor.log_query(
            query="",  # Empty query
            creator_id="test",
            correlation_id="invalid-correlation",
            consent_given=False
        )
        
        assert log_entry['input_length'] == 0
    
    @pytest.mark.asyncio 
    async def test_health_and_alerting_integration(self):
        """Test integration between health checks and alerting"""
        
        health_checker = ModelHealthChecker()
        alert_manager = AlertManager()
        
        # Run health checks
        health_results = await health_checker.run_comprehensive_health_check()
        
        # Verify health check results
        assert isinstance(health_results, dict)
        assert len(health_results) > 0
        
        # Test alert evaluation (should not raise exceptions)
        alerts = await alert_manager.evaluate_alert_rules()
        assert isinstance(alerts, list)
        
        # Test SLA monitoring
        sla_summary = alert_manager.sla_monitor.get_sla_summary()
        assert 'overall_compliance' in sla_summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])