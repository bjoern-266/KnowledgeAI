"""Research Engine (Sprint 2).

Produces a structured :class:`~acis.domain.models.KnowledgeBase` from retrieved
documents - not a pile of search hits. It screens topics cheaply for source
availability, then for the winning topic gathers, cross-verifies, types, and
scores facts, and pre-computes hooks and visual ideas so downstream engines
(Content, Canva, Quality) need almost no extra logic.

Hard rule: every fact traces to a retrieved source. Nothing is invented,
estimated, or creatively completed - unsupported claims are flagged, not filled.

See ``docs/architecture/modules/research-engine.md`` and
``CONTENT_INTELLIGENCE.md`` §2, §4.
"""

from acis.engines.research.engine import ResearchEngine, ResearchEngineConfig

__all__ = ["ResearchEngine", "ResearchEngineConfig"]
