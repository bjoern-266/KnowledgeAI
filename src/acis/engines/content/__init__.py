"""Content Engine (Sprint 4).

Turns a :class:`~acis.domain.models.KnowledgeBase` into finished, platform-ready
content: an Instagram carousel (primary) plus a derived TikTok script, with
caption, hashtags and CTA. It draws entirely from the knowledge base - it never
researches - and only uses corroborated facts, so every on-screen highlight
traces to verified sources.

See ``docs/architecture/modules/content-engine.md`` and
``CONTENT_INTELLIGENCE.md`` §4, §6.
"""

from acis.engines.content.engine import ContentEngine, ContentEngineConfig

__all__ = ["ContentEngine", "ContentEngineConfig"]
