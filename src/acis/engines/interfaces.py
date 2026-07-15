"""Engine interfaces (contracts only).

These Protocols define the boundary of every business module. The pipeline
orchestrator depends solely on these types; it does not know which concrete
implementation (or the mock/live mode of its integrations) sits behind them.

Implementations are added per-module after architecture review. Until then a
minimal *reference* pipeline (see :mod:`acis.core.pipeline`) can be assembled
from lightweight built-in implementations to prove the end-to-end flow with
mock integrations.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from acis.domain.models import (
    Asset,
    ContentPiece,
    DesignResult,
    KnowledgeBase,
    PublishReceipt,
    QualityReport,
    SourceAvailability,
    Topic,
    Trend,
    VideoResult,
    ViralityScore,
)


@runtime_checkable
class TrendIntelligenceEngine(Protocol):
    """Step 1-2: detect trends and collect candidate topics."""

    def discover(self, *, region: str = "global", limit: int = 20) -> list[Trend]: ...

    def to_topics(self, trends: list[Trend]) -> list[Topic]: ...


@runtime_checkable
class ResearchEngine(Protocol):
    """Step 3 (screen) + step 5 (deep research).

    ``screen`` is a cheap, pre-virality check that only establishes whether a
    topic has enough credible sources to be worth pursuing. ``research`` is the
    expensive step that extracts and verifies facts, run only for the single
    winning topic. Splitting them lets the pipeline discard weak topics before
    spending resources on scoring or content creation.
    """

    def screen(self, topic: Topic) -> SourceAvailability: ...

    def research(self, topic: Topic) -> KnowledgeBase: ...


@runtime_checkable
class ViralityEngine(Protocol):
    """Step 4: score topics (that passed screening) by share/save potential."""

    def score(self, topic: Topic) -> ViralityScore: ...

    def rank(self, topics: list[Topic]) -> list[Topic]: ...


@runtime_checkable
class ContentEngine(Protocol):
    """Step 5: turn a knowledge base into platform-ready content."""

    def create(self, topic: Topic, knowledge: KnowledgeBase) -> ContentPiece: ...


@runtime_checkable
class CanvaAutomationEngine(Protocol):
    """Step 6: produce branded designs automatically via Canva."""

    def design(self, content: ContentPiece) -> DesignResult: ...


@runtime_checkable
class TikTokVideoEngine(Protocol):
    """Derive a TikTok video from a content piece / design."""

    def render(self, content: ContentPiece, design: DesignResult) -> VideoResult: ...


@runtime_checkable
class QualityEngine(Protocol):
    """Fact/source/spelling/design/score gates before publishing."""

    def evaluate(
        self,
        content: ContentPiece,
        knowledge: KnowledgeBase,
        assets: list[Asset],
    ) -> QualityReport: ...


@runtime_checkable
class PublishingEngine(Protocol):
    """Step 7: publish (or prepare) content on each platform."""

    def publish(self, content: ContentPiece, assets: list[Asset]) -> PublishReceipt: ...


@runtime_checkable
class AnalyticsEngine(Protocol):
    """Step 8: collect performance metrics for published content."""

    def collect(self, receipt: PublishReceipt) -> dict[str, float]: ...


@runtime_checkable
class LearningEngine(Protocol):
    """Step 9: turn performance into guidance for future content."""

    def learn(self, receipt: PublishReceipt, metrics: dict[str, float]) -> dict[str, float]: ...
