"""Trend Intelligence Engine (Sprint 1).

The first production engine. It aggregates trend signals from one or more
sources, filters them to the knowledge niche, removes duplicates, assigns a
preliminary relevance score, and emits a structured, ranked list of candidate
topics.

See the design doc: ``docs/architecture/modules/trend-intelligence-engine.md``
and the business rules in ``CONTENT_INTELLIGENCE.md`` §1-2.
"""

from acis.engines.trend.engine import TrendEngine, TrendEngineConfig

__all__ = ["TrendEngine", "TrendEngineConfig"]
