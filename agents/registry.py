"""FinPilot Agent Registry.

Defines metadata for all agents across 6 organisational layers.
Status:
  active   — fully implemented, running in production
  advisory — LLM role-wrapper, generates text advice
  planned  — next sprint, not yet built

Auto-verification
-----------------
``audit_registry()`` scans the ``agents/`` package, discovers all
``BaseAgent`` subclasses and cross-references them against ``AGENT_REGISTRY``.
Call it from tests or the ``GET /agent/registry/audit`` endpoint to detect
drift between the registry (human-readable metadata) and the codebase.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Layer = Literal["management", "engineering", "strategy", "growth", "quality", "ops"]
Status = Literal["active", "planned", "advisory"]


@dataclass
class AgentMeta:
    id: int
    name: str
    key: str  # task key used in the API (or "advisory" for advisory-only)
    layer: Layer
    description: str
    status: Status
    capabilities: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "key": self.key,
            "layer": self.layer,
            "description": self.description,
            "status": self.status,
            "capabilities": self.capabilities,
        }


AGENT_REGISTRY: list[AgentMeta] = [
    # ── Layer 1: Management ──────────────────────────────────────────────
    AgentMeta(
        1,
        "CEO",
        "full",
        "management",
        "Ana orkestratör — LangGraph workflow yönetimi, tüm agent'ları koordine eder",
        "active",
        ["orchestrate", "delegate", "pipeline", "decide"],
    ),
    AgentMeta(
        2,
        "CTO",
        "advisory",
        "management",
        "Teknik kararlar, mimari denetim, güvenlik ve performans onayı",
        "advisory",
        ["architecture", "security", "review", "approve"],
    ),
    AgentMeta(
        3,
        "CPO",
        "advisory",
        "management",
        "Ürün önceliklendirme (P0-P3), özellik spesifikasyonu, MVP kararları",
        "advisory",
        ["prioritize", "roadmap", "ux", "spec"],
    ),
    AgentMeta(
        4,
        "CMO",
        "advisory",
        "management",
        "Pazarlama stratejisi, marka konumlandırması, büyüme hedefleri",
        "advisory",
        ["brand", "campaign", "positioning", "growth"],
    ),
    # ── Layer 2: Engineering ─────────────────────────────────────────────
    AgentMeta(
        5,
        "Senior Dev",
        "advisory",
        "engineering",
        "Backend ve API geliştirme, karmaşık bug çözümü, kod kalite denetimi",
        "advisory",
        ["backend", "api", "debug", "review"],
    ),
    AgentMeta(
        6,
        "Frontend Dev",
        "advisory",
        "engineering",
        "Dashboard bileşenleri, responsive tasarım, UI test",
        "advisory",
        ["ui", "component", "responsive", "test"],
    ),
    AgentMeta(
        7,
        "AI/ML Dev",
        "advisory",
        "engineering",
        "DRL model eğitimi, feature engineering, LLM entegrasyon",
        "advisory",
        ["train", "model", "features", "evaluate"],
    ),
    AgentMeta(
        8,
        "DevOps",
        "advisory",
        "engineering",
        "CI/CD pipeline, monitoring, secrets yönetimi, bulut maliyet",
        "advisory",
        ["deploy", "monitor", "ci-cd", "infra"],
    ),
    # ── Layer 3: Strategy & Research ─────────────────────────────────────
    AgentMeta(
        9,
        "Quant Research",
        "research",
        "strategy",
        "Haber araştırması, strateji hipotezleri, DRL reward araştırması",
        "active",
        ["research", "news", "hypothesis", "academic"],
    ),
    AgentMeta(
        10,
        "Strategy Optimizer",
        "optimize",
        "strategy",
        "Parametre optimizasyonu, walk-forward ve out-of-sample test",
        "active",
        ["optimize", "walk-forward", "sharpe", "bayesian"],
    ),
    AgentMeta(
        11,
        "Backtest Agent",
        "backtest",
        "strategy",
        "Strateji geriye dönük test motoru; tek sembol + çoklu-strateji rejim testi",
        "active",
        ["backtest", "strategy", "historical", "regime"],
    ),
    AgentMeta(
        11,
        "Combination Testing",
        "backtest_combo",
        "strategy",
        "Multi-kombinasyon test matrisi, A/B strateji karşılaştırması, overfit riski",
        "active",
        ["test", "matrix", "compare", "overfit"],
    ),
    AgentMeta(
        12,
        "Market Intelligence",
        "market_intel",
        "strategy",
        "Piyasa rejimi tespiti (trend/chop/volatile), sentiment, sektör rotasyonu",
        "active",
        ["regime", "sentiment", "rotation", "macro"],
    ),
    AgentMeta(
        13,
        "Performance Monitor",
        "monitor",
        "strategy",
        "Canlı sinyal performans takibi, strateji bozulma (decay) tespiti",
        "active",
        ["track", "warn", "stop", "decay"],
    ),
    # ── Layer 4: Growth ──────────────────────────────────────────────────
    AgentMeta(
        14,
        "Growth Marketer",
        "advisory",
        "growth",
        "Kullanıcı edinme stratejileri, funnel optimizasyonu, kanal metrikleri",
        "advisory",
        ["acquire", "funnel", "cac", "retention"],
    ),
    AgentMeta(
        15,
        "Content Strategist",
        "advisory",
        "growth",
        "Blog, YouTube script, LinkedIn içerikleri, SEO, Academy modülü",
        "advisory",
        ["write", "seo", "social", "academy"],
    ),
    AgentMeta(
        16,
        "Business Dev",
        "advisory",
        "growth",
        "Partner araştırması, yatırımcı ilişkileri, pitch deck",
        "advisory",
        ["prospect", "pitch", "partner", "investor"],
    ),
    AgentMeta(
        17,
        "Competitive Intel",
        "advisory",
        "growth",
        "Rakip ürün takibi, farklılaşma matrisi, pazar boşluğu tespiti",
        "advisory",
        ["analyze", "differentiate", "monitor", "gap"],
    ),
    # ── Layer 5: Quality ─────────────────────────────────────────────────
    AgentMeta(
        18,
        "QA / Test",
        "advisory",
        "quality",
        "Unit/integration/E2E test yönetimi, bug raporu ve önceliklendirme",
        "advisory",
        ["test", "coverage", "report", "regression"],
    ),
    AgentMeta(
        19,
        "Code Review",
        "advisory",
        "quality",
        "PR inceleme, güvenlik ve performans kontrolü, refactor önerileri",
        "advisory",
        ["review", "security", "performance", "refactor"],
    ),
    AgentMeta(
        20,
        "Data Quality",
        "data_quality",
        "quality",
        "Veri şema validasyonu, anomali tespiti, pipeline güvenilirlik kontrolü",
        "active",
        ["validate", "anomaly", "schema", "pipeline"],
    ),
    # ── Layer 6: Operations ──────────────────────────────────────────────
    AgentMeta(
        21,
        "Project Manager",
        "advisory",
        "ops",
        "Sprint planlama, görev atama, blocker tespiti ve eskalasyon",
        "advisory",
        ["plan", "assign", "track", "escalate"],
    ),
    AgentMeta(
        22,
        "Documentation",
        "report",
        "ops",
        "Günlük Markdown raporu, API dokümantasyonu, karar notları",
        "active",
        ["document", "summarize", "markdown", "adr"],
    ),
    AgentMeta(
        23,
        "Customer Success",
        "advisory",
        "ops",
        "Kullanıcı geri bildirim analizi, NPS takibi, churn riski uyarısı",
        "advisory",
        ["feedback", "nps", "churn", "onboard"],
    ),
    # ── Layer 3 additions: INT-5 researchers + Social Intelligence ───────
    AgentMeta(
        24,
        "Bull Researcher",
        "bull_research",
        "strategy",
        "Sembol başına boğa tezi üretimi — LLM destekli 3-5 yükseliş argümanı + katalizörler",
        "active",
        ["bull", "catalyst", "upside", "debate"],
    ),
    AgentMeta(
        25,
        "Bear Researcher",
        "bear_research",
        "strategy",
        "Sembol başına ayı tezi üretimi — LLM destekli 3-5 risk argümanı + tehditler",
        "active",
        ["bear", "risk", "downside", "debate"],
    ),
    AgentMeta(
        26,
        "Social Intelligence",
        "social_intel",
        "strategy",
        "Reddit/HN/Polymarket sosyal sentiment tespiti; buzz seviyesi + FinBERT skoru",
        "active",
        ["sentiment", "reddit", "polymarket", "social"],
    ),
    # ── Worker agents missing from original org-chart registry ───────────
    AgentMeta(
        27,
        "Alert Agent",
        "alert",
        "ops",
        "Onaylanan sinyal için Telegram + dashboard bildirimi",
        "active",
        ["telegram", "notify", "alert", "signal"],
    ),
    AgentMeta(
        28,
        "Analysis Agent",
        "analysis",
        "strategy",
        "Sembol başına teknik + bağlamsal analiz; rejim ve LLM destekli yorum",
        "active",
        ["analysis", "technical", "llm", "context"],
    ),
    AgentMeta(
        29,
        "Risk Agent",
        "risk",
        "strategy",
        "Pozisyon riski değerlendirmesi; Kelly kriterli boyutlandırma ve DD limiti kontrolü",
        "active",
        ["risk", "kelly", "position", "drawdown"],
    ),
    AgentMeta(
        30,
        "Alpha Tracker",
        "alpha_tracker",
        "quality",
        "Sembol bazlı rolling win-rate ve profit-factor; dinamik skor eşik önerisi",
        "active",
        ["win-rate", "alpha", "threshold", "tracker"],
    ),
]

# Quick lookup helpers
_by_id: dict[int, AgentMeta] = {a.id: a for a in AGENT_REGISTRY}
_by_key: dict[str, list[AgentMeta]] = {}
for _a in AGENT_REGISTRY:
    _by_key.setdefault(_a.key, []).append(_a)


def get_by_id(agent_id: int) -> AgentMeta | None:
    return _by_id.get(agent_id)


def get_by_layer(layer: Layer) -> list[AgentMeta]:
    return [a for a in AGENT_REGISTRY if a.layer == layer]


def get_by_status(status: Status) -> list[AgentMeta]:
    return [a for a in AGENT_REGISTRY if a.status == status]


def registry_as_dict() -> dict:
    layers: dict[str, list[dict]] = {}
    for a in AGENT_REGISTRY:
        layers.setdefault(a.layer, []).append(a.to_dict())
    return {
        "total": len(AGENT_REGISTRY),
        "by_status": {
            "active": len(get_by_status("active")),
            "planned": len(get_by_status("planned")),
            "advisory": len(get_by_status("advisory")),
        },
        "layers": layers,
        "agents": [a.to_dict() for a in AGENT_REGISTRY],
    }


# ---------------------------------------------------------------------------
# Auto-verification (Audit #5)
# ---------------------------------------------------------------------------

def discover_agent_classes() -> dict[str, str]:
    """Scan ``agents/`` package and return all BaseAgent subclass names.

    Returns
    -------
    dict mapping class_name → module_path (e.g. "ScannerAgent" → "agents.scanner_agent")
    Skips modules that fail to import (missing optional deps, etc.).
    """
    import importlib
    import inspect
    import pkgutil
    import agents as _agents_pkg
    from agents.base import BaseAgent

    found: dict[str, str] = {}
    for module_info in pkgutil.iter_modules(_agents_pkg.__path__):
        mod_name = f"agents.{module_info.name}"
        try:
            mod = importlib.import_module(mod_name)
        except Exception:  # noqa: BLE001 — optional deps, skip silently
            continue
        for name, obj in inspect.getmembers(mod, inspect.isclass):
            if (
                issubclass(obj, BaseAgent)
                and obj is not BaseAgent
                and obj.__module__ == mod_name
            ):
                found[name] = mod_name
    return found


def audit_registry() -> dict:
    """Cross-reference discovered BaseAgent subclasses against AGENT_REGISTRY.

    Returns a summary with:
    - ``discovered``: all BaseAgent subclasses found in agents/ (class → module)
    - ``registered_active``: names of active agents in registry
    - ``in_code_not_registry``: classes found in code but missing from registry
    - ``in_registry_not_code``: active registry entries with no matching class
    - ``ok``: True when no discrepancies
    """
    discovered = discover_agent_classes()

    # Strip internal/base classes that aren't real agents
    _INTERNAL = {"_AdvisoryBase"}
    discovered_real = {k: v for k, v in discovered.items() if k not in _INTERNAL}

    registered_active = {
        a.name.replace(" ", "") + "Agent": a.name
        for a in AGENT_REGISTRY
        if a.status == "active"
    }
    # Explicit class-name → registry mapping covering all layers
    _key_to_class: dict[str, str] = {
        "scanner": "ScannerAgent",
        "full": "ScannerAgent",
        "research": "ResearchAgent",
        "analysis": "AnalysisAgent",
        "risk": "RiskAgent",
        "alert": "AlertAgent",
        "backtest": "BacktestAgent",
        "bull_research": "BullResearcherAgent",
        "bear_research": "BearResearcherAgent",
        "social_intel": "SocialIntelligenceAgent",
        "market_intel": "MarketIntelligenceAgent",
        "data_quality": "DataQualityAgent",
        "optimize": "StrategyOptimizerAgent",
        "monitor": "PerformanceMonitorAgent",
        "report": "ReportAgent",
        "alpha_tracker": "AlphaTrackerAgent",
        "backtest_combo": "ComboTestingAgent",
        # Advisory personas — named agents in advisory.py
        "advisory": "SeniorDevAgent",  # placeholder; advisory key covers all personas
    }
    # Collect all registered class names (active + advisory persona classes)
    registered_class_names: set[str] = {
        _key_to_class.get(a.key, "")
        for a in AGENT_REGISTRY
        if a.status in ("active", "advisory")
    } - {""}
    # Also add advisory dynamic classes by convention
    advisory_class_names = {
        k for k in discovered_real
        if discovered_real[k] == "agents.advisory"
    }
    registered_class_names |= advisory_class_names

    in_code_not_registry = sorted(
        set(discovered_real.keys()) - registered_class_names
    )
    in_registry_not_code = sorted(
        registered_class_names - set(discovered_real.keys())
    )

    return {
        "discovered": discovered_real,
        "registered_active_count": len([a for a in AGENT_REGISTRY if a.status == "active"]),
        "discovered_count": len(discovered_real),
        "in_code_not_registry": in_code_not_registry,
        "in_registry_not_code": in_registry_not_code,
        "ok": not in_code_not_registry and not in_registry_not_code,
    }
