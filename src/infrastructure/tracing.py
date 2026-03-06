"""
Distributed Tracing

Provides OpenTelemetry tracing for distributed system observability.
"""

import uuid
import logging
from typing import Optional, Dict, Any, Callable
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from functools import wraps
import time

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider, SpanProcessor
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
        SimpleSpanProcessor,
    )
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.prometheus import PrometheusMetricsExporter
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME
    from opentelemetry.trace import Status, StatusCode, SpanKind
    from opentelemetry.instrumentation.aiohttp import AioHttpInstrumentor
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    from opentelemetry.propagate import inject, extract, set_global_textmap
    from opentelemetry.propagators.b3 import B3Propagator

    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    trace = None
    StatusCode = None
    Status = None
    SpanKind = None

from infrastructure.config import get_config

logger = logging.getName(__name__)


_tracer_provider: Optional[Any] = None
_tracer: Optional[Any] = None


@dataclass
class TraceContext:
    """Trace context for propagating across service boundaries."""

    trace_id: str = ""
    span_id: str = ""
    parent_span_id: str = ""
    baggage: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, str]:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            **self.baggage,
        }


class TracingConfig:
    """Configuration for tracing."""

    def __init__(self):
        self.enabled = True
        self.service_name = "agentxploitor"
        self.export_console = False
        self.export_otlp = False
        self.otlp_endpoint = "http://localhost:4317"
        self.sample_rate = 1.0
        self.propagators = ["b3"]

    @classmethod
    def from_config(cls, config: Any = None) -> "TracingConfig":
        """Create from application config."""
        cfg = cls()
        if config:
            cfg.enabled = getattr(config, "tracing_enabled", True)
            cfg.service_name = getattr(config, "service_name", "agentxploitor")
            cfg.export_console = getattr(config, "tracing_export_console", False)
            cfg.export_otlp = getattr(config, "tracing_export_otlp", False)
            cfg.otlp_endpoint = getattr(
                config, "tracing_otlp_endpoint", cfg.otlp_endpoint
            )
            cfg.sample_rate = getattr(config, "tracing_sample_rate", 1.0)
        return cfg


def init_tracing(config: Optional[TracingConfig] = None) -> None:
    """Initialize the tracing provider."""
    global _tracer_provider, _tracer

    if not OPENTELEMETRY_AVAILABLE:
        logger.warning("OpenTelemetry not installed, tracing disabled")
        return

    config = config or TracingConfig()

    resource = Resource.create(
        {
            SERVICE_NAME: config.service_name,
            "service.version": "2.0.0",
            "deployment.environment": "production",
        }
    )

    provider = TracerProvider(resource=resource)

    if config.export_console:
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    if config.export_otlp:
        try:
            otlp_exporter = OTLPSpanExporter(endpoint=config.otlp_endpoint)
            provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        except Exception as e:
            logger.error(f"Failed to setup OTLP exporter: {e}")

    trace.set_tracer_provider(provider)

    _tracer_provider = provider
    _tracer = trace.get_tracer(__name__)

    set_global_textmap(B3Propagator())

    _setup_instrumentation()

    logger.info(f"Tracing initialized: service={config.service_name}")


def _setup_instrumentation() -> None:
    """Setup auto-instrumentation for common libraries."""
    if not OPENTELEMETRY_AVAILABLE:
        return

    try:
        AioHttpInstrumentor().instrument()
    except Exception as e:
        logger.debug(f"Failed to instrument aiohttp: {e}")

    try:
        RedisInstrumentor().instrument()
    except Exception as e:
        logger.debug(f"Failed to instrument redis: {e}")


def get_tracer(name: str = None):
    """Get a tracer instance."""
    global _tracer
    if _tracer is None:
        if OPENTELEMETRY_AVAILABLE:
            _tracer = trace.get_tracer(name or __name__)
        else:
            return None
    return _tracer


def get_current_span() -> Optional[Any]:
    """Get the current active span."""
    if not OPENTELEMETRY_AVAILABLE:
        return None
    return trace.get_current_span()


def get_trace_id() -> str:
    """Get the current trace ID as hex string."""
    span = get_current_span()
    if span and OPENTELEMETRY_AVAILABLE:
        return format(span.get_span_context().trace_id, "032x")
    return ""


