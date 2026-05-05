"""
Tests for core.validation module.

Tests Pydantic validation models for input validation.
"""

import pytest
from pydantic import ValidationError

from core.validation import (
    LoginRequest,
    PositionSize,
    PriceTarget,
    RegisterRequest,
    ScanRequest,
    SignalFilter,
    TickerList,
    TickerSymbol,
    UserSettingsInput,
)

# =============================================================================
# TICKER SYMBOL TESTS
# =============================================================================


class TestTickerSymbol:
    """Tests for ticker symbol validation."""

    def test_valid_simple_symbol(self):
        """Should accept simple symbols like AAPL."""
        ts = TickerSymbol(symbol="AAPL")
        assert ts.symbol == "AAPL"

    def test_uppercase_conversion(self):
        """Should convert to uppercase."""
        ts = TickerSymbol(symbol="aapl")
        assert ts.symbol == "AAPL"

    def test_valid_with_hyphen(self):
        """Should accept symbols with hyphen like BRK-B."""
        ts = TickerSymbol(symbol="BRK-B")
        assert ts.symbol == "BRK-B"

    def test_valid_with_dot(self):
        """Should accept symbols with dot like THYAO.IS."""
        ts = TickerSymbol(symbol="THYAO.IS")
        assert ts.symbol == "THYAO.IS"

    def test_strips_whitespace(self):
        """Should strip leading/trailing whitespace."""
        ts = TickerSymbol(symbol="  AAPL  ")
        assert ts.symbol == "AAPL"

    def test_rejects_empty(self):
        """Should reject empty symbol."""
        with pytest.raises(ValidationError):
            TickerSymbol(symbol="")

    def test_rejects_too_long(self):
        """Should reject symbols > 10 chars."""
        with pytest.raises(ValidationError):
            TickerSymbol(symbol="TOOLONGSYMBOL")

    def test_rejects_special_chars(self):
        """Should reject invalid special characters."""
        with pytest.raises(ValidationError):
            TickerSymbol(symbol="AAP$L")


class TestTickerList:
    """Tests for ticker list validation."""

    def test_valid_list(self):
        """Should accept valid symbol list."""
        tl = TickerList(symbols=["AAPL", "MSFT", "GOOGL"])
        assert len(tl.symbols) == 3

    def test_removes_duplicates(self):
        """Should remove duplicate symbols."""
        tl = TickerList(symbols=["AAPL", "MSFT", "AAPL"])
        assert tl.symbols == ["AAPL", "MSFT"]

    def test_uppercase_all(self):
        """Should uppercase all symbols."""
        tl = TickerList(symbols=["aapl", "msft"])
        assert tl.symbols == ["AAPL", "MSFT"]

    def test_rejects_empty_list(self):
        """Should reject empty list."""
        with pytest.raises(ValidationError):
            TickerList(symbols=[])

    def test_rejects_invalid_in_list(self):
        """Should reject if any symbol is invalid."""
        with pytest.raises(ValidationError):
            TickerList(symbols=["AAPL", "INVALID$$$"])


# =============================================================================
# SCAN REQUEST TESTS
# =============================================================================


class TestScanRequest:
    """Tests for scan request validation."""

    def test_default_values(self):
        """Should use sensible defaults."""
        sr = ScanRequest()

        assert sr.symbols is None
        assert sr.aggressive is False
        assert sr.market == "US"
        assert sr.timeframe == "1d"
        assert sr.max_results == 50

    def test_valid_aggressive_mode(self):
        """Should accept aggressive mode."""
        sr = ScanRequest(aggressive=True)
        assert sr.aggressive is True

    def test_valid_market(self):
        """Should accept valid markets."""
        for market in ["US", "BIST", "ETF", "ALL"]:
            sr = ScanRequest(market=market)  # type: ignore[arg-type]
            assert sr.market == market

    def test_rejects_invalid_market(self):
        """Should reject invalid market."""
        with pytest.raises(ValidationError):
            ScanRequest(market="INVALID")  # type: ignore[arg-type]

    def test_max_results_bounds(self):
        """Should enforce max_results bounds."""
        sr = ScanRequest(max_results=100)
        assert sr.max_results == 100

        with pytest.raises(ValidationError):
            ScanRequest(max_results=0)

        with pytest.raises(ValidationError):
            ScanRequest(max_results=1000)


# =============================================================================
# USER SETTINGS TESTS
# =============================================================================


