"""Integration *ports* - the abstract contracts engines depend on.

These Protocols express what the rest of the system needs from each external
service, phrased in domain terms. Engines depend on these ports, never on a
concrete adapter, so mock and live implementations are freely interchangeable.

Keeping the surface small is deliberate: the narrower the port, the easier both
the mock and the live adapter are to keep correct.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from acis.domain.models import (
    Asset,
    ContentPiece,
    DesignResult,
    PublishReceipt,
    Trend,
    VideoResult,
)


@runtime_checkable
class TrendSourcePort(Protocol):
    """A source of trending signals (Google Trends, TikTok, news, ...)."""

    def fetch_trends(self, *, region: str = "global", limit: int = 20) -> list[Trend]: ...


@runtime_checkable
class LLMPort(Protocol):
    """A large-language-model provider used for research/writing tasks."""

    def complete(self, prompt: str, *, system: str = "", max_tokens: int = 1024) -> str: ...


@runtime_checkable
class CanvaPort(Protocol):
    """Automated design creation and export (Canva Premium)."""

    def create_design(self, content: ContentPiece) -> DesignResult: ...

    def export(self, design_id: str, *, fmt: str = "png") -> list[Asset]: ...


@runtime_checkable
class InstagramPort(Protocol):
    """Publishing to Instagram (carousel)."""

    def publish_carousel(self, content: ContentPiece, assets: list[Asset]) -> PublishReceipt: ...


@runtime_checkable
class TikTokPort(Protocol):
    """Publishing to TikTok (video)."""

    def publish_video(self, content: ContentPiece, video: VideoResult) -> PublishReceipt: ...


@runtime_checkable
class AnalyticsPort(Protocol):
    """Retrieving performance metrics for published content."""

    def fetch_metrics(self, external_id: str) -> dict[str, float]: ...
