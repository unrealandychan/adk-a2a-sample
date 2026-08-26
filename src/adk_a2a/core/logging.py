"""Structured logging and correlation tracking for Harness Engineering observability."""

import logging
import sys
import uuid
from contextvars import ContextVar

# Correlation ID context for distributed request/agent tracing
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    """Gets the current correlation ID or generates a new one."""
    cid = correlation_id_ctx.get()
    if not cid:
        cid = str(uuid.uuid4())
        correlation_id_ctx.set(cid)
    return cid


def set_correlation_id(correlation_id: str) -> None:
    """Explicitly sets the correlation ID in context."""
    correlation_id_ctx.set(correlation_id)


class CorrelationFilter(logging.Filter):
    """Logging filter that injects the active correlation_id into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.__dict__["correlation_id"] = get_correlation_id()
        return True


def configure_logging(level: str = "INFO") -> None:
    """Configures application-wide structured logging format with correlation ID."""
    log_format = "%(asctime)s [%(levelname)s] [corr_id=%(correlation_id)s] %(name)s: %(message)s"
    formatter = logging.Formatter(log_format)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(CorrelationFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level.upper())
    # Avoid duplicate handlers on re-configuration
    root_logger.handlers.clear()
    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Creates a configured logger with correlation filter."""
    logger = logging.getLogger(name)
    return logger
