"""Reference engine implementations - foundation scaffolding.

These are intentionally minimal implementations of the engine interfaces, built
directly on the mock/live integration ports. Their sole purpose is to prove the
end-to-end wiring (Definition of Success) works today, before any real engine
is built.

Each will be superseded by a full, reviewed engine implementation under
``acis/engines/<name>/``. Because everything depends on the interfaces in
:mod:`acis.engines.interfaces`, swapping a reference engine for its real
counterpart is a one-line change in :func:`build_reference_pipeline` - nothing
else in the system is affected.
"""

from __future__ import annotations

from acis.core.context import AppContext
from acis.core.pipeline import ContentPipeline
from acis.domain.models import PublishReceipt
from acis.engines.analytics import AnalyticsEngine, AnalyticsEngineConfig
from acis.engines.canva import CanvaEngine, CanvaEngineConfig
from acis.engines.content import ContentEngine, ContentEngineConfig
from acis.engines.publishing import PublishingEngine, PublishingEngineConfig
from acis.engines.quality import QualityEngine, QualityEngineConfig
from acis.engines.research import ResearchEngine, ResearchEngineConfig
from acis.engines.tiktok import TikTokVideoEngine
from acis.engines.trend import TrendEngine, TrendEngineConfig
from acis.engines.virality import ViralityEngine


class ReferenceLearningEngine:
    def learn(self, receipt: PublishReceipt, metrics: dict[str, float]) -> dict[str, float]:
        # Foundation stub: echo the save/share rates as "learned" signals.
        return {
            "save_rate": metrics.get("save_rate", 0.0),
            "share_rate": metrics.get("share_rate", 0.0),
        }


def build_trend_engine(context: AppContext) -> TrendEngine:
    """Construct the production Trend Intelligence Engine (Sprint 1)."""
    s = context.settings
    return TrendEngine(
        sources=[context.integrations.trends],
        repository=context.repository,
        config=TrendEngineConfig.from_topic_values(s.content.topics),
    )


def build_research_engine(context: AppContext) -> ResearchEngine:
    """Construct the production Research Engine (Sprint 2)."""
    s = context.settings
    return ResearchEngine(
        sources=[context.integrations.research],
        repository=context.repository,
        config=ResearchEngineConfig.from_settings(s.quality.min_sources_per_topic),
    )


def build_virality_engine(context: AppContext) -> ViralityEngine:
    """Construct the production Virality Engine (Sprint 3).

    Historical priors are empty until the Learning Engine (Sprint 10) supplies
    them; the engine falls back to base category appeal.
    """
    return ViralityEngine(historical_priors={})


def build_content_engine(context: AppContext) -> ContentEngine:
    """Construct the production Content Engine (Sprint 4)."""
    s = context.settings
    return ContentEngine(ContentEngineConfig.from_settings(s.content.instagram_carousel_slides))


def build_canva_engine(context: AppContext) -> CanvaEngine:
    """Construct the production Canva Automation Engine (Sprint 5)."""
    return CanvaEngine(
        context.integrations.canva,
        CanvaEngineConfig.from_branding(context.settings.branding),
    )


def build_tiktok_video_engine(context: AppContext) -> TikTokVideoEngine:
    """Construct the production TikTok Video Engine (Sprint 6)."""
    return TikTokVideoEngine()


def build_quality_engine(context: AppContext) -> QualityEngine:
    """Construct the production Quality Engine (Sprint 7)."""
    return QualityEngine(QualityEngineConfig.from_settings(context.settings))


def build_publishing_engine(context: AppContext) -> PublishingEngine:
    """Construct the production Publishing Engine (Sprint 8)."""
    return PublishingEngine(
        context.integrations.instagram,
        context.integrations.tiktok,
        repository=context.repository,
        config=PublishingEngineConfig.from_settings(context.settings),
    )


def build_analytics_engine(context: AppContext) -> AnalyticsEngine:
    """Construct the production Analytics Engine (Sprint 9)."""
    return AnalyticsEngine(
        context.integrations.analytics,
        repository=context.repository,
        config=AnalyticsEngineConfig(),
    )


def build_reference_pipeline(context: AppContext) -> ContentPipeline:
    """Assemble a runnable pipeline: production engines where available, reference
    stand-ins for the rest. As each sprint lands, its reference engine here is
    replaced by the real implementation - the rest of the system is untouched.
    """
    return ContentPipeline(
        settings=context.settings,
        trend=build_trend_engine(context),  # Sprint 1: production engine
        research=build_research_engine(context),  # Sprint 2: production engine
        virality=build_virality_engine(context),  # Sprint 3: production engine
        content=build_content_engine(context),  # Sprint 4: production engine
        canva=build_canva_engine(context),  # Sprint 5: production engine
        tiktok=build_tiktok_video_engine(context),  # Sprint 6: production engine
        quality=build_quality_engine(context),  # Sprint 7: production engine
        publishing=build_publishing_engine(context),  # Sprint 8: production engine
        analytics=build_analytics_engine(context),  # Sprint 9: production engine
        learning=ReferenceLearningEngine(),
        repository=context.repository,
    )
