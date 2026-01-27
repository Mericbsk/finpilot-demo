"""
FinPilot Structured Logging
===========================

Merkezi logging altyapısı:
- Structured JSON logging
- Context-aware logging
- Performance timing
- Error tracking

Kullanım:
    from core.logging import get_logger, log_context

    logger = get_logger(__name__)

    logger.info("Starting scan", extra={"tickers": 500})

    with log_context(operation="backtest", ticker="AAPL"):
        logger.info("Running backtest")

Author: FinPilot Team
Version: 1.0.0
"""

from __future__ import annotations

import functools
import json
import logging
import sys
import threading
import time
from contextvars import ContextVar
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional, ParamSpec, TypeVar

P = ParamSpec("P")
T = TypeVar("T")

# =============================================================================
# CONTEXT MANAGEMENT
# =============================================================================

# Thread-local context for structured logging
_log_context: ContextVar[dict[str, Any]] = ContextVar("log_context", default={})


class LogContext:
    """
    Context manager for adding structured context to logs.

    Usage:
        with LogContext(request_id="abc123", user_id=42):
            logger.info("Processing request")  # Includes request_id and user_id
    """

    def __init__(self, **kwargs: Any):
        self.new_context = kwargs
        self.old_context: dict[str, Any] = {}

    def __enter__(self) -> "LogContext":
        self.old_context = _log_context.get().copy()
        new = {**self.old_context, **self.new_context}
        _log_context.set(new)
        return self

    def __exit__(self, *args: Any) -> None:
        _log_context.set(self.old_context)


def log_context(**kwargs: Any) -> LogContext:
    """Create a log context."""
    return LogContext(**kwargs)


def get_context() -> dict[str, Any]:
    """Get current log context."""
    return _log_context.get().copy()


def set_context(**kwargs: Any) -> None:
    """Set log context values."""
    current = _log_context.get().copy()
    current.update(kwargs)
    _log_context.set(current)


def clear_context() -> None:
    """Clear all log context."""
    _log_context.set({})


# =============================================================================
# JSON FORMATTER
# =============================================================================


class JSONFormatter(logging.Formatter):
    """
    JSON log formatter for structured logging.

    Output format:
    {
        "timestamp": "2025-01-25T12:00:00.000Z",
        "level": "INFO",
        "logger": "scanner",
        "message": "Scanning complete",
        "context": {"tickers": 500, "duration": 1.23}
    }
    """

    def __init__(
        self,
        include_traceback: bool = True,
        timestamp_format: str = "%Y-%m-%dT%H:%M:%S.%f",
    ):
        super().__init__()
        self.include_traceback = include_traceback
        self.timestamp_format = timestamp_format

    def format(self, record: logging.LogRecord) -> str:
        # Base log entry
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().strftime(self.timestamp_format)[:-3] + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add context from ContextVar
        context = get_context()
        if context:
            log_entry["context"] = context

        # Add extra fields
        extra: Dict[str, Any] = {}
        for key, value in record.__dict__.items():
            if key not in (
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "exc_info",
                "exc_text",
                "thread",
                "threadName",
                "message",
                "taskName",
            ):
                extra[key] = value

        if extra:
            if "context" in log_entry and isinstance(log_entry["context"], dict):
                log_entry["context"].update(extra)
            else:
                log_entry["context"] = extra

        # Add source location
        log_entry["source"] = {
            "file": record.filename,
            "line": record.lineno,
            "function": record.funcName,
        }

        # Add exception info
        if record.exc_info and self.include_traceback:
            import traceback

            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info),
            }

        return json.dumps(log_entry, default=str)


# =============================================================================
# TEXT FORMATTER
# =============================================================================


class ColoredTextFormatter(logging.Formatter):
    """
    Colored text formatter for development.

    Output: 2025-01-25 12:00:00 | INFO | scanner | Scanning complete | tickers=500
    """

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def __init__(self, use_colors: bool = True):
        super().__init__()
        self.use_colors = use_colors

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname

        # Colorize level
        if self.use_colors and level in self.COLORS:
            level = f"{self.COLORS[level]}{level}{self.RESET}"

        # Format message
        msg = record.getMessage()

        # Add context
        context_parts = []
        context = get_context()
        if context:
            context_parts.extend(f"{k}={v}" for k, v in context.items())

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in (
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "exc_info",
                "exc_text",
                "thread",
                "threadName",
                "message",
                "taskName",
            ):
                context_parts.append(f"{key}={value}")

        context_str = " | " + ", ".join(context_parts) if context_parts else ""

        # Build log line
        log_line = f"{timestamp} | {level:8} | {record.name:20} | {msg}{context_str}"

        # Add exception
        if record.exc_info:
            import traceback

            log_line += "\n" + "".join(traceback.format_exception(*record.exc_info))

        return log_line


# =============================================================================
# LOGGER CONFIGURATION
# =============================================================================

_loggers: dict[str, logging.Logger] = {}
_configured = False


