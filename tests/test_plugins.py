# -*- coding: utf-8 -*-
"""
Tests for Plugin Architecture
"""
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from core.plugins import (
    BuiltinHooks,
    DataSourcePlugin,
    HookPriority,
    HookRegistration,
    IndicatorPlugin,
    Plugin,
    PluginInfo,
    PluginManager,
    PluginStatus,
    StrategyPlugin,
    hook,
)

# ============================================
# Test Plugins
# ============================================


class SimplePlugin(Plugin):
    """Simple test plugin."""

    name = "simple"
    version = "1.0.0"
    description = "A simple test plugin"
    author = "Test"

    def __init__(self, config=None):
        super().__init__(config)
        self.activated = False
        self.deactivated = False

    def on_activate(self):
        self.activated = True

    def on_deactivate(self):
        self.deactivated = True


class HookedPlugin(Plugin):
    """Plugin with hooks."""

    name = "hooked"
    version = "1.0.0"

    @hook(BuiltinHooks.SCAN_BEFORE, priority=HookPriority.HIGH)
    def before_scan(self, symbols=None):
        return [s.upper() for s in (symbols or [])]

    @hook(BuiltinHooks.SCAN_AFTER)
    def after_scan(self, results=None):
        return {"count": len(results or [])}


class DependentPlugin(Plugin):
    """Plugin with dependencies."""

    name = "dependent"
    version = "1.0.0"
    dependencies = ["simple"]


# ============================================
# Plugin Tests
# ============================================


class TestPlugin:
    """Tests for Plugin base class."""

    def test_plugin_creation(self):
        """Test basic plugin creation."""
        plugin = SimplePlugin()

        assert plugin.name == "simple"
        assert plugin.version == "1.0.0"
        assert plugin.status == PluginStatus.REGISTERED

    def test_plugin_with_config(self):
        """Test plugin with configuration."""
        config = {"threshold": 0.5}
        plugin = SimplePlugin(config=config)

        assert plugin.config["threshold"] == 0.5

    def test_plugin_info(self):
        """Test plugin info property."""
        plugin = SimplePlugin()
        info = plugin.info

        assert isinstance(info, PluginInfo)
        assert info.name == "simple"
        assert info.version == "1.0.0"
        assert info.author == "Test"

    def test_plugin_lifecycle(self):
        """Test plugin activation/deactivation."""
        plugin = SimplePlugin()

        assert not plugin.activated
        plugin.on_activate()
        assert plugin.activated

        assert not plugin.deactivated
        plugin.on_deactivate()
        assert plugin.deactivated

    def test_plugin_hooks_discovery(self):
        """Test hook discovery from plugin."""
        plugin = HookedPlugin()
        hooks = plugin.get_hooks()

        assert BuiltinHooks.SCAN_BEFORE in hooks
        assert BuiltinHooks.SCAN_AFTER in hooks
        assert len(hooks[BuiltinHooks.SCAN_BEFORE]) == 1


# ============================================
# Hook Decorator Tests
# ============================================


class TestHookDecorator:
    """Tests for hook decorator."""

    def test_hook_sets_attributes(self):
        """Test that hook decorator sets function attributes."""
        plugin = HookedPlugin()

        assert hasattr(plugin.before_scan, "_hook_name")
        assert plugin.before_scan._hook_name == BuiltinHooks.SCAN_BEFORE

    def test_hook_priority(self):
        """Test hook priority setting."""
        plugin = HookedPlugin()

        assert plugin.before_scan._hook_priority == HookPriority.HIGH


# ============================================
# PluginManager Tests
# ============================================


class TestPluginManager:
    """Tests for PluginManager."""

    def test_manager_creation(self):
        """Test manager creation."""
        pm = PluginManager()

        assert len(pm.plugins) == 0
        assert len(pm.active_plugins) == 0

    def test_register_plugin(self):
        """Test plugin registration."""
        pm = PluginManager()
        plugin = SimplePlugin()

        result = pm.register(plugin)

        assert result is True
        assert "simple" in pm.plugins

    def test_register_duplicate_fails(self):
        """Test duplicate registration fails."""
        pm = PluginManager()

        pm.register(SimplePlugin())
        result = pm.register(SimplePlugin())

        assert result is False

    def test_unregister_plugin(self):
        """Test plugin unregistration."""
        pm = PluginManager()
        pm.register(SimplePlugin())

        result = pm.unregister("simple")

        assert result is True
        assert "simple" not in pm.plugins

    def test_activate_plugin(self):
        """Test plugin activation."""
        pm = PluginManager()
        plugin = SimplePlugin()
        pm.register(plugin)

        result = pm.activate("simple")

        assert result is True
        assert plugin.status == PluginStatus.ACTIVE
        assert plugin.activated is True

    def test_deactivate_plugin(self):
        """Test plugin deactivation."""
        pm = PluginManager()
        plugin = SimplePlugin()
        pm.register(plugin)
        pm.activate("simple")

        result = pm.deactivate("simple")

        assert result is True
        assert plugin.status == PluginStatus.DISABLED
        assert plugin.deactivated is True

    def test_activate_all(self):
        """Test activating all plugins."""
        pm = PluginManager()
        pm.register(SimplePlugin())
        pm.register(HookedPlugin())

        pm.activate_all()

        assert len(pm.active_plugins) == 2

    def test_dependency_check(self):
        """Test dependency checking."""
        pm = PluginManager()

        # Should fail - dependency not registered
        result = pm.register(DependentPlugin())
        assert result is False

        # Should succeed after registering dependency
        pm.register(SimplePlugin())
        result = pm.register(DependentPlugin())
        assert result is True


