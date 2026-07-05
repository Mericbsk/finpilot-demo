"""FinPilot Distribution Layer — snapshot, brief rendering, lint, broadcast queue.

Single production line, three consumers:
  * web demo  (public/demo_snapshot.json)
  * free Telegram daily brief
  * premium Telegram daily brief

Design contract (see FinPilot_Ticari_Katman_Uygulama_Plani_2026-07-03.md):
  - Pure stdlib (no pandas / jinja2) so it runs anywhere the scheduler runs.
  - Every outbound financial text passes through ``lint.check_text`` and the
    human approval queue (``broadcast``) before publication.
  - The snapshot is versioned (``schema.SCHEMA_VERSION``) and stamped with the
    active feature-flag configuration (config_sha) for reproducibility.
"""

from distribution.schema import SCHEMA_VERSION, validate_snapshot  # noqa: F401
