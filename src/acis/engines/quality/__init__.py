"""Quality Engine (Sprint 7).

The gatekeeper. Runs independent gates - fact, source, language/spelling, and
design/branding - aggregates them into an overall score, and reports whether the
content clears the configured threshold. It only *reports*; the pipeline
enforces the hard stop, so the rule lives in exactly one place.

Fail-closed: uncertainty or missing evidence lowers or blocks the score, never
raises it. See ``docs/architecture/modules/quality-engine.md`` and
``CONTENT_INTELLIGENCE.md`` §7.
"""

from acis.engines.quality.engine import QualityEngine, QualityEngineConfig

__all__ = ["QualityEngine", "QualityEngineConfig"]
