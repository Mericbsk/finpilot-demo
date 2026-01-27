"""
FinPilot Exception Hierarchy
============================

Standart exception sınıfları ve error handling altyapısı.

Exception Hierarchy:
    FinPilotError (Base)
    ├── ConfigError - Konfigürasyon hataları
    ├── DataError - Veri işleme hataları
    │   ├── DataFetchError - API/veri çekme hataları
    │   ├── DataValidationError - Veri doğrulama hataları
    │   └── DataProcessingError - Veri işleme hataları
    ├── AuthError - Authentication hataları
    │   ├── AuthenticationError - Login hataları
    │   ├── AuthorizationError - Yetki hataları
    │   └── TokenError - JWT token hataları
    ├── MarketError - Piyasa/trading hataları
    │   ├── InsufficientFundsError - Yetersiz bakiye
    │   ├── OrderError - Emir hataları
    │   └── PositionError - Pozisyon hataları
    ├── ModelError - ML model hataları
    │   ├── ModelNotFoundError - Model bulunamadı
    │   ├── ModelLoadError - Model yükleme hatası
    │   └── InferenceError - Tahmin hatası
    └── CacheError - Cache hataları

Kullanım:
    from core.exceptions import DataFetchError, handle_errors

    @handle_errors(default_return=None, log_error=True)
    def fetch_data(ticker: str) -> pd.DataFrame:
        ...
        raise DataFetchError(f"Failed to fetch {ticker}", ticker=ticker)

Author: FinPilot Team
Version: 1.0.0
"""

from __future__ import annotations

import functools
import traceback
from datetime import datetime
from typing import Any, Callable, Optional, ParamSpec, Type, TypeVar

P = ParamSpec("P")
T = TypeVar("T")


# =============================================================================
# BASE EXCEPTION
# =============================================================================


class FinPilotError(Exception):
    """
    FinPilot uygulamasının temel exception sınıfı.

    Attributes:
        message: Hata mesajı
        code: Hata kodu (opsiyonel)
        details: Ek detaylar (opsiyonel)
        timestamp: Hata zamanı
    """

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ):
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
        self.details.update(kwargs)
        self.timestamp = datetime.utcnow()
        super().__init__(self.message)

    def __str__(self) -> str:
        base = f"[{self.code}] {self.message}"
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            base += f" ({details_str})"
        return base

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, code={self.code!r})"

    def to_dict(self) -> dict[str, Any]:
        """Exception'ı dictionary olarak döndür."""
        return {
            "error": self.__class__.__name__,
            "code": self.code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }


# =============================================================================
# CONFIG EXCEPTIONS
# =============================================================================


class ConfigError(FinPilotError):
    """Konfigürasyon hataları için base class."""

    pass


class ConfigNotFoundError(ConfigError):
    """Konfigürasyon dosyası bulunamadı."""

    def __init__(self, config_path: str, **kwargs):
        super().__init__(
            f"Configuration file not found: {config_path}", config_path=config_path, **kwargs
        )


class ConfigValidationError(ConfigError):
    """Konfigürasyon değeri geçersiz."""

    def __init__(self, key: str, value: Any, reason: str, **kwargs):
        super().__init__(
            f"Invalid configuration value for '{key}': {reason}",
            key=key,
            value=value,
            reason=reason,
            **kwargs,
        )


# =============================================================================
# DATA EXCEPTIONS
# =============================================================================


class DataError(FinPilotError):
    """Veri işleme hataları için base class."""

    pass


class DataFetchError(DataError):
    """Veri çekme hatası (API, database, file)."""

    def __init__(self, message: str, source: Optional[str] = None, **kwargs):
        super().__init__(message, source=source, **kwargs)


