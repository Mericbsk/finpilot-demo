# -*- coding: utf-8 -*-
"""
FinPilot WebSocket Data Feeds
=============================

Real-time price feeds via WebSocket connections.

Features:
- Multiple provider support (Polygon, Finnhub, Alpha Vantage)
- Automatic reconnection
- Message queue and buffering
- Rate limiting
- Subscription management

Usage:
    from core.websocket_feeds import WebSocketFeed, create_feed

    async def on_price(symbol: str, price: float, volume: int):
        print(f"{symbol}: ${price}")

    feed = create_feed("polygon", api_key="...")
    feed.subscribe(["AAPL", "GOOGL"], on_price)
    await feed.connect()
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union

logger = logging.getLogger(__name__)


# ============================================
# 📊 Core Types
# ============================================


class FeedStatus(str, Enum):
    """WebSocket connection status."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


class MessageType(str, Enum):
    """WebSocket message types."""

    TRADE = "trade"
    QUOTE = "quote"
    BAR = "bar"
    STATUS = "status"
    ERROR = "error"
    AUTH = "auth"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"


@dataclass
class TradeMessage:
    """Real-time trade data."""

    symbol: str
    price: float
    size: int
    timestamp: datetime
    exchange: str = ""
    conditions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "trade",
            "symbol": self.symbol,
            "price": self.price,
            "size": self.size,
            "timestamp": self.timestamp.isoformat(),
            "exchange": self.exchange,
        }


@dataclass
class QuoteMessage:
    """Real-time quote data."""

    symbol: str
    bid: float
    bid_size: int
    ask: float
    ask_size: int
    timestamp: datetime

    @property
    def spread(self) -> float:
        return self.ask - self.bid

    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "quote",
            "symbol": self.symbol,
            "bid": self.bid,
            "bid_size": self.bid_size,
            "ask": self.ask,
            "ask_size": self.ask_size,
            "spread": self.spread,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class BarMessage:
    """Real-time bar/candle data."""

    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    timestamp: datetime
    vwap: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "bar",
            "symbol": self.symbol,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "vwap": self.vwap,
            "timestamp": self.timestamp.isoformat(),
        }


# Type aliases
PriceCallback = Callable[[TradeMessage], None]
QuoteCallback = Callable[[QuoteMessage], None]
BarCallback = Callable[[BarMessage], None]
StatusCallback = Callable[[FeedStatus, str], None]


# ============================================
# ⚙️ Feed Configuration
# ============================================


@dataclass
class FeedConfig:
    """WebSocket feed configuration."""

    api_key: str
    url: str = ""
    reconnect: bool = True
    reconnect_delay: float = 1.0
    max_reconnect_delay: float = 60.0
    heartbeat_interval: float = 30.0
    buffer_size: int = 1000
    rate_limit: int = 100  # messages per second


# ============================================
# 🔌 WebSocket Feed Base Class
# ============================================


