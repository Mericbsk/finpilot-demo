"""
FinPilot Input Validation Models
================================

Pydantic models for validating user inputs, API requests,
and form data throughout the application.

Usage:
    from core.validation import ScanRequest, UserSettingsInput

    # Validate scan request
    request = ScanRequest(symbols=["AAPL", "MSFT"], aggressive=True)

    # Validate user settings
    settings = UserSettingsInput(risk_score=7, portfolio_size=10000)

Author: FinPilot Team
Version: 1.0.0
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# =============================================================================
# TICKER SYMBOL VALIDATION
# =============================================================================


class TickerSymbol(BaseModel):
    """Validated stock ticker symbol."""

    symbol: str = Field(..., min_length=1, max_length=10)

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """
        Validate and normalize ticker symbol.

        - Uppercase
        - Allow alphanumeric, dot, hyphen
        - Common patterns: AAPL, BRK-B, THYAO.IS
        """
        v = v.strip().upper()

        if not v:
            raise ValueError("Symbol cannot be empty")

        # Allow: letters, numbers, dot, hyphen
        pattern = r"^[A-Z0-9][A-Z0-9.\-]{0,9}$"
        if not re.match(pattern, v):
            raise ValueError(
                f"Invalid symbol format: {v}. " "Use letters, numbers, dots, or hyphens only."
            )

        return v


class TickerList(BaseModel):
    """Validated list of ticker symbols."""

    symbols: List[str] = Field(..., min_length=1, max_length=500)

    @field_validator("symbols")
    @classmethod
    def validate_symbols(cls, v: List[str]) -> List[str]:
        """Validate and normalize all symbols."""
        validated = []
        for symbol in v:
            try:
                ts = TickerSymbol(symbol=symbol)
                validated.append(ts.symbol)
            except ValueError as e:
                raise ValueError(f"Invalid symbol in list: {e}")

        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for s in validated:
            if s not in seen:
                seen.add(s)
                unique.append(s)

        return unique


# =============================================================================
# SCAN REQUEST VALIDATION
# =============================================================================


class ScanRequest(BaseModel):
    """Validated scan request parameters."""

    model_config = ConfigDict(str_strip_whitespace=True)

    symbols: Optional[List[str]] = Field(
        default=None, description="List of symbols to scan. If None, uses default list."
    )

    aggressive: bool = Field(
        default=False, description="Enable aggressive mode with relaxed thresholds"
    )

    market: Literal["US", "BIST", "ETF", "ALL"] = Field(default="US", description="Market to scan")

    timeframe: Literal["1h", "4h", "1d", "1w"] = Field(
        default="1d", description="Primary timeframe for analysis"
    )

    max_results: int = Field(
        default=50, ge=1, le=500, description="Maximum number of results to return"
    )

    include_etf: bool = Field(default=False, description="Include ETFs in scan results")

    @field_validator("symbols")
    @classmethod
    def validate_symbols(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return None

        tl = TickerList(symbols=v)
        return tl.symbols


# =============================================================================
# USER SETTINGS VALIDATION
# =============================================================================


class UserSettingsInput(BaseModel):
    """Validated user settings input."""

    model_config = ConfigDict(str_strip_whitespace=True)

    risk_score: int = Field(
        default=5, ge=1, le=10, description="Risk tolerance (1=conservative, 10=aggressive)"
    )

    portfolio_size: float = Field(
        default=10000.0, ge=100.0, le=100_000_000.0, description="Total portfolio size in USD"
    )

    max_loss_pct: float = Field(
        default=10.0, ge=1.0, le=50.0, description="Maximum acceptable loss percentage"
    )

    strategy: Literal["Normal", "Agresif", "Defansif", "Momentum"] = Field(
        default="Normal", description="Trading strategy preset"
    )

    market: Literal["US", "BIST", "ETF"] = Field(default="US", description="Primary market focus")

    telegram_active: bool = Field(default=False, description="Enable Telegram notifications")

    telegram_id: str = Field(
        default="", max_length=50, description="Telegram chat ID for notifications"
    )

    @field_validator("telegram_id")
    @classmethod
    def validate_telegram_id(cls, v: str, info) -> str:
        """Validate Telegram ID format."""
        v = v.strip()

        if not v:
            return ""

        # Telegram IDs are numeric
        if not v.lstrip("-").isdigit():
            raise ValueError("Telegram ID must be numeric")

        return v

    @model_validator(mode="after")
    def check_telegram_config(self) -> "UserSettingsInput":
        """Ensure Telegram ID is set if active."""
        if self.telegram_active and not self.telegram_id:
            raise ValueError("Telegram ID required when notifications are active")
        return self


# =============================================================================
# AUTHENTICATION VALIDATION
# =============================================================================


class LoginRequest(BaseModel):
    """Validated login request."""

    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=1, max_length=128)
    remember_me: bool = Field(default=False)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Basic email validation."""
        v = v.strip().lower()

        # Simple regex for email
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError("Invalid email format")

        return v