class DataValidationError(DataError):
    """Veri doğrulama hatası."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        expected: Optional[Any] = None,
        actual: Optional[Any] = None,
        **kwargs,
    ):
        super().__init__(message, field=field, expected=expected, actual=actual, **kwargs)


class DataProcessingError(DataError):
    """Veri işleme hatası (transformation, calculation)."""

    def __init__(self, message: str, operation: Optional[str] = None, **kwargs):
        super().__init__(message, operation=operation, **kwargs)


class InsufficientDataError(DataError):
    """Yetersiz veri hatası."""

    def __init__(
        self,
        message: str,
        required: Optional[int] = None,
        available: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(message, required=required, available=available, **kwargs)


# =============================================================================
# AUTH EXCEPTIONS
# =============================================================================


class AuthError(FinPilotError):
    """Authentication/Authorization hataları için base class."""

    pass


class AuthenticationError(AuthError):
    """Kimlik doğrulama hatası (login failed)."""

    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(message, **kwargs)


class AuthorizationError(AuthError):
    """Yetkilendirme hatası (permission denied)."""

    def __init__(
        self,
        message: str = "Permission denied",
        required_permission: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(message, required_permission=required_permission, **kwargs)


class TokenError(AuthError):
    """JWT token hatası."""

    pass


class TokenExpiredError(TokenError):
    """Token süresi dolmuş."""

    def __init__(self, message: str = "Token has expired", **kwargs):
        super().__init__(message, **kwargs)


class TokenInvalidError(TokenError):
    """Token geçersiz."""

    def __init__(self, message: str = "Invalid token", **kwargs):
        super().__init__(message, **kwargs)


class UserNotFoundError(AuthError):
    """Kullanıcı bulunamadı."""

    def __init__(self, identifier: str, **kwargs):
        super().__init__(f"User not found: {identifier}", identifier=identifier, **kwargs)


class UserExistsError(AuthError):
    """Kullanıcı zaten mevcut."""

    def __init__(self, identifier: str, **kwargs):
        super().__init__(f"User already exists: {identifier}", identifier=identifier, **kwargs)


# =============================================================================
# MARKET EXCEPTIONS
# =============================================================================


class MarketError(FinPilotError):
    """Piyasa/trading hataları için base class."""

    pass


class InsufficientFundsError(MarketError):
    """Yetersiz bakiye."""

    def __init__(self, required: float, available: float, **kwargs):
        super().__init__(
            f"Insufficient funds: required ${required:.2f}, available ${available:.2f}",
            required=required,
            available=available,
            **kwargs,
        )


class OrderError(MarketError):
    """Emir hatası."""

    def __init__(
        self,
        message: str,
        order_id: Optional[str] = None,
        order_type: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(message, order_id=order_id, order_type=order_type, **kwargs)


class PositionError(MarketError):
    """Pozisyon hatası."""

    def __init__(
        self,
        message: str,
        ticker: Optional[str] = None,
        position_size: Optional[float] = None,
        **kwargs,
    ):
        super().__init__(message, ticker=ticker, position_size=position_size, **kwargs)


class TickerNotFoundError(MarketError):
    """Ticker bulunamadı."""

    def __init__(self, ticker: str, **kwargs):
        super().__init__(f"Ticker not found: {ticker}", ticker=ticker, **kwargs)


class MarketClosedError(MarketError):
    """Piyasa kapalı."""

    def __init__(self, message: str = "Market is closed", **kwargs):
        super().__init__(message, **kwargs)


# =============================================================================
# MODEL EXCEPTIONS
# =============================================================================


class ModelError(FinPilotError):
    """ML model hataları için base class."""

    pass


class ModelNotFoundError(ModelError):
    """Model bulunamadı."""

    def __init__(self, model_name: str, model_path: Optional[str] = None, **kwargs):
        super().__init__(
            f"Model not found: {model_name}", model_name=model_name, model_path=model_path, **kwargs
        )


class ModelLoadError(ModelError):
    """Model yükleme hatası."""

    def __init__(self, model_name: str, reason: Optional[str] = None, **kwargs):
        super().__init__(
            f"Failed to load model: {model_name}" + (f" - {reason}" if reason else ""),
            model_name=model_name,
            reason=reason,
            **kwargs,
        )


class ModelTrainingError(ModelError):
    """Model eğitim hatası."""

    def __init__(self, message: str, epoch: Optional[int] = None, **kwargs):
        super().__init__(message, epoch=epoch, **kwargs)


class InferenceError(ModelError):
    """Model inference/prediction hatası."""

    def __init__(
        self,
        message: str,
        model_name: Optional[str] = None,
        input_shape: Optional[tuple] = None,
        **kwargs,
    ):
        super().__init__(message, model_name=model_name, input_shape=input_shape, **kwargs)


class FeatureError(ModelError):
    """Feature engineering hatası."""

    def __init__(self, message: str, feature_name: Optional[str] = None, **kwargs):
        super().__init__(message, feature_name=feature_name, **kwargs)


# =============================================================================
# CACHE EXCEPTIONS
# =============================================================================


class CacheError(FinPilotError):
    """Cache hataları için base class."""

    pass


class CacheConnectionError(CacheError):
    """Cache bağlantı hatası (Redis vs.)."""

    def __init__(self, message: str = "Cache connection failed", **kwargs):
        super().__init__(message, **kwargs)


class CacheKeyError(CacheError):
    """Cache key hatası."""

    def __init__(self, key: str, **kwargs):
        super().__init__(f"Cache key error: {key}", key=key, **kwargs)


# =============================================================================
# ERROR HANDLER DECORATOR
# =============================================================================


def handle_errors(
    *catch: Type[Exception],
    default_return: Any = None,
    log_error: bool = True,
    reraise: bool = False,
    reraise_as: Optional[Type[FinPilotError]] = None,
) -> Callable[[Callable[P, T]], Callable[P, T | Any]]:
    """
    Fonksiyonlardaki exception'ları yakalayan decorator.

    Args:
        *catch: Yakalanacak exception tipleri (boş = tümü)
        default_return: Hata durumunda döndürülecek değer
        log_error: Hatayı logla mı?
        reraise: Hatayı tekrar fırlat mı?
        reraise_as: Hatayı bu tipte fırlat

    Usage:
        @handle_errors(DataFetchError, default_return=pd.DataFrame())
        def fetch_data(ticker: str) -> pd.DataFrame:
            ...

        @handle_errors(reraise_as=DataError)
        def process_data(df: pd.DataFrame) -> pd.DataFrame:
            ...
    """
    catch_types = catch or (Exception,)

    def decorator(func: Callable[P, T]) -> Callable[P, T | Any]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T | Any:
            try:
                return func(*args, **kwargs)
            except catch_types as e:
                # Log error
                if log_error:
                    # Import here to avoid circular imports
                    try:
                        from core.logging import get_logger

                        logger = get_logger(func.__module__)
                        logger.error(
                            f"Error in {func.__name__}: {e}",
                            exc_info=True,
                            extra={
                                "function": func.__name__,
                                "call_args": str(args)[:200],
                                "call_kwargs": str(kwargs)[:200],
                            },
                        )
                    except ImportError:
                        print(f"ERROR in {func.__name__}: {e}")

                # Reraise handling
                if reraise:
                    raise
                elif reraise_as:
                    raise reraise_as(str(e)) from e

                return default_return

        return wrapper

    return decorator


def retry_on_error(
    *catch: Type[Exception],
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    log_retry: bool = True,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Hata durumunda retry yapan decorator.

    Args:
        *catch: Yakalanacak exception tipleri
        max_retries: Maksimum deneme sayısı
        delay: İlk bekleme süresi (saniye)
        backoff: Her denemede çarpan
        log_retry: Retry'ları logla mı?

    Usage:
        @retry_on_error(DataFetchError, max_retries=3, delay=1.0)
        def fetch_with_retry(url: str) -> dict:
            ...
    """
    import time

    catch_types = catch or (Exception,)

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_exception: Optional[Exception] = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except catch_types as e:
                    last_exception = e

                    if attempt < max_retries:
                        if log_retry:
                            try:
                                from core.logging import get_logger

                                logger = get_logger(func.__module__)
                                logger.warning(
                                    f"Retry {attempt + 1}/{max_retries} for {func.__name__}: {e}"
                                )
                            except ImportError:
                                print(f"RETRY {attempt + 1}/{max_retries}: {e}")

                        time.sleep(current_delay)
                        current_delay *= backoff

            raise last_exception  # type: ignore

        return wrapper

    return decorator


