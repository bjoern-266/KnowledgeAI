"""Domain layer: the shared data contracts exchanged between modules.

These models are the *only* coupling permitted between otherwise independent
engines. An engine consumes some domain objects and produces others; it never
imports another engine's internals. Keeping this layer stable and explicit is
what makes the system modular and testable.
"""

from acis.domain.enums import (
    ContentFormat,
    FactType,
    HookType,
    Platform,
    PublishStatus,
    QualityCheck,
    SourceType,
    TopicCategory,
    VisualType,
)
from acis.domain.models import (
    Asset,
    CategoryPrior,
    ContentPiece,
    Definition,
    DesignResult,
    Fact,
    HookCandidate,
    KnowledgeBase,
    MetricSnapshot,
    PublishReceipt,
    QualityReport,
    RetrievedDocument,
    Slide,
    Source,
    SourceAvailability,
    Statistic,
    TimelineEntry,
    Topic,
    Trend,
    VideoResult,
    ViralityScore,
    VisualIdea,
)

__all__ = [
    "Asset",
    "CategoryPrior",
    "ContentFormat",
    "ContentPiece",
    "Definition",
    "DesignResult",
    "Fact",
    "FactType",
    "HookCandidate",
    "HookType",
    "KnowledgeBase",
    "MetricSnapshot",
    "Platform",
    "PublishReceipt",
    "PublishStatus",
    "QualityCheck",
    "QualityReport",
    "RetrievedDocument",
    "Slide",
    "Source",
    "SourceAvailability",
    "SourceType",
    "Statistic",
    "TimelineEntry",
    "Topic",
    "TopicCategory",
    "Trend",
    "VideoResult",
    "ViralityScore",
    "VisualIdea",
    "VisualType",
]
