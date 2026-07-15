"""Public P0 telemetry facade.

The score engine owns the calculation so production scoring and telemetry cannot
silently drift apart.
"""

from .score_engine import decision_telemetry, score_component_breakdown

__all__ = ["decision_telemetry", "score_component_breakdown"]
