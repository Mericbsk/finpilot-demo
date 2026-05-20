"""BaseAgent — abstract contract for all FinPilot specialist agents.

Every agent follows a strict input → process → output cycle:

    context : AgentContext   (read + write shared state)
    run()   : execute task   (single responsibility)
    return  : AgentResult    (success flag, data, optional error, duration)
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, TypedDict


class AgentMetadata(TypedDict, total=False):
    """Typed keys for AgentContext.metadata — prevents magic string bugs."""

    market_regime: str          # "bull" | "bear" | "sideways" | "volatile"
    market_summary: str
    backtest_results: dict
    strategy_hint: str          # "trend" | "momentum" | "rsi"
    cycle: int
    feedback_applied: bool


@dataclass
class AgentContext:
    """Shared context passed between agents in a workflow run.

    Agents read from context and return AgentResult — they do NOT mutate
    context directly.  The CEO / StateGraph merges results into state.
    """

    symbols: list[str] = field(default_factory=list)
    scan_results: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    """Standardised result returned by every agent.

    Attributes:
        agent:       Name of the agent that produced this result.
        success:     True if the agent completed without fatal error.
        data:        Primary output (dict, list, str — agent-specific).
        error:       Human-readable error message when success=False.
        duration_ms: Wall-clock execution time in milliseconds.
    """

    agent: str
    success: bool
    data: Any = None
    error: str | None = None
    duration_ms: float = 0.0


class BaseAgent(ABC):
    """Abstract base for all FinPilot agents.

    Subclasses must:
    1. Set ``name`` class attribute (unique, snake_case).
    2. Implement ``run(context) -> AgentResult``.
    3. Catch all exceptions inside ``run()`` and return a failed AgentResult
       rather than letting exceptions propagate.

    Usage::

        result = ScannerAgent().run(AgentContext(symbols=["AAPL"]))
        if result.success:
            print(result.data)
    """

    name: str = "base"

    @abstractmethod
    def run(self, context: AgentContext, **kwargs: Any) -> AgentResult:
        """Execute the agent's single responsibility.

        Args:
            context: Shared AgentContext carrying symbols and prior results.
            **kwargs: Agent-specific optional parameters.

        Returns:
            AgentResult with success flag, output data, and timing.
        """
        ...

    # ------------------------------------------------------------------
    # Convenience helper — subclasses may call super()._timed_run(fn)
    # to automatically record duration_ms.
    # ------------------------------------------------------------------

    def _timed(self, fn: Any, *args: Any, **kwargs: Any) -> tuple[Any, float]:
        """Run *fn* and return (result, duration_ms)."""
        t0 = time.perf_counter()
        result = fn(*args, **kwargs)
        return result, (time.perf_counter() - t0) * 1000
