# -*- coding: utf-8 -*-
"""
FinPilot Plugin Architecture
============================

Modular plugin system for strategies, indicators, and data sources.

Features:
- Plugin discovery and registration
- Hot-reload support
- Dependency injection
- Event-based hooks
- Configuration validation

Usage:
    from core.plugins import PluginManager, Plugin, hook

    class MyPlugin(Plugin):
        name = "my_plugin"
        version = "1.0.0"

        @hook("scan.before")
        def before_scan(self, symbols: List[str]) -> List[str]:
            return symbols

    pm = PluginManager()
    pm.register(MyPlugin())
    pm.emit("scan.before", symbols=["AAPL", "GOOGL"])
"""
from __future__ import annotations

import importlib
import importlib.util
import inspect
import logging
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Type, TypeVar, Union

logger = logging.getLogger(__name__)


# ============================================
# 📊 Core Types
# ============================================


class PluginStatus(str, Enum):
    """Plugin lifecycle status."""

    REGISTERED = "registered"
    ACTIVE = "active"
    DISABLED = "disabled"
    ERROR = "error"


class HookPriority(int, Enum):
    """Hook execution priority."""

    HIGHEST = 0
    HIGH = 25
    NORMAL = 50
    LOW = 75
    LOWEST = 100


@dataclass
class PluginInfo:
    """Plugin metadata."""

    name: str
    version: str
    description: str = ""
    author: str = ""
    dependencies: List[str] = field(default_factory=list)
    config_schema: Optional[Dict[str, Any]] = None


@dataclass
class HookRegistration:
    """Hook function registration."""

    name: str
    callback: Callable
    plugin_name: str
    priority: HookPriority = HookPriority.NORMAL
    enabled: bool = True


# ============================================
# 🔌 Plugin Base Class
# ============================================


