"""Content pipeline orchestrator.

Wires the ten workflow stages together, depending only on the engine
*interfaces* from :mod:`acis.engines.interfaces`. It knows the order of steps
and how data flows between them; it knows nothing about how any engine works or
whether its integrations are mock or live.

The quality gate is enforced here: content scoring below the configured
threshold is rejected and never published, satisfying the project's hard
requirement.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from acis.core.config import Settings
from acis.core.errors import NoViableTopicError, QualityGateError
from acis.core.logging import BoundLogger, get_logger
from acis.data.repository import Repository
from acis.domain.enums import PublishStatus
from acis.domain.models import (
    ContentPiece,
    DesignResult,
    KnowledgeBase,
    PublishReceipt,
    QualityReport,
    Topic,
    VideoResult,
)
from acis.engines.interfaces import (
    AnalyticsEngine,
    CanvaAutomationEngine,
    ContentEngine,
    LearningEngine,
    PublishingEngine,
    QualityEngine,
    ResearchEngine,
    TikTokVideoEngine,
    TrendIntelligenceEngine,
    ViralityEngine,
)


@dataclass
class PipelineResult:
    """The artifacts produced by one end-to-end run."""

    topic: Topic
    knowledge: KnowledgeBase
    content: ContentPiece
    design: DesignResult
    video: VideoResult
    quality: QualityReport
    receipts: list[PublishReceipt] = field(default_factory=list)
    #: Per-platform metrics: platform value -> KPI dict.
    metrics: dict[str, dict[str, float]] = field(default_factory=dict)


@dataclass
class ContentPipeline:
    """Orchestrates the full trend -> publish -> learn workflow."""

    settings: Settings
    trend: TrendIntelligenceEngine
    virality: ViralityEngine
    research: ResearchEngine
    content: ContentEngine
    canva: CanvaAutomationEngine
    tiktok: TikTokVideoEngine
    quality: QualityEngine
    publishing: PublishingEngine
    analytics: AnalyticsEngine
    learning: LearningEngine
    #: Optional store; when present, published topics are recorded for dedup.
    repository: Repository | None = None

    def __post_init__(self) -> None:
        self.log: BoundLogger = BoundLogger(get_logger("acis.pipeline"))

    def run_once(self, *, region: str = "global", publish: bool = True) -> PipelineResult:
        """Execute a single full cycle and return everything produced.

        Stage ordering is deliberate (see ADR-0005): cheap source **screening**
        happens *before* virality scoring so topics with a weak factual basis are
        discarded early, and the expensive deep **research** runs only for the
        single winning topic. This spends resources where they pay off.
        """
        # 1-2. Detect trends & collect candidate topics.
        trends = self.trend.discover(region=region)
        topics = self.trend.to_topics(trends)
        if not topics:
            raise NoViableTopicError("No topics could be derived from trends")

        # 3. Cheap screening: keep only topics with a sufficient source base.
        viable = [t for t in topics if self.research.screen(t).sufficient]
        self.log.info("pipeline.screened", candidates=len(topics), viable=len(viable))
        if not viable:
            raise NoViableTopicError(
                "No candidate topic passed source screening",
                context={"candidates": len(topics)},
            )

        # 4. Score virality on the survivors and pick the strongest.
        ranked = self.virality.rank(viable)
        topic = ranked[0]
        self.log.info("pipeline.topic_selected", topic=topic.title, category=topic.category.value)

        # 5. Deep research (verified facts) for the winning topic only.
        knowledge = self.research.research(topic)

        # 6. Create platform content (carousel is the primary artifact).
        content = self.content.create(topic, knowledge)

        # 7. Design automatically in Canva.
        design = self.canva.design(content)

        # 8. Derive the TikTok video from the same content/design.
        video = self.tiktok.render(content, design)

        # 9. Quality gate - fact/source/spelling/design/score checks.
        report = self.quality.evaluate(content, knowledge, design.assets)
        if not report.passed:
            self.log.warning(
                "pipeline.quality_rejected",
                score=report.overall,
                threshold=report.threshold,
                issues=len(report.issues),
            )
            raise QualityGateError(
                f"Content rejected by quality gate (score={report.overall:.2f} "
                f"< {report.threshold:.2f})",
                context={"content_id": content.id, "issues": report.issues},
            )

        result = PipelineResult(
            topic=topic,
            knowledge=knowledge,
            content=content,
            design=design,
            video=video,
            quality=report,
        )

        # 10. Publish (or prepare, when credentials are absent) to each platform.
        if publish:
            receipts = self.publishing.publish(content, design.assets, video)
            result.receipts.extend(receipts)
            # 11-12. Collect metrics and learn from them, per platform.
            for receipt in receipts:
                metrics = self.analytics.collect(receipt)
                if metrics:
                    result.metrics[receipt.platform.value] = metrics
                    self.learning.learn(topic, receipt, metrics)
            self._record_published(topic, receipts)

        self.log.info("pipeline.completed", content_id=content.id, published=publish)
        return result

    def _record_published(self, topic: Topic, receipts: list[PublishReceipt]) -> None:
        """Persist the topic so future runs de-duplicate against it (best-effort)."""
        if self.repository is None:
            return
        if not any(r.status is PublishStatus.PUBLISHED for r in receipts):
            return
        try:
            self.repository.save("published_topics", topic)
        except Exception:  # noqa: BLE001 - dedup persistence is best-effort
            self.log.exception("pipeline.record_published_failed")
