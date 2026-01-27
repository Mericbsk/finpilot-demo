# -*- coding: utf-8 -*-
"""
Tests for Social Trading module.
"""
from datetime import datetime, timedelta

import pytest

from core.social import (
    FeedItem,
    FeedItemType,
    LeaderboardEntry,
    LeaderboardType,
    PerformanceMetrics,
    PublicSignal,
    SignalDirection,
    SignalStatus,
    SocialHub,
    Trader,
    TraderTier,
    get_social_hub,
)

# ============================================
# PerformanceMetrics Tests
# ============================================


class TestPerformanceMetrics:
    """Tests for PerformanceMetrics."""

    def test_default_values(self):
        """Test default metric values."""
        metrics = PerformanceMetrics()
        assert metrics.total_signals == 0
        assert metrics.win_rate == 0.0
        assert metrics.total_pnl == 0.0

    def test_calculate_metrics(self):
        """Test metric calculation."""
        metrics = PerformanceMetrics(
            total_signals=10,
            winning_signals=7,
            losing_signals=3,
            total_pnl=150.0,
        )
        metrics.calculate_metrics()

        assert metrics.win_rate == 70.0
        assert metrics.avg_return == 15.0

    def test_calculate_metrics_no_signals(self):
        """Test calculation with no signals."""
        metrics = PerformanceMetrics()
        metrics.calculate_metrics()
        assert metrics.win_rate == 0.0

    def test_to_dict(self):
        """Test serialization."""
        metrics = PerformanceMetrics(total_signals=5, total_pnl=100.0)
        data = metrics.to_dict()

        assert "total_signals" in data
        assert data["total_signals"] == 5
        assert data["total_pnl"] == 100.0


# ============================================
# PublicSignal Tests
# ============================================


class TestPublicSignal:
    """Tests for PublicSignal."""

    def test_create_signal(self):
        """Test signal creation."""
        signal = PublicSignal(
            id="sig1",
            trader_id="trader1",
            symbol="AAPL",
            direction=SignalDirection.LONG,
            entry_price=150.0,
            created_at=datetime.now(),
        )

        assert signal.symbol == "AAPL"
        assert signal.direction == SignalDirection.LONG
        assert signal.status == SignalStatus.ACTIVE

    def test_close_signal_long_profit(self):
        """Test closing long signal with profit."""
        signal = PublicSignal(
            id="sig1",
            trader_id="trader1",
            symbol="AAPL",
            direction=SignalDirection.LONG,
            entry_price=100.0,
            created_at=datetime.now(),
        )

        signal.close(110.0)

        assert signal.status == SignalStatus.CLOSED
        assert signal.exit_price == 110.0
        assert signal.pnl == 10.0  # 10% profit
        assert signal.is_winner is True

    def test_close_signal_short_profit(self):
        """Test closing short signal with profit."""
        signal = PublicSignal(
            id="sig1",
            trader_id="trader1",
            symbol="AAPL",
            direction=SignalDirection.SHORT,
            entry_price=100.0,
            created_at=datetime.now(),
        )

        signal.close(90.0)

        assert signal.pnl == 10.0  # 10% profit on short
        assert signal.is_winner is True

    def test_close_signal_loss(self):
        """Test closing signal with loss."""
        signal = PublicSignal(
            id="sig1",
            trader_id="trader1",
            symbol="AAPL",
            direction=SignalDirection.LONG,
            entry_price=100.0,
            created_at=datetime.now(),
        )

        signal.close(95.0)

        assert signal.pnl == -5.0  # 5% loss
        assert signal.is_winner is False

    def test_pnl_active_signal(self):
        """Test P&L for active signal."""
        signal = PublicSignal(
            id="sig1",
            trader_id="trader1",
            symbol="AAPL",
            direction=SignalDirection.LONG,
            entry_price=100.0,
            created_at=datetime.now(),
        )

        assert signal.pnl is None
        assert signal.is_winner is None

    def test_signal_duration(self):
        """Test signal duration calculation."""
        now = datetime.now()
        signal = PublicSignal(
            id="sig1",
            trader_id="trader1",
            symbol="AAPL",
            direction=SignalDirection.LONG,
            entry_price=100.0,
            created_at=now,
        )

        assert signal.duration is None

        # Simulate closing after 1 hour
        signal.closed_at = now + timedelta(hours=1)
        signal.exit_price = 110.0
        signal.status = SignalStatus.CLOSED

        assert signal.duration == timedelta(hours=1)

    def test_to_dict(self):
        """Test signal serialization."""
        signal = PublicSignal(
            id="sig1",
            trader_id="trader1",
            symbol="AAPL",
            direction=SignalDirection.LONG,
            entry_price=100.0,
            stop_loss=95.0,
            take_profit=110.0,
            created_at=datetime.now(),
            tags=["momentum", "tech"],
        )

        data = signal.to_dict()

        assert data["id"] == "sig1"
        assert data["symbol"] == "AAPL"
        assert data["direction"] == "long"
        assert data["stop_loss"] == 95.0
        assert data["tags"] == ["momentum", "tech"]