class WebSocketFeed(ABC):
    """
    Abstract base class for WebSocket feeds.

    Subclass for specific data providers.
    """

    name: str = "base"

    def __init__(self, config: FeedConfig):
        self.config = config
        self.status = FeedStatus.DISCONNECTED

        # Subscriptions
        self._subscribed_symbols: Set[str] = set()

        # Callbacks
        self._trade_callbacks: List[PriceCallback] = []
        self._quote_callbacks: List[QuoteCallback] = []
        self._bar_callbacks: List[BarCallback] = []
        self._status_callbacks: List[StatusCallback] = []

        # Internal state
        self._ws = None
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._reconnect_attempts = 0
        self._last_message_time = 0.0

        # Rate limiting
        self._message_count = 0
        self._rate_limit_reset = 0.0

    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        return self.status == FeedStatus.CONNECTED

    @property
    def subscribed_symbols(self) -> Set[str]:
        """Get subscribed symbols."""
        return self._subscribed_symbols.copy()

    # ----------------------------------------
    # Subscription Management
    # ----------------------------------------

    def subscribe(
        self,
        symbols: Union[str, List[str]],
        on_trade: Optional[PriceCallback] = None,
        on_quote: Optional[QuoteCallback] = None,
        on_bar: Optional[BarCallback] = None,
    ) -> None:
        """
        Subscribe to symbols.

        Args:
            symbols: Symbol or list of symbols
            on_trade: Callback for trade messages
            on_quote: Callback for quote messages
            on_bar: Callback for bar messages
        """
        if isinstance(symbols, str):
            symbols = [symbols]

        for symbol in symbols:
            self._subscribed_symbols.add(symbol.upper())

        if on_trade:
            self._trade_callbacks.append(on_trade)
        if on_quote:
            self._quote_callbacks.append(on_quote)
        if on_bar:
            self._bar_callbacks.append(on_bar)

        # Send subscription if already connected
        if self.is_connected:
            asyncio.create_task(self._send_subscribe(symbols))

    def unsubscribe(self, symbols: Union[str, List[str]]) -> None:
        """Unsubscribe from symbols."""
        if isinstance(symbols, str):
            symbols = [symbols]

        for symbol in symbols:
            self._subscribed_symbols.discard(symbol.upper())

        if self.is_connected:
            asyncio.create_task(self._send_unsubscribe(symbols))

    def on_status(self, callback: StatusCallback) -> None:
        """Register status change callback."""
        self._status_callbacks.append(callback)

    # ----------------------------------------
    # Connection Management
    # ----------------------------------------

    async def connect(self) -> bool:
        """
        Connect to WebSocket server.

        Returns:
            True if connected successfully
        """
        try:
            self._set_status(FeedStatus.CONNECTING)

            # Import websockets here to avoid hard dependency
            try:
                import websockets
            except ImportError:
                logger.error("websockets package not installed")
                self._set_status(FeedStatus.ERROR)
                return False

            url = self._get_websocket_url()
            self._ws = await websockets.connect(url)

            # Authenticate
            if not await self._authenticate():
                self._set_status(FeedStatus.ERROR)
                return False

            self._set_status(FeedStatus.CONNECTED)
            self._running = True
            self._reconnect_attempts = 0

            # Subscribe to symbols
            if self._subscribed_symbols:
                await self._send_subscribe(list(self._subscribed_symbols))

            # Start message processing
            asyncio.create_task(self._message_loop())
            asyncio.create_task(self._heartbeat_loop())

            logger.info(f"Connected to {self.name} WebSocket feed")
            return True

        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self._set_status(FeedStatus.ERROR)

            if self.config.reconnect:
                asyncio.create_task(self._reconnect())

            return False

    async def disconnect(self) -> None:
        """Disconnect from WebSocket server."""
        self._running = False

        if self._ws:
            await self._ws.close()
            self._ws = None

        self._set_status(FeedStatus.DISCONNECTED)
        logger.info(f"Disconnected from {self.name} feed")

    async def _reconnect(self) -> None:
        """Attempt to reconnect."""
        self._set_status(FeedStatus.RECONNECTING)

        delay = min(
            self.config.reconnect_delay * (2**self._reconnect_attempts),
            self.config.max_reconnect_delay,
        )

        logger.info(f"Reconnecting in {delay:.1f}s...")
        await asyncio.sleep(delay)

        self._reconnect_attempts += 1
        await self.connect()

    # ----------------------------------------
    # Message Processing
    # ----------------------------------------

    async def _message_loop(self) -> None:
        """Main message receiving loop."""
        try:
            async for message in self._ws:
                if not self._running:
                    break

                # Rate limiting
                if not self._check_rate_limit():
                    continue

                self._last_message_time = time.time()

                try:
                    data = json.loads(message)
                    await self._process_message(data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON: {message[:100]}")

        except Exception as e:
            logger.error(f"Message loop error: {e}")

            if self.config.reconnect and self._running:
                asyncio.create_task(self._reconnect())

    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeats."""
        while self._running:
            await asyncio.sleep(self.config.heartbeat_interval)

            if self._ws and self.is_connected:
                try:
                    await self._send_heartbeat()
                except Exception as e:
                    logger.warning(f"Heartbeat failed: {e}")

    def _check_rate_limit(self) -> bool:
        """Check if within rate limit."""
        now = time.time()

        if now > self._rate_limit_reset:
            self._message_count = 0
            self._rate_limit_reset = now + 1.0

        self._message_count += 1
        return self._message_count <= self.config.rate_limit

    # ----------------------------------------
    # Callbacks
    # ----------------------------------------

    def _emit_trade(self, trade: TradeMessage) -> None:
        """Emit trade to all callbacks."""
        for callback in self._trade_callbacks:
            try:
                callback(trade)
            except Exception as e:
                logger.error(f"Trade callback error: {e}")

    def _emit_quote(self, quote: QuoteMessage) -> None:
        """Emit quote to all callbacks."""
        for callback in self._quote_callbacks:
            try:
                callback(quote)
            except Exception as e:
                logger.error(f"Quote callback error: {e}")

    def _emit_bar(self, bar: BarMessage) -> None:
        """Emit bar to all callbacks."""
        for callback in self._bar_callbacks:
            try:
                callback(bar)
            except Exception as e:
                logger.error(f"Bar callback error: {e}")

    def _set_status(self, status: FeedStatus, message: str = "") -> None:
        """Set status and notify callbacks."""
        self.status = status
        for callback in self._status_callbacks:
            try:
                callback(status, message)
            except Exception as e:
                logger.error(f"Status callback error: {e}")

    # ----------------------------------------
    # Abstract Methods (Provider-Specific)
    # ----------------------------------------

    @abstractmethod
    def _get_websocket_url(self) -> str:
        """Get WebSocket URL for provider."""
        pass

    @abstractmethod
    async def _authenticate(self) -> bool:
        """Authenticate with provider."""
        pass

    @abstractmethod
    async def _send_subscribe(self, symbols: List[str]) -> None:
        """Send subscription message."""
        pass

    @abstractmethod
    async def _send_unsubscribe(self, symbols: List[str]) -> None:
        """Send unsubscription message."""
        pass

    @abstractmethod
    async def _send_heartbeat(self) -> None:
        """Send heartbeat/ping message."""
        pass

    @abstractmethod
    async def _process_message(self, data: Dict[str, Any]) -> None:
        """Process incoming message."""
        pass


# ============================================
# 🔷 Polygon.io Feed
# ============================================


class PolygonFeed(WebSocketFeed):
    """
    Polygon.io WebSocket feed.

    Provides real-time trades, quotes, and minute bars.
    """

    name = "polygon"

    def _get_websocket_url(self) -> str:
        return "wss://socket.polygon.io/stocks"

    async def _authenticate(self) -> bool:
        auth_msg = {"action": "auth", "params": self.config.api_key}
        await self._ws.send(json.dumps(auth_msg))

        response = await self._ws.recv()
        data = json.loads(response)

        if isinstance(data, list) and data[0].get("status") == "auth_success":
            return True

        logger.error(f"Polygon auth failed: {data}")
        return False

    async def _send_subscribe(self, symbols: List[str]) -> None:
        # Subscribe to trades, quotes, and minute bars
        channels = []
        for symbol in symbols:
            channels.extend(
                [
                    f"T.{symbol}",  # Trades
                    f"Q.{symbol}",  # Quotes
                    f"AM.{symbol}",  # Minute aggregates
                ]
            )

        msg = {"action": "subscribe", "params": ",".join(channels)}
        await self._ws.send(json.dumps(msg))

    async def _send_unsubscribe(self, symbols: List[str]) -> None:
        channels = []
        for symbol in symbols:
            channels.extend([f"T.{symbol}", f"Q.{symbol}", f"AM.{symbol}"])

        msg = {"action": "unsubscribe", "params": ",".join(channels)}
        await self._ws.send(json.dumps(msg))

    async def _send_heartbeat(self) -> None:
        # Polygon doesn't require explicit heartbeats
        pass

    async def _process_message(self, data: Dict[str, Any]) -> None:
        if isinstance(data, list):
            for item in data:
                await self._process_single_message(item)
        else:
            await self._process_single_message(data)

    async def _process_single_message(self, item: Dict[str, Any]) -> None:
        ev = item.get("ev")

        if ev == "T":  # Trade
            trade = TradeMessage(
                symbol=item.get("sym", ""),
                price=item.get("p", 0),
                size=item.get("s", 0),
                timestamp=datetime.fromtimestamp(item.get("t", 0) / 1000),
                exchange=item.get("x", ""),
                conditions=item.get("c", []),
            )
            self._emit_trade(trade)

        elif ev == "Q":  # Quote
            quote = QuoteMessage(
                symbol=item.get("sym", ""),
                bid=item.get("bp", 0),
                bid_size=item.get("bs", 0),
                ask=item.get("ap", 0),
                ask_size=item.get("as", 0),
                timestamp=datetime.fromtimestamp(item.get("t", 0) / 1000),
            )
            self._emit_quote(quote)

        elif ev == "AM":  # Minute aggregate
            bar = BarMessage(
                symbol=item.get("sym", ""),
                open=item.get("o", 0),
                high=item.get("h", 0),
                low=item.get("l", 0),
                close=item.get("c", 0),
                volume=item.get("v", 0),
                vwap=item.get("vw"),
                timestamp=datetime.fromtimestamp(item.get("s", 0) / 1000),
            )
            self._emit_bar(bar)


# ============================================
# 🔹 Finnhub Feed
# ============================================


class FinnhubFeed(WebSocketFeed):
    """
    Finnhub WebSocket feed.

    Provides real-time trades.
    """

    name = "finnhub"

    def _get_websocket_url(self) -> str:
        return f"wss://ws.finnhub.io?token={self.config.api_key}"

    async def _authenticate(self) -> bool:
        # Token is in URL, no separate auth needed
        return True

    async def _send_subscribe(self, symbols: List[str]) -> None:
        for symbol in symbols:
            msg = {"type": "subscribe", "symbol": symbol}
            await self._ws.send(json.dumps(msg))

    async def _send_unsubscribe(self, symbols: List[str]) -> None:
        for symbol in symbols:
            msg = {"type": "unsubscribe", "symbol": symbol}
            await self._ws.send(json.dumps(msg))

    async def _send_heartbeat(self) -> None:
        await self._ws.ping()

    async def _process_message(self, data: Dict[str, Any]) -> None:
        if data.get("type") == "trade":
            for item in data.get("data", []):
                trade = TradeMessage(
                    symbol=item.get("s", ""),
                    price=item.get("p", 0),
                    size=item.get("v", 0),
                    timestamp=datetime.fromtimestamp(item.get("t", 0) / 1000),
                )
                self._emit_trade(trade)


# ============================================
# 🔶 Alpha Vantage Feed (Simulated)
# ============================================


class AlphaVantageFeed(WebSocketFeed):
    """
    Alpha Vantage feed (polling-based simulation).

    Alpha Vantage doesn't have WebSocket, so this polls their API.
    """

    name = "alphavantage"

    def __init__(self, config: FeedConfig):
        super().__init__(config)
        self._poll_interval = 60  # seconds

    def _get_websocket_url(self) -> str:
        # Not used - this is polling-based
        return ""

    async def connect(self) -> bool:
        """Start polling loop instead of WebSocket."""
        self._running = True
        self._set_status(FeedStatus.CONNECTED)
        asyncio.create_task(self._poll_loop())
        return True

    async def _poll_loop(self) -> None:
        """Poll Alpha Vantage API periodically."""
        import aiohttp

        while self._running:
            for symbol in self._subscribed_symbols:
                try:
                    url = (
                        f"https://www.alphavantage.co/query?"
                        f"function=GLOBAL_QUOTE&symbol={symbol}&apikey={self.config.api_key}"
                    )

                    async with aiohttp.ClientSession() as session:
                        async with session.get(url) as resp:
                            data = await resp.json()

                    quote = data.get("Global Quote", {})
                    if quote:
                        trade = TradeMessage(
                            symbol=symbol,
                            price=float(quote.get("05. price", 0)),
                            size=int(quote.get("06. volume", 0)),
                            timestamp=datetime.now(),
                        )
                        self._emit_trade(trade)

                except Exception as e:
                    logger.error(f"Alpha Vantage poll error: {e}")

            await asyncio.sleep(self._poll_interval)

    async def _authenticate(self) -> bool:
        return True

    async def _send_subscribe(self, symbols: List[str]) -> None:
        pass

    async def _send_unsubscribe(self, symbols: List[str]) -> None:
        pass

    async def _send_heartbeat(self) -> None:
        pass

    async def _process_message(self, data: Dict[str, Any]) -> None:
        pass


# ============================================
# 🧪 Mock Feed (for testing)
# ============================================


class MockFeed(WebSocketFeed):
    """
    Mock feed for testing without real connections.
    """

    name = "mock"

    def __init__(self, config: FeedConfig):
        super().__init__(config)
        self._mock_prices: Dict[str, float] = {}

    def _get_websocket_url(self) -> str:
        return "mock://localhost"

    async def connect(self) -> bool:
        self._running = True
        self._set_status(FeedStatus.CONNECTED)
        asyncio.create_task(self._generate_mock_data())
        return True

    async def _generate_mock_data(self) -> None:
        """Generate mock price data."""
        import random

        for symbol in self._subscribed_symbols:
            self._mock_prices[symbol] = 100.0 + random.random() * 100

        while self._running:
            for symbol in self._subscribed_symbols:
                # Random walk
                change = (random.random() - 0.5) * 2
                self._mock_prices[symbol] = max(1, self._mock_prices[symbol] + change)

                trade = TradeMessage(
                    symbol=symbol,
                    price=self._mock_prices[symbol],
                    size=random.randint(100, 10000),
                    timestamp=datetime.now(),
                )
                self._emit_trade(trade)

            await asyncio.sleep(0.1)  # 10 updates per second

    async def _authenticate(self) -> bool:
        return True

    async def _send_subscribe(self, symbols: List[str]) -> None:
        pass

    async def _send_unsubscribe(self, symbols: List[str]) -> None:
        pass

    async def _send_heartbeat(self) -> None:
        pass

    async def _process_message(self, data: Dict[str, Any]) -> None:
        pass


# ============================================
# 🏭 Feed Factory
# ============================================

FEED_PROVIDERS: Dict[str, type] = {
    "polygon": PolygonFeed,
    "finnhub": FinnhubFeed,
    "alphavantage": AlphaVantageFeed,
    "mock": MockFeed,
}


def create_feed(provider: str, api_key: str, **kwargs: Any) -> WebSocketFeed:
    """
    Create a WebSocket feed for a provider.

    Args:
        provider: Provider name (polygon, finnhub, alphavantage, mock)
        api_key: API key for the provider
        **kwargs: Additional config options

    Returns:
        WebSocketFeed instance
    """
    if provider not in FEED_PROVIDERS:
        raise ValueError(f"Unknown provider: {provider}. Available: {list(FEED_PROVIDERS.keys())}")

    config = FeedConfig(api_key=api_key, **kwargs)
    return FEED_PROVIDERS[provider](config)


def list_providers() -> List[str]:
    """List available feed providers."""
    return list(FEED_PROVIDERS.keys())


__all__ = [
    # Types
    "FeedStatus",
    "MessageType",
    "TradeMessage",
    "QuoteMessage",
    "BarMessage",
    # Config
    "FeedConfig",
    # Base class
    "WebSocketFeed",
    # Providers
    "PolygonFeed",
    "FinnhubFeed",
    "AlphaVantageFeed",
    "MockFeed",
    # Factory
    "create_feed",
    "list_providers",
    "FEED_PROVIDERS",
]
