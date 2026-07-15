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

from acis.core.config import Settings
from acis.core.context import AppContext
from acis.core.pipeline import ContentPipeline
from acis.domain.enums import (
    Platform,
    PublishStatus,
    QualityCheck,
)
from acis.domain.models import (
    Asset,
    ContentPiece,
    KnowledgeBase,
    PublishReceipt,
    QualityReport,
)
from acis.engines.canva import CanvaEngine, CanvaEngineConfig
from acis.engines.content import ContentEngine, ContentEngineConfig
from acis.engines.research import ResearchEngine, ResearchEngineConfig
from acis.engines.tiktok import TikTokVideoEngine
from acis.engines.trend import TrendEngine, TrendEngineConfig
from acis.engines.virality import ViralityEngine
from acis.integrations.base import IntegrationBundle


class ReferenceQualityEngine:
    def __init__(self, settings: Settings) -> None:
        self._q = settings.quality

    def evaluate(
        self,
        content: ContentPiece,
        knowledge: KnowledgeBase,
        assets: list[Asset],
    ) -> QualityReport:
        scores: dict[QualityCheck, float] = {}
        issues: list[str] = []

        scores[QualityCheck.SOURCE_CHECK] = (
            1.0 if knowledge.source_count >= self._q.min_sources_per_topic else 0.0
        )
        if scores[QualityCheck.SOURCE_CHECK] < 1.0:
            issues.append("insufficient sources")

        # Prefer corroborated facts; the knowledge base already flags uncertain ones.
        corroborated = [f for f in knowledge.facts if not f.uncertain]
        scores[QualityCheck.FACT_CHECK] = knowledge.confidence if corroborated else 0.0
        if not corroborated:
            issues.append("no corroborated facts")
        scores[QualityCheck.SPELLING_CHECK] = 1.0 if content.slides else 0.0
        scores[QualityCheck.DESIGN_CHECK] = 1.0 if assets else 0.0

        component_values = list(scores.values())
        overall = sum(component_values) / len(component_values) if component_values else 0.0
        scores[QualityCheck.OVERALL_SCORE] = round(overall, 3)

        return QualityReport(
            content_id=content.id,
            scores=scores,
            threshold=self._q.min_score,
            passed=overall >= self._q.min_score,
            issues=issues,
        )


class ReferencePublishingEngine:
    def __init__(self, integrations: IntegrationBundle) -> None:
        self._instagram = integrations.instagram

    def publish(self, content: ContentPiece, assets: list[Asset]) -> PublishReceipt:
        try:
            return self._instagram.publish_carousel(content, assets)
        except Exception as exc:  # noqa: BLE001 - degrade to "prepared" if live creds absent
            return PublishReceipt(
                content_id=content.id,
                platform=Platform.INSTAGRAM,
                status=PublishStatus.PREPARED,
                detail=f"prepared (publish unavailable: {exc})",
            )


class ReferenceAnalyticsEngine:
    def __init__(self, integrations: IntegrationBundle) -> None:
        self._analytics = integrations.analytics

    def collect(self, receipt: PublishReceipt) -> dict[str, float]:
        if not receipt.external_id:
            return {}
        try:
            return self._analytics.fetch_metrics(receipt.external_id)
        except Exception:  # noqa: BLE001 - metrics are best-effort
            return {}


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


def build_reference_pipeline(context: AppContext) -> ContentPipeline:
    """Assemble a runnable pipeline: production engines where available, reference
    stand-ins for the rest. As each sprint lands, its reference engine here is
    replaced by the real implementation - the rest of the system is untouched.
    """
    s = context.settings
    ints = context.integrations
    return ContentPipeline(
        settings=s,
        trend=build_trend_engine(context),  # Sprint 1: production engine
        research=build_research_engine(context),  # Sprint 2: production engine
        virality=build_virality_engine(context),  # Sprint 3: production engine
        content=build_content_engine(context),  # Sprint 4: production engine
        canva=build_canva_engine(context),  # Sprint 5: production engine
        tiktok=build_tiktok_video_engine(context),  # Sprint 6: production engine
        quality=ReferenceQualityEngine(s),
        publishing=ReferencePublishingEngine(ints),
        analytics=ReferenceAnalyticsEngine(ints),
        learning=ReferenceLearningEngine(),
    )
