"""
Prometheus Metrics

Provides comprehensive metrics collection for monitoring system health,
job processing, and business KPIs.
"""

import time
from typing import Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime

try:
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        Info,
        generate_latest,
        CONTENT_TYPE_LATEST,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

from infrastructure.config import get_config

logger = __name__


@dataclass
class MetricLabels:
    """Labels for metrics."""

    job_status: Optional[str] = None
    analyzer: Optional[str] = None
    workspace_id: Optional[str] = None
    priority: Optional[str] = None
    error_type: Optional[str] = None


class MetricsCollector:
    """
    Central metrics collector for AgentxploiTor.

    Provides:
    - Job metrics (latency, throughput, errors)
    - Queue metrics (depth, processing time)
    - Analyzer metrics (scan time, findings count)
    - Business KPIs (audits completed, costs)
    """

    VERSION = "1.0.0"

    def __init__(self):
        if not PROMETHEUS_AVAILABLE:
            logger.warning("prometheus-client not installed, metrics disabled")
            return

        self._setup_job_metrics()
        self._setup_queue_metrics()
        self._setup_analyzer_metrics()
        self._setup_business_metrics()
        self._setup_system_metrics()

    def _setup_job_metrics(self):
        """Setup job-related metrics."""
        self.jobs_total = Counter(
            "agentxploitor_jobs_total",
            "Total number of jobs processed",
            ["status", "priority", "workspace_id"],
        )

        self.job_latency = Histogram(
            "agentxploitor_job_latency_seconds",
            "Job processing latency in seconds",
            ["status", "priority"],
            buckets=[1, 5, 10, 30, 60, 120, 300, 600, 1800],
        )

        self.job_duration = Histogram(
            "agentxploitor_job_duration_seconds",
            "Total job duration from creation to completion",
            ["status"],
            buckets=[10, 30, 60, 120, 300, 600, 1800, 3600, 7200],
        )

    def _setup_queue_metrics(self):
        """Setup queue-related metrics."""
        self.queue_depth = Gauge(
            "agentxploitor_queue_depth",
            "Current number of jobs in queue",
            ["priority"],
        )

        self.processing_jobs = Gauge(
            "agentxploitor_processing_jobs",
            "Number of jobs currently being processed",
        )

        self.queue_wait_time = Histogram(
            "agentxploitor_queue_wait_seconds",
            "Time jobs spend waiting in queue",
            buckets=[0.1, 0.5, 1, 5, 10, 30, 60, 120],
        )

    def _setup_analyzer_metrics(self):
        """Setup analyzer-related metrics."""
        self.analyzer_runs = Counter(
            "agentxploitor_analyzer_runs_total",
            "Total number of analyzer runs",
            ["analyzer", "result"],
        )

        self.analyzer_duration = Histogram(
            "agentxploitor_analyzer_duration_seconds",
            "Analyzer execution duration",
            ["analyzer"],
            buckets=[1, 5, 10, 30, 60, 120, 300],
        )

        self.findings_count = Histogram(
            "agentxploitor_findings_count",
            "Number of findings per audit",
            ["severity"],
            buckets=[0, 1, 3, 5, 10, 20, 50],
        )

    def _setup_business_metrics(self):
        """Setup business KPI metrics."""
        self.audits_completed = Counter(
            "agentxploitor_audits_completed_total",
            "Total number of completed audits",
            ["workspace_id"],
        )

        self.audit_cost = Histogram(
            "agentxploitor_audit_cost_dollars",
            "Cost per audit in dollars",
            ["workspace_id"],
            buckets=[0.01, 0.05, 0.1, 0.5, 1, 5, 10, 50, 100],
        )

        self.api_calls = Counter(
            "agentxploitor_api_calls_total",
            "Total API calls to external services",
            ["service", "status"],
        )

        self.llm_tokens = Counter(
            "agentxploitor_llm_tokens_total",
            "Total LLM tokens used",
            ["model", "type"],
        )

    def _setup_system_metrics(self):
        """Setup system information metrics."""
        self.app_info = Info(
            "agentxploitor",
            "AgentxploiTor application information",
        )

        self.active_workers = Gauge(
            "agentxploitor_active_workers",
            "Number of active worker processes",
        )

        self.circuit_breaker_state = Gauge(
            "agentxploitor_circuit_breaker_state",
            "Circuit breaker state (0=closed, 1=half-open, 2=open)",
            ["service"],
        )

    def record_job_completed(
        self,
        status: str,
        priority: str,
        workspace_id: str,
        duration: float,
    ):
        """Record a completed job."""
        if not PROMETHEUS_AVAILABLE:
            return

        self.jobs_total.labels(
            status=status,
            priority=priority,
            workspace_id=workspace_id,
        ).inc()

        self.job_latency.labels(
            status=status,
            priority=priority,
        ).observe(duration)

        self.job_duration.labels(status=status).observe(duration)

        if status == "completed":
            self.audits_completed.labels(workspace_id=workspace_id).inc()

    def record_job_queued(self, priority: str):
        """Record a job being queued."""
        if not PROMETHEUS_AVAILABLE:
            return
        self.queue_depth.labels(priority=priority).inc()

    def record_job_dequeued(self, priority: str, wait_time: float):
        """Record a job being dequeued."""
        if not PROMETHEUS_AVAILABLE:
            return
        self.queue_depth.labels(priority=priority).dec()
        self.queue_wait_time.observe(wait_time)

    def record_analyzer_run(
        self,
        analyzer: str,
        result: str,
        duration: float,
        findings: int,
    ):
        """Record an analyzer execution."""
        if not PROMETHEUS_AVAILABLE:
            return

        self.analyzer_runs.labels(
            analyzer=analyzer,
            result=result,
        ).inc()

        self.analyzer_duration.labels(analyzer=analyzer).observe(duration)

        if findings > 0:
            severity = (
                "critical" if findings > 3 else "high" if findings > 1 else "medium"
            )
            self.findings_count.labels(severity=severity).observe(findings)

    def record_api_call(self, service: str, status: str):
        """Record an API call to external service."""
        if not PROMETHEUS_AVAILABLE:
            return
        self.api_calls.labels(service=service, status=status).inc()

    def record_llm_usage(self, model: str, token_type: str, tokens: int):
        """Record LLM token usage."""
        if not PROMETHEUS_AVAILABLE:
            return
        self.llm_tokens.labels(model=model, type=token_type).inc(tokens)

    def record_audit_cost(self, workspace_id: str, cost: float):
        """Record the cost of an audit."""
        if not PROMETHEUS_AVAILABLE:
            return
        self.audit_cost.labels(workspace_id=workspace_id).observe(cost)

    def update_queue_depth(self, priority: str, depth: int):
        """Update the current queue depth."""
        if not PROMETHEUS_AVAILABLE:
            return
        self.queue_depth.labels(priority=priority).set(depth)

    def update_processing_jobs(self, count: int):
        """Update the number of processing jobs."""
        if not PROMETHEUS_AVAILABLE:
            return
        self.processing_jobs.set(count)

    def update_circuit_breaker(self, service: str, state: str):
        """Update circuit breaker state (0=closed, 1=half-open, 2=open)."""
        if not PROMETHEUS_AVAILABLE:
            return

        state_map = {"closed": 0, "half_open": 1, "open": 2}
        self.circuit_breaker_state.labels(service=service).set(state_map.get(state, 0))

    def set_active_workers(self, count: int):
        """Set the number of active workers."""
        if not PROMETHEUS_AVAILABLE:
            return
        self.active_workers.set(count)

    def set_app_info(self, version: str = None):
        """Set application information."""
        if not PROMETHEUS_AVAILABLE:
            return
        version = version or self.VERSION
        self.app_info.info({"version": version})

    def generate_metrics(self) -> bytes:
        """Generate Prometheus metrics in text format."""
        if not PROMETHEUS_AVAILABLE:
            return b"# Metrics disabled - prometheus-client not installed"
        return generate_latest()

    def get_content_type(self) -> str:
        """Get the content type for Prometheus metrics."""
        return CONTENT_TYPE_LATEST


_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def record_job_completed(**kwargs):
    """Convenience function to record job completion."""
    get_metrics_collector().record_job_completed(**kwargs)


def record_analyzer_run(**kwargs):
    """Convenience function to record analyzer run."""
    get_metrics_collector().record_analyzer_run(**kwargs)


def record_api_call(**kwargs):
    """Convenience function to record API call."""
    get_metrics_collector().record_api_call(**kwargs)
