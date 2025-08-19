"""
Visual Program Builder - Debug & Analytics System
Comprehensive modular debugging and analytics system for program execution
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Type, Union
from enum import Enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
import statistics

from .program_models import ProgramDefinition, DebugLevel
from .step_models import ProgramStep, StepExecution
from .program_engine import ExecutionContext, ProgramExecutionResult, StepExecutionResult

logger = logging.getLogger(__name__)


# ==================== ANALYTICS TYPES & ENUMS ====================

class AnalyticsType(str, Enum):
    """Types of analytics data"""
    EXECUTION = "execution"
    PERFORMANCE = "performance"
    USER_JOURNEY = "user_journey"
    PERSONALITY = "personality"
    INTEGRATION = "integration"
    ERROR_TRACKING = "error_tracking"
    ENGAGEMENT = "engagement"
    CONTENT_EFFECTIVENESS = "content_effectiveness"


class StorageType(str, Enum):
    """Storage backend types"""
    TIMESERIES = "timeseries"
    RELATIONAL = "relational"
    DOCUMENT = "document"
    CACHE = "cache"


class InsightType(str, Enum):
    """Types of insights generated"""
    PERFORMANCE_BOTTLENECK = "performance_bottleneck"
    USER_BEHAVIOR_PATTERN = "user_behavior_pattern"
    CONTENT_OPTIMIZATION = "content_optimization"
    PERSONALITY_INCONSISTENCY = "personality_inconsistency"
    ENGAGEMENT_OPPORTUNITY = "engagement_opportunity"
    ERROR_TREND = "error_trend"


# ==================== DEBUG MODELS ====================

@dataclass
class DebugEvent:
    """Individual debug event"""
    event_id: str
    timestamp: datetime
    event_type: str
    event_name: str
    data: Dict[str, Any]
    severity: str = "info"  # info, warning, error, critical
    session_id: str = ""
    step_id: Optional[str] = None
    execution_time_ms: float = 0.0


@dataclass
class PerformanceMetric:
    """Performance metric data point"""
    metric_name: str
    value: float
    unit: str
    timestamp: datetime
    context: Dict[str, Any]
    tags: Dict[str, str]


@dataclass
class ExecutionTrace:
    """Execution trace for debugging"""
    trace_id: str
    program_id: str
    user_id: str
    started_at: datetime
    completed_at: Optional[datetime]
    events: List[DebugEvent]
    metrics: List[PerformanceMetric]
    error_count: int = 0
    warning_count: int = 0


# ==================== ANALYTICS COLLECTORS ====================

class AnalyticsCollector(ABC):
    """Abstract base class for analytics collectors"""
    
    @abstractmethod
    async def collect(self, execution_result: ProgramExecutionResult) -> Dict[str, Any]:
        """Collect analytics data from execution result"""
        pass
    
    @abstractmethod
    def get_collector_type(self) -> AnalyticsType:
        """Get the type of analytics this collector handles"""
        pass


class ExecutionAnalyticsCollector(AnalyticsCollector):
    """Collector for execution analytics"""
    
    async def collect(self, execution_result: ProgramExecutionResult) -> Dict[str, Any]:
        """Collect execution analytics"""
        
        return {
            "execution_id": execution_result.execution_id,
            "program_id": execution_result.program_id,
            "user_id": execution_result.user_id,
            "status": execution_result.status,
            "completion_percentage": execution_result.completion_percentage,
            "total_steps": execution_result.total_steps_executed,
            "successful_steps": execution_result.successful_steps,
            "failed_steps": execution_result.failed_steps,
            "execution_time_seconds": execution_result.execution_time_seconds,
            "collected_at": datetime.utcnow()
        }
    
    def get_collector_type(self) -> AnalyticsType:
        return AnalyticsType.EXECUTION


class PerformanceAnalyticsCollector(AnalyticsCollector):
    """Collector for performance analytics"""
    
    async def collect(self, execution_result: ProgramExecutionResult) -> Dict[str, Any]:
        """Collect performance analytics"""
        
        step_times = [r.execution_time_seconds for r in execution_result.step_results if r.execution_time_seconds > 0]
        
        performance_data = {
            "execution_id": execution_result.execution_id,
            "total_execution_time": execution_result.execution_time_seconds,
            "average_step_time": execution_result.average_step_time,
            "step_count": len(execution_result.step_results),
            "collected_at": datetime.utcnow()
        }
        
        if step_times:
            performance_data.update({
                "min_step_time": min(step_times),
                "max_step_time": max(step_times),
                "median_step_time": statistics.median(step_times),
                "step_time_std_dev": statistics.stdev(step_times) if len(step_times) > 1 else 0
            })
        
        # Performance categorization
        if execution_result.execution_time_seconds > 30:
            performance_data["performance_category"] = "slow"
        elif execution_result.execution_time_seconds > 10:
            performance_data["performance_category"] = "moderate"
        else:
            performance_data["performance_category"] = "fast"
        
        return performance_data
    
    def get_collector_type(self) -> AnalyticsType:
        return AnalyticsType.PERFORMANCE


class UserJourneyCollector(AnalyticsCollector):
    """Collector for user journey analytics"""
    
    async def collect(self, execution_result: ProgramExecutionResult) -> Dict[str, Any]:
        """Collect user journey analytics"""
        
        journey_steps = []
        for step_result in execution_result.step_results:
            journey_steps.append({
                "step_id": step_result.step_id,
                "success": step_result.success,
                "engagement_score": step_result.engagement_score,
                "execution_time": step_result.execution_time_seconds,
                "user_response": bool(step_result.user_response)
            })
        
        # Calculate journey metrics
        total_engagement = sum(r.engagement_score for r in execution_result.step_results if r.engagement_score > 0)
        avg_engagement = total_engagement / len(execution_result.step_results) if execution_result.step_results else 0
        
        drop_off_points = [
            r.step_id for r in execution_result.step_results 
            if not r.success or r.engagement_score < 0.3
        ]
        
        return {
            "execution_id": execution_result.execution_id,
            "user_id": execution_result.user_id,
            "journey_steps": journey_steps,
            "total_engagement_score": total_engagement,
            "average_engagement": avg_engagement,
            "completion_rate": execution_result.completion_percentage / 100,
            "drop_off_points": drop_off_points,
            "journey_length": len(journey_steps),
            "collected_at": datetime.utcnow()
        }
    
    def get_collector_type(self) -> AnalyticsType:
        return AnalyticsType.USER_JOURNEY


class PersonalityAnalyticsCollector(AnalyticsCollector):
    """Collector for personality consistency analytics"""
    
    async def collect(self, execution_result: ProgramExecutionResult) -> Dict[str, Any]:
        """Collect personality analytics"""
        
        personality_scores = [
            r.personality_consistency for r in execution_result.step_results 
            if r.personality_consistency > 0
        ]
        
        consistency_data = {
            "execution_id": execution_result.execution_id,
            "overall_consistency": execution_result.personality_consistency_score,
            "step_consistency_scores": personality_scores,
            "collected_at": datetime.utcnow()
        }
        
        if personality_scores:
            consistency_data.update({
                "min_consistency": min(personality_scores),
                "max_consistency": max(personality_scores),
                "avg_consistency": statistics.mean(personality_scores),
                "consistency_variance": statistics.variance(personality_scores) if len(personality_scores) > 1 else 0
            })
            
            # Identify inconsistent steps
            avg_score = statistics.mean(personality_scores)
            threshold = avg_score - 0.2  # 20% below average
            inconsistent_steps = [
                execution_result.step_results[i].step_id 
                for i, score in enumerate(personality_scores) 
                if score < threshold
            ]
            consistency_data["inconsistent_steps"] = inconsistent_steps
        
        return consistency_data
    
    def get_collector_type(self) -> AnalyticsType:
        return AnalyticsType.PERSONALITY


class IntegrationAnalyticsCollector(AnalyticsCollector):
    """Collector for integration system analytics"""
    
    async def collect(self, execution_result: ProgramExecutionResult) -> Dict[str, Any]:
        """Collect integration analytics"""
        
        integration_usage = {
            "personality_enhanced": 0,
            "knowledge_enhanced": 0,
            "ai_enhanced": 0,
            "total_steps": len(execution_result.step_results)
        }
        
        enhancement_effectiveness = []
        
        for step_result in execution_result.step_results:
            enhancements = step_result.result_data.get("enhancements_applied", {})
            
            if enhancements.get("personality", {}).get("personality_available"):
                integration_usage["personality_enhanced"] += 1
            
            if enhancements.get("knowledge", {}).get("knowledge_available"):
                integration_usage["knowledge_enhanced"] += 1
            
            if enhancements.get("ai", {}).get("ai_enhancement_applied"):
                integration_usage["ai_enhanced"] += 1
            
            # Track enhancement effectiveness
            personalization_score = step_result.result_data.get("personalization_score", 0)
            if personalization_score > 0:
                enhancement_effectiveness.append({
                    "step_id": step_result.step_id,
                    "personalization_score": personalization_score,
                    "engagement_score": step_result.engagement_score,
                    "success": step_result.success
                })
        
        # Calculate integration effectiveness
        if enhancement_effectiveness:
            avg_personalization = statistics.mean([e["personalization_score"] for e in enhancement_effectiveness])
            avg_engagement = statistics.mean([e["engagement_score"] for e in enhancement_effectiveness])
        else:
            avg_personalization = 0
            avg_engagement = 0
        
        return {
            "execution_id": execution_result.execution_id,
            "integration_usage": integration_usage,
            "enhancement_effectiveness": enhancement_effectiveness,
            "avg_personalization_score": avg_personalization,
            "avg_enhanced_engagement": avg_engagement,
            "integration_coverage": {
                "personality": integration_usage["personality_enhanced"] / integration_usage["total_steps"] if integration_usage["total_steps"] > 0 else 0,
                "knowledge": integration_usage["knowledge_enhanced"] / integration_usage["total_steps"] if integration_usage["total_steps"] > 0 else 0,
                "ai": integration_usage["ai_enhanced"] / integration_usage["total_steps"] if integration_usage["total_steps"] > 0 else 0
            },
            "collected_at": datetime.utcnow()
        }
    
    def get_collector_type(self) -> AnalyticsType:
        return AnalyticsType.INTEGRATION


# ==================== STORAGE BACKENDS ====================

class StorageBackend(ABC):
    """Abstract base class for storage backends"""
    
    @abstractmethod
    async def store(self, data: Dict[str, Any], storage_key: str) -> bool:
        """Store analytics data"""
        pass
    
    @abstractmethod
    async def retrieve(self, storage_key: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Retrieve analytics data"""
        pass
    
    @abstractmethod
    async def aggregate(self, storage_key: str, aggregation: Dict[str, Any]) -> Dict[str, Any]:
        """Perform aggregation on stored data"""
        pass


