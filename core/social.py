# -*- coding: utf-8 -*-
"""
FinPilot Social Trading
=======================

Signal sharing, leaderboards, and community features.

Features:
- Signal publication and subscription
- Trader performance tracking
- Leaderboard rankings
- Copy trading support
- Social feeds

Usage:
    from core.social import SocialHub, Trader, PublicSignal

    hub = SocialHub()
    trader = hub.create_trader("username", "display_name")
    signal = trader.publish_signal(symbol="AAPL", direction="LONG")
"""
from __future__ import annotations

import hashlib
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


# ============================================
# 📊 Core Types
# ============================================


class SignalDirection(str, Enum):
    """Signal direction."""

    LONG = "long"
    SHORT = "short"


class SignalStatus(str, Enum):
    """Signal lifecycle status."""

    ACTIVE = "active"
    CLOSED = "closed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class TraderTier(str, Enum):
    """Trader ranking tier."""

    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"


class LeaderboardType(str, Enum):
    """Leaderboard time periods."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ALL_TIME = "all_time"


@dataclass
class PerformanceMetrics:
    """Trader performance metrics."""

    total_signals: int = 0
    winning_signals: int = 0
    losing_signals: int = 0
    total_pnl: float = 0.0
    win_rate: float = 0.0
    avg_return: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    followers_gained: int = 0
    reputation_score: float = 0.0

    def calculate_metrics(self) -> None:
        """Recalculate derived metrics."""
        if self.total_signals > 0:
            self.win_rate = self.winning_signals / self.total_signals * 100
            self.avg_return = self.total_pnl / self.total_signals

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "total_signals": self.total_signals,
            "winning_signals": self.winning_signals,
            "losing_signals": self.losing_signals,
            "total_pnl": self.total_pnl,
            "win_rate": self.win_rate,
            "avg_return": self.avg_return,
            "sharpe_ratio": self.sharpe_ratio,
            "reputation_score": self.reputation_score,
        }


# ============================================
# 📢 Public Signal
# ============================================


@dataclass
class PublicSignal:
    """
    A publicly shared trading signal.
    """

    id: str
    trader_id: str
    symbol: str
    direction: SignalDirection
    entry_price: float
    created_at: datetime

    # Optional fields
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    exit_price: Optional[float] = None
    closed_at: Optional[datetime] = None
    status: SignalStatus = SignalStatus.ACTIVE

    # Engagement
    likes: int = 0
    copies: int = 0
    comments: int = 0

    # Metadata
    notes: str = ""
    tags: List[str] = field(default_factory=list)

    @property
    def pnl(self) -> Optional[float]:
        """Calculate P&L if closed."""
        if self.exit_price is None:
            return None

        if self.direction == SignalDirection.LONG:
            return (self.exit_price - self.entry_price) / self.entry_price * 100
        else:
            return (self.entry_price - self.exit_price) / self.entry_price * 100

    @property
    def is_winner(self) -> Optional[bool]:
        """Check if signal is profitable."""
        pnl = self.pnl
        if pnl is None:
            return None
        return pnl > 0

    @property
    def duration(self) -> Optional[timedelta]:
        """Get signal duration."""
        if self.closed_at is None:
            return None
        return self.closed_at - self.created_at

    def close(self, exit_price: float) -> None:
        """Close the signal."""
        self.exit_price = exit_price
        self.closed_at = datetime.now()
        self.status = SignalStatus.CLOSED

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "trader_id": self.trader_id,
            "symbol": self.symbol,
            "direction": self.direction.value,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "exit_price": self.exit_price,
            "status": self.status.value,
            "pnl": self.pnl,
            "likes": self.likes,
            "copies": self.copies,
            "created_at": self.created_at.isoformat(),
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "notes": self.notes,
            "tags": self.tags,
        }


# ============================================
# 👤 Trader Profile
# ============================================


@dataclass
class Trader:
    """
    Public trader profile.
    """

    id: str
    username: str
    display_name: str
    created_at: datetime

    # Profile
    bio: str = ""
    avatar_url: str = ""
    verified: bool = False

    # Social
    followers: Set[str] = field(default_factory=set)
    following: Set[str] = field(default_factory=set)

    # Performance
    tier: TraderTier = TraderTier.BRONZE
    metrics: PerformanceMetrics = field(default_factory=PerformanceMetrics)

    # Settings
    signals_public: bool = True
    allow_copy_trading: bool = True

    # Signals
    signals: List[str] = field(default_factory=list)  # Signal IDs

    @property
    def follower_count(self) -> int:
        """Get follower count."""
        return len(self.followers)

    @property
    def following_count(self) -> int:
        """Get following count."""
        return len(self.following)

    def follow(self, trader_id: str) -> None:
        """Follow another trader."""
        self.following.add(trader_id)

    def unfollow(self, trader_id: str) -> None:
        """Unfollow a trader."""
        self.following.discard(trader_id)

    def add_follower(self, follower_id: str) -> None:
        """Add a follower."""
        self.followers.add(follower_id)
        self.metrics.followers_gained += 1

    def remove_follower(self, follower_id: str) -> None:
        """Remove a follower."""
        self.followers.discard(follower_id)

    def update_tier(self) -> None:
        """Update tier based on performance."""
        score = self.metrics.reputation_score

        if score >= 1000:
            self.tier = TraderTier.DIAMOND
        elif score >= 500:
            self.tier = TraderTier.PLATINUM
        elif score >= 200:
            self.tier = TraderTier.GOLD
        elif score >= 50:
            self.tier = TraderTier.SILVER
        else:
            self.tier = TraderTier.BRONZE

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "username": self.username,
            "display_name": self.display_name,
            "bio": self.bio,
            "avatar_url": self.avatar_url,
            "verified": self.verified,
            "tier": self.tier.value,
            "follower_count": self.follower_count,
            "following_count": self.following_count,
            "signals_public": self.signals_public,
            "allow_copy_trading": self.allow_copy_trading,
            "metrics": self.metrics.to_dict(),
            "created_at": self.created_at.isoformat(),
        }


# ============================================
# 🏆 Leaderboard Entry
# ============================================


@dataclass
class LeaderboardEntry:
    """Leaderboard ranking entry."""

    rank: int
    trader_id: str
    username: str
    display_name: str
    tier: TraderTier
    total_pnl: float
    win_rate: float
    total_signals: int
    followers: int
    score: float

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "rank": self.rank,
            "trader_id": self.trader_id,
            "username": self.username,
            "display_name": self.display_name,
            "tier": self.tier.value,
            "total_pnl": self.total_pnl,
            "win_rate": self.win_rate,
            "total_signals": self.total_signals,
            "followers": self.followers,
            "score": self.score,
        }


# ============================================
# 💬 Social Feed Item
# ============================================


class FeedItemType(str, Enum):
    """Feed item types."""

    SIGNAL = "signal"
    SIGNAL_CLOSED = "signal_closed"
    FOLLOW = "follow"
    MILESTONE = "milestone"
    COMMENT = "comment"


@dataclass
class FeedItem:
    """Social feed item."""

    id: str
    type: FeedItemType
    trader_id: str
    created_at: datetime
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "trader_id": self.trader_id,
            "created_at": self.created_at.isoformat(),
            "data": self.data,
        }


# ============================================
# 🌐 Social Hub
# ============================================


class SocialHub:
    """
    Central social trading hub.

    Manages traders, signals, leaderboards, and social interactions.
    """

    def __init__(self):
        self._traders: Dict[str, Trader] = {}
        self._signals: Dict[str, PublicSignal] = {}
        self._feed: List[FeedItem] = []
        self._username_index: Dict[str, str] = {}  # username -> trader_id

    # ----------------------------------------
    # Trader Management
    # ----------------------------------------

    def create_trader(self, username: str, display_name: str, bio: str = "") -> Trader:
        """
        Create a new trader profile.

        Args:
            username: Unique username
            display_name: Display name
            bio: Profile bio

        Returns:
            New Trader instance
        """
        # Check username availability
        if username.lower() in self._username_index:
            raise ValueError(f"Username '{username}' already taken")

        trader_id = str(uuid.uuid4())[:8]

        trader = Trader(
            id=trader_id,
            username=username.lower(),
            display_name=display_name,
            bio=bio,
            created_at=datetime.now(),
        )

        self._traders[trader_id] = trader
        self._username_index[username.lower()] = trader_id

        logger.info(f"Created trader: {username} ({trader_id})")
        return trader

    def get_trader(self, trader_id: str) -> Optional[Trader]:
        """Get trader by ID."""
        return self._traders.get(trader_id)

    def get_trader_by_username(self, username: str) -> Optional[Trader]:
        """Get trader by username."""
        trader_id = self._username_index.get(username.lower())
        if trader_id:
            return self._traders.get(trader_id)
        return None

    def search_traders(self, query: str, limit: int = 20) -> List[Trader]:
        """Search traders by username or display name."""
        query = query.lower()
        results = []

        for trader in self._traders.values():
            if query in trader.username.lower() or query in trader.display_name.lower():
                results.append(trader)
                if len(results) >= limit:
                    break

        return results

    # ----------------------------------------
    # Signal Management
    # ----------------------------------------

    def publish_signal(
        self,
        trader_id: str,
        symbol: str,
        direction: SignalDirection,
        entry_price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        notes: str = "",
        tags: Optional[List[str]] = None,
    ) -> PublicSignal:
        """
        Publish a new trading signal.

        Args:
            trader_id: Trader ID
            symbol: Trading symbol
            direction: Long or short
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            notes: Signal notes
            tags: Signal tags

        Returns:
            Published signal
        """
        trader = self._traders.get(trader_id)
        if trader is None:
            raise ValueError(f"Trader not found: {trader_id}")

        if not trader.signals_public:
            raise ValueError("Trader has disabled public signals")

        signal_id = str(uuid.uuid4())[:8]

        signal = PublicSignal(
            id=signal_id,
            trader_id=trader_id,
            symbol=symbol.upper(),
            direction=direction,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            notes=notes,
            tags=tags or [],
            created_at=datetime.now(),
        )

        self._signals[signal_id] = signal
        trader.signals.append(signal_id)
        trader.metrics.total_signals += 1

        # Add to feed
        self._add_feed_item(
            FeedItemType.SIGNAL,
            trader_id,
            {"signal_id": signal_id, "symbol": symbol, "direction": direction.value},
        )

        logger.info(f"Published signal: {signal_id} by {trader_id}")
        return signal

    def close_signal(self, signal_id: str, exit_price: float) -> PublicSignal:
        """
        Close a trading signal.

        Args:
            signal_id: Signal ID
            exit_price: Exit price

        Returns:
            Closed signal
        """
        signal = self._signals.get(signal_id)
        if signal is None:
            raise ValueError(f"Signal not found: {signal_id}")

        signal.close(exit_price)

        # Update trader metrics
        trader = self._traders.get(signal.trader_id)
        if trader:
            pnl = signal.pnl or 0
            trader.metrics.total_pnl += pnl

            if signal.is_winner:
                trader.metrics.winning_signals += 1
                trader.metrics.reputation_score += 10
            else:
                trader.metrics.losing_signals += 1
                trader.metrics.reputation_score -= 5

            trader.metrics.calculate_metrics()
            trader.update_tier()

        # Add to feed
        self._add_feed_item(
            FeedItemType.SIGNAL_CLOSED,
            signal.trader_id,
            {"signal_id": signal_id, "pnl": signal.pnl},
        )

        return signal

    def get_signal(self, signal_id: str) -> Optional[PublicSignal]:
        """Get signal by ID."""
        return self._signals.get(signal_id)

    def get_trader_signals(
        self, trader_id: str, status: Optional[SignalStatus] = None, limit: int = 50
    ) -> List[PublicSignal]:
        """Get signals for a trader."""
        trader = self._traders.get(trader_id)
        if trader is None:
            return []

        signals = []
        for signal_id in reversed(trader.signals):  # Most recent first
            signal = self._signals.get(signal_id)
            if signal:
                if status is None or signal.status == status:
                    signals.append(signal)
                if len(signals) >= limit:
                    break

        return signals

    def get_recent_signals(
        self, limit: int = 50, symbol: Optional[str] = None
    ) -> List[PublicSignal]:
        """Get recent public signals."""
        signals = sorted(self._signals.values(), key=lambda s: s.created_at, reverse=True)

        if symbol:
            signals = [s for s in signals if s.symbol == symbol.upper()]

        return signals[:limit]

    # ----------------------------------------
    # Social Interactions
    # ----------------------------------------

    def follow(self, follower_id: str, target_id: str) -> None:
        """Follow a trader."""
        follower = self._traders.get(follower_id)
        target = self._traders.get(target_id)

        if follower is None or target is None:
            raise ValueError("Trader not found")

        if follower_id == target_id:
            raise ValueError("Cannot follow yourself")

        follower.follow(target_id)
        target.add_follower(follower_id)

        self._add_feed_item(
            FeedItemType.FOLLOW,
            follower_id,
            {"followed_id": target_id, "followed_username": target.username},
        )

    def unfollow(self, follower_id: str, target_id: str) -> None:
        """Unfollow a trader."""
        follower = self._traders.get(follower_id)
        target = self._traders.get(target_id)

        if follower and target:
            follower.unfollow(target_id)
            target.remove_follower(follower_id)

    def like_signal(self, trader_id: str, signal_id: str) -> None:
        """Like a signal."""
        signal = self._signals.get(signal_id)
        if signal:
            signal.likes += 1

            # Boost reputation
            author = self._traders.get(signal.trader_id)
            if author:
                author.metrics.reputation_score += 1

    def copy_signal(self, trader_id: str, signal_id: str) -> None:
        """Copy a signal."""
        signal = self._signals.get(signal_id)
        if signal:
            signal.copies += 1

            # Boost reputation
            author = self._traders.get(signal.trader_id)
            if author and author.allow_copy_trading:
                author.metrics.reputation_score += 5

    # ----------------------------------------
    # Leaderboard
    # ----------------------------------------

    def get_leaderboard(
        self, period: LeaderboardType = LeaderboardType.ALL_TIME, limit: int = 100
    ) -> List[LeaderboardEntry]:
        """
        Get leaderboard rankings.

        Args:
            period: Time period for rankings
            limit: Maximum entries

        Returns:
            List of leaderboard entries
        """
        # Calculate scores for each trader
        scored_traders = []

        for trader in self._traders.values():
            # Score formula: weighted combination of metrics
            score = (
                trader.metrics.win_rate * 2
                + trader.metrics.total_pnl * 0.1
                + trader.follower_count * 0.5
                + trader.metrics.reputation_score
            )

            scored_traders.append((trader, score))

        # Sort by score
        scored_traders.sort(key=lambda x: x[1], reverse=True)

        # Build leaderboard
        entries = []
        for rank, (trader, score) in enumerate(scored_traders[:limit], 1):
            entry = LeaderboardEntry(
                rank=rank,
                trader_id=trader.id,
                username=trader.username,
                display_name=trader.display_name,
                tier=trader.tier,
                total_pnl=trader.metrics.total_pnl,
                win_rate=trader.metrics.win_rate,
                total_signals=trader.metrics.total_signals,
                followers=trader.follower_count,
                score=score,
            )
            entries.append(entry)

        return entries

    # ----------------------------------------
    # Feed
    # ----------------------------------------

    def _add_feed_item(self, item_type: FeedItemType, trader_id: str, data: Dict[str, Any]) -> None:
        """Add item to social feed."""
        item = FeedItem(
            id=str(uuid.uuid4())[:8],
            type=item_type,
            trader_id=trader_id,
            created_at=datetime.now(),
            data=data,
        )
        self._feed.insert(0, item)

        # Keep feed size manageable
        if len(self._feed) > 10000:
            self._feed = self._feed[:5000]

    def get_feed(self, trader_id: Optional[str] = None, limit: int = 50) -> List[FeedItem]:
        """
        Get social feed.

        Args:
            trader_id: If provided, get feed for followed traders
            limit: Maximum items

        Returns:
            Feed items
        """
        if trader_id is None:
            return self._feed[:limit]

        trader = self._traders.get(trader_id)
        if trader is None:
            return []

        # Get feed from followed traders
        followed = trader.following | {trader_id}  # Include own activity

        feed = [item for item in self._feed if item.trader_id in followed]

        return feed[:limit]

    # ----------------------------------------
    # Statistics
    # ----------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Get hub statistics."""
        return {
            "total_traders": len(self._traders),
            "total_signals": len(self._signals),
            "active_signals": len(
                [s for s in self._signals.values() if s.status == SignalStatus.ACTIVE]
            ),
            "total_feed_items": len(self._feed),
        }


# ============================================
# 🌐 Global Hub
# ============================================

_social_hub: Optional[SocialHub] = None


def get_social_hub() -> SocialHub:
    """Get global social hub instance."""
    global _social_hub
    if _social_hub is None:
        _social_hub = SocialHub()
    return _social_hub


__all__ = [
    # Types
    "SignalDirection",
    "SignalStatus",
    "TraderTier",
    "LeaderboardType",
    "FeedItemType",
    # Dataclasses
    "PerformanceMetrics",
    "PublicSignal",
    "Trader",
    "LeaderboardEntry",
    "FeedItem",
    # Hub
    "SocialHub",
    "get_social_hub",
]
