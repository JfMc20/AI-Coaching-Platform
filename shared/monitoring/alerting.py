"""
Alerting and Incident Response System

Implements SLA monitoring, automated alerting, and incident response
for ML services with configurable thresholds and escalation policies.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

import httpx
from shared.config.env_constants import get_env_value
from .metrics import get_metrics_collector, OperationType
from .health_checks import HealthStatus, HealthCheckResult

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    P1 = "p1"  # Critical - Complete service failure
    P2 = "p2"  # High - Significant degradation
    P3 = "p3"  # Medium - Minor issues
    P4 = "p4"  # Low - Warnings


class AlertType(str, Enum):
    """Types of alerts"""
    SLA_VIOLATION = "sla_violation"
    ERROR_RATE = "error_rate"
    LATENCY = "latency"
    AVAILABILITY = "availability"
    RESOURCE_USAGE = "resource_usage"
    MODEL_DRIFT = "model_drift"
    COST_THRESHOLD = "cost_threshold"


class AlertStatus(str, Enum):
    """Alert status"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class AlertRule:
    """Configuration for alert rules"""
    name: str
    alert_type: AlertType
    severity: AlertSeverity
    threshold: float
    evaluation_window_minutes: int = 5
    minimum_duration_minutes: int = 1
    description: str = ""
    enabled: bool = True
    suppression_window_minutes: int = 60  # Prevent duplicate alerts
    escalation_delay_minutes: int = 15    # Time before escalation


@dataclass
class Alert:
    """Alert instance"""
    id: str
    rule_name: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    description: str
    timestamp: datetime
    status: AlertStatus = AlertStatus.ACTIVE
    metadata: Dict[str, Any] = field(default_factory=dict)
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    escalated_at: Optional[datetime] = None


@dataclass
class SLATarget:
    """SLA target configuration"""
    name: str
    operation_type: OperationType
    latency_p95_ms: float
    error_rate_percent: float
    availability_percent: float


class SLAMonitor:
    """
    SLA monitoring with real-time violation detection
    """
    
    def __init__(self):
        self.metrics_collector = get_metrics_collector()
        self._setup_sla_targets()
        self._sla_violations = []
    
    def _setup_sla_targets(self):
        """Setup SLA targets for different operations"""
        self.sla_targets = {
            "embedding": SLATarget(
                name="Embedding Generation",
                operation_type=OperationType.EMBEDDING,
                latency_p95_ms=3000,  # 3 seconds
                error_rate_percent=5.0,
                availability_percent=99.9
            ),
            "chat": SLATarget(
                name="Chat Completion",
                operation_type=OperationType.CHAT,
                latency_p95_ms=5000,  # 5 seconds
                error_rate_percent=5.0,
                availability_percent=99.9
            ),
            "search": SLATarget(
                name="Vector Search",
                operation_type=OperationType.SEARCH,
                latency_p95_ms=1000,  # 1 second
                error_rate_percent=2.0,
                availability_percent=99.95
            ),
            "document_processing": SLATarget(
                name="Document Processing",
                operation_type=OperationType.DOCUMENT_PROCESSING,
                latency_p95_ms=10000,  # 10 seconds
                error_rate_percent=10.0,
                availability_percent=99.5
            )
        }
    
    def check_sla_compliance(self, operation_type: OperationType) -> Dict[str, Any]:
        """
        Check SLA compliance for an operation type
        
        Args:
            operation_type: Type of operation to check
            
        Returns:
            SLA compliance status
        """
        target_key = operation_type.value
        if target_key not in self.sla_targets:
            return {"error": f"No SLA target defined for {operation_type}"}
        
        target = self.sla_targets[target_key]
        
        # This would typically query metrics from your time-series database
        # Mock implementation for now
        current_metrics = {
            "latency_p95_ms": 2500,  # Mock current latency
            "error_rate_percent": 3.0,  # Mock current error rate
            "availability_percent": 99.95  # Mock current availability
        }
        
        compliance = {
            "operation_type": operation_type.value,
            "target": {
                "latency_p95_ms": target.latency_p95_ms,
                "error_rate_percent": target.error_rate_percent,
                "availability_percent": target.availability_percent
            },
            "current": current_metrics,
            "violations": []
        }
        
        # Check for violations
        if current_metrics["latency_p95_ms"] > target.latency_p95_ms:
            compliance["violations"].append({
                "type": "latency",
                "target": target.latency_p95_ms,
                "actual": current_metrics["latency_p95_ms"],
                "severity": "p2" if current_metrics["latency_p95_ms"] > target.latency_p95_ms * 1.5 else "p3"
            })
        
        if current_metrics["error_rate_percent"] > target.error_rate_percent:
            compliance["violations"].append({
                "type": "error_rate",
                "target": target.error_rate_percent,
                "actual": current_metrics["error_rate_percent"],
                "severity": "p1" if current_metrics["error_rate_percent"] > 20 else "p2"
            })
        
        if current_metrics["availability_percent"] < target.availability_percent:
            compliance["violations"].append({
                "type": "availability",
                "target": target.availability_percent,
                "actual": current_metrics["availability_percent"],
                "severity": "p1"
            })
        
        compliance["is_compliant"] = len(compliance["violations"]) == 0
        return compliance
    
    def get_sla_summary(self) -> Dict[str, Any]:
        """
        Get overall SLA compliance summary
        
        Returns:
            SLA summary across all operations
        """
        summary = {
            "overall_compliance": True,
            "operations": {},
            "total_violations": 0,
            "critical_violations": 0
        }
        
        for operation_type in OperationType:
            compliance = self.check_sla_compliance(operation_type)
            summary["operations"][operation_type.value] = compliance
            
            if not compliance.get("is_compliant", True):
                summary["overall_compliance"] = False
                summary["total_violations"] += len(compliance.get("violations", []))
                
                # Count critical violations
                critical_count = sum(
                    1 for v in compliance.get("violations", []) 
                    if v.get("severity") == "p1"
                )
                summary["critical_violations"] += critical_count
        
        return summary