class TimeSeriesStorage(StorageBackend):
    """Time series storage backend for performance metrics"""
    
    def __init__(self):
        self.data_store: Dict[str, List[Dict[str, Any]]] = {}
    
    async def store(self, data: Dict[str, Any], storage_key: str) -> bool:
        """Store time series data"""
        try:
            if storage_key not in self.data_store:
                self.data_store[storage_key] = []
            
            # Add timestamp if not present
            if "timestamp" not in data:
                data["timestamp"] = datetime.utcnow()
            
            self.data_store[storage_key].append(data)
            
            # Keep only last 1000 entries per key
            if len(self.data_store[storage_key]) > 1000:
                self.data_store[storage_key] = self.data_store[storage_key][-1000:]
            
            return True
        except Exception as e:
            logger.error(f"TimeSeriesStorage store failed: {e}")
            return False
    
    async def retrieve(self, storage_key: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Retrieve time series data"""
        data = self.data_store.get(storage_key, [])
        
        if not filters:
            return data
        
        # Apply simple filters
        filtered_data = data
        
        if "start_time" in filters:
            start_time = filters["start_time"]
            filtered_data = [d for d in filtered_data if d.get("timestamp", datetime.min) >= start_time]
        
        if "end_time" in filters:
            end_time = filters["end_time"]
            filtered_data = [d for d in filtered_data if d.get("timestamp", datetime.max) <= end_time]
        
        if "limit" in filters:
            limit = filters["limit"]
            filtered_data = filtered_data[-limit:]
        
        return filtered_data
    
    async def aggregate(self, storage_key: str, aggregation: Dict[str, Any]) -> Dict[str, Any]:
        """Perform time series aggregation"""
        data = self.data_store.get(storage_key, [])
        
        if not data:
            return {}
        
        agg_type = aggregation.get("type", "avg")
        field = aggregation.get("field", "value")
        
        values = [d.get(field, 0) for d in data if field in d]
        
        if not values:
            return {}
        
        if agg_type == "avg":
            return {"result": statistics.mean(values)}
        elif agg_type == "sum":
            return {"result": sum(values)}
        elif agg_type == "min":
            return {"result": min(values)}
        elif agg_type == "max":
            return {"result": max(values)}
        elif agg_type == "count":
            return {"result": len(values)}
        else:
            return {"result": values}


class RelationalStorage(StorageBackend):
    """Relational storage backend for structured analytics"""
    
    def __init__(self):
        self.tables: Dict[str, List[Dict[str, Any]]] = {}
    
    async def store(self, data: Dict[str, Any], storage_key: str) -> bool:
        """Store relational data"""
        try:
            if storage_key not in self.tables:
                self.tables[storage_key] = []
            
            self.tables[storage_key].append(data)
            return True
        except Exception as e:
            logger.error(f"RelationalStorage store failed: {e}")
            return False
    
    async def retrieve(self, storage_key: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Retrieve relational data"""
        data = self.tables.get(storage_key, [])
        
        if not filters:
            return data
        
        # Apply filters
        filtered_data = data
        
        for field, value in filters.items():
            if field in ["limit", "start_time", "end_time"]:
                continue
            filtered_data = [d for d in filtered_data if d.get(field) == value]
        
        if "limit" in filters:
            filtered_data = filtered_data[:filters["limit"]]
        
        return filtered_data
    
    async def aggregate(self, storage_key: str, aggregation: Dict[str, Any]) -> Dict[str, Any]:
        """Perform relational aggregation"""
        data = self.tables.get(storage_key, [])
        
        group_by = aggregation.get("group_by")
        agg_func = aggregation.get("function", "count")
        field = aggregation.get("field")
        
        if group_by:
            groups = {}
            for row in data:
                key = row.get(group_by, "unknown")
                if key not in groups:
                    groups[key] = []
                groups[key].append(row)
            
            result = {}
            for key, group_data in groups.items():
                if agg_func == "count":
                    result[key] = len(group_data)
                elif field and agg_func == "avg":
                    values = [d.get(field, 0) for d in group_data if field in d]
                    result[key] = statistics.mean(values) if values else 0
                elif field and agg_func == "sum":
                    values = [d.get(field, 0) for d in group_data if field in d]
                    result[key] = sum(values)
            
            return result
        else:
            return {"total_records": len(data)}


class DocumentStorage(StorageBackend):
    """Document storage backend for complex analytics"""
    
    def __init__(self):
        self.documents: Dict[str, Dict[str, Any]] = {}
    
    async def store(self, data: Dict[str, Any], storage_key: str) -> bool:
        """Store document data"""
        try:
            doc_id = data.get("id", f"{storage_key}_{datetime.utcnow().isoformat()}")
            self.documents[doc_id] = data
            return True
        except Exception as e:
            logger.error(f"DocumentStorage store failed: {e}")
            return False
    
    async def retrieve(self, storage_key: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Retrieve document data"""
        # Return all documents for now (simplified implementation)
        matching_docs = []
        
        for doc_id, doc in self.documents.items():
            if storage_key in doc_id or storage_key in str(doc):
                matching_docs.append(doc)
        
        if filters and "limit" in filters:
            matching_docs = matching_docs[:filters["limit"]]
        
        return matching_docs
    
    async def aggregate(self, storage_key: str, aggregation: Dict[str, Any]) -> Dict[str, Any]:
        """Perform document aggregation"""
        docs = await self.retrieve(storage_key)
        return {"document_count": len(docs)}


# ==================== INSIGHT ANALYZERS ====================

class InsightAnalyzer(ABC):
    """Abstract base class for insight analyzers"""
    
    @abstractmethod
    async def analyze(self, program_id: str, time_range: Dict[str, datetime]) -> List[Dict[str, Any]]:
        """Analyze data and generate insights"""
        pass
    
    @abstractmethod
    def get_insight_type(self) -> InsightType:
        """Get the type of insights this analyzer generates"""
        pass


class PerformanceInsightAnalyzer(InsightAnalyzer):
    """Analyzer for performance-related insights"""
    
    def __init__(self, storage_backend: StorageBackend):
        self.storage = storage_backend
    
    async def analyze(self, program_id: str, time_range: Dict[str, datetime]) -> List[Dict[str, Any]]:
        """Analyze performance data for insights"""
        
        # Retrieve performance data
        filters = {
            "start_time": time_range.get("start"),
            "end_time": time_range.get("end"),
            "limit": 100
        }
        
        performance_data = await self.storage.retrieve(f"performance_{program_id}", filters)
        
        insights = []
        
        if performance_data:
            # Analyze execution times
            execution_times = [d.get("total_execution_time", 0) for d in performance_data]
            avg_execution_time = statistics.mean(execution_times)
            
            if avg_execution_time > 20:  # Slow execution threshold
                insights.append({
                    "type": "performance_bottleneck",
                    "severity": "warning",
                    "title": "Slow Program Execution Detected",
                    "description": f"Average execution time ({avg_execution_time:.1f}s) exceeds recommended threshold (20s)",
                    "recommendation": "Consider optimizing step complexity or reducing integration overhead",
                    "metrics": {
                        "avg_execution_time": avg_execution_time,
                        "sample_size": len(execution_times)
                    }
                })
            
            # Analyze step time variance
            step_times = []
            for d in performance_data:
                if "step_time_std_dev" in d:
                    step_times.append(d["step_time_std_dev"])
            
            if step_times and statistics.mean(step_times) > 5:
                insights.append({
                    "type": "performance_inconsistency",
                    "severity": "info",
                    "title": "Inconsistent Step Performance",
                    "description": "High variance in step execution times detected",
                    "recommendation": "Review steps with high execution time variance",
                    "metrics": {
                        "avg_variance": statistics.mean(step_times)
                    }
                })
        
        return insights
    
    def get_insight_type(self) -> InsightType:
        return InsightType.PERFORMANCE_BOTTLENECK


class EngagementInsightAnalyzer(InsightAnalyzer):
    """Analyzer for engagement-related insights"""
    
    def __init__(self, storage_backend: StorageBackend):
        self.storage = storage_backend
    
    async def analyze(self, program_id: str, time_range: Dict[str, datetime]) -> List[Dict[str, Any]]:
        """Analyze engagement data for insights"""
        
        filters = {
            "start_time": time_range.get("start"),
            "end_time": time_range.get("end"),
            "limit": 100
        }
        
        journey_data = await self.storage.retrieve(f"journey_{program_id}", filters)
        
        insights = []
        
        if journey_data:
            # Analyze engagement trends
            engagement_scores = [d.get("average_engagement", 0) for d in journey_data]
            avg_engagement = statistics.mean(engagement_scores)
            
            if avg_engagement < 0.6:  # Low engagement threshold
                insights.append({
                    "type": "low_engagement",
                    "severity": "warning",
                    "title": "Low User Engagement Detected",
                    "description": f"Average engagement score ({avg_engagement:.2f}) is below optimal threshold (0.6)",
                    "recommendation": "Review content effectiveness and personality consistency",
                    "metrics": {
                        "avg_engagement": avg_engagement,
                        "sample_size": len(engagement_scores)
                    }
                })
            
            # Analyze drop-off patterns
            all_drop_offs = []
            for d in journey_data:
                all_drop_offs.extend(d.get("drop_off_points", []))
            
            if all_drop_offs:
                # Count drop-off frequency by step
                drop_off_counts = {}
                for step_id in all_drop_offs:
                    drop_off_counts[step_id] = drop_off_counts.get(step_id, 0) + 1
                
                # Find most problematic step
                most_problematic = max(drop_off_counts.items(), key=lambda x: x[1])
                
                if most_problematic[1] > len(journey_data) * 0.3:  # 30% drop-off rate
                    insights.append({
                        "type": "high_dropout_step",
                        "severity": "error",
                        "title": f"High Drop-off Rate at Step {most_problematic[0]}",
                        "description": f"Step {most_problematic[0]} has {most_problematic[1]} drop-offs ({most_problematic[1]/len(journey_data)*100:.1f}%)",
                        "recommendation": "Review and optimize this step for better user experience",
                        "metrics": {
                            "step_id": most_problematic[0],
                            "drop_off_count": most_problematic[1],
                            "drop_off_rate": most_problematic[1]/len(journey_data)
                        }
                    })
        
        return insights
    
    def get_insight_type(self) -> InsightType:
        return InsightType.ENGAGEMENT_OPPORTUNITY


# ==================== CORE ANALYTICS SYSTEM ====================

class AnalyticsSystem:
    """Core analytics and debugging system"""
    
    def __init__(self):
        # Analytics collectors
        self.collectors: Dict[AnalyticsType, AnalyticsCollector] = {
            AnalyticsType.EXECUTION: ExecutionAnalyticsCollector(),
            AnalyticsType.PERFORMANCE: PerformanceAnalyticsCollector(),
            AnalyticsType.USER_JOURNEY: UserJourneyCollector(),
            AnalyticsType.PERSONALITY: PersonalityAnalyticsCollector(),
            AnalyticsType.INTEGRATION: IntegrationAnalyticsCollector()
        }
        
        # Storage backends
        self.storage_backends: Dict[StorageType, StorageBackend] = {
            StorageType.TIMESERIES: TimeSeriesStorage(),
            StorageType.RELATIONAL: RelationalStorage(),
            StorageType.DOCUMENT: DocumentStorage()
        }
        
        # Insight analyzers
        self.insight_analyzers: Dict[InsightType, InsightAnalyzer] = {
            InsightType.PERFORMANCE_BOTTLENECK: PerformanceInsightAnalyzer(self.storage_backends[StorageType.TIMESERIES]),
            InsightType.ENGAGEMENT_OPPORTUNITY: EngagementInsightAnalyzer(self.storage_backends[StorageType.RELATIONAL])
        }
        
        # Debug session storage
        self.debug_sessions: Dict[str, ExecutionTrace] = {}
        
        logger.info("Analytics System initialized")
    
    def register_collector(self, analytics_type: AnalyticsType, collector: AnalyticsCollector):
        """Register custom analytics collector"""
        self.collectors[analytics_type] = collector
        logger.info(f"Registered analytics collector: {analytics_type}")
    
    def register_storage_backend(self, storage_type: StorageType, backend: StorageBackend):
        """Register custom storage backend"""
        self.storage_backends[storage_type] = backend
        logger.info(f"Registered storage backend: {storage_type}")
    
    def register_insight_analyzer(self, insight_type: InsightType, analyzer: InsightAnalyzer):
        """Register custom insight analyzer"""
        self.insight_analyzers[insight_type] = analyzer
        logger.info(f"Registered insight analyzer: {insight_type}")
    
    async def collect_execution_analytics(
        self, 
        execution_result: ProgramExecutionResult
    ) -> Dict[str, Any]:
        """Collect analytics from program execution"""
        
        collected_data = {}
        collection_errors = []
        
        # Run all collectors
        for analytics_type, collector in self.collectors.items():
            try:
                data = await collector.collect(execution_result)
                collected_data[analytics_type.value] = data
                
                # Store data in appropriate backend
                storage_key = f"{analytics_type.value}_{execution_result.program_id}"
                
                # Determine storage backend
                if analytics_type in [AnalyticsType.PERFORMANCE]:
                    await self.storage_backends[StorageType.TIMESERIES].store(data, storage_key)
                elif analytics_type in [AnalyticsType.EXECUTION, AnalyticsType.USER_JOURNEY]:
                    await self.storage_backends[StorageType.RELATIONAL].store(data, storage_key)
                else:
                    await self.storage_backends[StorageType.DOCUMENT].store(data, storage_key)
                
            except Exception as e:
                error_msg = f"Analytics collection failed for {analytics_type}: {str(e)}"
                collection_errors.append(error_msg)
                logger.error(error_msg)
        
        # Create analytics report
        analytics_report = {
            "execution_id": execution_result.execution_id,
            "program_id": execution_result.program_id,
            "user_id": execution_result.user_id,
            "collected_at": datetime.utcnow(),
            "analytics_data": collected_data,
            "collection_errors": collection_errors,
            "collectors_run": len(self.collectors),
            "successful_collections": len(collected_data)
        }
        
        # Store the complete report
        await self.storage_backends[StorageType.DOCUMENT].store(
            analytics_report, 
            f"analytics_report_{execution_result.execution_id}"
        )
        
        return analytics_report
    
    async def generate_program_insights(
        self, 
        program_id: str, 
        time_range: Optional[Dict[str, datetime]] = None
    ) -> List[Dict[str, Any]]:
        """Generate insights for a program"""
        
        if not time_range:
            time_range = {
                "start": datetime.utcnow() - timedelta(days=7),
                "end": datetime.utcnow()
            }
        
        all_insights = []
        
        # Run all insight analyzers
        for insight_type, analyzer in self.insight_analyzers.items():
            try:
                insights = await analyzer.analyze(program_id, time_range)
                all_insights.extend(insights)
            except Exception as e:
                logger.error(f"Insight analysis failed for {insight_type}: {str(e)}")
        
        # Sort insights by severity
        severity_order = {"critical": 0, "error": 1, "warning": 2, "info": 3}
        all_insights.sort(key=lambda x: severity_order.get(x.get("severity", "info"), 3))
        
        return all_insights
    
    async def get_program_analytics_summary(
        self, 
        program_id: str, 
        time_range: Optional[Dict[str, datetime]] = None
    ) -> Dict[str, Any]:
        """Get comprehensive analytics summary for a program"""
        
        if not time_range:
            time_range = {
                "start": datetime.utcnow() - timedelta(days=30),
                "end": datetime.utcnow()
            }
        
        summary = {
            "program_id": program_id,
            "time_range": time_range,
            "generated_at": datetime.utcnow(),
            "analytics": {},
            "insights": [],
            "recommendations": []
        }
        
        # Collect analytics data
        for analytics_type in self.collectors.keys():
            try:
                storage_key = f"{analytics_type.value}_{program_id}"
                filters = {
                    "start_time": time_range["start"],
                    "end_time": time_range["end"],
                    "limit": 100
                }
                
                # Get appropriate storage backend
                if analytics_type == AnalyticsType.PERFORMANCE:
                    backend = self.storage_backends[StorageType.TIMESERIES]
                elif analytics_type in [AnalyticsType.EXECUTION, AnalyticsType.USER_JOURNEY]:
                    backend = self.storage_backends[StorageType.RELATIONAL]
                else:
                    backend = self.storage_backends[StorageType.DOCUMENT]
                
                data = await backend.retrieve(storage_key, filters)
                summary["analytics"][analytics_type.value] = {
                    "data_points": len(data),
                    "latest_data": data[-1] if data else None
                }
                
                # Add aggregations
                if data:
                    if analytics_type == AnalyticsType.PERFORMANCE:
                        agg_result = await backend.aggregate(storage_key, {"type": "avg", "field": "total_execution_time"})
                        summary["analytics"][analytics_type.value]["avg_execution_time"] = agg_result.get("result", 0)
                    elif analytics_type == AnalyticsType.USER_JOURNEY:
                        agg_result = await backend.aggregate(storage_key, {"type": "avg", "field": "average_engagement"})
                        summary["analytics"][analytics_type.value]["avg_engagement"] = agg_result.get("result", 0)
                
            except Exception as e:
                logger.error(f"Failed to retrieve analytics for {analytics_type}: {str(e)}")
        
        # Generate insights
        summary["insights"] = await self.generate_program_insights(program_id, time_range)
        
        # Generate recommendations based on insights
        summary["recommendations"] = self._generate_recommendations(summary["insights"])
        
        return summary
    
    def _generate_recommendations(self, insights: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable recommendations from insights"""
        
        recommendations = []
        
        for insight in insights:
            if insight.get("recommendation"):
                recommendations.append(insight["recommendation"])
        
        # Add general recommendations
        if any(i.get("type") == "performance_bottleneck" for i in insights):
            recommendations.append("Consider implementing caching for frequently executed steps")
        
        if any(i.get("type") == "low_engagement" for i in insights):
            recommendations.append("Review content personalization and personality consistency")
        
        return list(set(recommendations))  # Remove duplicates
    
    async def get_program_analytics(
        self, 
        creator_id: str, 
        program_id: str, 
        start_date: datetime, 
        end_date: datetime,
        analytics_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get program analytics data for a specific time period"""
        
        try:
            analytics_data = {
                "program_id": program_id,
                "creator_id": creator_id,
                "time_range": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "generated_at": datetime.utcnow().isoformat(),
                "analytics": {}
            }
            
            # Get data for specific analytics type or all types
            target_types = []
            if analytics_type:
                # Try to find matching analytics type
                for atype in AnalyticsType:
                    if atype.value == analytics_type:
                        target_types = [atype]
                        break
            else:
                target_types = list(AnalyticsType)
            
            for atype in target_types:
                try:
                    storage_key = f"{atype.value}_{program_id}"
                    
                    # Choose appropriate storage backend
                    if atype in [AnalyticsType.PERFORMANCE]:
                        backend = self.storage_backends[StorageType.TIMESERIES]
                    elif atype in [AnalyticsType.EXECUTION, AnalyticsType.USER_JOURNEY]:
                        backend = self.storage_backends[StorageType.RELATIONAL]
                    else:
                        backend = self.storage_backends[StorageType.DOCUMENT]
                    
                    # Retrieve data with time filtering
                    filters = {
                        "start_date": start_date,
                        "end_date": end_date,
                        "limit": 1000
                    }
                    
                    data = await backend.retrieve(storage_key, filters)
                    
                    # Process and aggregate data
                    if data:
                        analytics_data["analytics"][atype.value] = {
                            "total_records": len(data),
                            "data_points": data[:10],  # First 10 records as sample
                            "summary": await self._summarize_analytics_data(atype, data)
                        }
                    else:
                        analytics_data["analytics"][atype.value] = {
                            "total_records": 0,
                            "data_points": [],
                            "summary": {"message": "No data available for this time period"}
                        }
                        
                except Exception as e:
                    logger.error(f"Failed to retrieve {atype.value} analytics: {str(e)}")
                    analytics_data["analytics"][atype.value] = {
                        "error": str(e),
                        "total_records": 0,
                        "data_points": []
                    }
            
            return analytics_data
            
        except Exception as e:
            logger.error(f"Failed to get program analytics: {str(e)}")
            return {
                "program_id": program_id,
                "creator_id": creator_id,
                "error": str(e),
                "analytics": {}
            }
    
    async def _summarize_analytics_data(self, analytics_type: AnalyticsType, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize analytics data based on type"""
        
        if not data:
            return {"message": "No data to summarize"}
        
        summary = {}
        
        try:
            if analytics_type == AnalyticsType.EXECUTION:
                # Summarize execution data
                total_executions = len(data)
                successful = sum(1 for d in data if d.get("success_rate", 0) > 0.8)
                avg_success_rate = sum(d.get("success_rate", 0) for d in data) / total_executions
                avg_execution_time = sum(d.get("total_execution_time", 0) for d in data) / total_executions
                
                summary = {
                    "total_executions": total_executions,
                    "successful_executions": successful,
                    "success_percentage": (successful / total_executions) * 100,
                    "average_success_rate": avg_success_rate,
                    "average_execution_time_seconds": avg_execution_time
                }
                
            elif analytics_type == AnalyticsType.PERFORMANCE:
                # Summarize performance data
                avg_response_time = sum(d.get("average_response_time", 0) for d in data) / len(data)
                max_response_time = max(d.get("max_response_time", 0) for d in data)
                min_response_time = min(d.get("min_response_time", float('inf')) for d in data if d.get("min_response_time", float('inf')) != float('inf'))
                
                summary = {
                    "average_response_time_ms": avg_response_time,
                    "max_response_time_ms": max_response_time,
                    "min_response_time_ms": min_response_time if min_response_time != float('inf') else 0,
                    "total_performance_records": len(data)
                }
                
            elif analytics_type == AnalyticsType.USER_JOURNEY:
                # Summarize user journey data
                avg_engagement = sum(d.get("average_engagement", 0) for d in data) / len(data)
                total_users = len(set(d.get("user_id", "") for d in data if d.get("user_id")))
                
                summary = {
                    "average_engagement_score": avg_engagement,
                    "total_unique_users": total_users,
                    "total_journey_records": len(data)
                }
                
            elif analytics_type == AnalyticsType.PERSONALITY:
                # Summarize personality data
                avg_consistency = sum(d.get("personality_consistency_score", 0) for d in data) / len(data)
                
                summary = {
                    "average_personality_consistency": avg_consistency,
                    "total_personality_records": len(data)
                }
                
            else:
                summary = {
                    "total_records": len(data),
                    "data_type": analytics_type.value
                }
                
        except Exception as e:
            summary = {
                "error": f"Failed to summarize {analytics_type.value} data: {str(e)}",
                "total_records": len(data)
            }
        
        return summary
    
    def create_debug_session(self, program_id: str, user_id: str, debug_level: DebugLevel) -> str:
        """Create new debug session"""
        
        session_id = f"debug_{program_id}_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        trace = ExecutionTrace(
            trace_id=session_id,
            program_id=program_id,
            user_id=user_id,
            started_at=datetime.utcnow(),
            completed_at=None,
            events=[],
            metrics=[]
        )
        
        self.debug_sessions[session_id] = trace
        
        logger.info(f"Created debug session: {session_id}")
        return session_id
    
    def log_debug_event(
        self, 
        session_id: str, 
        event_type: str, 
        event_name: str, 
        data: Dict[str, Any],
        severity: str = "info"
    ):
        """Log debug event to session"""
        
        if session_id not in self.debug_sessions:
            logger.warning(f"Debug session not found: {session_id}")
            return
        
        event = DebugEvent(
            event_id=f"event_{len(self.debug_sessions[session_id].events)}",
            timestamp=datetime.utcnow(),
            event_type=event_type,
            event_name=event_name,
            data=data,
            severity=severity,
            session_id=session_id
        )
        
        self.debug_sessions[session_id].events.append(event)
        
        if severity == "error":
            self.debug_sessions[session_id].error_count += 1
        elif severity == "warning":
            self.debug_sessions[session_id].warning_count += 1
    
    def finalize_debug_session(self, session_id: str) -> Optional[ExecutionTrace]:
        """Finalize and return debug session"""
        
        if session_id not in self.debug_sessions:
            return None
        
        trace = self.debug_sessions[session_id]
        trace.completed_at = datetime.utcnow()
        
        # Store debug trace for later analysis
        asyncio.create_task(self.storage_backends[StorageType.DOCUMENT].store(
            asdict(trace), 
            f"debug_trace_{session_id}"
        ))
        
        logger.info(f"Finalized debug session: {session_id}")
        return trace
    
    async def start_debug_session(
        self, 
        creator_id: str, 
        program_id: str, 
        execution_type: str = "manual"
    ) -> str:
        """Start a new debug session"""
        
        session_id = f"debug_{creator_id}_{program_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        trace = ExecutionTrace(
            trace_id=session_id,
            program_id=program_id,
            user_id=creator_id,  # Using creator as user for debugging
            started_at=datetime.utcnow(),
            completed_at=None,
            events=[],
            metrics=[]
        )
        
        self.debug_sessions[session_id] = trace
        
        # Log initial event
        self.log_debug_event(
            session_id=session_id,
            event_type="session",
            event_name="debug_session_started",
            data={
                "creator_id": creator_id,
                "program_id": program_id,
                "execution_type": execution_type
            },
            severity="info"
        )
        
        logger.info(f"Started debug session: {session_id} for creator {creator_id}")
        return session_id
    
    async def list_debug_sessions(
        self, 
        creator_id: str, 
        program_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List debug sessions for a creator"""
        
        sessions = []
        
        for session_id, trace in self.debug_sessions.items():
            # Filter by creator and optionally by program
            if trace.user_id == creator_id:
                if program_id is None or trace.program_id == program_id:
                    sessions.append({
                        "session_id": session_id,
                        "program_id": trace.program_id,
                        "started_at": trace.started_at.isoformat() if trace.started_at else None,
                        "completed_at": trace.completed_at.isoformat() if trace.completed_at else None,
                        "status": "completed" if trace.completed_at else "active",
                        "total_events": len(trace.events),
                        "error_count": trace.error_count,
                        "warning_count": trace.warning_count,
                        "total_metrics": len(trace.metrics)
                    })
        
        # Sort by start time (most recent first)
        sessions.sort(key=lambda x: x["started_at"] if x["started_at"] else "", reverse=True)
        
        logger.info(f"Listed {len(sessions)} debug sessions for creator {creator_id}")
        return sessions
    
    async def get_debug_session(
        self, 
        creator_id: str, 
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get detailed debug session information"""
        
        if session_id not in self.debug_sessions:
            logger.warning(f"Debug session not found: {session_id}")
            return None
        
        trace = self.debug_sessions[session_id]
        
        # Verify creator has access to this session
        if trace.user_id != creator_id:
            logger.warning(f"Creator {creator_id} attempted to access debug session {session_id} owned by {trace.user_id}")
            return None
        
        session_details = {
            "session_id": session_id,
            "program_id": trace.program_id,
            "creator_id": trace.user_id,
            "started_at": trace.started_at.isoformat() if trace.started_at else None,
            "completed_at": trace.completed_at.isoformat() if trace.completed_at else None,
            "status": "completed" if trace.completed_at else "active",
            "total_events": len(trace.events),
            "error_count": trace.error_count,
            "warning_count": trace.warning_count,
            "total_metrics": len(trace.metrics),
            "events": [
                {
                    "event_id": event.event_id,
                    "timestamp": event.timestamp.isoformat() if event.timestamp else None,
                    "event_type": event.event_type,
                    "event_name": event.event_name,
                    "data": event.data,
                    "severity": event.severity
                } for event in trace.events
            ],
            "metrics": [
                {
                    "metric_name": metric.metric_name,
                    "metric_value": metric.metric_value,
                    "timestamp": metric.timestamp.isoformat() if metric.timestamp else None,
                    "unit": metric.unit,
                    "tags": metric.tags
                } for metric in trace.metrics
            ]
        }
        
        logger.info(f"Retrieved debug session details: {session_id}")
        return session_details


# ==================== GLOBAL ANALYTICS INSTANCE ====================

_analytics_system: Optional[AnalyticsSystem] = None
_debug_manager: Optional[DebugManager] = None


def get_analytics_system() -> AnalyticsSystem:
    """Get global analytics system instance"""
    global _analytics_system
    if _analytics_system is None:
        _analytics_system = AnalyticsSystem()
    return _analytics_system


def get_debug_manager() -> AnalyticsSystem:
    """Get global debug manager instance (same as analytics system)"""
    # Debug functionality is integrated into AnalyticsSystem
    return get_analytics_system()


# ==================== UTILITY FUNCTIONS ====================

async def analyze_program_performance(program_id: str, days: int = 7) -> Dict[str, Any]:
    """Utility function to analyze program performance"""
    
    analytics = get_analytics_system()
    time_range = {
        "start": datetime.utcnow() - timedelta(days=days),
        "end": datetime.utcnow()
    }
    
    return await analytics.get_program_analytics_summary(program_id, time_range)


async def get_program_insights(program_id: str, days: int = 7) -> List[Dict[str, Any]]:
    """Utility function to get program insights"""
    
    analytics = get_analytics_system()
    time_range = {
        "start": datetime.utcnow() - timedelta(days=days),
        "end": datetime.utcnow()
    }
    
    return await analytics.generate_program_insights(program_id, time_range)