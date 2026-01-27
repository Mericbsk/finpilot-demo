"""Alternative data adapters and utilities."""

from . import exceptions
from .async_base import (
    AsyncBaseAdapter,
    AsyncCircuitBreaker,
    AsyncHTTPAdapter,
    AsyncHTTPClient,
    CircuitBreakerConfig,
    FallbackAdapter,
    RateLimitConfig,
    RetryConfig,
)
from .base import BaseAdapter, DataAdapter, DataSlice
from .news import NewsAdapter, NewsRecord, RawNewsFetcher, normalize_news_rows
from .onchain import OnChainAdapter, RawOnChainFetcher, normalize_onchain_rows

__all__ = [
    "BaseAdapter",
    "DataAdapter",
    "DataSlice",
    "AsyncBaseAdapter",
    "AsyncHTTPAdapter",
    "AsyncHTTPClient",
    "AsyncCircuitBreaker",
    "CircuitBreakerConfig",
    "FallbackAdapter",
    "RateLimitConfig",
    "RetryConfig",
    "NewsAdapter",
    "NewsRecord",
    "RawNewsFetcher",
    "normalize_news_rows",
    "OnChainAdapter",
    "RawOnChainFetcher",
    "normalize_onchain_rows",
    "exceptions",
]
