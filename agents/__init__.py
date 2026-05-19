"""FinPilot Multi-Agent System — Sprint 6.

Layer architecture:
    Data Layer        →  yfinance, scanner, DRL inference
    LLM Provider      →  llm/router.py (Claude/Gemini/Groq failover)
    Agent Layer       →  agents/ (this package)
    Workflow Layer    →  agents/ceo.py LangGraph StateGraph
    API Interface     →  api/routers/agent.py  POST /api/v1/agent/run
"""

from agents.base import AgentContext, AgentResult, BaseAgent
from agents.ceo import get_graph

__all__ = ["AgentContext", "AgentResult", "BaseAgent", "get_graph"]