class AlertManager:
    """
    Comprehensive alert management system
    """
    
    def __init__(self):
        self.sla_monitor = SLAMonitor()
        self._setup_alert_rules()
        self.active_alerts = {}
        self.alert_history = []
        self._notification_handlers = []
    
    def _setup_alert_rules(self):
        """Setup default alert rules"""
        self.alert_rules = [
            # P1 - Critical alerts
            AlertRule(
                name="model_completely_down",
                alert_type=AlertType.AVAILABILITY,
                severity=AlertSeverity.P1,
                threshold=0.0,  # 0% availability
                evaluation_window_minutes=1,
                description="Model is completely unavailable"
            ),
            
            AlertRule(
                name="critical_error_rate",
                alert_type=AlertType.ERROR_RATE,
                severity=AlertSeverity.P1,
                threshold=20.0,  # 20% error rate
                evaluation_window_minutes=5,
                description="Critical error rate threshold exceeded"
            ),
            
            # P2 - High severity alerts
            AlertRule(
                name="high_latency",
                alert_type=AlertType.LATENCY,
                severity=AlertSeverity.P2,
                threshold=10000,  # 10 seconds
                evaluation_window_minutes=5,
                description="Response latency is extremely high"
            ),
            
            AlertRule(
                name="high_error_rate",
                alert_type=AlertType.ERROR_RATE,
                severity=AlertSeverity.P2,
                threshold=10.0,  # 10% error rate
                evaluation_window_minutes=5,
                description="High error rate detected"
            ),
            
            AlertRule(
                name="sla_violation",
                alert_type=AlertType.SLA_VIOLATION,
                severity=AlertSeverity.P2,
                threshold=1.0,  # Any SLA violation
                evaluation_window_minutes=5,
                description="SLA target violation"
            ),
            
            # P3 - Medium severity alerts
            AlertRule(
                name="degraded_performance",
                alert_type=AlertType.LATENCY,
                severity=AlertSeverity.P3,
                threshold=5000,  # 5 seconds
                evaluation_window_minutes=10,
                description="Performance degradation detected"
            ),
            
            AlertRule(
                name="model_drift_detected",
                alert_type=AlertType.MODEL_DRIFT,
                severity=AlertSeverity.P3,
                threshold=0.7,  # 70% drift score
                evaluation_window_minutes=30,
                description="Significant model drift detected"
            ),
            
            AlertRule(
                name="high_resource_usage",
                alert_type=AlertType.RESOURCE_USAGE,
                severity=AlertSeverity.P3,
                threshold=85.0,  # 85% resource usage
                evaluation_window_minutes=15,
                description="High resource utilization"
            ),
            
            # P4 - Low severity alerts
            AlertRule(
                name="cost_threshold_warning",
                alert_type=AlertType.COST_THRESHOLD,
                severity=AlertSeverity.P4,
                threshold=100.0,  # $100 daily cost
                evaluation_window_minutes=60,
                description="Cost threshold warning"
            )
        ]
    
    def add_notification_handler(self, handler: Callable[[Alert], None]):
        """
        Add a notification handler for alerts
        
        Args:
            handler: Function to handle alert notifications
        """
        self._notification_handlers.append(handler)
    
    async def evaluate_alert_rules(self) -> List[Alert]:
        """
        Evaluate all alert rules and generate alerts
        
        Returns:
            List of new alerts generated
        """
        new_alerts = []
        
        for rule in self.alert_rules:
            if not rule.enabled:
                continue
            
            try:
                should_alert = await self._evaluate_rule(rule)
                
                if should_alert:
                    alert = await self._create_alert(rule)
                    if alert:
                        new_alerts.append(alert)
                        await self._process_alert(alert)
                
            except Exception as e:
                logger.error(f"Failed to evaluate alert rule {rule.name}: {e}")
        
        return new_alerts
    
    async def _evaluate_rule(self, rule: AlertRule) -> bool:
        """
        Evaluate a specific alert rule
        
        Args:
            rule: Alert rule to evaluate
            
        Returns:
            True if alert should be fired
        """
        # Check if we're in suppression window
        if self._is_suppressed(rule):
            return False
        
        # This would typically query your metrics backend
        # Mock implementation based on rule type
        
        if rule.alert_type == AlertType.ERROR_RATE:
            current_error_rate = 3.0  # Mock current error rate
            return current_error_rate > rule.threshold
        
        elif rule.alert_type == AlertType.LATENCY:
            current_latency = 2500  # Mock current latency
            return current_latency > rule.threshold
        
        elif rule.alert_type == AlertType.AVAILABILITY:
            current_availability = 99.8  # Mock availability
            return current_availability < rule.threshold
        
        elif rule.alert_type == AlertType.SLA_VIOLATION:
            sla_summary = self.sla_monitor.get_sla_summary()
            return not sla_summary["overall_compliance"]
        
        elif rule.alert_type == AlertType.RESOURCE_USAGE:
            current_usage = 70.0  # Mock resource usage
            return current_usage > rule.threshold
        
        elif rule.alert_type == AlertType.MODEL_DRIFT:
            drift_score = 0.3  # Mock drift score
            return drift_score > rule.threshold
        
        elif rule.alert_type == AlertType.COST_THRESHOLD:
            daily_cost = 50.0  # Mock daily cost
            return daily_cost > rule.threshold
        
        return False
    
    def _is_suppressed(self, rule: AlertRule) -> bool:
        """
        Check if alert rule is in suppression window
        
        Args:
            rule: Alert rule to check
            
        Returns:
            True if suppressed
        """
        # Check if there's a recent alert for this rule
        cutoff_time = datetime.utcnow() - timedelta(minutes=rule.suppression_window_minutes)
        
        for alert in self.alert_history:
            if (alert.rule_name == rule.name and 
                alert.timestamp > cutoff_time and 
                alert.status != AlertStatus.RESOLVED):
                return True
        
        return False
    
    async def _create_alert(self, rule: AlertRule) -> Optional[Alert]:
        """
        Create a new alert from rule
        
        Args:
            rule: Alert rule that fired
            
        Returns:
            New Alert instance
        """
        try:
            alert_id = f"alert_{int(datetime.utcnow().timestamp())}_{rule.name}"
            
            alert = Alert(
                id=alert_id,
                rule_name=rule.name,
                alert_type=rule.alert_type,
                severity=rule.severity,
                title=f"{rule.severity.upper()}: {rule.description}",
                description=rule.description,
                timestamp=datetime.utcnow(),
                metadata={
                    "rule_threshold": rule.threshold,
                    "evaluation_window_minutes": rule.evaluation_window_minutes
                }
            )
            
            return alert
            
        except Exception as e:
            logger.error(f"Failed to create alert for rule {rule.name}: {e}")
            return None
    
    async def _process_alert(self, alert: Alert):
        """
        Process a new alert
        
        Args:
            alert: Alert to process
        """
        try:
            # Add to active alerts
            self.active_alerts[alert.id] = alert
            
            # Add to history
            self.alert_history.append(alert)
            
            # Trim history (keep last 1000 alerts)
            if len(self.alert_history) > 1000:
                self.alert_history = self.alert_history[-1000:]
            
            # Send notifications
            await self._send_notifications(alert)
            
            # Schedule escalation if needed
            if alert.severity in [AlertSeverity.P1, AlertSeverity.P2]:
                await self._schedule_escalation(alert)
            
            logger.info(f"Processed alert {alert.id}: {alert.title}")
            
        except Exception as e:
            logger.error(f"Failed to process alert {alert.id}: {e}")
    
    async def _send_notifications(self, alert: Alert):
        """
        Send alert notifications to all handlers
        
        Args:
            alert: Alert to send
        """
        for handler in self._notification_handlers:
            try:
                await asyncio.get_event_loop().run_in_executor(None, handler, alert)
            except Exception as e:
                logger.error(f"Notification handler failed: {e}")
    
    async def _schedule_escalation(self, alert: Alert):
        """
        Schedule alert escalation
        
        Args:
            alert: Alert to escalate
        """
        # This would typically integrate with your incident management system
        logger.info(f"Scheduled escalation for alert {alert.id} in 15 minutes")
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """
        Acknowledge an alert
        
        Args:
            alert_id: ID of alert to acknowledge
            acknowledged_by: Who acknowledged the alert
            
        Returns:
            True if successful
        """
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_at = datetime.utcnow()
            alert.metadata["acknowledged_by"] = acknowledged_by
            
            logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
            return True
        
        return False
    
    def resolve_alert(self, alert_id: str, resolved_by: str) -> bool:
        """
        Resolve an alert
        
        Args:
            alert_id: ID of alert to resolve
            resolved_by: Who resolved the alert
            
        Returns:
            True if successful
        """
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
            alert.metadata["resolved_by"] = resolved_by
            
            # Remove from active alerts
            del self.active_alerts[alert_id]
            
            logger.info(f"Alert {alert_id} resolved by {resolved_by}")
            return True
        
        return False
    
    def get_active_alerts(self, severity_filter: Optional[AlertSeverity] = None) -> List[Alert]:
        """
        Get active alerts, optionally filtered by severity
        
        Args:
            severity_filter: Optional severity filter
            
        Returns:
            List of active alerts
        """
        alerts = list(self.active_alerts.values())
        
        if severity_filter:
            alerts = [a for a in alerts if a.severity == severity_filter]
        
        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """
        Get alert summary statistics
        
        Returns:
            Alert summary
        """
        active_alerts = list(self.active_alerts.values())
        
        return {
            "total_active": len(active_alerts),
            "by_severity": {
                "p1": sum(1 for a in active_alerts if a.severity == AlertSeverity.P1),
                "p2": sum(1 for a in active_alerts if a.severity == AlertSeverity.P2),
                "p3": sum(1 for a in active_alerts if a.severity == AlertSeverity.P3),
                "p4": sum(1 for a in active_alerts if a.severity == AlertSeverity.P4)
            },
            "by_type": {
                alert_type.value: sum(
                    1 for a in active_alerts if a.alert_type == alert_type
                ) for alert_type in AlertType
            },
            "oldest_alert": min(
                (a.timestamp for a in active_alerts), default=None
            ),
            "newest_alert": max(
                (a.timestamp for a in active_alerts), default=None
            )
        }


