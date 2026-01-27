# -*- coding: utf-8 -*-
"""
Tests for WebSocket Feeds Module
"""
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.websocket_feeds import (
    FEED_PROVIDERS,
    BarMessage,
    FeedConfig,
    FeedStatus,
    FinnhubFeed,
    MessageType,
    MockFeed,
    PolygonFeed,
    QuoteMessage,
    TradeMessage,
    WebSocketFeed,
    create_feed,
    list_providers,
)

# ============================================
# Message Tests
# ============================================


class TestTradeMessage:
    """Tests for TradeMessage dataclass."""

    def test_trade_message_creation(self):
        """Test basic trade message creation."""
        trade = TradeMessage(
            symbol="AAPL",
            price=175.50,
            size=100,
            timestamp=datetime(2023, 1, 1, 10, 30, 0),
            exchange="NASDAQ",
        )

        assert trade.symbol == "AAPL"
        assert trade.price == 175.50
        assert trade.size == 100
        assert trade.exchange == "NASDAQ"

    def test_trade_message_to_dict(self):
        """Test trade message serialization."""
        trade = TradeMessage(
            symbol="AAPL",
            price=175.50,
            size=100,
            timestamp=datetime(2023, 1, 1, 10, 30, 0),
        )

        data = trade.to_dict()

        assert data["type"] == "trade"
        assert data["symbol"] == "AAPL"
        assert data["price"] == 175.50
        assert "timestamp" in data


class TestQuoteMessage:
    """Tests for QuoteMessage dataclass."""

    def test_quote_message_creation(self):
        """Test basic quote message creation."""
        quote = QuoteMessage(
            symbol="AAPL",
            bid=175.45,
            bid_size=500,
            ask=175.55,
            ask_size=300,
            timestamp=datetime(2023, 1, 1, 10, 30, 0),
        )

        assert quote.symbol == "AAPL"
        assert quote.bid == 175.45
        assert quote.ask == 175.55

    def test_quote_message_spread(self):
        """Test spread calculation."""
        quote = QuoteMessage(
            symbol="AAPL",
            bid=175.45,
            bid_size=500,
            ask=175.55,
            ask_size=300,
            timestamp=datetime.now(),
        )

        assert quote.spread == pytest.approx(0.10, rel=1e-2)

    def test_quote_message_mid(self):
        """Test mid price calculation."""
        quote = QuoteMessage(
            symbol="AAPL",
            bid=175.00,
            bid_size=500,
            ask=176.00,
            ask_size=300,
            timestamp=datetime.now(),
        )

        assert quote.mid == 175.50

    def test_quote_message_to_dict(self):
        """Test quote message serialization."""
        quote = QuoteMessage(
            symbol="AAPL",
            bid=175.45,
            bid_size=500,
            ask=175.55,
            ask_size=300,
            timestamp=datetime.now(),
        )

        data = quote.to_dict()

        assert data["type"] == "quote"
        assert "spread" in data


class TestBarMessage:
    """Tests for BarMessage dataclass."""

    def test_bar_message_creation(self):
        """Test basic bar message creation."""
        bar = BarMessage(
            symbol="AAPL",
            open=174.00,
            high=176.00,
            low=173.50,
            close=175.50,
            volume=1000000,
            timestamp=datetime(2023, 1, 1, 10, 30, 0),
        )

        assert bar.symbol == "AAPL"
        assert bar.open == 174.00
        assert bar.close == 175.50
        assert bar.volume == 1000000

    def test_bar_message_with_vwap(self):
        """Test bar message with VWAP."""
        bar = BarMessage(
            symbol="AAPL",
            open=174.00,
            high=176.00,
            low=173.50,
            close=175.50,
            volume=1000000,
            timestamp=datetime.now(),
            vwap=175.25,
        )

        assert bar.vwap == 175.25

    def test_bar_message_to_dict(self):
        """Test bar message serialization."""
        bar = BarMessage(
            symbol="AAPL",
            open=174.00,
            high=176.00,
            low=173.50,
            close=175.50,
            volume=1000000,
            timestamp=datetime.now(),
        )

        data = bar.to_dict()

        assert data["type"] == "bar"
        assert data["volume"] == 1000000


# ============================================
# FeedConfig Tests
# ============================================


class TestFeedConfig:
    """Tests for FeedConfig."""

    def test_config_creation(self):
        """Test config creation with defaults."""
        config = FeedConfig(api_key="test_key")

        assert config.api_key == "test_key"
        assert config.reconnect is True
        assert config.buffer_size == 1000

    def test_config_custom_values(self):
        """Test config with custom values."""
        config = FeedConfig(
            api_key="test_key",
            reconnect=False,
            reconnect_delay=5.0,
            rate_limit=50,
        )

        assert config.reconnect is False
        assert config.reconnect_delay == 5.0
        assert config.rate_limit == 50


# ============================================
# Feed Factory Tests
# ============================================


class TestFeedFactory:
    """Tests for feed factory functions."""

    def test_list_providers(self):
        """Test listing available providers."""
        providers = list_providers()

        assert "polygon" in providers
        assert "finnhub" in providers
        assert "mock" in providers

    def test_create_feed_polygon(self):
        """Test creating Polygon feed."""
        feed = create_feed("polygon", api_key="test_key")

        assert isinstance(feed, PolygonFeed)
        assert feed.name == "polygon"

    def test_create_feed_finnhub(self):
        """Test creating Finnhub feed."""
        feed = create_feed("finnhub", api_key="test_key")

        assert isinstance(feed, FinnhubFeed)
        assert feed.name == "finnhub"

    def test_create_feed_mock(self):
        """Test creating mock feed."""
        feed = create_feed("mock", api_key="test_key")

        assert isinstance(feed, MockFeed)
        assert feed.name == "mock"

    def test_create_feed_unknown_provider(self):
        """Test error for unknown provider."""
        with pytest.raises(ValueError, match="Unknown provider"):
            create_feed("unknown", api_key="test_key")


# ============================================
# WebSocketFeed Base Tests
# ============================================


class TestMockFeed:
    """Tests for MockFeed."""

    def test_mock_feed_creation(self):
        """Test mock feed creation."""
        feed = MockFeed(FeedConfig(api_key="test"))

        assert feed.status == FeedStatus.DISCONNECTED
        assert feed.name == "mock"

    def test_mock_feed_subscribe(self):
        """Test subscription."""
        feed = MockFeed(FeedConfig(api_key="test"))

        feed.subscribe(["AAPL", "GOOGL"])

        assert "AAPL" in feed.subscribed_symbols
        assert "GOOGL" in feed.subscribed_symbols

    def test_mock_feed_subscribe_single(self):
        """Test single symbol subscription."""
        feed = MockFeed(FeedConfig(api_key="test"))

        feed.subscribe("AAPL")

        assert "AAPL" in feed.subscribed_symbols

    def test_mock_feed_unsubscribe(self):
        """Test unsubscription."""
        feed = MockFeed(FeedConfig(api_key="test"))

        feed.subscribe(["AAPL", "GOOGL"])
        feed.unsubscribe("AAPL")

        assert "AAPL" not in feed.subscribed_symbols
        assert "GOOGL" in feed.subscribed_symbols

    def test_mock_feed_callback_registration(self):
        """Test callback registration."""
        feed = MockFeed(FeedConfig(api_key="test"))

        trades = []
        quotes = []

        def on_trade(t):
            trades.append(t)

        def on_quote(q):
            quotes.append(q)

        feed.subscribe(["AAPL"], on_trade=on_trade, on_quote=on_quote)

        assert len(feed._trade_callbacks) == 1
        assert len(feed._quote_callbacks) == 1

    def test_mock_feed_status_callback(self):
        """Test status callback registration."""
        feed = MockFeed(FeedConfig(api_key="test"))

        statuses = []

        def on_status(status, msg):
            statuses.append(status)

        feed.on_status(on_status)

        assert len(feed._status_callbacks) == 1


# ============================================
# PolygonFeed Tests
# ============================================


class TestPolygonFeed:
    """Tests for PolygonFeed."""

    def test_polygon_feed_creation(self):
        """Test Polygon feed creation."""
        feed = PolygonFeed(FeedConfig(api_key="test_key"))

        assert feed.name == "polygon"

    def test_polygon_websocket_url(self):
        """Test WebSocket URL."""
        feed = PolygonFeed(FeedConfig(api_key="test_key"))

        url = feed._get_websocket_url()

        assert "polygon.io" in url


# ============================================
# FinnhubFeed Tests
# ============================================


class TestFinnhubFeed:
    """Tests for FinnhubFeed."""

    def test_finnhub_feed_creation(self):
        """Test Finnhub feed creation."""
        feed = FinnhubFeed(FeedConfig(api_key="test_key"))

        assert feed.name == "finnhub"

    def test_finnhub_websocket_url(self):
        """Test WebSocket URL contains token."""
        feed = FinnhubFeed(FeedConfig(api_key="my_api_key"))

        url = feed._get_websocket_url()

        assert "finnhub.io" in url
        assert "my_api_key" in url


# ============================================
# Async Tests (require pytest-asyncio)
# ============================================


class TestMockFeedAsync:
    """Async tests for MockFeed."""

    @pytest.mark.skip(reason="Requires pytest-asyncio configuration")
    def test_mock_feed_connect(self):
        """Test mock feed connection."""
        pass

    @pytest.mark.skip(reason="Requires pytest-asyncio configuration")
    def test_mock_feed_disconnect(self):
        """Test mock feed disconnection."""
        pass

    @pytest.mark.skip(reason="Requires pytest-asyncio configuration")
    def test_mock_feed_generates_trades(self):
        """Test that mock feed generates trade data."""
        pass


# ============================================
# Rate Limiting Tests
# ============================================


class TestRateLimiting:
    """Tests for rate limiting functionality."""

    def test_rate_limit_check(self):
        """Test rate limit checking."""
        feed = MockFeed(FeedConfig(api_key="test", rate_limit=5))

        # First 5 should pass
        for _ in range(5):
            assert feed._check_rate_limit() is True

        # 6th should fail
        assert feed._check_rate_limit() is False
