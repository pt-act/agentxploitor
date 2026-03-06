"""
Structured Logging Configuration

Provides JSON-structured logging with correlation IDs for
log aggregation and debugging.
"""

import json
import logging
import sys
import uuid
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from contextvars import ContextVar
from functools import wraps
from logging import LogRecord
from logging.handlers import RotatingFileHandler

try:
    from pythonjsonlogger import jsonlogger

    JSON_LOGGER_AVAILABLE = True
except ImportError:
    JSON_LOGGER_AVAILABLE = False

from dataclasses import dataclass, field
from enum import Enum


_correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
_workspace_id: ContextVar[Optional[str]] = ContextVar("workspace_id", default=None)
_user_id: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
_job_id: ContextVar[Optional[str]] = ContextVar("job_id", default=None)


class LogLevel(str, Enum):
    """Log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogContext:
    """Additional context for logging."""

    correlation_id: Optional[str] = None
    workspace_id: Optional[str] = None
    user_id: Optional[str] = None
    job_id: Optional[str] = None
    request_id: Optional[str] = None
    session_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.correlation_id:
            result["correlation_id"] = self.correlation_id
        if self.workspace_id:
            result["workspace_id"] = self.workspace_id
        if self.user_id:
            result["user_id"] = self.user_id
        if self.job_id:
            result["job_id"] = self.job_id
        if self.request_id:
            result["request_id"] = self.request_id
        if self.session_id:
            result["session_id"] = self.session_id
        return result


class StructuredLogFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""

    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: LogRecord,
        message_dict: Dict[str, Any],
    ):
        super().add_fields(log_record, record, message_dict)

        log_record["timestamp"] = datetime.now(timezone.utc).isoformat()
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["message"] = record.getMessage()
        log_record["module"] = record.module
        log_record["function"] = record.funcName
        log_record["line"] = record.lineno

        ctx = get_log_context()
        if ctx.correlation_id:
            log_record["correlation_id"] = ctx.correlation_id
        if ctx.workspace_id:
            log_record["workspace_id"] = ctx.workspace_id
        if ctx.user_id:
            log_record["user_id"] = ctx.user_id
        if ctx.job_id:
            log_record["job_id"] = ctx.job_id

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        thread_name = getattr(record, "threadName", None)
        if thread_name:
            log_record["thread"] = thread_name

        process_name = getattr(record, "processName", None)
        if process_name:
            log_record["process"] = process_name


class StructuredLogger:
    """
    Structured logger with correlation ID support.

    Usage:
        logger = get_structured_logger(__name__)
        logger.info("Processing job", extra={"job_id": "123"})

        with correlation_id("abc-123"):
            logger.info("Job started")
    """

    def __init__(self, name: str, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level))
        self.logger.propagate = False

    def _log(
        self,
        level: str,
        message: str,
        extra: Dict[str, Any] = None,
        exc_info: bool = False,
    ):
        extra = extra or {}

        extra["correlation_id"] = _correlation_id.get() or extra.get("correlation_id")
        extra["workspace_id"] = _workspace_id.get() or extra.get("workspace_id")
        extra["user_id"] = _user_id.get() or extra.get("user_id")
        extra["job_id"] = _job_id.get() or extra.get("job_id")

        getattr(self.logger, level.lower())(
            message,
            extra=extra,
            exc_info=exc_info,
        )

    def debug(self, message: str, **kwargs):
        self._log("DEBUG", message, **kwargs)

    def info(self, message: str, **kwargs):
        self._log("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs):
        self._log("WARNING", message, **kwargs)

    def error(self, message: str, exc_info: bool = False, **kwargs):
        self._log("ERROR", message, exc_info=exc_info, **kwargs)

    def critical(self, message: str, exc_info: bool = False, **kwargs):
        self._log("CRITICAL", message, exc_info=exc_info, **kwargs)

    def exception(self, message: str, **kwargs):
        self.error(message, exc_info=True, **kwargs)

    def log_job(self, job_id: str, action: str, **kwargs):
        """Log with job context."""
        self.info(
            f"[{action}] Job {job_id}",
            extra={"job_id": job_id, "action": action},
            **kwargs,
        )

    def log_audit(self, workspace_id: str, action: str, **kwargs):
        """Log with audit context."""
        self.info(
            f"[{action}] Audit",
            extra={"workspace_id": workspace_id, "action": action},
            **kwargs,
        )


def setup_logging(
    level: str = "INFO",
    json_format: bool = True,
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> None:
    """
    Setup structured logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Use JSON format for logs
        log_file: Optional file path for log output
        max_bytes: Max size of log file before rotation
        backup_count: Number of backup files to keep
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level))

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    if json_format and JSON_LOGGER_AVAILABLE:
        formatter = StructuredLogFormatter(
            "%(timestamp)s %(level)s %(name)s %(message)s",
            rename_fields={"level": "severity", "message": "msg"},
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    if log_file:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    logging.getLogger("agentxploitor").setLevel(getattr(logging, level))

    logging.info(
        f"Logging initialized: format={'json' if json_format else 'text'}, level={level}"
    )


def get_structured_logger(name: str, level: str = "INFO") -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(name, level)


def get_correlation_id() -> Optional[str]:
    """Get the current correlation ID."""
    return _correlation_id.get()


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID for the current context."""
    _correlation_id.set(correlation_id)


def get_log_context() -> LogContext:
    """Get the current log context."""
    return LogContext(
        correlation_id=_correlation_id.get(),
        workspace_id=_workspace_id.get(),
        user_id=_user_id.get(),
        job_id=_job_id.get(),
    )


@contextmanager
def correlation_id(cid: Optional[str] = None):
    """Context manager for setting correlation ID."""
    if cid is None:
        cid = str(uuid.uuid4())

    token = _correlation_id.set(cid)
    try:
        yield cid
    finally:
        _correlation_id.reset(token)


@contextmanager
def workspace_context(workspace_id: str):
    """Context manager for setting workspace ID."""
    token = _workspace_id.set(workspace_id)
    try:
        yield workspace_id
    finally:
        _workspace_id.reset(token)


@contextmanager
def user_context(user_id: str):
    """Context manager for setting user ID."""
    token = _user_id.set(user_id)
    try:
        yield user_id
    finally:
        _user_id.reset(token)


@contextmanager
def job_context(job_id: str):
    """Context manager for setting job ID."""
    token = _job_id.set(job_id)
    try:
        yield job_id
    finally:
        _job_id.reset(token)


@contextmanager
def log_context(**kwargs):
    """Context manager for setting multiple context values."""
    tokens = {}

    if "correlation_id" in kwargs:
        tokens["correlation_id"] = _correlation_id.set(kwargs["correlation_id"])
    if "workspace_id" in kwargs:
        tokens["workspace_id"] = _workspace_id.set(kwargs["workspace_id"])
    if "user_id" in kwargs:
        tokens["user_id"] = _user_id.set(kwargs["user_id"])
    if "job_id" in kwargs:
        tokens["job_id"] = _job_id.set(kwargs["job_id"])

    try:
        yield
    finally:
        for var, token in tokens.items():
            if var == "correlation_id":
                _correlation_id.reset(token)
            elif var == "workspace_id":
                _workspace_id.reset(token)
            elif var == "user_id":
                _user_id.reset(token)
            elif var == "job_id":
                _job_id.reset(token)


def trace_function(func):
    """Decorator to add trace context to function calls."""

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        cid = get_correlation_id() or str(uuid.uuid4())
        with correlation_id(cid):
            logger = get_structured_logger(func.__module__)
            logger.debug(f"Calling {func.__name__}", extra={"function": func.__name__})
            try:
                result = await func(*args, **kwargs)
                logger.debug(f"Completed {func.__name__}")
                return result
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
                raise

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        cid = get_correlation_id() or str(uuid.uuid4())
        with correlation_id(cid):
            logger = get_structured_logger(func.__module__)
            logger.debug(f"Calling {func.__name__}", extra={"function": func.__name__})
            try:
                result = func(*args, **kwargs)
                logger.debug(f"Completed {func.__name__}")
                return result
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
                raise

    import asyncio

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper
