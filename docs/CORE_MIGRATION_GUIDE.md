# FinPilot Core Infrastructure Migration Guide
## v1.0.0 - Ocak 2025

Bu döküman, mevcut modüllerin yeni `core/` altyapısına nasıl geçirileceğini açıklar.

---

## 📁 Core Modül Yapısı

```
core/
├── __init__.py         # Public API exports
├── config.py           # Pydantic Settings (merkezi konfigürasyon)
├── exceptions.py       # Exception hiyerarşisi + decorators
├── cache.py            # Multi-layer cache (L1 Memory, L2 Redis)
├── logging.py          # Structured JSON logging
└── monitoring.py       # Prometheus metrics + health checks
```

---

## 1. Config Migration

### ❌ Eski Yöntem (scanner/config.py)
```python
from scanner.config import SETTINGS, get_setting

min_price = get_setting("min_price", 5.0)
rsi_oversold = 30  # hardcoded
```

### ✅ Yeni Yöntem (core/config.py)
```python
from core.config import settings

min_price = settings.scanner.min_price
rsi_oversold = settings.scanner.rsi_oversold
```

### Preset Kullanımı
```python
# Conservative/Aggressive modlar
aggressive = settings.get_scanner_preset("aggressive")
print(aggressive.rsi_oversold)  # 35.0
```

### Environment Variables
```bash
# .env dosyasında
POLYGON_API_KEY=your_key
DEBUG=true
ENVIRONMENT=production
```

---

## 2. Exception Migration

### ❌ Eski Yöntem
```python
try:
    data = fetch_data(ticker)
except Exception:
    return None  # Silent failure
```

### ✅ Yeni Yöntem - Decorator
```python
from core.exceptions import handle_errors, DataFetchError

@handle_errors(DataFetchError, default_return=pd.DataFrame())
def fetch_data(ticker: str) -> pd.DataFrame:
    # Exception otomatik handle edilir
    ...
```

### ✅ Yeni Yöntem - Explicit
```python
from core.exceptions import DataFetchError, DataValidationError

def fetch_data(ticker: str) -> pd.DataFrame:
    try:
        data = api.get(ticker)
    except APIError as e:
        raise DataFetchError(
            f"Failed to fetch {ticker}",
            source="polygon",
            ticker=ticker,
        ) from e

    if data.empty:
        raise DataValidationError(
            "Empty data received",
            field="data",
            ticker=ticker,
        )

    return data
```

### Exception Hiyerarşisi
```
FinPilotError (Base)
├── ConfigError
├── DataError
│   ├── DataFetchError
│   ├── DataValidationError
│   └── DataProcessingError
├── AuthError
│   ├── AuthenticationError
│   ├── AuthorizationError
│   └── TokenError
├── MarketError
│   ├── InsufficientFundsError
│   ├── OrderError
│   └── PositionError
├── ModelError
│   ├── ModelNotFoundError
│   └── InferenceError
└── CacheError
```

---

## 3. Cache Migration

### ❌ Eski Yöntem
```python
@st.cache_data(ttl=300)
def get_stock_data(ticker: str):
    ...
```

### ✅ Yeni Yöntem
```python
from core.cache import cached, cache_market_data

# Generic cache
@cached(ttl=300, prefix="stock")
def get_stock_data(ticker: str):
    ...

# Specialized decorator
@cache_market_data(ttl=60)
def get_realtime_price(ticker: str):
    ...
```

### Manuel Cache Kullanımı
```python
from core.cache import cache_manager

# Set
cache_manager.set("portfolio:user123", portfolio_data, ttl=3600)

# Get
data = cache_manager.get("portfolio:user123")

# Get or compute
data = cache_manager.get_or_set(
    "expensive:key",
    factory=lambda: compute_expensive_thing(),
    ttl=1800
)
```

---

## 4. Logging Migration

### ❌ Eski Yöntem
```python
print(f"Scanning {ticker}...")
```

### ✅ Yeni Yöntem
```python
from core.logging import get_logger, log_context

logger = get_logger(__name__)

# Basic logging
logger.info("Scanning started", extra={"ticker": ticker, "interval": "1d"})

# Context-aware logging
with log_context(user_id=user.id, session_id=session.id):
    logger.info("User action")  # Otomatik context eklenir

# Timing
from core.logging import Timer

with Timer("data_processing") as t:
    process_data()

print(f"Took {t.duration:.2f}s")
```