def get_span_id() -> str:
    """Get the current span ID as hex string."""
    span = get_current_span()
    if span and OPENTELEMETRY_AVAILABLE:
        return format(span.get_span_context().span_id, "016x")
    return ""


def start_span(
    name: str,
    kind: str = "internal",
    attributes: Optional[Dict[str, Any]] = None,
) -> Any:
    """
    Start a new span.

    Args:
        name: Span name
        kind: Span kind (internal, server, client, producer, consumer)
        attributes: Initial attributes

    Returns:
        Context manager for the span
    """
    tracer = get_tracer()
    if not tracer or not OPENTELEMETRY_AVAILABLE:
        return _NoOpSpan()

    kind_map = {
        "internal": SpanKind.INTERNAL,
        "server": SpanKind.SERVER,
        "client": SpanKind.CLIENT,
        "producer": SpanKind.PRODUCER,
        "consumer": SpanKind.CONSUMER,
    }

    span_kind = kind_map.get(kind, SpanKind.INTERNAL)

    with tracer.start_as_current_span(name, kind=span_kind) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, str(value))

        yield span


def trace_async_function(
    name: str = None,
    attributes: Optional[Dict[str, Any]] = None,
):
    """Decorator to trace an async function."""

    def decorator(func: Callable):
        span_name = name or func.__name__

        @wraps(func)
        async def wrapper(*args, **kwargs):
            tracer = get_tracer()
            if not tracer or not OPENTELEMETRY_AVAILABLE:
                return await func(*args, **kwargs)

            with tracer.start_as_current_span(span_name) as span:
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, str(value))

                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)

                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        return wrapper

    return decorator


def trace_sync_function(
    name: str = None,
    attributes: Optional[Dict[str, Any]] = None,
):
    """Decorator to trace a sync function."""

    def decorator(func: Callable):
        span_name = name or func.__name__

        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            if not tracer or not OPENTELEMETRY_AVAILABLE:
                return func(*args, **kwargs)

            with tracer.start_as_current_span(span_name) as span:
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, str(value))

                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)

                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        return wrapper

    return decorator


def add_span_attribute(key: str, value: Any) -> None:
    """Add an attribute to the current span."""
    span = get_current_span()
    if span and OPENTELEMETRY_AVAILABLE:
        span.set_attribute(key, str(value))


def add_span_event(name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
    """Add an event to the current span."""
    span = get_current_span()
    if span and OPENTELEMETRY_AVAILABLE:
        span.add_event(name, attributes=attributes or {})


def record_exception(
    error: Exception, attributes: Optional[Dict[str, Any]] = None
) -> None:
    """Record an exception on the current span."""
    span = get_current_span()
    if span and OPENTELEMETRY_AVAILABLE:
        span.record_exception(error)
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, str(value))


def inject_trace_context() -> Dict[str, str]:
    """Inject trace context into carrier for propagation."""
    if not OPENTELEMETRY_AVAILABLE:
        return {}

    carrier = {}
    inject(carrier)
    return carrier


def extract_trace_context(carrier: Dict[str, str]) -> None:
    """Extract trace context from carrier."""
    if not OPENTELEMETRY_AVAILABLE:
        return

    if carrier:
        extract(carrier)


class _NoOpSpan:
    """No-op span for when tracing is disabled."""

    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def set_attribute(self, key: str, value: Any):
        pass

    def add_event(self, name: str, attributes: Dict[str, Any] = None):
        pass

    def set_status(self, status):
        pass

    def record_exception(self, error: Exception):
        pass


class TracingMiddleware:
    """Middleware for adding tracing to request handlers."""

    def __init__(self, app=None):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            headers = dict(scope.get("headers", []))
            headers = {k.decode(): v.decode() for k, v in headers.items()}

            extract_trace_context(headers)

            span = get_current_span()
            if span and OPENTELEMETRY_AVAILABLE:
                span.set_attribute("http.method", scope.get("method", ""))
                span.set_attribute("http.url", scope.get("path", ""))
                span.set_attribute("http.scheme", scope.get("scheme", ""))

        if self.app:
            await self.app(scope, receive, send)


def create_trace_context() -> TraceContext:
    """Create a new trace context."""
    return TraceContext(
        trace_id=get_trace_id(),
        span_id=get_span_id(),
    )
