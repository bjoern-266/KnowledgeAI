"""Engine layer - the business modules of ACIS.

Each of the ten engines owns exactly one stage of the workflow. In the
foundation only the *interfaces* exist (see :mod:`acis.engines.interfaces`);
concrete implementations are added one module at a time, each after its own
architecture review, as required by the project plan.

The interfaces are expressed as ``Protocol`` classes over domain models, so an
engine's collaborators (and tests) can depend on the contract without importing
any implementation. This is what enforces "modules communicate only through
defined interfaces".
"""

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

__all__ = [
    "AnalyticsEngine",
    "CanvaAutomationEngine",
    "ContentEngine",
    "LearningEngine",
    "PublishingEngine",
    "QualityEngine",
    "ResearchEngine",
    "TikTokVideoEngine",
    "TrendIntelligenceEngine",
    "ViralityEngine",
]
