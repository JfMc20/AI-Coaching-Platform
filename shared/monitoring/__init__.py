"""
ML Model Observability and Monitoring Module

This module provides comprehensive monitoring and observability for ML models
with built-in privacy protection and GDPR compliance.

Components:
- OpenTelemetry distributed tracing
- Prometheus metrics collection
- Privacy-preserving input monitoring
- Automated alerting and health checks
- GDPR-compliant data sampling
"""

from .tracing import (
    get_tracer,
    trace_ml_operation,
    create_correlation_id,
    TraceContext
)
from .metrics import (
    MetricsCollector,
    MLMetrics,
    PerformanceMetrics,
    ErrorMetrics,
    OperationType,
    get_metrics_collector
)
from .privacy import (
    PrivacyPreservingMonitor,
    InputSanitizer,
    DataSampler,
    PrivacyConfig
)
from .health_checks import (
    ModelHealthChecker,
    SyntheticRequestRunner,
    HealthStatus,
    HealthCheckResult,
    get_health_checker
)
from .alerting import (
    AlertManager,
    SLAMonitor,
    IncidentResponse,
    AlertSeverity,
    AlertType,
    AlertStatus,
    get_alert_manager
)

__all__ = [
    # Tracing
    "get_tracer",
    "trace_ml_operation", 
    "create_correlation_id",
    "TraceContext",
    
    # Metrics
    "MetricsCollector",
    "MLMetrics",
    "PerformanceMetrics", 
    "ErrorMetrics",
    "OperationType",
    "get_metrics_collector",
    
    # Privacy
    "PrivacyPreservingMonitor",
    "InputSanitizer",
    "DataSampler",
    "PrivacyConfig",
    
    # Health
    "ModelHealthChecker",
    "SyntheticRequestRunner",
    "HealthStatus",
    "HealthCheckResult",
    "get_health_checker",
    
    # Alerting
    "AlertManager",
    "SLAMonitor", 
    "IncidentResponse",
    "AlertSeverity",
    "AlertType",
    "AlertStatus",
    "get_alert_manager"
]