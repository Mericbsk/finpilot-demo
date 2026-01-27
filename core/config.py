"""
FinPilot Merkezi Konfigürasyon
==============================

Pydantic Settings ile tüm konfigürasyonların merkezi yönetimi.
.env dosyası, environment variables ve varsayılan değerler tek noktada.

Kullanım:
    from core.config import settings

    print(settings.POLYGON_API_KEY)
    print(settings.scanner.rsi_oversold)

Author: FinPilot Team
Version: 1.0.0
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# =============================================================================
# BASE PATHS
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
LOGS_DIR = DATA_DIR / "logs"
CACHE_DIR = PROJECT_ROOT / ".cache"

# Ensure directories exist
for dir_path in [DATA_DIR, MODELS_DIR, LOGS_DIR, CACHE_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)


# =============================================================================
# NESTED CONFIG MODELS
# =============================================================================


class ScannerConfig(BaseModel):
    """Scanner modülü konfigürasyonu."""

    # RSI Settings
    rsi_oversold: float = Field(default=30.0, ge=0, le=100)
    rsi_overbought: float = Field(default=70.0, ge=0, le=100)
    rsi_period: int = Field(default=14, ge=1)

    # Volume Settings
    volume_surge_threshold: float = Field(default=2.0, ge=1.0)
    min_volume: int = Field(default=100_000, ge=0)

    # Price Settings
    min_price: float = Field(default=5.0, ge=0)
    max_price: float = Field(default=500.0, ge=0)

    # MACD Settings
    macd_fast: int = Field(default=12, ge=1)
    macd_slow: int = Field(default=26, ge=1)
    macd_signal: int = Field(default=9, ge=1)

    # Bollinger Bands
    bb_period: int = Field(default=20, ge=1)
    bb_std: float = Field(default=2.0, ge=0)

    # Z-Score
    zscore_threshold: float = Field(default=-2.0)
    zscore_lookback: int = Field(default=20, ge=1)

    # Scanning
    max_stocks_to_scan: int = Field(default=500, ge=1)
    signal_threshold: int = Field(default=3, ge=1)

    @model_validator(mode="after")
    def validate_rsi_range(self) -> "ScannerConfig":
        if self.rsi_oversold >= self.rsi_overbought:
            raise ValueError("rsi_oversold must be less than rsi_overbought")
        return self


class DRLConfig(BaseModel):
    """Deep Reinforcement Learning modülü konfigürasyonu."""

    # Model Settings
    algorithm: Literal["PPO", "A2C", "SAC", "TD3"] = "PPO"
    policy: str = "MlpPolicy"
    total_timesteps: int = Field(default=100_000, ge=1000)

    # Network Architecture
    hidden_layers: list[int] = Field(default=[256, 256])
    activation: Literal["tanh", "relu", "elu"] = "tanh"

    # Training Hyperparameters
    learning_rate: float = Field(default=3e-4, gt=0)
    batch_size: int = Field(default=64, ge=1)
    n_epochs: int = Field(default=10, ge=1)
    gamma: float = Field(default=0.99, ge=0, le=1)
    gae_lambda: float = Field(default=0.95, ge=0, le=1)
    clip_range: float = Field(default=0.2, ge=0, le=1)

    # Environment
    initial_balance: float = Field(default=100_000.0, gt=0)
    transaction_cost: float = Field(default=0.001, ge=0)
    max_position_size: float = Field(default=0.2, ge=0, le=1)
    lookback_window: int = Field(default=30, ge=1)

    # Features
    feature_columns: list[str] = Field(
        default=[
            "open",
            "high",
            "low",
            "close",
            "volume",
            "rsi",
            "macd",
            "macd_signal",
            "bb_upper",
            "bb_lower",
        ]
    )

    # Validation
    validation_split: float = Field(default=0.2, ge=0, lt=1)
    early_stopping_patience: int = Field(default=10, ge=1)


class AuthConfig(BaseModel):
    """Authentication modülü konfigürasyonu."""

    # JWT Settings
    secret_key: str = Field(default="finpilot-secret-key-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=30, ge=1)
    refresh_token_expire_days: int = Field(default=7, ge=1)

    # Password Policy
    min_password_length: int = Field(default=8, ge=4)
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digit: bool = True
    require_special: bool = False

    # Rate Limiting
    max_login_attempts: int = Field(default=5, ge=1)
    lockout_duration_minutes: int = Field(default=15, ge=1)

    # Session
    session_timeout_minutes: int = Field(default=60, ge=1)


class TelegramConfig(BaseModel):
    """Telegram bot konfigürasyonu."""

    enabled: bool = False
    bot_token: str = ""
    chat_id: str = ""

    # Notification Settings
    send_signals: bool = True
    send_daily_summary: bool = True
    send_errors: bool = True

    # Rate Limiting
    max_messages_per_minute: int = Field(default=20, ge=1)


class CacheConfig(BaseModel):
    """Cache sistemi konfigürasyonu."""

    enabled: bool = True

    # Memory Cache (L1)
    memory_max_size: int = Field(default=1000, ge=1)
    memory_ttl_seconds: int = Field(default=300, ge=1)  # 5 minutes

    # Redis Cache (L2) - Optional
    redis_enabled: bool = False
    redis_url: str = "redis://localhost:6379/0"
    redis_ttl_seconds: int = Field(default=3600, ge=1)  # 1 hour

    # Specific TTLs
    market_data_ttl: int = Field(default=60, ge=1)  # 1 minute
    feature_ttl: int = Field(default=300, ge=1)  # 5 minutes
    model_ttl: int = Field(default=3600, ge=1)  # 1 hour


class MonitoringConfig(BaseModel):
    """Monitoring ve observability konfigürasyonu."""

    enabled: bool = True

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: Literal["json", "text"] = "json"
    log_file: Optional[str] = None

    # Prometheus
    prometheus_enabled: bool = False
    prometheus_port: int = Field(default=8000, ge=1, le=65535)

    # MLflow
    mlflow_enabled: bool = False
    mlflow_tracking_uri: str = "sqlite:///mlflow.db"
    mlflow_experiment_name: str = "finpilot-drl"


class DatabaseConfig(BaseModel):
    """Database konfigürasyonu."""

    # SQLite (Default)
    sqlite_path: str = str(DATA_DIR / "finpilot.db")

    # PostgreSQL (Optional)
    postgres_enabled: bool = False
    postgres_url: str = ""

    # Connection Pool
    pool_size: int = Field(default=5, ge=1)
    max_overflow: int = Field(default=10, ge=0)


class APIConfig(BaseModel):
    """External API konfigürasyonları."""

    # Polygon.io
    polygon_api_key: str = ""
    polygon_base_url: str = "https://api.polygon.io"

    # Alpha Vantage
    alpha_vantage_api_key: str = ""

    # Finnhub
    finnhub_api_key: str = ""

    # Request Settings
    request_timeout: int = Field(default=30, ge=1)
    max_retries: int = Field(default=3, ge=0)
    retry_delay: float = Field(default=1.0, ge=0)


# =============================================================================
# MAIN SETTINGS CLASS
# =============================================================================


class Settings(BaseSettings):
    """
    Ana konfigürasyon sınıfı.

    Öncelik sırası:
    1. Environment variables
    2. .env file
    3. Default values

    Kullanım:
        from core.config import settings

        # Direct access
        print(settings.DEBUG)

        # Nested access
        print(settings.scanner.rsi_oversold)
    """

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    # ==========================================================================
    # APPLICATION SETTINGS
    # ==========================================================================

    APP_NAME: str = "FinPilot"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # ==========================================================================
    # API KEYS (from environment)
    # ==========================================================================

    POLYGON_API_KEY: str = ""
    ALPHA_VANTAGE_API_KEY: str = ""
    FINNHUB_API_KEY: str = ""
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    # ==========================================================================
    # NESTED CONFIGURATIONS
    # ==========================================================================

    scanner: ScannerConfig = Field(default_factory=ScannerConfig)
    drl: DRLConfig = Field(default_factory=DRLConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    api: APIConfig = Field(default_factory=APIConfig)

    # ==========================================================================
    # COMPUTED PROPERTIES
    # ==========================================================================

    @property
    def project_root(self) -> Path:
        return PROJECT_ROOT

    @property
    def data_dir(self) -> Path:
        return DATA_DIR

    @property
    def models_dir(self) -> Path:
        return MODELS_DIR

    @property
    def logs_dir(self) -> Path:
        return LOGS_DIR

    @property
    def cache_dir(self) -> Path:
        return CACHE_DIR

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    # ==========================================================================
    # VALIDATORS
    # ==========================================================================

    @model_validator(mode="after")
    def sync_api_keys(self) -> "Settings":
        """Sync top-level API keys to nested configs."""
        if self.POLYGON_API_KEY:
            self.api.polygon_api_key = self.POLYGON_API_KEY
        if self.ALPHA_VANTAGE_API_KEY:
            self.api.alpha_vantage_api_key = self.ALPHA_VANTAGE_API_KEY
        if self.FINNHUB_API_KEY:
            self.api.finnhub_api_key = self.FINNHUB_API_KEY
        if self.TELEGRAM_BOT_TOKEN:
            self.telegram.bot_token = self.TELEGRAM_BOT_TOKEN
            self.telegram.enabled = True
        if self.TELEGRAM_CHAT_ID:
            self.telegram.chat_id = self.TELEGRAM_CHAT_ID
        return self

    # ==========================================================================
    # UTILITY METHODS
    # ==========================================================================

    def get_scanner_preset(
        self, preset: Literal["conservative", "moderate", "aggressive"]
    ) -> ScannerConfig:
        """Get scanner config with preset values."""
        presets = {
            "conservative": ScannerConfig(
                rsi_oversold=25.0,
                rsi_overbought=75.0,
                volume_surge_threshold=2.5,
                signal_threshold=4,
            ),
            "moderate": ScannerConfig(),  # Default values
            "aggressive": ScannerConfig(
                rsi_oversold=35.0,
                rsi_overbought=65.0,
                volume_surge_threshold=1.5,
                signal_threshold=2,
            ),
        }
        return presets[preset]

    def to_dict(self) -> dict[str, Any]:
        """Export settings as dictionary (excluding secrets)."""
        data = self.model_dump()
        # Mask sensitive values
        sensitive_keys = ["api_key", "secret", "token", "password"]

        def mask_sensitive(d: dict) -> dict:
            for key, value in d.items():
                if isinstance(value, dict):
                    d[key] = mask_sensitive(value)
                elif isinstance(value, str) and any(s in key.lower() for s in sensitive_keys):
                    d[key] = "***" if value else ""
            return d

        return mask_sensitive(data)


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global instance for easy access
settings = get_settings()


# =============================================================================
# BACKWARD COMPATIBILITY
# =============================================================================


def get_scanner_settings() -> dict:
    """Legacy function for scanner module compatibility."""
    return settings.scanner.model_dump()


def get_drl_config() -> dict:
    """Legacy function for DRL module compatibility."""
    return settings.drl.model_dump()


# =============================================================================
# TESTING UTILITIES
# =============================================================================


def override_settings(**kwargs) -> Settings:
    """
    Create a new Settings instance with overridden values.
    Useful for testing.

    Usage:
        test_settings = override_settings(DEBUG=True, ENVIRONMENT="testing")
    """
    return Settings(**kwargs)


if __name__ == "__main__":
    # Print current configuration (masked)
    import json

    print(json.dumps(settings.to_dict(), indent=2))