class RegisterRequest(BaseModel):
    """Validated registration request."""

    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(..., min_length=5, max_length=255)
    username: str = Field(..., min_length=3, max_length=30)
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)
    display_name: Optional[str] = Field(default=None, max_length=100)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError("Invalid email format")
        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()

        # Alphanumeric and underscore only
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]{2,29}$", v):
            raise ValueError(
                "Username must start with a letter and contain "
                "only letters, numbers, and underscores"
            )

        return v

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength."""
        issues = []

        if len(v) < 8:
            issues.append("at least 8 characters")
        if not any(c.isupper() for c in v):
            issues.append("one uppercase letter")
        if not any(c.islower() for c in v):
            issues.append("one lowercase letter")
        if not any(c.isdigit() for c in v):
            issues.append("one digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            issues.append("one special character")

        if issues:
            raise ValueError(f"Password must contain: {', '.join(issues)}")

        return v

    @model_validator(mode="after")
    def check_passwords_match(self) -> "RegisterRequest":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


# =============================================================================
# API/TRADING VALIDATION
# =============================================================================


class PriceTarget(BaseModel):
    """Validated price target input."""

    entry_price: float = Field(..., gt=0)
    stop_loss: float = Field(..., gt=0)
    take_profit: float = Field(..., gt=0)

    @model_validator(mode="after")
    def validate_price_logic(self) -> "PriceTarget":
        """Ensure price targets make sense."""
        # For long positions: SL < Entry < TP
        if self.stop_loss >= self.entry_price:
            raise ValueError("Stop loss must be below entry price for long positions")

        if self.take_profit <= self.entry_price:
            raise ValueError("Take profit must be above entry price for long positions")

        return self


class PositionSize(BaseModel):
    """Validated position sizing input."""

    portfolio_value: float = Field(..., gt=0)
    risk_per_trade_pct: float = Field(default=2.0, ge=0.1, le=10.0)
    entry_price: float = Field(..., gt=0)
    stop_loss_price: float = Field(..., gt=0)

    @property
    def risk_amount(self) -> float:
        """Calculate dollar risk amount."""
        return self.portfolio_value * (self.risk_per_trade_pct / 100)

    @property
    def shares(self) -> int:
        """Calculate number of shares based on risk."""
        price_risk = abs(self.entry_price - self.stop_loss_price)
        if price_risk <= 0:
            return 0
        return int(self.risk_amount / price_risk)

    @property
    def position_value(self) -> float:
        """Calculate total position value."""
        return self.shares * self.entry_price


# =============================================================================
# FILTER/SEARCH VALIDATION
# =============================================================================


class SignalFilter(BaseModel):
    """Validated signal filter parameters."""

    min_score: int = Field(default=0, ge=0, le=100)
    max_score: int = Field(default=100, ge=0, le=100)

    min_rsi: float = Field(default=0, ge=0, le=100)
    max_rsi: float = Field(default=100, ge=0, le=100)

    min_volume: Optional[int] = Field(default=None, ge=0)

    entry_ok_only: bool = Field(default=False)

    sectors: Optional[List[str]] = Field(default=None)

    @model_validator(mode="after")
    def validate_ranges(self) -> "SignalFilter":
        if self.min_score > self.max_score:
            raise ValueError("min_score cannot be greater than max_score")

        if self.min_rsi > self.max_rsi:
            raise ValueError("min_rsi cannot be greater than max_rsi")

        return self


# =============================================================================
# EXPORT HELPERS
# =============================================================================

__all__ = [
    # Ticker
    "TickerSymbol",
    "TickerList",
    # Scan
    "ScanRequest",
    # User
    "UserSettingsInput",
    # Auth
    "LoginRequest",
    "RegisterRequest",
    # Trading
    "PriceTarget",
    "PositionSize",
    # Filter
    "SignalFilter",
]
