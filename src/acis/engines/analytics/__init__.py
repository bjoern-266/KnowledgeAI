"""Analytics Engine (Sprint 9).

Collects per-post performance via the analytics port, normalises it into
platform-agnostic KPIs (emphasising the north-star save-rate and share-rate),
and persists a :class:`~acis.domain.models.MetricSnapshot` time series linked to
the content/platform so the Learning Engine can attribute performance.

See ``docs/architecture/modules/analytics-engine.md`` and
``CONTENT_INTELLIGENCE.md`` §8.
"""

from acis.engines.analytics.engine import AnalyticsEngine, AnalyticsEngineConfig

__all__ = ["AnalyticsEngine", "AnalyticsEngineConfig"]
