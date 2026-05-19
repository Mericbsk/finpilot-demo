"""FinPilot Agent Registry.

Defines metadata for all 23 agents across 6 organisational layers.
Status:
  active   — fully implemented, running in production
  planned  — next sprint, not yet built
  advisory — LLM role-wrapper, generates text advice
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
        "Combination Testing",
        "backtest",
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
        "advisory",
        "quality",
        "Veri şema validasyonu, anomali tespiti, pipeline güvenilirlik kontrolü",
        "advisory",
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
