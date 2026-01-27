"""Async adapter infrastructure for alternative data providers."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, Mapping, Optional, Sequence, Tuple, TypeVar

import httpx
from aiolimiter import AsyncLimiter
from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from .base import BaseAdapter, DataSlice
from .exceptions import (
    AdapterCircuitOpenError,
    AdapterError,
    AdapterRateLimitError,
    AdapterResponseError,
    AdapterRetryableError,
    AdapterTimeoutError,
)

T = TypeVar("T")


@dataclass(frozen=True)
class RateLimitConfig:
    """Rate-limit contract per provider."""

    max_calls: int
    period: float

    def build(self) -> AsyncLimiter:
        return AsyncLimiter(self.max_calls, self.period)


@dataclass(frozen=True)
class RetryConfig:
    """Retry policy for transient provider failures."""

    attempts: int = 5
    base: float = 0.5
    maximum: float = 8.0
    jitter: float = 0.1
    retriable: Tuple[type[BaseException], ...] = (
        httpx.TransportError,
        AdapterRetryableError,
        AdapterTimeoutError,
        AdapterRateLimitError,
    )


@dataclass(frozen=True)
class CircuitBreakerConfig:
    """Circuit breaker thresholds."""

    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    success_threshold: int = 3


class AsyncCircuitBreaker:
    """Minimal async-friendly circuit breaker implementation."""

    def __init__(self, *, config: CircuitBreakerConfig, provider: str) -> None:
        self._config = config
        self._provider = provider
        self._state = "closed"
        self._failure_count = 0
        self._success_count = 0
        self._opened_at = 0.0
        self._lock = asyncio.Lock()

    async def call(self, func: Callable[[], Awaitable[T]]) -> T:
        async with self._lock:
            state = self._state
            if state == "open":
                if time.monotonic() - self._opened_at >= self._config.recovery_timeout:
                    self._state = "half-open"
                    self._success_count = 0
                else:
                    raise AdapterCircuitOpenError(
                        f"Circuit breaker open for provider {self._provider}",
                        provider=self._provider,
                    )

        try:
            result = await func()
        except Exception:
            await self._register_failure()
            raise
        else:
            await self._register_success()
            return result

    async def _register_failure(self) -> None:
        async with self._lock:
            self._failure_count += 1
            if self._state == "half-open":
                self._state = "open"
                self._opened_at = time.monotonic()
                return
            if self._failure_count >= self._config.failure_threshold:
                self._state = "open"
                self._opened_at = time.monotonic()

    async def _register_success(self) -> None:
        async with self._lock:
            self._failure_count = 0
            if self._state == "half-open":
                self._success_count += 1
                if self._success_count >= self._config.success_threshold:
                    self._state = "closed"
                    self._success_count = 0


class AsyncHTTPClient:
    """HTTP client with rate limiting, retries, and circuit breaker."""

    def __init__(
        self,
        *,
        base_url: str,
        provider: str,
        timeout: Optional[float] = 10.0,
        default_headers: Optional[Mapping[str, str]] = None,
        rate_limit: Optional[RateLimitConfig] = None,
        retry: Optional[RetryConfig] = None,
        circuit_breaker: Optional[CircuitBreakerConfig] = None,
        http2: bool = True,
    ) -> None:
        self._provider = provider
        self._base_url = base_url
        self._timeout = timeout
        self._default_headers = dict(default_headers or {})
        self._retry = retry or RetryConfig()
        self._limiter = rate_limit.build() if rate_limit else None
        self._breaker = AsyncCircuitBreaker(
            config=circuit_breaker or CircuitBreakerConfig(),
            provider=provider,
        )
        self._client: Optional[httpx.AsyncClient] = None
        self._client_lock = asyncio.Lock()
        self._http2 = http2

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            async with self._client_lock:
                if self._client is None:
                    self._client = httpx.AsyncClient(
                        base_url=self._base_url,
                        timeout=self._timeout,
                        headers=self._default_headers,
                        http2=self._http2,
                    )
        return self._client

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
        json: Optional[Any] = None,
        data: Optional[Any] = None,
        timeout: Optional[float] = None,
    ) -> httpx.Response:
        async def _send() -> httpx.Response:
            client = await self._ensure_client()
            try:
                response = await client.request(
                    method,
                    url,
                    params=params,
                    headers=headers,
                    json=json,
                    data=data,
                    timeout=timeout or self._timeout,
                )
            except httpx.TimeoutException as exc:
                raise AdapterTimeoutError(str(exc), provider=self._provider) from exc
            except httpx.TransportError as exc:
                raise AdapterRetryableError(str(exc), provider=self._provider) from exc

            if response.status_code == 429:
                retry_after = float(response.headers.get("Retry-After", "0") or 0)
                raise AdapterRateLimitError(
                    "Provider rate limit exceeded",
                    retry_after=retry_after,
                    provider=self._provider,
                )
            if response.status_code >= 500:
                raise AdapterRetryableError(
                    f"Provider returned {response.status_code}",
                    provider=self._provider,
                )
            if response.status_code >= 400:
                raise AdapterResponseError(
                    f"Provider request failed with {response.status_code}",
                    status_code=response.status_code,
                    provider=self._provider,
                )
            return response

        async def _runner() -> httpx.Response:
            if self._limiter is None:
                return await _send()
            async with self._limiter:
                return await _send()

        retrying = AsyncRetrying(
            stop=stop_after_attempt(self._retry.attempts),
            wait=wait_exponential_jitter(
                initial=self._retry.base,
                max=self._retry.maximum,
                jitter=self._retry.jitter,
            ),
            retry=retry_if_exception_type(self._retry.retriable),
            reraise=True,
        )

        try:
            async for attempt in retrying:
                with attempt:
                    return await self._breaker.call(_runner)
        except RetryError as exc:
            raise AdapterError(
                f"Provider {self._provider} failed after {self._retry.attempts} retries",
                provider=self._provider,
            ) from exc

    async def get_json(
        self,
        url: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> Mapping[str, Any]:
        response = await self.request("GET", url, params=params, headers=headers)
        try:
            return response.json()
        except ValueError as exc:
            raise AdapterResponseError(
                "Provider returned invalid JSON",
                provider=self._provider,
            ) from exc


class AsyncBaseAdapter(BaseAdapter):
    """Async extension for adapters. Prefer using ``fetch_async``."""

    async def fetch_async(
        self,
        symbol: str,
        *,
        start: Optional[Any] = None,
        end: Optional[Any] = None,
    ) -> DataSlice:
        raise NotImplementedError

    def fetch(
        self,
        symbol: str,
        *,
        start: Optional[Any] = None,
        end: Optional[Any] = None,
    ) -> DataSlice:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.fetch_async(symbol, start=start, end=end))
        raise RuntimeError(
            "fetch() cannot be called from an active event loop; use fetch_async instead"
        )


class AsyncHTTPAdapter(AsyncBaseAdapter):
    """Base class for HTTP-based asynchronous adapters."""

    def __init__(self, *, client: AsyncHTTPClient, provider: str) -> None:
        super().__init__(provider=provider)
        self._client = client

    @property
    def client(self) -> AsyncHTTPClient:
        return self._client

    async def aclose(self) -> None:
        await self._client.aclose()


class FallbackAdapter(AsyncBaseAdapter):
    """Tries a sequence of adapters until one succeeds."""

    def __init__(self, adapters: Sequence[AsyncBaseAdapter], *, provider: str = "fallback") -> None:
        if not adapters:
            raise ValueError("FallbackAdapter requires at least one adapter")
        super().__init__(provider=provider)
        self._adapters = list(adapters)

    async def fetch_async(
        self,
        symbol: str,
        *,
        start: Optional[Any] = None,
        end: Optional[Any] = None,
    ) -> DataSlice:
        errors: Dict[str, Exception] = {}
        for adapter in self._adapters:
            try:
                return await adapter.fetch_async(symbol, start=start, end=end)
            except AdapterCircuitOpenError as exc:
                errors[adapter.provider] = exc
                continue
            except AdapterError as exc:
                errors[adapter.provider] = exc
                continue
        raise AdapterError(
            f"All fallback providers failed: {', '.join(errors)}",
            provider=self.provider,
        )


__all__ = [
    "AsyncBaseAdapter",
    "AsyncHTTPAdapter",
    "AsyncHTTPClient",
    "AsyncCircuitBreaker",
    "RateLimitConfig",
    "RetryConfig",
    "CircuitBreakerConfig",
    "FallbackAdapter",
]
