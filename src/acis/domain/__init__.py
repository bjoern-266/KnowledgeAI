"""Domain layer: the shared data contracts exchanged between modules.

These models are the *only* coupling permitted between otherwise independent
engines. An engine consumes some domain objects and produces others; it never
imports another engine's internals. Keeping this layer stable and explicit is
what makes the system modular and testable.
"""

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

__all__ = [
    "Asset",
    "ContentFormat",
    "ContentPiece",
    "DesignResult",
    "Platform",
    "PublishReceipt",
    "PublishStatus",
    "QualityCheck",
    "QualityReport",
    "ResearchDossier",
    "Slide",
    "Source",
    "SourceAvailability",
    "Topic",
    "TopicCategory",
    "Trend",
    "VideoResult",
    "ViralityScore",
]
