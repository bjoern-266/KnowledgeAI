"""Publishing Engine (Sprint 8).

Publishes approved content to Instagram (carousel) and TikTok (video) - or, when
credentials are absent or the live API is unavailable, prepares it for one-click
go-live. Idempotent (never double-posts) and persists a receipt per attempt.

Switching mock -> live is pure configuration: once credentials are present and
the live adapters implemented, the same engine publishes automatically.

See ``docs/architecture/modules/publishing-engine.md``.
"""

from acis.engines.publishing.engine import PublishingEngine, PublishingEngineConfig

__all__ = ["PublishingEngine", "PublishingEngineConfig"]
