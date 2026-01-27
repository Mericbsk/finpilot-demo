# -*- coding: utf-8 -*-
"""
FinPilot Audit Logging System
==============================

Centralized audit logging for user actions, system events, and security.
Provides structured logging with rotation, async writing, and multiple outputs.

Features:
- Structured JSON audit logs
- Automatic log rotation
- Async file writing (non-blocking)
- Multiple output targets (file, console, remote)
- User action tracking
- Security event logging
- Performance metrics

Usage:
    from core.audit import audit_log, AuditAction, log_user_action

    # Log a user action
    log_user_action(
        action=AuditAction.SCAN_STARTED,
        user_id="user123",
        details={"symbols_count": 50}
    )

    # Or use the audit_log instance directly
    audit_log.log(
        action="custom_action",
        level="INFO",
        details={"key": "value"}
    )
"""
from __future__ import annotations

import atexit
import json
import logging
import os
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from queue import Empty, Queue
from typing import Any, Dict, List, Optional, Union

# ============================================
# 📊 Audit Action Types
# ============================================


class AuditAction(str, Enum):
    """Standard audit action types."""

    # Authentication
    LOGIN_SUCCESS = "auth.login.success"
    LOGIN_FAILED = "auth.login.failed"
    LOGOUT = "auth.logout"
    SESSION_EXPIRED = "auth.session.expired"
    PASSWORD_CHANGED = "auth.password.changed"

    # Scanning
    SCAN_STARTED = "scan.started"
    SCAN_COMPLETED = "scan.completed"
    SCAN_FAILED = "scan.failed"
    SCAN_CANCELLED = "scan.cancelled"

    # Data Operations
    CSV_UPLOADED = "data.csv.uploaded"
    CSV_VALIDATION_FAILED = "data.csv.validation_failed"
    SHORTLIST_LOADED = "data.shortlist.loaded"
    EXPORT_GENERATED = "data.export.generated"

    # User Actions
    SETTINGS_UPDATED = "user.settings.updated"
    WATCHLIST_MODIFIED = "user.watchlist.modified"
    SYMBOL_SELECTED = "user.symbol.selected"
    RESEARCH_REQUESTED = "user.research.requested"

    # System Events
    APP_STARTED = "system.app.started"
    APP_ERROR = "system.app.error"
    CACHE_CLEARED = "system.cache.cleared"
    CONFIG_LOADED = "system.config.loaded"

    # Trading (if applicable)
    SIGNAL_GENERATED = "trading.signal.generated"
    ALERT_SENT = "trading.alert.sent"

    # Security
    RATE_LIMIT_HIT = "security.rate_limit.hit"
    INVALID_INPUT = "security.input.invalid"
    UNAUTHORIZED_ACCESS = "security.access.unauthorized"