# ============================================
# Trader Tests
# ============================================


class TestTrader:
    """Tests for Trader."""

    def test_create_trader(self):
        """Test trader creation."""
        trader = Trader(
            id="t1",
            username="testuser",
            display_name="Test User",
            created_at=datetime.now(),
        )

        assert trader.username == "testuser"
        assert trader.tier == TraderTier.BRONZE
        assert trader.follower_count == 0

    def test_follow_unfollow(self):
        """Test follow/unfollow."""
        trader = Trader(
            id="t1",
            username="testuser",
            display_name="Test User",
            created_at=datetime.now(),
        )

        trader.follow("t2")
        assert "t2" in trader.following
        assert trader.following_count == 1

        trader.unfollow("t2")
        assert "t2" not in trader.following
        assert trader.following_count == 0

    def test_add_remove_follower(self):
        """Test adding/removing followers."""
        trader = Trader(
            id="t1",
            username="testuser",
            display_name="Test User",
            created_at=datetime.now(),
        )

        trader.add_follower("f1")
        trader.add_follower("f2")

        assert trader.follower_count == 2
        assert trader.metrics.followers_gained == 2

        trader.remove_follower("f1")
        assert trader.follower_count == 1

    def test_update_tier(self):
        """Test tier updates."""
        trader = Trader(
            id="t1",
            username="testuser",
            display_name="Test User",
            created_at=datetime.now(),
        )

        assert trader.tier == TraderTier.BRONZE

        trader.metrics.reputation_score = 50
        trader.update_tier()
        assert trader.tier == TraderTier.SILVER

        trader.metrics.reputation_score = 200
        trader.update_tier()
        assert trader.tier == TraderTier.GOLD

        trader.metrics.reputation_score = 500
        trader.update_tier()
        assert trader.tier == TraderTier.PLATINUM

        trader.metrics.reputation_score = 1000
        trader.update_tier()
        assert trader.tier == TraderTier.DIAMOND

    def test_to_dict(self):
        """Test trader serialization."""
        trader = Trader(
            id="t1",
            username="testuser",
            display_name="Test User",
            bio="Test bio",
            verified=True,
            created_at=datetime.now(),
        )

        data = trader.to_dict()

        assert data["id"] == "t1"
        assert data["username"] == "testuser"
        assert data["verified"] is True
        assert data["tier"] == "bronze"
        assert "metrics" in data


# ============================================
# SocialHub Tests
# ============================================