# ============================================
# Hook Emission Tests
# ============================================


class TestHookEmission:
    """Tests for hook emission."""

    def test_emit_hook(self):
        """Test basic hook emission."""
        pm = PluginManager()
        pm.register(HookedPlugin())
        pm.activate("hooked")

        results = pm.emit(BuiltinHooks.SCAN_BEFORE, symbols=["aapl", "googl"])

        assert len(results) == 1
        assert results[0] == ["AAPL", "GOOGL"]

    def test_emit_to_inactive_plugin(self):
        """Test that inactive plugins don't receive hooks."""
        pm = PluginManager()
        pm.register(HookedPlugin())
        # Not activated

        results = pm.emit(BuiltinHooks.SCAN_BEFORE, symbols=["aapl"])

        assert len(results) == 0

    def test_emit_chain(self):
        """Test chain emission."""
        pm = PluginManager()
        pm.register(HookedPlugin())
        pm.activate("hooked")

        result = pm.emit_chain(BuiltinHooks.SCAN_BEFORE, ["aapl", "googl"], value_key="symbols")

        assert result == ["AAPL", "GOOGL"]

    def test_emit_nonexistent_hook(self):
        """Test emitting non-existent hook."""
        pm = PluginManager()

        results = pm.emit("nonexistent.hook")

        assert results == []


# ============================================
# Priority Tests
# ============================================


class TestHookPriority:
    """Tests for hook priority ordering."""

    def test_priority_ordering(self):
        """Test that hooks are called in priority order."""
        execution_order = []

        class FirstPlugin(Plugin):
            name = "first"
            version = "1.0.0"

            @hook("test.order", priority=HookPriority.HIGHEST)
            def handle(self, **kwargs):
                execution_order.append("first")

        class LastPlugin(Plugin):
            name = "last"
            version = "1.0.0"

            @hook("test.order", priority=HookPriority.LOWEST)
            def handle(self, **kwargs):
                execution_order.append("last")

        class MiddlePlugin(Plugin):
            name = "middle"
            version = "1.0.0"

            @hook("test.order", priority=HookPriority.NORMAL)
            def handle(self, **kwargs):
                execution_order.append("middle")

        pm = PluginManager()
        pm.register(LastPlugin())
        pm.register(MiddlePlugin())
        pm.register(FirstPlugin())
        pm.activate_all()

        pm.emit("test.order")

        assert execution_order == ["first", "middle", "last"]


# ============================================
# Plugin Status Tests
# ============================================


class TestPluginStatus:
    """Tests for plugin status reporting."""

    def test_get_plugin_status(self):
        """Test getting all plugin status."""
        pm = PluginManager()
        pm.register(SimplePlugin())
        pm.register(HookedPlugin())
        pm.activate("simple")

        status = pm.get_plugin_status()

        assert "simple" in status
        assert "hooked" in status
        assert status["simple"]["status"] == "active"
        assert status["hooked"]["status"] == "registered"


# ============================================
# Strategy Plugin Tests
# ============================================


class TestStrategyPlugin:
    """Tests for StrategyPlugin base class."""

    def test_strategy_plugin_interface(self):
        """Test strategy plugin interface."""

        class MyStrategy(StrategyPlugin):
            name = "my_strategy"
            version = "1.0.0"

            def get_signals(self, data, symbol):
                return [{"signal": "BUY", "symbol": symbol}]

        plugin = MyStrategy()
        signals = plugin.get_signals(None, "AAPL")

        assert len(signals) == 1
        assert signals[0]["symbol"] == "AAPL"

    def test_strategy_parameters(self):
        """Test strategy parameter setting."""

        class MyStrategy(StrategyPlugin):
            name = "my_strategy"
            version = "1.0.0"

        plugin = MyStrategy(config={"period": 14})
        plugin.set_parameters({"threshold": 0.5})

        assert plugin.config["period"] == 14
        assert plugin.config["threshold"] == 0.5