class AuditLevel(str, Enum):
    """Audit log severity levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    SECURITY = "SECURITY"  # Special level for security events


# ============================================
# 📦 Audit Entry Dataclass
# ============================================


@dataclass
class AuditEntry:
    """
    Structured audit log entry.

    All audit events are captured with consistent fields
    for easy parsing and analysis.
    """

    action: str
    level: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])

    # Context
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    # Details
    details: Dict[str, Any] = field(default_factory=dict)

    # Performance
    duration_ms: Optional[float] = None

    # Error info
    error_type: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        result = {}
        for key, value in asdict(self).items():
            if value is not None and value != {} and value != []:
                result[key] = value
        return result

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)


# ============================================
# 🔧 Audit Logger Implementation
# ============================================


class AuditLogger:
    """
    Centralized audit logging system.

    Provides async file writing with rotation, structured logging,
    and multiple output targets.

    Features:
    - Non-blocking async writes to file
    - Automatic log rotation by date
    - JSON-formatted entries for easy parsing
    - Thread-safe queue-based writing
    - Graceful shutdown handling
    """

    def __init__(
        self,
        log_dir: str = "data/logs/audit",
        console_output: bool = False,
        max_queue_size: int = 1000,
        flush_interval: float = 5.0,
    ):
        """
        Initialize audit logger.

        Args:
            log_dir: Directory for audit log files
            console_output: Also print to console
            max_queue_size: Maximum pending entries in queue
            flush_interval: Seconds between file flushes
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.console_output = console_output
        self.flush_interval = flush_interval

        # Async writing queue
        self._queue: Queue[Optional[AuditEntry]] = Queue(maxsize=max_queue_size)
        self._current_file: Optional[Path] = None
        self._current_date: Optional[str] = None
        self._file_handle: Optional[Any] = None

        # Background writer thread
        self._writer_thread: Optional[threading.Thread] = None
        self._shutdown = threading.Event()

        # Start background writer
        self._start_writer()

        # Register shutdown handler
        atexit.register(self.shutdown)

        # Python logger for fallback
        self._logger = logging.getLogger("finpilot.audit")

    def _start_writer(self) -> None:
        """Start the background writer thread."""
        if self._writer_thread is not None and self._writer_thread.is_alive():
            return

        self._shutdown.clear()
        self._writer_thread = threading.Thread(
            target=self._writer_loop, name="AuditWriter", daemon=True
        )
        self._writer_thread.start()

    def _writer_loop(self) -> None:
        """Background loop for writing entries to file."""
        while not self._shutdown.is_set():
            try:
                # Wait for entries with timeout
                entry = self._queue.get(timeout=self.flush_interval)

                if entry is None:
                    # Shutdown signal
                    break

                self._write_entry(entry)

            except Empty:
                # Flush on timeout
                self._flush()
            except Exception as e:
                self._logger.error(f"Audit writer error: {e}")

        # Final flush on shutdown
        self._drain_queue()
        self._close_file()

    def _get_log_file(self) -> Path:
        """Get current log file path, rotating if needed."""
        today = datetime.now().strftime("%Y-%m-%d")

        if today != self._current_date:
            self._close_file()
            self._current_date = today
            self._current_file = self.log_dir / f"audit_{today}.jsonl"

        return self._current_file or self.log_dir / f"audit_{today}.jsonl"

    def _write_entry(self, entry: AuditEntry) -> None:
        """Write a single entry to file."""
        try:
            log_file = self._get_log_file()

            # Open file if needed
            if self._file_handle is None:
                self._file_handle = open(log_file, "a", encoding="utf-8")

            # Write JSON line
            self._file_handle.write(entry.to_json() + "\n")

            # Console output if enabled
            if self.console_output:
                print(f"[AUDIT] {entry.level}: {entry.action} - {entry.details}")

        except Exception as e:
            self._logger.error(f"Failed to write audit entry: {e}")

    def _flush(self) -> None:
        """Flush file buffer."""
        if self._file_handle:
            try:
                self._file_handle.flush()
            except Exception:
                pass

    def _close_file(self) -> None:
        """Close current file handle."""
        if self._file_handle:
            try:
                self._file_handle.flush()
                self._file_handle.close()
            except Exception:
                pass
            self._file_handle = None

    def _drain_queue(self) -> None:
        """Drain remaining entries from queue."""
        while True:
            try:
                entry = self._queue.get_nowait()
                if entry is not None:
                    self._write_entry(entry)
            except Empty:
                break

    def log(
        self,
        action: Union[str, AuditAction],
        level: Union[str, AuditLevel] = AuditLevel.INFO,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None,
        error: Optional[Exception] = None,
        **kwargs: Any,
    ) -> str:
        """
        Log an audit entry.

        Args:
            action: Action type (string or AuditAction enum)
            level: Log level (string or AuditLevel enum)
            user_id: User identifier
            session_id: Session identifier
            details: Additional details dictionary
            duration_ms: Operation duration in milliseconds
            error: Exception if this is an error log
            **kwargs: Additional fields to include in details

        Returns:
            Event ID of the logged entry
        """
        # Handle enums
        action_str = action.value if isinstance(action, AuditAction) else str(action)
        level_str = level.value if isinstance(level, AuditLevel) else str(level)

        # Merge details with kwargs
        merged_details = {**(details or {}), **kwargs}

        # Create entry
        entry = AuditEntry(
            action=action_str,
            level=level_str,
            user_id=user_id,
            session_id=session_id,
            details=merged_details,
            duration_ms=duration_ms,
        )

        # Add error info if present
        if error:
            entry.error_type = type(error).__name__
            entry.error_message = str(error)

        # Queue for async writing
        try:
            self._queue.put_nowait(entry)
        except Exception:
            # Queue full - log directly as fallback
            self._write_entry(entry)

        return entry.event_id

    def shutdown(self) -> None:
        """Gracefully shutdown the audit logger."""
        if self._shutdown.is_set():
            return

        self._shutdown.set()

        # Send shutdown signal
        try:
            self._queue.put_nowait(None)
        except Exception:
            pass

        # Wait for writer to finish
        if self._writer_thread and self._writer_thread.is_alive():
            self._writer_thread.join(timeout=5.0)

    def get_recent_entries(
        self,
        limit: int = 100,
        action_filter: Optional[str] = None,
        level_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Read recent audit entries.

        Args:
            limit: Maximum number of entries to return
            action_filter: Filter by action prefix
            level_filter: Filter by level

        Returns:
            List of audit entry dictionaries
        """
        entries = []

        # Get all log files sorted by date (newest first)
        log_files = sorted(self.log_dir.glob("audit_*.jsonl"), reverse=True)

        for log_file in log_files:
            if len(entries) >= limit:
                break

            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if len(entries) >= limit:
                            break

                        try:
                            entry = json.loads(line.strip())

                            # Apply filters
                            if action_filter and not entry.get("action", "").startswith(
                                action_filter
                            ):
                                continue
                            if level_filter and entry.get("level") != level_filter:
                                continue

                            entries.append(entry)
                        except json.JSONDecodeError:
                            continue

            except Exception as e:
                self._logger.warning(f"Failed to read log file {log_file}: {e}")

        return entries


# ============================================
# 🌍 Global Audit Logger Instance
# ============================================

# Singleton instance
_audit_log: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance."""
    global _audit_log
    if _audit_log is None:
        _audit_log = AuditLogger()
    return _audit_log


# Convenience alias
audit_log = property(lambda self: get_audit_logger())


# ============================================
# 🔗 Convenience Functions
# ============================================


def log_user_action(
    action: Union[str, AuditAction],
    user_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> str:
    """
    Log a user action.

    Convenience function for common user action logging.

    Args:
        action: Action type
        user_id: User identifier
        details: Additional details
        **kwargs: Extra fields

    Returns:
        Event ID
    """
    return get_audit_logger().log(
        action=action, level=AuditLevel.INFO, user_id=user_id, details=details, **kwargs
    )


def log_security_event(
    action: Union[str, AuditAction],
    user_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> str:
    """
    Log a security-related event.

    Args:
        action: Security action type
        user_id: User identifier
        details: Additional details
        **kwargs: Extra fields

    Returns:
        Event ID
    """
    return get_audit_logger().log(
        action=action, level=AuditLevel.SECURITY, user_id=user_id, details=details, **kwargs
    )


def log_error(
    action: Union[str, AuditAction],
    error: Exception,
    user_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> str:
    """
    Log an error event.

    Args:
        action: Action that caused the error
        error: The exception
        user_id: User identifier
        details: Additional details
        **kwargs: Extra fields

    Returns:
        Event ID
    """
    return get_audit_logger().log(
        action=action,
        level=AuditLevel.ERROR,
        user_id=user_id,
        details=details,
        error=error,
        **kwargs,
    )


def log_scan_event(
    action: AuditAction,
    symbols_count: int = 0,
    buyable_count: int = 0,
    duration_ms: Optional[float] = None,
    source: Optional[str] = None,
    user_id: Optional[str] = None,
    **kwargs: Any,
) -> str:
    """
    Log a scan-related event.

    Args:
        action: Scan action type
        symbols_count: Number of symbols scanned
        buyable_count: Number of buyable opportunities
        duration_ms: Scan duration
        source: Scan source (csv, live, etc.)
        user_id: User identifier
        **kwargs: Extra fields

    Returns:
        Event ID
    """
    return get_audit_logger().log(
        action=action,
        level=AuditLevel.INFO,
        user_id=user_id,
        details={
            "symbols_count": symbols_count,
            "buyable_count": buyable_count,
            "source": source,
            **kwargs,
        },
        duration_ms=duration_ms,
    )


__all__ = [
    # Classes
    "AuditAction",
    "AuditLevel",
    "AuditEntry",
    "AuditLogger",
    # Functions
    "get_audit_logger",
    "log_user_action",
    "log_security_event",
    "log_error",
    "log_scan_event",
]