class TestSocialHub:
    """Tests for SocialHub."""

    @pytest.fixture
    def hub(self):
        """Create fresh hub for each test."""
        return SocialHub()

    def test_create_trader(self, hub):
        """Test creating a trader."""
        trader = hub.create_trader("alice", "Alice Smith", "Professional trader")

        assert trader.username == "alice"
        assert trader.display_name == "Alice Smith"
        assert trader.bio == "Professional trader"

    def test_create_trader_duplicate_username(self, hub):
        """Test duplicate username rejection."""
        hub.create_trader("alice", "Alice")

        with pytest.raises(ValueError, match="already taken"):
            hub.create_trader("Alice", "Another Alice")  # Case insensitive

    def test_get_trader(self, hub):
        """Test getting trader by ID."""
        created = hub.create_trader("bob", "Bob")

        retrieved = hub.get_trader(created.id)
        assert retrieved is not None
        assert retrieved.username == "bob"

    def test_get_trader_by_username(self, hub):
        """Test getting trader by username."""
        hub.create_trader("charlie", "Charlie")

        trader = hub.get_trader_by_username("CHARLIE")  # Case insensitive
        assert trader is not None
        assert trader.display_name == "Charlie"

    def test_search_traders(self, hub):
        """Test trader search."""
        hub.create_trader("alice", "Alice Smith")
        hub.create_trader("bob", "Bob Jones")
        hub.create_trader("charlie", "Charlie Smith")

        # Search by username
        results = hub.search_traders("ali")
        assert len(results) == 1

        # Search by display name
        results = hub.search_traders("smith")
        assert len(results) == 2

    def test_publish_signal(self, hub):
        """Test publishing a signal."""
        trader = hub.create_trader("alice", "Alice")

        signal = hub.publish_signal(
            trader_id=trader.id,
            symbol="AAPL",
            direction=SignalDirection.LONG,
            entry_price=150.0,
            stop_loss=145.0,
            take_profit=165.0,
            notes="Strong momentum",
            tags=["tech", "momentum"],
        )

        assert signal.symbol == "AAPL"
        assert signal.status == SignalStatus.ACTIVE
        assert trader.metrics.total_signals == 1

    def test_publish_signal_invalid_trader(self, hub):
        """Test publishing signal with invalid trader."""
        with pytest.raises(ValueError, match="Trader not found"):
            hub.publish_signal(
                trader_id="invalid",
                symbol="AAPL",
                direction=SignalDirection.LONG,
                entry_price=150.0,
            )

    def test_publish_signal_private_trader(self, hub):
        """Test publishing signal when signals are disabled."""
        trader = hub.create_trader("alice", "Alice")
        trader.signals_public = False

        with pytest.raises(ValueError, match="disabled public signals"):
            hub.publish_signal(
                trader_id=trader.id,
                symbol="AAPL",
                direction=SignalDirection.LONG,
                entry_price=150.0,
            )

    def test_close_signal(self, hub):
        """Test closing a signal."""
        trader = hub.create_trader("alice", "Alice")
        signal = hub.publish_signal(
            trader_id=trader.id,
            symbol="AAPL",
            direction=SignalDirection.LONG,
            entry_price=100.0,
        )

        closed = hub.close_signal(signal.id, 110.0)

        assert closed.status == SignalStatus.CLOSED
        assert closed.pnl == 10.0
        assert trader.metrics.winning_signals == 1
        assert trader.metrics.total_pnl == 10.0

    def test_close_signal_loss(self, hub):
        """Test closing a losing signal."""
        trader = hub.create_trader("alice", "Alice")
        signal = hub.publish_signal(
            trader_id=trader.id,
            symbol="AAPL",
            direction=SignalDirection.LONG,
            entry_price=100.0,
        )

        hub.close_signal(signal.id, 90.0)

        assert trader.metrics.losing_signals == 1
        assert trader.metrics.total_pnl == -10.0

    def test_get_trader_signals(self, hub):
        """Test getting trader signals."""
        trader = hub.create_trader("alice", "Alice")

        hub.publish_signal(trader.id, "AAPL", SignalDirection.LONG, 150.0)
        hub.publish_signal(trader.id, "GOOGL", SignalDirection.SHORT, 100.0)
        hub.publish_signal(trader.id, "MSFT", SignalDirection.LONG, 200.0)

        signals = hub.get_trader_signals(trader.id)
        assert len(signals) == 3

        # Most recent first
        assert signals[0].symbol == "MSFT"

    def test_get_trader_signals_filter_status(self, hub):
        """Test filtering signals by status."""
        trader = hub.create_trader("alice", "Alice")

        sig1 = hub.publish_signal(trader.id, "AAPL", SignalDirection.LONG, 150.0)
        hub.publish_signal(trader.id, "GOOGL", SignalDirection.LONG, 100.0)

        hub.close_signal(sig1.id, 160.0)

        active = hub.get_trader_signals(trader.id, status=SignalStatus.ACTIVE)
        assert len(active) == 1
        assert active[0].symbol == "GOOGL"

        closed = hub.get_trader_signals(trader.id, status=SignalStatus.CLOSED)
        assert len(closed) == 1
        assert closed[0].symbol == "AAPL"

    def test_get_recent_signals(self, hub):
        """Test getting recent signals."""
        t1 = hub.create_trader("alice", "Alice")
        t2 = hub.create_trader("bob", "Bob")

        hub.publish_signal(t1.id, "AAPL", SignalDirection.LONG, 150.0)
        hub.publish_signal(t2.id, "GOOGL", SignalDirection.SHORT, 100.0)
        hub.publish_signal(t1.id, "AAPL", SignalDirection.LONG, 155.0)

        all_signals = hub.get_recent_signals()
        assert len(all_signals) == 3

        # Filter by symbol
        aapl_signals = hub.get_recent_signals(symbol="AAPL")
        assert len(aapl_signals) == 2

    def test_follow(self, hub):
        """Test following a trader."""
        alice = hub.create_trader("alice", "Alice")
        bob = hub.create_trader("bob", "Bob")

        hub.follow(alice.id, bob.id)

        assert bob.id in alice.following
        assert alice.id in bob.followers

    def test_follow_self(self, hub):
        """Test self-follow rejection."""
        alice = hub.create_trader("alice", "Alice")

        with pytest.raises(ValueError, match="Cannot follow yourself"):
            hub.follow(alice.id, alice.id)

    def test_unfollow(self, hub):
        """Test unfollowing a trader."""
        alice = hub.create_trader("alice", "Alice")
        bob = hub.create_trader("bob", "Bob")

        hub.follow(alice.id, bob.id)
        hub.unfollow(alice.id, bob.id)

        assert bob.id not in alice.following
        assert alice.id not in bob.followers

    def test_like_signal(self, hub):
        """Test liking a signal."""
        alice = hub.create_trader("alice", "Alice")
        signal = hub.publish_signal(alice.id, "AAPL", SignalDirection.LONG, 150.0)

        initial_reputation = alice.metrics.reputation_score

        hub.like_signal("bob_id", signal.id)
        hub.like_signal("charlie_id", signal.id)

        assert signal.likes == 2
        assert alice.metrics.reputation_score == initial_reputation + 2

    def test_copy_signal(self, hub):
        """Test copying a signal."""
        alice = hub.create_trader("alice", "Alice")
        signal = hub.publish_signal(alice.id, "AAPL", SignalDirection.LONG, 150.0)

        initial_reputation = alice.metrics.reputation_score

        hub.copy_signal("bob_id", signal.id)

        assert signal.copies == 1
        assert alice.metrics.reputation_score == initial_reputation + 5

    def test_leaderboard(self, hub):
        """Test leaderboard generation."""
        # Create traders with different performance
        alice = hub.create_trader("alice", "Alice")
        bob = hub.create_trader("bob", "Bob")
        charlie = hub.create_trader("charlie", "Charlie")

        # Give different reputations
        alice.metrics.reputation_score = 100
        bob.metrics.reputation_score = 50
        charlie.metrics.reputation_score = 200

        leaderboard = hub.get_leaderboard()

        assert len(leaderboard) == 3
        assert leaderboard[0].username == "charlie"  # Highest score
        assert leaderboard[0].rank == 1
        assert leaderboard[1].username == "alice"
        assert leaderboard[2].username == "bob"

    def test_feed(self, hub):
        """Test social feed."""
        alice = hub.create_trader("alice", "Alice")
        bob = hub.create_trader("bob", "Bob")

        hub.follow(alice.id, bob.id)
        hub.publish_signal(alice.id, "AAPL", SignalDirection.LONG, 150.0)

        # Global feed
        global_feed = hub.get_feed()
        assert len(global_feed) >= 2  # Signal + follow

        # Personal feed
        alice_feed = hub.get_feed(alice.id)
        # Should include own activity
        assert len(alice_feed) >= 1

    def test_get_stats(self, hub):
        """Test hub statistics."""
        hub.create_trader("alice", "Alice")
        hub.create_trader("bob", "Bob")

        stats = hub.get_stats()

        assert stats["total_traders"] == 2
        assert stats["total_signals"] == 0


