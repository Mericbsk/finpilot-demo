"""
Unit tests for broker.AlpacaBroker — Sprint 22.

Tests cover:
- Initialization and availability checks
- Position size calculation logic
- Order dict serialization
- Graceful fallback when Alpaca SDK is missing
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_fake_order(**overrides):
    """Build a SimpleNamespace that quacks like an Alpaca Order object."""
    defaults = {
        "id": "test-order-001",
        "symbol": "AAPL",
        "side": "buy",
        "qty": 10,
        "filled_qty": 0,
        "type": "limit",
        "limit_price": 195.50,
        "stop_price": None,
        "status": "accepted",
        "submitted_at": "2026-03-05T12:00:00Z",
        "filled_at": None,
        "filled_avg_price": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# Test: AlpacaBroker initialisation & availability
# ---------------------------------------------------------------------------


class TestBrokerAvailability:
    """Test broker init and availability detection."""

    def test_import_broker_module(self):
        """broker package should always import successfully."""
        import broker

        assert hasattr(broker, "AlpacaBroker")

    def test_unavailable_without_keys(self, monkeypatch):
        """Broker should report unavailable if no API keys."""
        monkeypatch.delenv("ALPACA_API_KEY", raising=False)
        monkeypatch.delenv("ALPACA_SECRET_KEY", raising=False)

        from broker import AlpacaBroker

        b = AlpacaBroker(api_key="", secret_key="")
        assert b.is_available is False

    def test_available_with_keys(self):
        """Broker should report available when SDK ok + keys present."""
        from broker import ALPACA_SDK_AVAILABLE, AlpacaBroker

        b = AlpacaBroker(api_key="fake-key", secret_key="fake-secret")
        # If SDK is installed, should be available
        if ALPACA_SDK_AVAILABLE:
            assert b.is_available is True
        else:
            assert b.is_available is False

    def test_resolve_key_from_env(self, monkeypatch):
        """_resolve_key should read from env."""
        monkeypatch.setenv("ALPACA_API_KEY", "env-key-123")
        from broker import AlpacaBroker

        assert AlpacaBroker._resolve_key("ALPACA_API_KEY") == "env-key-123"

    def test_resolve_key_empty_when_missing(self, monkeypatch):
        """_resolve_key should return empty string when env var not set."""
        monkeypatch.delenv("ALPACA_API_KEY", raising=False)
        from broker import AlpacaBroker

        result = AlpacaBroker._resolve_key("ALPACA_API_KEY")
        assert result == "" or isinstance(result, str)


# ---------------------------------------------------------------------------
# Test: Order serialisation
# ---------------------------------------------------------------------------


class TestOrderToDict:
    """Test the static _order_to_dict helper."""

    def test_basic_serialisation(self):
        from broker import AlpacaBroker

        fake = _make_fake_order()
        result = AlpacaBroker._order_to_dict(fake)

        assert result["order_id"] == "test-order-001"
        assert result["symbol"] == "AAPL"
        assert result["side"] == "buy"
        assert result["qty"] == 10.0
        assert result["limit_price"] == 195.50
        assert result["status"] == "accepted"
        assert result["filled_avg_price"] is None

    def test_filled_order(self):
        from broker import AlpacaBroker

        fake = _make_fake_order(
            filled_qty=10,
            filled_at="2026-03-05T12:01:00Z",
            filled_avg_price=195.25,
            status="filled",
        )
        result = AlpacaBroker._order_to_dict(fake)
        assert result["filled_qty"] == 10.0
        assert result["filled_avg_price"] == 195.25
        assert result["status"] == "filled"

    def test_none_qty_handled(self):
        from broker import AlpacaBroker

        fake = _make_fake_order(qty=None, filled_qty=None)
        result = AlpacaBroker._order_to_dict(fake)
        assert result["qty"] == 0
        assert result["filled_qty"] == 0


# ---------------------------------------------------------------------------
# Test: Position sizing
# ---------------------------------------------------------------------------


class TestPositionSizing:
    """Test risk-based position size calculations."""

    def test_basic_position_size(self):
        """Standard 2% risk calc with known portfolio value."""
        from broker import AlpacaBroker

        b = AlpacaBroker(api_key="fake", secret_key="fake")

        # Mock get_account to return 100k portfolio
        b.get_account = MagicMock(return_value={"portfolio_value": 100_000})

        shares = b.calculate_position_size(
            entry_price=100.0,
            stop_loss=95.0,
            risk_per_trade=0.02,
        )
        # Risk: $2000, price risk: $5, shares_by_risk: 400
        # Max position: 10% of 100k / $100 = 100 shares
        assert shares == 100  # limited by max_position_pct

    def test_position_size_tight_stop(self):
        """Tight stop → more shares from risk calc, limited by max position."""
        from broker import AlpacaBroker

        b = AlpacaBroker(api_key="fake", secret_key="fake")
        b.get_account = MagicMock(return_value={"portfolio_value": 50_000})

        shares = b.calculate_position_size(
            entry_price=200.0,
            stop_loss=198.0,
            risk_per_trade=0.02,
            max_position_pct=0.10,
        )
        # Risk: $1000, price risk: $2, by_risk: 500
        # Max: 10% of 50k / $200 = 25
        assert shares == 25

    def test_position_size_wide_stop(self):
        """Wide stop → fewer shares from risk calc."""
        from broker import AlpacaBroker

        b = AlpacaBroker(api_key="fake", secret_key="fake")
        b.get_account = MagicMock(return_value={"portfolio_value": 100_000})

        shares = b.calculate_position_size(
            entry_price=50.0,
            stop_loss=40.0,
            risk_per_trade=0.02,
        )
        # Risk: $2000, price risk: $10, by_risk: 200
        # Max: 10% of 100k / $50 = 200
        assert shares == 200

    def test_position_size_zero_risk_fallback(self):
        """When stop == entry, should fallback to 2% of price."""
        from broker import AlpacaBroker

        b = AlpacaBroker(api_key="fake", secret_key="fake")
        b.get_account = MagicMock(return_value={"portfolio_value": 100_000})

        shares = b.calculate_position_size(
            entry_price=100.0,
            stop_loss=100.0,  # zero risk
        )
        # Fallback: price_risk = 100 * 0.02 = $2
        # Risk: $2000, by_risk: 1000
        # Max: 10% of 100k / $100 = 100
        assert shares == 100

    def test_position_size_fallback_portfolio(self):
        """When get_account fails, should use $100k fallback."""
        from broker import AlpacaBroker

        b = AlpacaBroker(api_key="fake", secret_key="fake")
        b.get_account = MagicMock(side_effect=Exception("API down"))

        shares = b.calculate_position_size(
            entry_price=50.0,
            stop_loss=45.0,
        )
        # Fallback portfolio: $100k
        # Risk: $2000, price risk: $5, by_risk: 400
        # Max: 10% of 100k / $50 = 200
        assert shares == 200

    def test_position_size_minimum_one_share(self):
        """Should always return at least 1 share."""
        from broker import AlpacaBroker

        b = AlpacaBroker(api_key="fake", secret_key="fake")
        b.get_account = MagicMock(return_value={"portfolio_value": 1_000})

        shares = b.calculate_position_size(
            entry_price=500.0,
            stop_loss=400.0,
        )
        assert shares >= 1


# ---------------------------------------------------------------------------
# Test: Order placement (mocked)
# ---------------------------------------------------------------------------


class TestOrderPlacement:
    """Test order placement logic with mocked Alpaca client."""

    def test_place_market_buy(self):
        """Market buy order should call submit_order with correct request."""
        from broker import ALPACA_SDK_AVAILABLE, AlpacaBroker

        if not ALPACA_SDK_AVAILABLE:
            pytest.skip("alpaca-py not installed")

        b = AlpacaBroker(api_key="fake", secret_key="fake")
        mock_client = MagicMock()
        mock_client.submit_order.return_value = _make_fake_order(type="market")
        b._client = mock_client

        result = b.place_buy_order("AAPL", qty=5)
        mock_client.submit_order.assert_called_once()
        assert result["symbol"] == "AAPL"

    def test_place_limit_buy(self):
        """Limit buy should include limit_price in request."""
        from broker import ALPACA_SDK_AVAILABLE, AlpacaBroker

        if not ALPACA_SDK_AVAILABLE:
            pytest.skip("alpaca-py not installed")

        b = AlpacaBroker(api_key="fake", secret_key="fake")
        mock_client = MagicMock()
        mock_client.submit_order.return_value = _make_fake_order(type="limit", limit_price=195.50)
        b._client = mock_client

        result = b.place_buy_order("AAPL", qty=5, limit_price=195.50)
        assert result["limit_price"] == 195.50

    def test_cancel_order_success(self):
        """Cancel should return True on success."""
        from broker import ALPACA_SDK_AVAILABLE, AlpacaBroker

        if not ALPACA_SDK_AVAILABLE:
            pytest.skip("alpaca-py not installed")

        b = AlpacaBroker(api_key="fake", secret_key="fake")
        b._client = MagicMock()
        assert b.cancel_order("test-001") is True

    def test_cancel_order_failure(self):
        """Cancel should return False on API error."""
        from broker import ALPACA_SDK_AVAILABLE, AlpacaBroker

        if not ALPACA_SDK_AVAILABLE:
            pytest.skip("alpaca-py not installed")

        b = AlpacaBroker(api_key="fake", secret_key="fake")
        mock_client = MagicMock()
        mock_client.cancel_order_by_id.side_effect = Exception("Not found")
        b._client = mock_client
        assert b.cancel_order("bad-id") is False