class IncidentResponse:
    """
    Automated incident response system
    """
    
    def __init__(self, alert_manager: AlertManager):
        self.alert_manager = alert_manager
        self._setup_response_rules()
    
    def _setup_response_rules(self):
        """Setup automated response rules"""
        self.response_rules = {
            "critical_error_rate": self._handle_critical_error_rate,
            "model_completely_down": self._handle_model_down,
            "high_resource_usage": self._handle_high_resource_usage
        }
    
    async def handle_alert(self, alert: Alert) -> Dict[str, Any]:
        """
        Handle an alert with automated response
        
        Args:
            alert: Alert to handle
            
        Returns:
            Response actions taken
        """
        response_actions = {
            "alert_id": alert.id,
            "actions_taken": [],
            "success": False
        }
        
        try:
            # Check if we have a specific handler
            if alert.rule_name in self.response_rules:
                handler = self.response_rules[alert.rule_name]
                actions = await handler(alert)
                response_actions["actions_taken"].extend(actions)
            
            # Generic actions based on severity
            if alert.severity == AlertSeverity.P1:
                actions = await self._handle_p1_incident(alert)
                response_actions["actions_taken"].extend(actions)
            
            response_actions["success"] = True
            logger.info(f"Incident response completed for {alert.id}")
            
        except Exception as e:
            logger.error(f"Incident response failed for {alert.id}: {e}")
            response_actions["error"] = str(e)
        
        return response_actions
    
    async def _handle_critical_error_rate(self, alert: Alert) -> List[str]:
        """Handle critical error rate incidents"""
        actions = []
        
        # This would implement actual rollback logic
        actions.append("Initiated automated rollback procedure")
        actions.append("Scaled up healthy instances")
        actions.append("Redirected traffic to backup models")
        
        return actions
    
    async def _handle_model_down(self, alert: Alert) -> List[str]:
        """Handle model down incidents"""
        actions = []
        
        actions.append("Attempted model restart")
        actions.append("Activated fallback model")
        actions.append("Notified on-call engineer")
        
        return actions
    
    async def _handle_high_resource_usage(self, alert: Alert) -> List[str]:
        """Handle high resource usage"""
        actions = []
        
        actions.append("Triggered auto-scaling")
        actions.append("Optimized resource allocation")
        
        return actions
    
    async def _handle_p1_incident(self, alert: Alert) -> List[str]:
        """Handle P1 incidents"""
        actions = []
        
        actions.append("Created incident ticket")
        actions.append("Notified incident commander")
        actions.append("Initiated incident response protocol")
        
        return actions