# =============================================================================
# EXCEPTION UTILITIES
# =============================================================================


def format_exception(e: Exception) -> str:
    """Exception'ı formatlanmış string olarak döndür."""
    if isinstance(e, FinPilotError):
        return str(e)
    return f"{type(e).__name__}: {e}"


def get_exception_chain(e: Exception) -> list[Exception]:
    """Exception zincirini döndür (cause chain)."""
    chain: list[Exception] = [e]
    current: BaseException = e
    while current.__cause__ is not None:
        if isinstance(current.__cause__, Exception):
            chain.append(current.__cause__)
        current = current.__cause__
    return chain


def safe_execute(
    func: Callable[P, T], *args: P.args, default: T = None, **kwargs: P.kwargs  # type: ignore
) -> tuple[T, Optional[Exception]]:
    """
    Fonksiyonu güvenli şekilde çalıştır, (result, error) tuple döndür.

    Usage:
        result, error = safe_execute(fetch_data, "AAPL")
        if error:
            handle_error(error)
        else:
            process(result)
    """
    try:
        return func(*args, **kwargs), None
    except Exception as e:
        return default, e


__all__ = [
    # Base
    "FinPilotError",
    # Config
    "ConfigError",
    "ConfigNotFoundError",
    "ConfigValidationError",
    # Data
    "DataError",
    "DataFetchError",
    "DataValidationError",
    "DataProcessingError",
    "InsufficientDataError",
    # Auth
    "AuthError",
    "AuthenticationError",
    "AuthorizationError",
    "TokenError",
    "TokenExpiredError",
    "TokenInvalidError",
    "UserNotFoundError",
    "UserExistsError",
    # Market
    "MarketError",
    "InsufficientFundsError",
    "OrderError",
    "PositionError",
    "TickerNotFoundError",
    "MarketClosedError",
    # Model
    "ModelError",
    "ModelNotFoundError",
    "ModelLoadError",
    "ModelTrainingError",
    "InferenceError",
    "FeatureError",
    # Cache
    "CacheError",
    "CacheConnectionError",
    "CacheKeyError",
    # Decorators
    "handle_errors",
    "retry_on_error",
    # Utilities
    "format_exception",
    "get_exception_chain",
    "safe_execute",
]