class TestGlobalHub:
    """Tests for global hub instance."""

    def test_get_social_hub(self):
        """Test getting global hub."""
        hub1 = get_social_hub()
        hub2 = get_social_hub()

        assert hub1 is hub2


# ============================================
# LeaderboardEntry Tests
# ============================================


class TestLeaderboardEntry:
    """Tests for LeaderboardEntry."""

    def test_to_dict(self):
        """Test serialization."""
        entry = LeaderboardEntry(
            rank=1,
            trader_id="t1",
            username="alice",
            display_name="Alice",
            tier=TraderTier.GOLD,
            total_pnl=1500.0,
            win_rate=75.0,
            total_signals=100,
            followers=50,
            score=500.0,
        )

        data = entry.to_dict()

        assert data["rank"] == 1
        assert data["tier"] == "gold"
        assert data["win_rate"] == 75.0


# ============================================
# FeedItem Tests
# ============================================


class TestFeedItem:
    """Tests for FeedItem."""

    def test_to_dict(self):
        """Test serialization."""
        item = FeedItem(
            id="f1",
            type=FeedItemType.SIGNAL,
            trader_id="t1",
            created_at=datetime.now(),
            data={"symbol": "AAPL"},
        )

        data = item.to_dict()

        assert data["type"] == "signal"
        assert data["data"]["symbol"] == "AAPL"
