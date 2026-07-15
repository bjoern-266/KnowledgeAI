"""Virality Engine (Sprint 3).

Scores the topics that passed source screening by expected share/save potential
and ranks them, so the pipeline always invests in the highest-leverage,
evidence-backed idea. The score is transparent (per-component breakdown +
rationale), never a black box, and a diversity guard keeps the system from
collapsing onto a single category.

See ``docs/architecture/modules/virality-engine.md`` and
``CONTENT_INTELLIGENCE.md`` §3.
"""

from acis.engines.virality.engine import ViralityEngine, ViralityEngineConfig

__all__ = ["ViralityEngine", "ViralityEngineConfig"]
