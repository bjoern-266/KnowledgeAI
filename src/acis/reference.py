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
    ContentFormat,
    Platform,
    PublishStatus,
    QualityCheck,
    TopicCategory,
)
from acis.domain.models import (
    Asset,
    ContentPiece,
    DesignResult,
    PublishReceipt,
    QualityReport,
    ResearchDossier,
    Slide,
    Source,
    SourceAvailability,
    Topic,
    Trend,
    VideoResult,
    ViralityScore,
)
from acis.integrations.base import IntegrationBundle


class ReferenceTrendEngine:
    def __init__(self, integrations: IntegrationBundle) -> None:
        self._trends = integrations.trends

    def discover(self, *, region: str = "global", limit: int = 20) -> list[Trend]:
        return self._trends.fetch_trends(region=region, limit=limit)

    def to_topics(self, trends: list[Trend]) -> list[Topic]:
        topics: list[Topic] = []
        for trend in trends:
            topics.append(
                Topic(
                    title=trend.keyword.title(),
                    category=trend.category or TopicCategory.CURIOSITIES,
                    angle="Myth vs. reality",
                    source_trends=[trend.id],
                    keywords=[trend.keyword],
                )
            )
        return topics


class ReferenceViralityEngine:
    def score(self, topic: Topic) -> ViralityScore:
        # Simple heuristic: knowledge categories with strong "share" appeal.
        weights = {
            TopicCategory.SPACE: 0.9,
            TopicCategory.SCIENCE: 0.85,
            TopicCategory.PSYCHOLOGY: 0.85,
            TopicCategory.STATISTICS: 0.8,
        }
        base = weights.get(topic.category, 0.7)
        return ViralityScore(
            value=base,
            components={"category_fit": base, "novelty": 0.7},
            rationale="Heuristic reference score",
        )

    def rank(self, topics: list[Topic]) -> list[Topic]:
        for topic in topics:
            topic.virality = self.score(topic)
        return sorted(topics, key=lambda t: t.virality.value if t.virality else 0.0, reverse=True)


class ReferenceResearchEngine:
    def __init__(self, integrations: IntegrationBundle, min_sources: int) -> None:
        self._llm = integrations.llm
        self._min_sources = min_sources

    def screen(self, topic: Topic) -> SourceAvailability:
        # Cheap pre-check: how many candidate sources exist for this topic?
        # The reference stand-in assumes the mock encyclopedia can supply the
        # minimum for any well-formed topic; a real engine would query sources.
        count = self._min_sources if topic.title else 0
        sufficient = count >= self._min_sources
        return SourceAvailability(
            topic_id=topic.id,
            source_count=count,
            sufficient=sufficient,
            reason="" if sufficient else "no candidate sources found",
        )

    def research(self, topic: Topic) -> ResearchDossier:
        completion = self._llm.complete(
            f"Research verified facts about: {topic.title}",
            system="You are a rigorous fact researcher.",
        )
        facts = [line[2:] for line in completion.splitlines() if line.startswith("- ")]
        sources = [
            Source(
                url=f"https://sources.example/{topic.id[:8]}/{i}",
                title=f"Reference source {i + 1}",
                publisher="mock-encyclopedia",
                reliability=0.9,
            )
            for i in range(max(self._min_sources, 2))
        ]
        return ResearchDossier(
            topic_id=topic.id,
            summary=f"Verified overview of {topic.title}.",
            facts=facts or ["Placeholder fact."],
            sources=sources,
        )


class ReferenceContentEngine:
    def __init__(self, slides: int) -> None:
        self._slides = slides

    def create(self, topic: Topic, dossier: ResearchDossier) -> ContentPiece:
        slides = [Slide(index=0, headline=topic.title, body=dossier.summary, highlight=topic.angle)]
        for i, fact in enumerate(dossier.facts[: self._slides - 2], start=1):
            slides.append(Slide(index=i, headline=f"Fact {i}", body=fact, highlight=""))
        slides.append(
            Slide(index=len(slides), headline="Save & share", body="Follow for more.", highlight="")
        )
        return ContentPiece(
            topic_id=topic.id,
            dossier_id=dossier.id,
            platform=Platform.INSTAGRAM,
            content_format=ContentFormat.INSTAGRAM_CAROUSEL,
            hook=f"{topic.title}: what most people get wrong",
            slides=slides,
            caption=f"{dossier.summary} Sources in comments.",
            hashtags=["#knowledge", f"#{topic.category.value}"],
            cta="Save this for later.",
            status=PublishStatus.DRAFT,
        )


class ReferenceCanvaEngine:
    def __init__(self, integrations: IntegrationBundle) -> None:
        self._canva = integrations.canva

    def design(self, content: ContentPiece) -> DesignResult:
        return self._canva.create_design(content)


class ReferenceTikTokEngine:
    def render(self, content: ContentPiece, design: DesignResult) -> VideoResult:
        asset = Asset(
            kind="video",
            uri=f"mock://tiktok/{content.id[:8]}.mp4",
            mime_type="video/mp4",
            width=1080,
            height=1920,
        )
        return VideoResult(content_id=content.id, asset=asset, duration_seconds=22.0)


class ReferenceQualityEngine:
    def __init__(self, settings: Settings) -> None:
        self._q = settings.quality

    def evaluate(
        self,
        content: ContentPiece,
        dossier: ResearchDossier,
        assets: list[Asset],
    ) -> QualityReport:
        scores: dict[QualityCheck, float] = {}
        issues: list[str] = []

        scores[QualityCheck.SOURCE_CHECK] = (
            1.0 if dossier.source_count >= self._q.min_sources_per_topic else 0.0
        )
        if scores[QualityCheck.SOURCE_CHECK] < 1.0:
            issues.append("insufficient sources")

        scores[QualityCheck.FACT_CHECK] = 1.0 if dossier.facts else 0.0
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


def build_reference_pipeline(context: AppContext) -> ContentPipeline:
    """Assemble a runnable pipeline from reference engines + wired integrations."""
    s = context.settings
    ints = context.integrations
    return ContentPipeline(
        settings=s,
        trend=ReferenceTrendEngine(ints),
        virality=ReferenceViralityEngine(),
        research=ReferenceResearchEngine(ints, s.quality.min_sources_per_topic),
        content=ReferenceContentEngine(s.content.instagram_carousel_slides),
        canva=ReferenceCanvaEngine(ints),
        tiktok=ReferenceTikTokEngine(),
        quality=ReferenceQualityEngine(s),
        publishing=ReferencePublishingEngine(ints),
        analytics=ReferenceAnalyticsEngine(ints),
        learning=ReferenceLearningEngine(),
    )
