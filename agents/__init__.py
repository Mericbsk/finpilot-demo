"""FinPilot Multi-Agent System.

Layer architecture:
    Data Layer        →  yfinance, scanner, DRL inference
    LLM Provider      →  llm/router.py (Claude/Gemini/Groq failover)
    Agent Layer       →  agents/ (this package)
    Workflow Layer    →  core/pipeline.py  run_cycle() — LangGraph-free canonical orchestrator
    Scheduler         →  core/scheduler.py APScheduler loop
    API Interface     →  api/routers/agent.py  POST /api/v1/agent/run

Note: agents/ceo.py (LangGraph StateGraph) has been archived to
      archive/core_legacy/ceo_langgraph.py (2026-06-12).
      Use ``core.pipeline.run_cycle`` instead.
"""

from agents.advisory import advisory_agent_for, list_advisory_keys
from agents.alpha_tracker import AlphaTrackerAgent, get_symbol_win_rate, get_threshold_boosts
from agents.backtest_agent import BacktestAgent
from agents.base import AgentContext, AgentResult, BaseAgent
from agents.combo_testing import ComboTestingAgent
from agents.market_intelligence import MarketIntelligenceAgent
from agents.performance_monitor import PerformanceMonitorAgent
from agents.report_agent import ReportAgent
from agents.research_agent import ResearchAgent
from agents.social_intelligence_agent import SocialIntelligenceAgent
from agents.strategy_optimizer import StrategyOptimizerAgent


def get_graph() -> None:  # type: ignore[return]
    """Deprecated: LangGraph CEO graph has been archived.

    Use ``core.pipeline.run_cycle`` instead.
    """
    import warnings

    warnings.warn(
        "get_graph() is deprecated. Use core.pipeline.run_cycle() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    raise ImportError(
        "agents.ceo LangGraph graph has been archived. "
        "Use core.pipeline.run_cycle(symbols, task, stages=...) instead."
    )


__all__ = [
    "AgentContext",
    "AgentResult",
    "BaseAgent",
    "AlphaTrackerAgent",
    "get_symbol_win_rate",
    "get_threshold_boosts",
    "get_graph",
    "ResearchAgent",
    "SocialIntelligenceAgent",
    "BacktestAgent",
    "ReportAgent",
    "MarketIntelligenceAgent",
    "StrategyOptimizerAgent",
    "PerformanceMonitorAgent",
    "ComboTestingAgent",
    "advisory_agent_for",
    "list_advisory_keys",
]
