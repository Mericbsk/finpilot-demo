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
    "OllamaProvider",
    "MockProvider",
]


def __getattr__(name):  # lazy export — providers loaded only when accessed
    if name == "OllamaProvider":
        from llm.ollama_provider import OllamaProvider

        return OllamaProvider
    if name == "MockProvider":
        from llm.mock_provider import MockProvider

        return MockProvider
    raise AttributeError(f"module 'llm' has no attribute {name!r}")