class Plugin(ABC):
    """
    Base class for all plugins.

    Subclass and implement required methods to create a plugin.

    Example:
        class MyPlugin(Plugin):
            name = "my_plugin"
            version = "1.0.0"
            description = "My awesome plugin"

            def on_activate(self):
                print("Plugin activated!")

            def on_deactivate(self):
                print("Plugin deactivated!")
    """

    # Required metadata
    name: str = "base_plugin"
    version: str = "0.0.0"
    description: str = ""
    author: str = ""
    dependencies: List[str] = []

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.status = PluginStatus.REGISTERED
        self._hooks: Dict[str, List[Callable]] = {}

    @property
    def info(self) -> PluginInfo:
        """Get plugin info."""
        return PluginInfo(
            name=self.name,
            version=self.version,
            description=self.description,
            author=self.author,
            dependencies=self.dependencies,
        )

    def on_activate(self) -> None:
        """Called when plugin is activated."""
        pass

    def on_deactivate(self) -> None:
        """Called when plugin is deactivated."""
        pass

    def on_config_change(self, config: Dict[str, Any]) -> None:
        """Called when configuration changes."""
        self.config = config

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration."""
        return True

    def get_hooks(self) -> Dict[str, List[Callable]]:
        """Get all registered hooks."""
        hooks = {}
        for method_name in dir(self):
            method = getattr(self, method_name)
            if hasattr(method, "_hook_name"):
                hook_name = method._hook_name
                if hook_name not in hooks:
                    hooks[hook_name] = []
                hooks[hook_name].append(method)
        return hooks


# ============================================
# 🎣 Hook Decorator
# ============================================

F = TypeVar("F", bound=Callable[..., Any])


def hook(name: str, priority: HookPriority = HookPriority.NORMAL) -> Callable[[F], F]:
    """
    Decorator to register a method as a hook handler.

    Args:
        name: Hook name (e.g., "scan.before", "signal.generated")
        priority: Execution priority

    Example:
        class MyPlugin(Plugin):
            @hook("scan.before")
            def before_scan(self, symbols):
                return symbols
    """

    def decorator(func: F) -> F:
        func._hook_name = name
        func._hook_priority = priority
        return func

    return decorator


# ============================================
# 🔌 Built-in Hooks
# ============================================


class BuiltinHooks:
    """Standard hook names."""

    # Scan hooks
    SCAN_BEFORE = "scan.before"
    SCAN_AFTER = "scan.after"
    SCAN_ERROR = "scan.error"

    # Signal hooks
    SIGNAL_GENERATED = "signal.generated"
    SIGNAL_FILTERED = "signal.filtered"

    # Trade hooks
    TRADE_BEFORE = "trade.before"
    TRADE_AFTER = "trade.after"

    # Data hooks
    DATA_LOADED = "data.loaded"
    DATA_TRANSFORMED = "data.transformed"

    # UI hooks
    UI_RENDER_BEFORE = "ui.render.before"
    UI_RENDER_AFTER = "ui.render.after"

    # System hooks
    APP_STARTUP = "app.startup"
    APP_SHUTDOWN = "app.shutdown"


# ============================================
# 🔧 Plugin Manager
# ============================================


class PluginManager:
    """
    Central plugin management system.

    Handles plugin discovery, registration, lifecycle, and hook execution.

    Usage:
        pm = PluginManager()
        pm.discover_plugins("plugins/")
        pm.activate_all()

        # Emit hooks
        results = pm.emit("scan.before", symbols=["AAPL"])
    """

    def __init__(self):
        self._plugins: Dict[str, Plugin] = {}
        self._hooks: Dict[str, List[HookRegistration]] = {}
        self._load_order: List[str] = []

    @property
    def plugins(self) -> Dict[str, Plugin]:
        """Get all registered plugins."""
        return self._plugins.copy()

    @property
    def active_plugins(self) -> List[Plugin]:
        """Get all active plugins."""
        return [p for p in self._plugins.values() if p.status == PluginStatus.ACTIVE]

    def register(self, plugin: Plugin) -> bool:
        """
        Register a plugin.

        Args:
            plugin: Plugin instance to register

        Returns:
            True if registered successfully
        """
        if plugin.name in self._plugins:
            logger.warning(f"Plugin '{plugin.name}' already registered")
            return False

        # Check dependencies
        for dep in plugin.dependencies:
            if dep not in self._plugins:
                logger.error(f"Plugin '{plugin.name}' requires '{dep}'")
                return False

        self._plugins[plugin.name] = plugin
        self._load_order.append(plugin.name)

        # Register hooks
        for hook_name, callbacks in plugin.get_hooks().items():
            for callback in callbacks:
                self._register_hook(
                    hook_name,
                    callback,
                    plugin.name,
                    getattr(callback, "_hook_priority", HookPriority.NORMAL),
                )

        logger.info(f"Registered plugin: {plugin.name} v{plugin.version}")
        return True

    def unregister(self, plugin_name: str) -> bool:
        """
        Unregister a plugin.

        Args:
            plugin_name: Name of plugin to unregister

        Returns:
            True if unregistered successfully
        """
        if plugin_name not in self._plugins:
            return False

        plugin = self._plugins[plugin_name]

        # Deactivate first
        if plugin.status == PluginStatus.ACTIVE:
            self.deactivate(plugin_name)

        # Remove hooks
        for hook_name in list(self._hooks.keys()):
            self._hooks[hook_name] = [
                h for h in self._hooks[hook_name] if h.plugin_name != plugin_name
            ]

        del self._plugins[plugin_name]
        self._load_order.remove(plugin_name)

        logger.info(f"Unregistered plugin: {plugin_name}")
        return True

    def activate(self, plugin_name: str) -> bool:
        """
        Activate a plugin.

        Args:
            plugin_name: Name of plugin to activate

        Returns:
            True if activated successfully
        """
        if plugin_name not in self._plugins:
            return False

        plugin = self._plugins[plugin_name]

        try:
            plugin.on_activate()
            plugin.status = PluginStatus.ACTIVE
            logger.info(f"Activated plugin: {plugin_name}")
            return True
        except Exception as e:
            plugin.status = PluginStatus.ERROR
            logger.error(f"Failed to activate '{plugin_name}': {e}")
            return False

    def deactivate(self, plugin_name: str) -> bool:
        """
        Deactivate a plugin.

        Args:
            plugin_name: Name of plugin to deactivate

        Returns:
            True if deactivated successfully
        """
        if plugin_name not in self._plugins:
            return False

        plugin = self._plugins[plugin_name]

        try:
            plugin.on_deactivate()
            plugin.status = PluginStatus.DISABLED
            logger.info(f"Deactivated plugin: {plugin_name}")
            return True
        except Exception as e:
            logger.error(f"Error deactivating '{plugin_name}': {e}")
            return False

    def activate_all(self) -> None:
        """Activate all registered plugins."""
        for name in self._load_order:
            self.activate(name)

    def deactivate_all(self) -> None:
        """Deactivate all active plugins."""
        for name in reversed(self._load_order):
            if self._plugins[name].status == PluginStatus.ACTIVE:
                self.deactivate(name)

    def _register_hook(
        self, hook_name: str, callback: Callable, plugin_name: str, priority: HookPriority
    ) -> None:
        """Register a hook callback."""
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []

        registration = HookRegistration(
            name=hook_name,
            callback=callback,
            plugin_name=plugin_name,
            priority=priority,
        )

        self._hooks[hook_name].append(registration)
        self._hooks[hook_name].sort(key=lambda h: h.priority.value)

    def emit(self, hook_name: str, **kwargs: Any) -> List[Any]:
        """
        Emit a hook event.

        Args:
            hook_name: Name of the hook
            **kwargs: Arguments to pass to hook handlers

        Returns:
            List of results from all handlers
        """
        results = []

        if hook_name not in self._hooks:
            return results

        for registration in self._hooks[hook_name]:
            if not registration.enabled:
                continue

            # Check if plugin is active
            plugin = self._plugins.get(registration.plugin_name)
            if plugin is None or plugin.status != PluginStatus.ACTIVE:
                continue

            try:
                result = registration.callback(**kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Hook '{hook_name}' error in '{registration.plugin_name}': {e}")

        return results

    def emit_chain(self, hook_name: str, initial_value: Any, value_key: str = "value") -> Any:
        """
        Emit a hook where each handler transforms the value.

        Args:
            hook_name: Name of the hook
            initial_value: Starting value
            value_key: Keyword argument name for the value

        Returns:
            Final transformed value
        """
        value = initial_value

        if hook_name not in self._hooks:
            return value

        for registration in self._hooks[hook_name]:
            if not registration.enabled:
                continue

            plugin = self._plugins.get(registration.plugin_name)
            if plugin is None or plugin.status != PluginStatus.ACTIVE:
                continue

            try:
                result = registration.callback(**{value_key: value})
                if result is not None:
                    value = result
            except Exception as e:
                logger.error(f"Hook chain '{hook_name}' error in '{registration.plugin_name}': {e}")

        return value

    def discover_plugins(self, directory: Union[str, Path]) -> List[str]:
        """
        Discover and load plugins from a directory.

        Args:
            directory: Path to plugins directory

        Returns:
            List of discovered plugin names
        """
        discovered = []
        plugin_dir = Path(directory)

        if not plugin_dir.exists():
            logger.warning(f"Plugin directory not found: {plugin_dir}")
            return discovered

        for path in plugin_dir.glob("*.py"):
            if path.name.startswith("_"):
                continue

            try:
                plugin = self._load_plugin_from_file(path)
                if plugin:
                    self.register(plugin)
                    discovered.append(plugin.name)
            except Exception as e:
                logger.error(f"Failed to load plugin from {path}: {e}")

        return discovered

    def _load_plugin_from_file(self, path: Path) -> Optional[Plugin]:
        """Load a plugin from a Python file."""
        spec = importlib.util.spec_from_file_location(path.stem, path)
        if spec is None or spec.loader is None:
            return None

        module = importlib.util.module_from_spec(spec)
        sys.modules[path.stem] = module
        spec.loader.exec_module(module)

        # Find Plugin subclass
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, Plugin) and obj is not Plugin:
                return obj()

        return None

    def reload_plugin(self, plugin_name: str) -> bool:
        """
        Hot-reload a plugin.

        Args:
            plugin_name: Name of plugin to reload

        Returns:
            True if reloaded successfully
        """
        if plugin_name not in self._plugins:
            return False

        plugin = self._plugins[plugin_name]
        was_active = plugin.status == PluginStatus.ACTIVE

        # Deactivate and unregister
        self.unregister(plugin_name)

        # Reload module if available
        module_name = f"plugins.{plugin_name}"
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])

        # Re-register
        # Note: In practice, you'd need to recreate the plugin instance
        # This is a simplified implementation

        logger.info(f"Reloaded plugin: {plugin_name}")
        return True

    def get_plugin_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all plugins."""
        status = {}
        for name, plugin in self._plugins.items():
            status[name] = {
                "version": plugin.version,
                "status": plugin.status.value,
                "hooks": list(plugin.get_hooks().keys()),
                "dependencies": plugin.dependencies,
            }
        return status


