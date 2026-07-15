"""Enumerations shared across the domain."""

from __future__ import annotations

from enum import StrEnum


class Platform(StrEnum):
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"


class ContentFormat(StrEnum):
    INSTAGRAM_CAROUSEL = "instagram_carousel"
    TIKTOK_VIDEO = "tiktok_video"


class TopicCategory(StrEnum):
    SCIENCE = "science"
    HISTORY = "history"
    TECHNOLOGY = "technology"
    AI = "ai"
    ECONOMY = "economy"
    PSYCHOLOGY = "psychology"
    HEALTH = "health"
    NUTRITION = "nutrition"
    SPACE = "space"
    NATURE = "nature"
    GEOGRAPHY = "geography"
    CURIOSITIES = "curiosities"
    MYTH_VS_REALITY = "myth_vs_reality"
    STATISTICS = "statistics"
    RANKINGS = "rankings"
    CURRENT_AFFAIRS = "current_affairs"


class QualityCheck(StrEnum):
    """The distinct gates every content piece must pass before publishing."""

    FACT_CHECK = "fact_check"
    SOURCE_CHECK = "source_check"
    SPELLING_CHECK = "spelling_check"
    DESIGN_CHECK = "design_check"
    OVERALL_SCORE = "overall_score"


class PublishStatus(StrEnum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    PREPARED = "prepared"  # ready but credentials absent -> awaiting manual go
    FAILED = "failed"
    REJECTED = "rejected"  # blocked by the quality gate
