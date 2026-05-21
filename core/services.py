"""core/services.py — Simple service registry for FinPilot.

Provides a lightweight, thread-safe singleton registry that maps service names
to their status and optional client instances.  Intended as a discovery layer
so components can check whether a dependency (Redis, Telegram, Scheduler, …)
is alive without importing each module directly.

Usage::

    from core.services import registry

    # Register at startup / when a client becomes available
    registry.register("redis", client=redis_client, healthy=True)
    registry.register("scheduler", healthy=True, meta={"jobs": 5})

    # Query
    entry = registry.get("redis")
    if entry and entry.healthy:
        ...

    # Iterate all registered services
    for name, entry in registry.all().items():
        print(name, entry.healthy)

    # Health summary dict (for /health endpoint)
    summary = registry.health_summary()
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ServiceEntry:
    name: str
    healthy: bool = False
    client: Any = None
    meta: dict[str, Any] = field(default_factory=dict)


class ServiceRegistry:
    """Thread-safe singleton service registry."""

    _lock: threading.Lock = threading.Lock()
    _services: dict[str, ServiceEntry] = {}

    def register(
        self,
        name: str,
        *,
        client: Any = None,
        healthy: bool = True,
        meta: dict[str, Any] | None = None,
    ) -> ServiceEntry:
        """Register or update a service entry."""
        entry = ServiceEntry(name=name, healthy=healthy, client=client, meta=meta or {})
        with self._lock:
            self._services[name] = entry
        return entry

    def get(self, name: str) -> ServiceEntry | None:
        with self._lock:
            return self._services.get(name)

    def set_healthy(self, name: str, healthy: bool) -> None:
        with self._lock:
            if entry := self._services.get(name):
                entry.healthy = healthy

    def deregister(self, name: str) -> None:
        with self._lock:
            self._services.pop(name, None)

    def all(self) -> dict[str, ServiceEntry]:
        with self._lock:
            return dict(self._services)

    def health_summary(self) -> dict[str, bool]:
        """Return {service_name: is_healthy} mapping — useful for /health endpoint."""
        with self._lock:
            return {name: e.healthy for name, e in self._services.items()}

    def any_unhealthy(self) -> bool:
        with self._lock:
            return any(not e.healthy for e in self._services.values())


# Module-level singleton
registry = ServiceRegistry()
