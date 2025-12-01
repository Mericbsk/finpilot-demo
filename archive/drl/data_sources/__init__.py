"""Alternative data adapters and utilities."""
from .base import BaseAdapter, DataAdapter, DataSlice
from .async_base import (
    AsyncBaseAdapter,
    AsyncHTTPAdapter,
    AsyncHTTPClient,
    AsyncCircuitBreaker,
    CircuitBreakerConfig,
    FallbackAdapter,
    RateLimitConfig,
    RetryConfig,
)
from .news import NewsAdapter, NewsRecord, RawNewsFetcher, normalize_news_rows
from .onchain import OnChainAdapter, RawOnChainFetcher, normalize_onchain_rows
from . import exceptions

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