def configure_logging(
    level: str = "INFO",
    format: str = "json",  # "json" or "text"
    log_file: Optional[str] = None,
    use_colors: bool = True,
) -> None:
    """
    Configure root logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Output format ("json" or "text")
        log_file: Optional file path for log output
        use_colors: Use colored output for text format
    """
    global _configured

    # Get root logger
    root_logger = logging.getLogger("finpilot")
    root_logger.setLevel(getattr(logging, level.upper()))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Choose formatter
    if format == "json":
        formatter = JSONFormatter()
    else:
        formatter = ColoredTextFormatter(use_colors=use_colors)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(JSONFormatter())  # Always JSON for files
        root_logger.addHandler(file_handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    Usage:
        logger = get_logger(__name__)
        logger.info("Message", extra={"key": "value"})
    """
    global _configured

    # Auto-configure with defaults if not configured
    if not _configured:
        try:
            from core.config import settings

            configure_logging(
                level=settings.monitoring.log_level,
                format=settings.monitoring.log_format,
                log_file=settings.monitoring.log_file,
            )
        except ImportError:
            configure_logging()

    # Use finpilot namespace
    if not name.startswith("finpilot"):
        name = f"finpilot.{name}"

    if name not in _loggers:
        _loggers[name] = logging.getLogger(name)

    return _loggers[name]


# =============================================================================
# LOGGING DECORATORS
# =============================================================================


def log_call(
    level: str = "DEBUG",
    log_args: bool = True,
    log_result: bool = False,
    log_time: bool = True,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator to log function calls.

    Args:
        level: Log level for the messages
        log_args: Include function arguments in log
        log_result: Include function result in log
        log_time: Include execution time in log

    Usage:
        @log_call(level="INFO", log_time=True)
        def process_data(ticker: str) -> pd.DataFrame:
            ...
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        logger = get_logger(func.__module__)
        log_level = getattr(logging, level.upper())

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            start_time = time.time()

            # Build log context
            extra: dict[str, Any] = {"function": func.__name__}

            if log_args:
                extra["args"] = str(args)[:200]
                extra["kwargs"] = str(kwargs)[:200]

            logger.log(log_level, f"Calling {func.__name__}", extra=extra)

            try:
                result = func(*args, **kwargs)

                if log_time:
                    extra["duration"] = round(time.time() - start_time, 4)
                if log_result:
                    extra["result"] = str(result)[:200]

                logger.log(log_level, f"Completed {func.__name__}", extra=extra)

                return result

            except Exception as e:
                extra["error"] = str(e)
                if log_time:
                    extra["duration"] = round(time.time() - start_time, 4)

                logger.error(f"Error in {func.__name__}", extra=extra, exc_info=True)
                raise

        return wrapper

    return decorator


def timed(name: Optional[str] = None) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator to log execution time.

    Usage:
        @timed("data_fetch")
        def fetch_data() -> dict:
            ...
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        logger = get_logger(func.__module__)
        timer_name = name or func.__name__

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.perf_counter() - start
                logger.debug(
                    f"Timer: {timer_name}",
                    extra={"timer": timer_name, "duration_ms": round(duration * 1000, 2)},
                )

        return wrapper

    return decorator


# =============================================================================
# PERFORMANCE TIMER
# =============================================================================


class Timer:
    """
    Context manager for timing code blocks.

    Usage:
        with Timer("data_processing") as t:
            process_data()

        print(f"Took {t.duration:.2f}s")
    """

    def __init__(self, name: str, logger: Optional[logging.Logger] = None):
        self.name = name
        self.logger = logger or get_logger("timer")
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    @property
    def duration(self) -> float:
        if self.start_time is None:
            return 0.0
        end = self.end_time or time.perf_counter()
        return end - self.start_time

    def __enter__(self) -> "Timer":
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args: Any) -> None:
        self.end_time = time.perf_counter()
        self.logger.debug(
            f"Timer: {self.name}",
            extra={
                "timer": self.name,
                "duration_ms": round(self.duration * 1000, 2),
            },
        )


# =============================================================================
# METRICS LOGGING
# =============================================================================


class MetricsLogger:
    """
    Helper for logging metrics.

    Usage:
        metrics = MetricsLogger("scanner")
        metrics.counter("signals_generated", 42)
        metrics.gauge("processing_time", 1.23)
        metrics.histogram("batch_size", [10, 20, 30, 40])
    """

    def __init__(self, namespace: str):
        self.namespace = namespace
        self.logger = get_logger(f"metrics.{namespace}")

    def counter(self, name: str, value: int = 1, **labels: Any) -> None:
        """Log a counter metric."""
        self.logger.info(
            "metric.counter",
            extra={
                "metric_type": "counter",
                "metric_name": f"{self.namespace}.{name}",
                "value": value,
                **labels,
            },
        )

    def gauge(self, name: str, value: float, **labels: Any) -> None:
        """Log a gauge metric."""
        self.logger.info(
            "metric.gauge",
            extra={
                "metric_type": "gauge",
                "metric_name": f"{self.namespace}.{name}",
                "value": value,
                **labels,
            },
        )

    def histogram(self, name: str, values: list[float], **labels: Any) -> None:
        """Log histogram metrics."""
        import statistics

        if not values:
            return

        self.logger.info(
            "metric.histogram",
            extra={
                "metric_type": "histogram",
                "metric_name": f"{self.namespace}.{name}",
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                **labels,
            },
        )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Configuration
    "configure_logging",
    "get_logger",
    # Context
    "LogContext",
    "log_context",
    "get_context",
    "set_context",
    "clear_context",
    # Formatters
    "JSONFormatter",
    "ColoredTextFormatter",
    # Decorators
    "log_call",
    "timed",
    # Utilities
    "Timer",
    "MetricsLogger",
]
