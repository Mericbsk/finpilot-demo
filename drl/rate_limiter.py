"""
Rate Limiting Utilities for External API Calls

yfinance, LLM ve diğer harici API çağrıları için
hız sınırlama ve backoff stratejileri.
"""

import functools
import logging
import time
from collections import defaultdict
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Global rate limit tracker
_call_timestamps: dict = defaultdict(list)


def rate_limit(calls_per_minute: int = 30, key: str = "default") -> Callable:
    """
    Dakikada maksimum çağrı sayısını sınırlayan dekoratör.

    Args:
        calls_per_minute: Dakikada izin verilen maksimum çağrı
        key: Rate limit grubu (farklı API'ler için farklı anahtarlar)

    Kullanım:
        @rate_limit(calls_per_minute=30, key="yfinance")
        def fetch_data(symbol):
            ...
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            now = time.time()
            window_start = now - 60  # Son 1 dakika

            # Eski kayıtları temizle
            _call_timestamps[key] = [ts for ts in _call_timestamps[key] if ts > window_start]

            # Limit kontrolü
            if len(_call_timestamps[key]) >= calls_per_minute:
                wait_time = 60 - (now - _call_timestamps[key][0])
                if wait_time > 0:
                    logger.warning(f"Rate limit aşıldı ({key}). {wait_time:.1f}s bekleniyor...")
                    time.sleep(wait_time)

            # Çağrıyı kaydet
            _call_timestamps[key].append(time.time())

            return func(*args, **kwargs)

        return wrapper

    return decorator


def exponential_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,),
) -> Callable:
    """
    Başarısız çağrıları üstel backoff ile tekrar deneyen dekoratör.

    Args:
        max_retries: Maksimum deneme sayısı
        base_delay: Başlangıç bekleme süresi (saniye)
        max_delay: Maksimum bekleme süresi (saniye)
        exceptions: Yakalanacak exception türleri

    Kullanım:
        @exponential_backoff(max_retries=3, base_delay=1.0)
        def call_api():
            ...
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception: BaseException = Exception("No attempts made")

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < max_retries:
                        delay = min(base_delay * (2**attempt), max_delay)
                        logger.warning(
                            f"{func.__name__} başarısız (deneme {attempt + 1}/{max_retries + 1}). "
                            f"{delay:.1f}s sonra tekrar deneniyor... Hata: {e}"
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"{func.__name__} {max_retries + 1} denemede başarısız. Son hata: {e}"
                        )

            raise last_exception

        return wrapper

    return decorator


def combined_rate_limit_backoff(
    calls_per_minute: int = 30, key: str = "default", max_retries: int = 3, base_delay: float = 1.0
) -> Callable:
    """
    Rate limit ve backoff'u birleştiren dekoratör.

    Kullanım:
        @combined_rate_limit_backoff(calls_per_minute=30, key="llm")
        def call_llm(prompt):
            ...
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @rate_limit(calls_per_minute=calls_per_minute, key=key)
        @exponential_backoff(max_retries=max_retries, base_delay=base_delay)
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            return func(*args, **kwargs)

        return wrapper

    return decorator


# Hazır konfigürasyonlar
def yfinance_rate_limit(func: Callable[..., T]) -> Callable[..., T]:
    """yfinance için optimize edilmiş rate limit."""
    return rate_limit(calls_per_minute=60, key="yfinance")(func)


def llm_rate_limit(func: Callable[..., T]) -> Callable[..., T]:
    """LLM API'leri için rate limit + backoff."""
    return combined_rate_limit_backoff(
        calls_per_minute=20, key="llm", max_retries=2, base_delay=2.0
    )(func)
