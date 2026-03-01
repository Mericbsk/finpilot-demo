"""
FinPilot LLM Abstraction Layer
===============================

Provider-agnostic LLM interface with automatic failover.

Sprint 19: Initial implementation — Groq, Claude, Gemini providers + smart router.

Usage:
    from llm import get_router

    router = get_router()
    response = router.generate("Analyze AAPL stock", language="tr")
    # or stream:
    for chunk in router.stream("Analyze AAPL stock"):
        print(chunk, end="")
"""

from llm.base import LLMProvider, LLMResponse
from llm.router import LLMRouter, get_router

__all__ = [
    "LLMProvider",
    "LLMResponse",
    "LLMRouter",
    "get_router",
]
