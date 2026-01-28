"""Structured logging utility for CloudWatch integration."""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

import structlog


class CloudWatchJSONFormatter(logging.Formatter):
    """Custom formatter for CloudWatch Logs with JSON output."""

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add correlation ID if present
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id

        # Add execution ID if present
        if hasattr(record, "execution_id"):
            log_data["execution_id"] = record.execution_id

        # Add any extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class RulesEngineLogger:
    """Structured logger for Rules Engine Framework."""

    def __init__(
        self,
        name: str,
        log_level: str = "INFO",
        correlation_id: Optional[str] = None,
        execution_id: Optional[str] = None,
    ):
        """
        Initialize the logger.

        Args:
            name: Logger name (typically module name)
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            correlation_id: Optional correlation ID for request tracing
            execution_id: Optional execution ID for validation runs
        """
        self.name = name
        self.correlation_id = correlation_id or str(uuid4())
        self.execution_id = execution_id

        # Configure structlog
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(
                logging.getLevelName(log_level)
            ),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )

        self.logger = structlog.get_logger(name)

    def _add_context(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Add context to log entries.

        Args:
            **kwargs: Additional context fields

        Returns:
            Dictionary with context fields
        """
        context = {
            "correlation_id": self.correlation_id,
        }
        if self.execution_id:
            context["execution_id"] = self.execution_id
        context.update(kwargs)
        return context

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self.logger.debug(message, **self._add_context(**kwargs))

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self.logger.info(message, **self._add_context(**kwargs))

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self.logger.warning(message, **self._add_context(**kwargs))

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self.logger.error(message, **self._add_context(**kwargs))

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message."""
        self.logger.critical(message, **self._add_context(**kwargs))

    def exception(self, message: str, exc: Exception, **kwargs: Any) -> None:
        """
        Log exception with traceback.

        Args:
            message: Log message
            exc: Exception instance
            **kwargs: Additional context
        """
        self.logger.error(
            message,
            exc_info=exc,
            exception_type=type(exc).__name__,
            exception_message=str(exc),
            **self._add_context(**kwargs),
        )


def get_logger(
    name: str,
    log_level: str = "INFO",
    correlation_id: Optional[str] = None,
    execution_id: Optional[str] = None,
) -> RulesEngineLogger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name
        log_level: Logging level
        correlation_id: Optional correlation ID
        execution_id: Optional execution ID

    Returns:
        Configured logger instance
    """
    return RulesEngineLogger(name, log_level, correlation_id, execution_id)


def setup_cloudwatch_logging(
    log_group_name: str,
    log_level: str = "INFO",
    stream_name: Optional[str] = None,
) -> logging.Logger:
    """
    Set up CloudWatch logging handler.

    Args:
        log_group_name: CloudWatch log group name
        log_level: Logging level
        stream_name: Optional stream name (defaults to timestamp-based)

    Returns:
        Configured logger
    """
    logger = logging.getLogger(log_group_name)
    logger.setLevel(getattr(logging, log_level.upper()))

    # Create CloudWatch handler (requires boto3)
    try:
        import boto3

        client = boto3.client("logs")
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(CloudWatchJSONFormatter())
        logger.addHandler(handler)
    except ImportError:
        # Fallback to standard handler if boto3 not available
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(CloudWatchJSONFormatter())
        logger.addHandler(handler)

    return logger