class TestUserSettingsInput:
    """Tests for user settings validation."""

    def test_default_values(self):
        """Should have sensible defaults."""
        us = UserSettingsInput()

        assert us.risk_score == 5
        assert us.portfolio_size == 10000.0
        assert us.strategy == "Normal"

    def test_risk_score_bounds(self):
        """Should enforce risk score 1-10."""
        us = UserSettingsInput(risk_score=7)
        assert us.risk_score == 7

        with pytest.raises(ValidationError):
            UserSettingsInput(risk_score=0)

        with pytest.raises(ValidationError):
            UserSettingsInput(risk_score=11)

    def test_portfolio_size_bounds(self):
        """Should enforce portfolio size bounds."""
        with pytest.raises(ValidationError):
            UserSettingsInput(portfolio_size=50)  # Too small

    def test_telegram_validation(self):
        """Should validate Telegram config."""
        # Valid: active with ID
        us = UserSettingsInput(telegram_active=True, telegram_id="123456789")
        assert us.telegram_active is True

        # Invalid: active without ID
        with pytest.raises(ValidationError):
            UserSettingsInput(telegram_active=True, telegram_id="")

    def test_telegram_id_format(self):
        """Should validate Telegram ID is numeric."""
        us = UserSettingsInput(telegram_id="123456789")
        assert us.telegram_id == "123456789"

        # Negative IDs are valid (group chats)
        us = UserSettingsInput(telegram_id="-100123456789")
        assert us.telegram_id == "-100123456789"

        # Non-numeric should fail
        with pytest.raises(ValidationError):
            UserSettingsInput(telegram_active=True, telegram_id="abc123")


# =============================================================================
# AUTH VALIDATION TESTS
# =============================================================================


class TestLoginRequest:
    """Tests for login request validation."""

    def test_valid_login(self):
        """Should accept valid login."""
        lr = LoginRequest(email="user@example.com", password="password123")

        assert lr.email == "user@example.com"

    def test_email_lowercase(self):
        """Should lowercase email."""
        lr = LoginRequest(email="User@EXAMPLE.COM", password="password")

        assert lr.email == "user@example.com"

    def test_rejects_invalid_email(self):
        """Should reject invalid email format."""
        with pytest.raises(ValidationError):
            LoginRequest(email="not-an-email", password="password")


class TestRegisterRequest:
    """Tests for registration validation."""

    def test_valid_registration(self):
        """Should accept valid registration."""
        rr = RegisterRequest(
            email="user@example.com",
            username="testuser",
            password="SecurePass123!",
            confirm_password="SecurePass123!",
        )

        assert rr.email == "user@example.com"
        assert rr.username == "testuser"

    def test_password_mismatch(self):
        """Should reject mismatched passwords."""
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="user@example.com",
                username="testuser",
                password="SecurePass123!",
                confirm_password="DifferentPass123!",
            )

    def test_weak_password(self):
        """Should reject weak password."""
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="user@example.com",
                username="testuser",
                password="weak",
                confirm_password="weak",
            )

    def test_invalid_username(self):
        """Should reject invalid username."""
        # Must start with letter
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="user@example.com",
                username="123user",
                password="SecurePass123!",
                confirm_password="SecurePass123!",
            )


# =============================================================================
# TRADING VALIDATION TESTS
# =============================================================================


class TestPriceTarget:
    """Tests for price target validation."""

    def test_valid_long_position(self):
        """Should accept valid long position targets."""
        pt = PriceTarget(entry_price=100.0, stop_loss=95.0, take_profit=110.0)

        assert pt.entry_price == 100.0

    def test_rejects_sl_above_entry(self):
        """Should reject stop loss above entry for long."""
        with pytest.raises(ValidationError):
            PriceTarget(entry_price=100.0, stop_loss=105.0, take_profit=110.0)  # Above entry

    def test_rejects_tp_below_entry(self):
        """Should reject take profit below entry for long."""
        with pytest.raises(ValidationError):
            PriceTarget(entry_price=100.0, stop_loss=95.0, take_profit=98.0)  # Below entry


class TestPositionSize:
    """Tests for position sizing validation."""

    def test_calculates_shares(self):
        """Should calculate correct number of shares."""
        ps = PositionSize(
            portfolio_value=10000.0, risk_per_trade_pct=2.0, entry_price=100.0, stop_loss_price=95.0
        )

        # Risk: $200, Price risk: $5, Shares: 40
        assert ps.risk_amount == 200.0
        assert ps.shares == 40
        assert ps.position_value == 4000.0

    def test_risk_percentage_bounds(self):
        """Should enforce risk percentage bounds."""
        with pytest.raises(ValidationError):
            PositionSize(
                portfolio_value=10000,
                risk_per_trade_pct=15.0,  # Too high
                entry_price=100,
                stop_loss_price=95,
            )


class TestSignalFilter:
    """Tests for signal filter validation."""

    def test_default_values(self):
        """Should have sensible defaults."""
        sf = SignalFilter()

        assert sf.min_score == 0
        assert sf.max_score == 100
        assert sf.entry_ok_only is False

    def test_rejects_inverted_range(self):
        """Should reject min > max."""
        with pytest.raises(ValidationError):
            SignalFilter(min_score=80, max_score=20)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