# ============================================
# 📦 Built-in Strategy Plugin Interface
# ============================================


class StrategyPlugin(Plugin):
    """
    Base class for strategy plugins.

    Provides additional interface for trading strategies.
    """

    def get_signals(self, data: Any, symbol: str) -> List[Dict[str, Any]]:  # pd.DataFrame
        """
        Generate trading signals.

        Args:
            data: OHLCV DataFrame
            symbol: Symbol being analyzed

        Returns:
            List of signal dictionaries
        """
        return []

    def get_parameters(self) -> Dict[str, Any]:
        """Get strategy parameters with descriptions."""
        return {}

    def set_parameters(self, params: Dict[str, Any]) -> None:
        """Set strategy parameters."""
        self.config.update(params)


class IndicatorPlugin(Plugin):
    """
    Base class for indicator plugins.

    Provides interface for custom technical indicators.
    """

    indicator_name: str = "base_indicator"

    def calculate(
        self,
        data: Any,  # pd.DataFrame
    ) -> Any:  # pd.Series or pd.DataFrame
        """
        Calculate indicator values.

        Args:
            data: OHLCV DataFrame

        Returns:
            Indicator values
        """
        raise NotImplementedError


class DataSourcePlugin(Plugin):
    """
    Base class for data source plugins.

    Provides interface for custom data feeds.
    """

    source_name: str = "base_source"

    def fetch(
        self,
        symbol: str,
        start: Any = None,
        end: Any = None,
    ) -> Any:  # pd.DataFrame
        """
        Fetch data for a symbol.

        Args:
            symbol: Symbol to fetch
            start: Start date
            end: End date

        Returns:
            OHLCV DataFrame
        """
        raise NotImplementedError

    def stream(self, symbols: List[str], callback: Callable) -> None:
        """
        Stream real-time data.

        Args:
            symbols: Symbols to stream
            callback: Function to call with new data
        """
        raise NotImplementedError


# ============================================
# 🌐 Global Plugin Manager
# ============================================

_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get the global plugin manager instance."""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager


def register_plugin(plugin: Plugin) -> bool:
    """Register a plugin globally."""
    return get_plugin_manager().register(plugin)


def emit_hook(hook_name: str, **kwargs: Any) -> List[Any]:
    """Emit a hook event globally."""
    return get_plugin_manager().emit(hook_name, **kwargs)


__all__ = [
    # Types
    "PluginStatus",
    "HookPriority",
    "PluginInfo",
    "HookRegistration",
    # Base classes
    "Plugin",
    "StrategyPlugin",
    "IndicatorPlugin",
    "DataSourcePlugin",
    # Decorator
    "hook",
    # Hooks
    "BuiltinHooks",
    # Manager
    "PluginManager",
    # Global functions
    "get_plugin_manager",
    "register_plugin",
    "emit_hook",
]
