"""
Monitoring endpoints for AI Engine Service

Provides endpoints for metrics, health checks, and observability data.
"""

import time
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import PlainTextResponse

from shared.monitoring import (
    get_metrics_collector, get_health_checker, get_alert_manager,
    HealthStatus, AlertSeverity
)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/metrics", response_class=PlainTextResponse)
async def get_prometheus_metrics():
    """
    Get Prometheus metrics for scraping
    
    Returns:
        Prometheus exposition format metrics
    """
    try:
        metrics_collector = get_metrics_collector()
        return metrics_collector.get_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {e}")


@router.get("/health/summary")
async def get_health_summary():
    """
    Get comprehensive health summary
    
    Returns:
        Health status summary
    """
    try:
        health_checker = get_health_checker()
        return health_checker.get_health_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get health summary: {e}")


@router.get("/health/detailed")
async def get_detailed_health():
    """
    Run detailed health checks
    
    Returns:
        Detailed health check results
    """
    try:
        health_checker = get_health_checker()
        results = await health_checker.run_comprehensive_health_check()
        
        # Convert results to serializable format
        serializable_results = {}
        for check_name, result in results.items():
            serializable_results[check_name] = {
                "check_name": result.check_name,
                "check_type": result.check_type.value,
                "status": result.status.value,
                "timestamp": result.timestamp.isoformat(),
                "duration_ms": result.duration_ms,
                "details": result.details,
                "error_message": result.error_message,
                "recovery_suggestions": result.recovery_suggestions
            }
        
        return serializable_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run health checks: {e}")


@router.get("/alerts/active")
async def get_active_alerts(severity: Optional[str] = None):
    """
    Get active alerts
    
    Args:
        severity: Optional severity filter (p1, p2, p3, p4)
    
    Returns:
        List of active alerts
    """
    try:
        alert_manager = get_alert_manager()
        
        severity_filter = None
        if severity:
            severity_filter = AlertSeverity(severity.lower())
        
        alerts = alert_manager.get_active_alerts(severity_filter)
        
        # Convert alerts to serializable format
        serializable_alerts = []
        for alert in alerts:
            serializable_alerts.append({
                "id": alert.id,
                "rule_name": alert.rule_name,
                "alert_type": alert.alert_type.value,
                "severity": alert.severity.value,
                "title": alert.title,
                "description": alert.description,
                "timestamp": alert.timestamp.isoformat(),
                "status": alert.status.value,
                "metadata": alert.metadata,
                "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
                "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None
            })
        
        return {"alerts": serializable_alerts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {e}")


@router.get("/alerts/summary")
async def get_alert_summary():
    """
    Get alert summary statistics
    
    Returns:
        Alert summary
    """
    try:
        alert_manager = get_alert_manager()
        summary = alert_manager.get_alert_summary()
        
        # Convert datetime objects to ISO strings
        if summary.get("oldest_alert"):
            summary["oldest_alert"] = summary["oldest_alert"].isoformat()
        if summary.get("newest_alert"):
            summary["newest_alert"] = summary["newest_alert"].isoformat()
        
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alert summary: {e}")


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, acknowledged_by: str = "system"):
    """
    Acknowledge an alert
    
    Args:
        alert_id: ID of alert to acknowledge
        acknowledged_by: Who acknowledged the alert
    
    Returns:
        Success status
    """
    try:
        alert_manager = get_alert_manager()
        success = alert_manager.acknowledge_alert(alert_id, acknowledged_by)
        
        if success:
            return {"status": "acknowledged", "alert_id": alert_id}
        else:
            raise HTTPException(status_code=404, detail="Alert not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge alert: {e}")


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str, resolved_by: str = "system"):
    """
    Resolve an alert
    
    Args:
        alert_id: ID of alert to resolve
        resolved_by: Who resolved the alert
    
    Returns:
        Success status
    """
    try:
        alert_manager = get_alert_manager()
        success = alert_manager.resolve_alert(alert_id, resolved_by)
        
        if success:
            return {"status": "resolved", "alert_id": alert_id}
        else:
            raise HTTPException(status_code=404, detail="Alert not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve alert: {e}")


@router.get("/sla/compliance")
async def get_sla_compliance():
    """
    Get SLA compliance status
    
    Returns:
        SLA compliance summary
    """
    try:
        alert_manager = get_alert_manager()
        compliance = alert_manager.sla_monitor.get_sla_summary()
        
        return compliance
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get SLA compliance: {e}")


@router.get("/models/status")
async def get_model_status():
    """
    Get status of all ML models
    
    Returns:
        Model status information
    """
    try:
        # This would typically query your model registry
        # Mock implementation for now
        models = {
            "llama2:7b-chat": {
                "status": "healthy",
                "version": "v1.0.0",
                "last_health_check": datetime.utcnow().isoformat(),
                "availability": 99.95,
                "avg_latency_ms": 2500,
                "error_rate": 0.5
            },
            "nomic-embed-text": {
                "status": "healthy", 
                "version": "v1.0.0",
                "last_health_check": datetime.utcnow().isoformat(),
                "availability": 99.99,
                "avg_latency_ms": 150,
                "error_rate": 0.1
            }
        }
        
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model status: {e}")


@router.get("/privacy/compliance")
async def get_privacy_compliance(request: Request):
    """
    Get privacy compliance report
    
    Returns:
        Privacy compliance status
    """
    try:
        privacy_monitor = request.app.state.privacy_monitor
        compliance_report = privacy_monitor.get_privacy_compliance_report()
        
        return compliance_report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get privacy compliance: {e}")


@router.get("/observability/dashboard")
async def get_observability_dashboard():
    """
    Get comprehensive observability dashboard data
    
    Returns:
        Dashboard data combining metrics, health, alerts, and SLA
    """
    try:
        # Get health summary
        health_checker = get_health_checker()
        health_summary = health_checker.get_health_summary()
        
        # Get alert summary
        alert_manager = get_alert_manager()
        alert_summary = alert_manager.get_alert_summary()
        
        # Get SLA compliance
        sla_compliance = alert_manager.sla_monitor.get_sla_summary()
        
        # Get model status (mock for now)
        model_status = {
            "total_models": 2,
            "healthy_models": 2,
            "degraded_models": 0,
            "unhealthy_models": 0
        }
        
        dashboard = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": health_summary.get("overall_status", "unknown"),
            "health": health_summary,
            "alerts": alert_summary,
            "sla": sla_compliance,
            "models": model_status,
            "uptime_hours": 24.0,  # Mock uptime
            "total_requests_24h": 1500,  # Mock request count
            "avg_response_time_ms": 1200  # Mock response time
        }
        
        return dashboard
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard data: {e}")