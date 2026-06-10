"""FinPilot Multi-Agent System — Sprint 8.

Layer architecture:
    Data Layer        →  yfinance, scanner, DRL inference
    LLM Provider      →  llm/router.py (Claude/Gemini/Groq failover)
    Agent Layer       →  agents/ (this package)
    Workflow Layer    →  agents/ceo.py LangGraph StateGraph
    Scheduler         →  core/scheduler.py APScheduler loop
    API Interface     →  api/routers/agent.py  POST /api/v1/agent/run
"""

from agents.advisory import advisory_agent_for, list_advisory_keys
from agents.alpha_tracker import AlphaTrackerAgent, get_symbol_win_rate, get_threshold_boosts
from agents.backtest_agent import BacktestAgent
from agents.base import AgentContext, AgentResult, BaseAgent
from agents.ceo import get_graph
from agents.combo_testing import ComboTestingAgent
from agents.market_intelligence import MarketIntelligenceAgent
from agents.performance_monitor import PerformanceMonitorAgent
from agents.report_agent import ReportAgent
from agents.research_agent import ResearchAgent
from agents.social_intelligence_agent import SocialIntelligenceAgent
from agents.strategy_optimizer import StrategyOptimizerAgent

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
