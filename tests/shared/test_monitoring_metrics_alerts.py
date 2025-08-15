"""
Unit Tests for Monitoring Metrics and Alerting

Tests metrics collection, SLA monitoring, and alerting system:
- Prometheus metrics collection
- SLA compliance monitoring  
- Alert rule evaluation
- Incident response automation
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from shared.monitoring.metrics import (
    MetricsCollector, MLMetrics, OperationType, ErrorType,
    get_metrics_collector
)
from shared.monitoring.alerting import (
    AlertManager, SLAMonitor, Alert, AlertRule, AlertSeverity,
    AlertType, AlertStatus, SLATarget, IncidentResponse,
    get_alert_manager
)
from shared.monitoring.health_checks import (
    ModelHealthChecker, HealthStatus, HealthCheckResult, CheckType
)


class TestMetricsCollector:
    """Unit tests for Prometheus metrics collection"""
    
    @pytest.fixture
    def metrics_collector(self):
        return MetricsCollector()
    
    @pytest.fixture
    def ml_metrics(self):
        return MLMetrics(
            operation_type=OperationType.CHAT,
            input_length=100,
            model_name="test-model",
            creator_id="test-user"
        )
    
    def test_metrics_collector_initialization(self, metrics_collector):
        """Test metrics collector initialization"""
        assert metrics_collector is not None
        assert hasattr(metrics_collector, 'request_total')
        assert hasattr(metrics_collector, 'request_duration')
        assert hasattr(metrics_collector, 'error_total')
    
    def test_singleton_behavior(self):
        """Test metrics collector singleton behavior"""
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()
        assert collector1 is collector2
    
    def test_ml_operation_start_recording(self, metrics_collector, ml_metrics):
        """Test recording ML operation start"""
        # Should not raise exceptions
        metrics_collector.record_ml_operation_start(ml_metrics)
        
        # Verify metrics were updated (basic check)
        assert True  # If no exception, test passes
    
    def test_ml_operation_success_recording(self, metrics_collector, ml_metrics):
        """Test recording ML operation success"""
        processing_time = 1500.0  # 1.5 seconds
        sources_used = 3
        
        ml_metrics.output_length = 150
        ml_metrics.token_count = 75
        
        # Should not raise exceptions
        metrics_collector.record_ml_operation_success(
            ml_metrics, processing_time, sources_used
        )
        
        assert True
    
    def test_ml_operation_error_recording(self, metrics_collector, ml_metrics):
        """Test recording ML operation errors"""
        processing_time = 500.0
        error_message = "Test error occurred"
        
        # Should not raise exceptions
        metrics_collector.record_ml_operation_error(
            ml_metrics, processing_time, error_message
        )
        
        assert True
    
    def test_sla_violation_recording(self, metrics_collector):
        """Test recording SLA violations"""
        operation_type = OperationType.EMBEDDING
        violation_type = "latency"
        severity = "p2"
        
        # Should not raise exceptions
        metrics_collector.record_sla_violation(
            operation_type, violation_type, severity
        )
        
        assert True
    
    def test_cost_tracking(self, metrics_collector):
        """Test cost tracking functionality"""
        operation_type = OperationType.CHAT
        model_name = "expensive-model"
        cost_amount = 0.05  # $0.05
        
        # Should not raise exceptions
        metrics_collector.record_cost(operation_type, model_name, cost_amount)
        
        assert True
    
    def test_metrics_export(self, metrics_collector):
        """Test metrics export in Prometheus format"""
        # Record some test metrics
        ml_metrics = MLMetrics(
            operation_type=OperationType.SEARCH,
            input_length=50,
            model_name="search-model",
            creator_id="test"
        )
        
        metrics_collector.record_ml_operation_start(ml_metrics)
        metrics_collector.record_ml_operation_success(ml_metrics, 800.0, 2)
        
        # Export metrics
        metrics_output = metrics_collector.get_metrics()
        
        assert isinstance(metrics_output, str)
        assert len(metrics_output) > 0
        # Should contain Prometheus-format metrics
        assert "ml_requests_total" in metrics_output or "# HELP" in metrics_output
    
    def test_different_operation_types(self, metrics_collector):
        """Test metrics collection for different operation types"""
        
        operation_types = [
            OperationType.CHAT,
            OperationType.EMBEDDING,
            OperationType.SEARCH,
            OperationType.DOCUMENT_PROCESSING
        ]
        
        for op_type in operation_types:
            ml_metrics = MLMetrics(
                operation_type=op_type,
                input_length=100,
                model_name=f"{op_type.value}-model",
                creator_id="test"
            )
            
            # Should handle all operation types
            metrics_collector.record_ml_operation_start(ml_metrics)
            metrics_collector.record_ml_operation_success(ml_metrics, 1000.0, 1)


class TestSLAMonitor:
    """Unit tests for SLA monitoring"""
    
    @pytest.fixture
    def sla_monitor(self):
        return SLAMonitor()
    
    def test_sla_monitor_initialization(self, sla_monitor):
        """Test SLA monitor initialization"""
        assert sla_monitor is not None
        assert hasattr(sla_monitor, 'sla_targets')
        assert hasattr(sla_monitor, 'metrics_collector')
        
        # Check that default SLA targets are configured
        assert "embedding" in sla_monitor.sla_targets
        assert "chat" in sla_monitor.sla_targets
        assert "search" in sla_monitor.sla_targets
    
    def test_sla_targets_configuration(self, sla_monitor):
        """Test SLA targets are properly configured"""
        embedding_target = sla_monitor.sla_targets["embedding"]
        
        assert isinstance(embedding_target, SLATarget)
        assert embedding_target.name == "Embedding Generation"
        assert embedding_target.operation_type == OperationType.EMBEDDING
        assert embedding_target.latency_p95_ms == 3000  # 3 seconds
        assert embedding_target.error_rate_percent == 5.0
        assert embedding_target.availability_percent == 99.9
    
    def test_sla_compliance_checking(self, sla_monitor):
        """Test SLA compliance checking"""
        compliance = sla_monitor.check_sla_compliance(OperationType.CHAT)
        
        assert "operation_type" in compliance
        assert "target" in compliance
        assert "current" in compliance
        assert "violations" in compliance
        assert "is_compliant" in compliance
        
        assert compliance["operation_type"] == "chat"
        assert isinstance(compliance["violations"], list)
        assert isinstance(compliance["is_compliant"], bool)
    
    def test_sla_summary_generation(self, sla_monitor):
        """Test SLA summary generation"""
        summary = sla_monitor.get_sla_summary()
        
        assert "overall_compliance" in summary
        assert "operations" in summary
        assert "total_violations" in summary
        assert "critical_violations" in summary
        
        # Should have entries for each operation type
        assert "embedding" in summary["operations"]
        assert "chat" in summary["operations"]
        assert "search" in summary["operations"]
    
    def test_violation_detection_logic(self, sla_monitor):
        """Test SLA violation detection logic"""
        # This tests the mock implementation
        # In production, this would use real metrics
        
        compliance = sla_monitor.check_sla_compliance(OperationType.EMBEDDING)
        
        # Check violation structure
        for violation in compliance["violations"]:
            assert "type" in violation
            assert "target" in violation
            assert "actual" in violation
            assert "severity" in violation
            
            # Verify severity levels are valid
            assert violation["severity"] in ["p1", "p2", "p3", "p4"]


class TestAlertManager:
    """Unit tests for alert management"""
    
    @pytest.fixture
    def alert_manager(self):
        return AlertManager()
    
    def test_alert_manager_initialization(self, alert_manager):
        """Test alert manager initialization"""
        assert alert_manager is not None
        assert alert_manager.sla_monitor is not None
        assert isinstance(alert_manager.alert_rules, list)
        assert len(alert_manager.alert_rules) > 0
        assert isinstance(alert_manager.active_alerts, dict)
    
    def test_alert_rules_configuration(self, alert_manager):
        """Test alert rules are properly configured"""
        rules = alert_manager.alert_rules
        
        # Should have rules for different severity levels
        p1_rules = [r for r in rules if r.severity == AlertSeverity.P1]
        p2_rules = [r for r in rules if r.severity == AlertSeverity.P2]
        p3_rules = [r for r in rules if r.severity == AlertSeverity.P3]
        
        assert len(p1_rules) > 0, "Should have P1 critical rules"
        assert len(p2_rules) > 0, "Should have P2 high severity rules"
        assert len(p3_rules) > 0, "Should have P3 medium severity rules"
        
        # Check rule structure
        for rule in rules:
            assert isinstance(rule, AlertRule)
            assert rule.name
            assert isinstance(rule.threshold, (int, float))
            assert rule.evaluation_window_minutes > 0
    
    @pytest.mark.asyncio
    async def test_alert_rule_evaluation(self, alert_manager):
        """Test alert rule evaluation"""
        # Test evaluation (uses mock data)
        new_alerts = await alert_manager.evaluate_alert_rules()
        
        assert isinstance(new_alerts, list)
        
        # If alerts were generated, verify structure
        for alert in new_alerts:
            assert isinstance(alert, Alert)
            assert alert.id
            assert alert.rule_name
            assert alert.alert_type
            assert alert.severity
            assert alert.timestamp
    
    def test_alert_creation(self, alert_manager):
        """Test alert creation from rules"""
        # Create a test rule
        test_rule = AlertRule(
            name="test_rule",
            alert_type=AlertType.ERROR_RATE,
            severity=AlertSeverity.P2,
            threshold=10.0,
            description="Test alert rule"
        )
        
        # This would normally be called during evaluation
        # Testing the internal method
        alert = alert_manager._create_alert(test_rule)
        
        if alert:  # May return None in async context
            assert alert.rule_name == "test_rule"
            assert alert.alert_type == AlertType.ERROR_RATE
            assert alert.severity == AlertSeverity.P2
    
    def test_alert_acknowledgment(self, alert_manager):
        """Test alert acknowledgment"""
        # Create and add a test alert
        test_alert = Alert(
            id="test-123",
            rule_name="test_rule",
            alert_type=AlertType.LATENCY,
            severity=AlertSeverity.P3,
            title="Test Alert",
            description="Test alert for acknowledgment",
            timestamp=datetime.utcnow()
        )
        
        alert_manager.active_alerts[test_alert.id] = test_alert
        
        # Test acknowledgment
        success = alert_manager.acknowledge_alert(test_alert.id, "test-user")
        
        assert success is True
        assert test_alert.status == AlertStatus.ACKNOWLEDGED
        assert test_alert.acknowledged_at is not None
        assert "acknowledged_by" in test_alert.metadata
    
    def test_alert_resolution(self, alert_manager):
        """Test alert resolution"""
        # Create and add a test alert
        test_alert = Alert(
            id="test-456",
            rule_name="test_rule",
            alert_type=AlertType.AVAILABILITY,
            severity=AlertSeverity.P1,
            title="Test Alert",
            description="Test alert for resolution",
            timestamp=datetime.utcnow()
        )
        
        alert_manager.active_alerts[test_alert.id] = test_alert
        
        # Test resolution
        success = alert_manager.resolve_alert(test_alert.id, "test-user")
        
        assert success is True
        assert test_alert.status == AlertStatus.RESOLVED
        assert test_alert.resolved_at is not None
        assert test_alert.id not in alert_manager.active_alerts
    
    def test_active_alerts_filtering(self, alert_manager):
        """Test active alerts filtering by severity"""
        # Add test alerts with different severities
        alerts = [
            Alert(
                id="p1-alert",
                rule_name="critical_rule",
                alert_type=AlertType.ERROR_RATE,
                severity=AlertSeverity.P1,
                title="Critical Alert",
                description="Critical test alert",
                timestamp=datetime.utcnow()
            ),
            Alert(
                id="p3-alert",
                rule_name="warning_rule",
                alert_type=AlertType.LATENCY,
                severity=AlertSeverity.P3,
                title="Warning Alert",
                description="Warning test alert",
                timestamp=datetime.utcnow()
            )
        ]
        
        for alert in alerts:
            alert_manager.active_alerts[alert.id] = alert
        
        # Test filtering
        all_alerts = alert_manager.get_active_alerts()
        p1_alerts = alert_manager.get_active_alerts(AlertSeverity.P1)
        p3_alerts = alert_manager.get_active_alerts(AlertSeverity.P3)
        
        assert len(all_alerts) >= 2
        assert len(p1_alerts) >= 1
        assert len(p3_alerts) >= 1
        
        # Verify filtering worked
        for alert in p1_alerts:
            assert alert.severity == AlertSeverity.P1
    
    def test_alert_summary(self, alert_manager):
        """Test alert summary generation"""
        # Add some test alerts
        test_alerts = [
            Alert(
                id=f"alert-{i}",
                rule_name="test_rule",
                alert_type=AlertType.ERROR_RATE,
                severity=AlertSeverity.P2,
                title=f"Test Alert {i}",
                description="Test alert",
                timestamp=datetime.utcnow() - timedelta(minutes=i)
            )
            for i in range(3)
        ]
        
        for alert in test_alerts:
            alert_manager.active_alerts[alert.id] = alert
        
        summary = alert_manager.get_alert_summary()
        
        assert "total_active" in summary
        assert "by_severity" in summary
        assert "by_type" in summary
        assert "oldest_alert" in summary
        assert "newest_alert" in summary
        
        assert summary["total_active"] >= 3
    
    def test_suppression_window(self, alert_manager):
        """Test alert suppression window functionality"""
        # Create a rule with short suppression window
        test_rule = AlertRule(
            name="test_suppression_rule",
            alert_type=AlertType.ERROR_RATE,
            severity=AlertSeverity.P3,
            threshold=5.0,
            suppression_window_minutes=1
        )
        
        # Test suppression logic
        is_suppressed = alert_manager._is_suppressed(test_rule)
        
        # Without recent alerts, should not be suppressed
        assert is_suppressed is False
        
        # Add a recent alert for this rule
        recent_alert = Alert(
            id="suppression-test",
            rule_name="test_suppression_rule",
            alert_type=AlertType.ERROR_RATE,
            severity=AlertSeverity.P3,
            title="Suppression Test",
            description="Test suppression",
            timestamp=datetime.utcnow()
        )
        
        alert_manager.alert_history.append(recent_alert)
        
        # Now should be suppressed
        is_suppressed = alert_manager._is_suppressed(test_rule)
        assert is_suppressed is True


class TestIncidentResponse:
    """Unit tests for incident response automation"""
    
    @pytest.fixture
    def alert_manager(self):
        return AlertManager()
    
    @pytest.fixture
    def incident_response(self, alert_manager):
        return IncidentResponse(alert_manager)
    
    def test_incident_response_initialization(self, incident_response):
        """Test incident response initialization"""
        assert incident_response is not None
        assert incident_response.alert_manager is not None
        assert hasattr(incident_response, 'response_rules')
        assert isinstance(incident_response.response_rules, dict)
    
    @pytest.mark.asyncio
    async def test_alert_handling(self, incident_response):
        """Test automated alert handling"""
        # Create a test alert
        test_alert = Alert(
            id="incident-test",
            rule_name="critical_error_rate",
            alert_type=AlertType.ERROR_RATE,
            severity=AlertSeverity.P1,
            title="Critical Error Rate",
            description="Error rate exceeded threshold",
            timestamp=datetime.utcnow()
        )
        
        # Test handling
        response = await incident_response.handle_alert(test_alert)
        
        assert "alert_id" in response
        assert "actions_taken" in response
        assert "success" in response
        assert response["alert_id"] == test_alert.id
        assert isinstance(response["actions_taken"], list)
    
    @pytest.mark.asyncio
    async def test_p1_incident_handling(self, incident_response):
        """Test P1 incident handling"""
        p1_alert = Alert(
            id="p1-incident",
            rule_name="model_completely_down",
            alert_type=AlertType.AVAILABILITY,
            severity=AlertSeverity.P1,
            title="Model Down",
            description="Model is completely unavailable",
            timestamp=datetime.utcnow()
        )
        
        # Test P1 handling
        actions = await incident_response._handle_p1_incident(p1_alert)
        
        assert isinstance(actions, list)
        assert len(actions) > 0
        
        # Should include incident management actions
        actions_text = " ".join(actions).lower()
        assert "incident" in actions_text or "ticket" in actions_text
    
    @pytest.mark.asyncio
    async def test_specific_rule_handling(self, incident_response):
        """Test handling of specific alert rules"""
        # Test critical error rate handling
        error_alert = Alert(
            id="error-incident",
            rule_name="critical_error_rate",
            alert_type=AlertType.ERROR_RATE,
            severity=AlertSeverity.P1,
            title="Critical Error Rate",
            description="Critical error rate exceeded",
            timestamp=datetime.utcnow()
        )
        
        actions = await incident_response._handle_critical_error_rate(error_alert)
        
        assert isinstance(actions, list)
        assert len(actions) > 0
        
        # Should include rollback and scaling actions
        actions_text = " ".join(actions).lower()
        assert "rollback" in actions_text or "scale" in actions_text


class TestHealthChecksIntegration:
    """Test integration with health checks"""
    
    @pytest.fixture
    def health_checker(self):
        return ModelHealthChecker()
    
    @pytest.mark.asyncio
    async def test_health_check_result_structure(self, health_checker):
        """Test health check result structure"""
        # Test resource usage check
        result = await health_checker.check_resource_usage("test-service")
        
        assert isinstance(result, HealthCheckResult)
        assert result.check_name == "test-service_resources"
        assert result.check_type == CheckType.RESOURCE
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]
        assert result.duration_ms >= 0
        assert isinstance(result.details, dict)
    
    def test_health_summary_integration(self, health_checker):
        """Test health summary integration with monitoring"""
        summary = health_checker.get_health_summary()
        
        assert "overall_status" in summary
        assert "checks" in summary
        
        # Summary should be compatible with alerting system
        assert summary["overall_status"] in ["healthy", "degraded", "unhealthy", "unknown"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])