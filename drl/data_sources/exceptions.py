"""Exception hierarchy for alternative data adapters."""

from __future__ import annotations

from typing import Optional


class AdapterError(Exception):
    """Base error raised by alternative data adapters."""

    def __init__(self, message: str, *, provider: Optional[str] = None) -> None:
        self.provider = provider
        super().__init__(message)


class AdapterConfigurationError(AdapterError):
    """Raised when an adapter is misconfigured (e.g. missing credentials)."""


class AdapterRateLimitError(AdapterError):
    """Raised when a provider indicates the caller exceeded the rate limit."""

    def __init__(
        self, message: str, *, retry_after: Optional[float] = None, provider: Optional[str] = None
    ) -> None:
        super().__init__(message, provider=provider)
        self.retry_after = retry_after


class AdapterTimeoutError(AdapterError):
    """Raised when a provider request times out."""


class AdapterCircuitOpenError(AdapterError):
    """Raised when the circuit breaker is open and calls are short-circuited."""


class AdapterResponseError(AdapterError):
    """Raised when the provider returns an unexpected payload or status."""

    def __init__(
        self, message: str, *, status_code: Optional[int] = None, provider: Optional[str] = None
    ) -> None:
        super().__init__(message, provider=provider)
        self.status_code = status_code


class AdapterRetryableError(AdapterError):
    """Marker for retryable transient failures."""


__all__ = [
    "AdapterError",
    "AdapterConfigurationError",
    "AdapterRateLimitError",
    "AdapterTimeoutError",
    "AdapterCircuitOpenError",
    "AdapterResponseError",
    "AdapterRetryableError",
]