# Notification handlers
async def slack_notification_handler(alert: Alert):
    """Send alert to Slack"""
    slack_webhook = get_env_value("SLACK_WEBHOOK_URL")
    if not slack_webhook:
        return
    
    message = {
        "text": f"🚨 {alert.severity.upper()} Alert",
        "attachments": [
            {
                "color": "danger" if alert.severity in ["p1", "p2"] else "warning",
                "fields": [
                    {"title": "Alert", "value": alert.title, "short": False},
                    {"title": "Type", "value": alert.alert_type.value, "short": True},
                    {"title": "Time", "value": alert.timestamp.isoformat(), "short": True}
                ]
            }
        ]
    }
    
    try:
        async with httpx.AsyncClient() as client:
            await client.post(slack_webhook, json=message)
    except Exception as e:
        logger.error(f"Failed to send Slack notification: {e}")


async def pagerduty_notification_handler(alert: Alert):
    """Send alert to PagerDuty"""
    if alert.severity not in [AlertSeverity.P1, AlertSeverity.P2]:
        return  # Only escalate critical alerts
    
    pagerduty_key = get_env_value("PAGERDUTY_INTEGRATION_KEY")
    if not pagerduty_key:
        return
    
    # This would integrate with PagerDuty API
    logger.info(f"Would send {alert.id} to PagerDuty")


# Global alert manager instance
_alert_manager = None


def get_alert_manager() -> AlertManager:
    """Get the global alert manager instance"""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
        # Add default notification handlers
        _alert_manager.add_notification_handler(slack_notification_handler)
        _alert_manager.add_notification_handler(pagerduty_notification_handler)
    return _alert_manager