### Log Output (JSON format)
```json
{
    "timestamp": "2025-01-25T12:00:00.000Z",
    "level": "INFO",
    "logger": "finpilot.scanner",
    "message": "Scanning started",
    "context": {"ticker": "AAPL", "interval": "1d"},
    "source": {"file": "scanner.py", "line": 42}
}
```

---

## 5. Monitoring Migration

### Metrics Kullanımı
```python
from core.monitoring import metrics, track_time, count_calls

# Manual metric
metrics.signals_generated.inc(ticker="AAPL", signal_type="buy")
metrics.scan_duration.observe(1.23, scan_type="full")

# Decorators
@count_calls(metrics.scans_total, scan_type="quick")
@track_time(metrics.scan_duration, scan_type="quick")
def quick_scan():
    ...
```

### Mevcut Metrikler
```python
# Scanner
metrics.scans_total           # Counter - toplam scan sayısı
metrics.signals_generated     # Counter - üretilen sinyaller
metrics.scan_duration         # Histogram - scan süresi
metrics.tickers_scanned       # Gauge - taranan ticker sayısı

# DRL
metrics.training_episodes     # Counter - eğitim episode'ları
metrics.training_reward       # Gauge - son reward
metrics.model_inference_duration  # Histogram - inference süresi

# Auth
metrics.login_attempts        # Counter - login denemeleri
metrics.active_sessions       # Gauge - aktif session sayısı

# System
metrics.errors_total          # Counter - hatalar
metrics.cache_hits            # Counter - cache hit'leri
metrics.memory_usage          # Gauge - memory kullanımı
```

### Health Checks
```python
from core.monitoring import health_check, HealthCheckResult, HealthStatus

@health_check.register("external_api")
def check_polygon():
    try:
        response = requests.get("https://api.polygon.io/v2/status")
        return response.status_code == 200
    except Exception:
        return False

# Run all checks
status = health_check.run()
# {"status": "healthy", "checks": [...]}
```

### Prometheus Export
```python
from core.monitoring import metrics

# Prometheus format
prometheus_output = metrics.export_prometheus()
```

---

## 6. Quick Start - Yeni Modül Oluşturma

```python
"""
views/new_feature.py
"""
from core.config import settings
from core.exceptions import handle_errors, DataError
from core.cache import cached
from core.logging import get_logger
from core.monitoring import metrics

logger = get_logger(__name__)


@cached(ttl=300, prefix="feature")
@handle_errors(DataError, default_return=[])
def get_feature_data(ticker: str) -> list:
    """
    New feature implementation using core infrastructure.
    """
    logger.info("Fetching feature data", extra={"ticker": ticker})

    # Use centralized settings
    if settings.scanner.min_price > 0:
        # filter logic
        pass

    # Track metrics
    metrics.api_requests.inc(endpoint="feature", status_code="200")

    return data
```

---

## 7. Testing with Core

```python
import pytest
from core.config import override_settings
from core.exceptions import DataFetchError

def test_with_custom_config():
    """Test with overridden settings."""
    test_settings = override_settings(DEBUG=True)
    assert test_settings.DEBUG is True

def test_exception_handling():
    """Test custom exceptions."""
    with pytest.raises(DataFetchError) as exc_info:
        raise DataFetchError("Test", ticker="AAPL")

    assert exc_info.value.details["ticker"] == "AAPL"
```

---

## 8. Checklist - Module Migration

Her modül için:

- [ ] `from core.config import settings` ekle
- [ ] Hardcoded değerleri `settings.X` ile değiştir
- [ ] `except Exception:` bloklarını `@handle_errors` ile değiştir
- [ ] `print()` ifadelerini `logger.X()` ile değiştir
- [ ] Expensive işlemlere `@cached` ekle
- [ ] Önemli event'lere metrics ekle
- [ ] Test'leri güncelle

---

## 📊 Mevcut Durum

| Modül | Config | Exceptions | Cache | Logging | Metrics |
|-------|--------|------------|-------|---------|---------|
| scanner/ | ✅ Partial | ⚠️ TODO | ✅ Own | ⚠️ TODO | ⚠️ TODO |
| drl/ | ⚠️ TODO | ⚠️ TODO | ⚠️ TODO | ⚠️ TODO | ⚠️ TODO |
| auth/ | ✅ Own | ✅ Own | ⚠️ TODO | ⚠️ TODO | ⚠️ TODO |
| views/ | ⚠️ TODO | ⚠️ TODO | ✅ st.cache | ⚠️ TODO | ⚠️ TODO |

✅ = Entegre
⚠️ = Migration gerekli
