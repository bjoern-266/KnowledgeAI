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


class FactType(StrEnum):
    """Typed classification of a researched fact (Research Engine, Sprint 2).

    Typing facts up front lets later engines (Content, Canva, Quality) build
    slides and pick visuals without re-analysing free text.
    """

    KEY_CLAIM = "key_claim"
    DEFINITION = "definition"
    STATISTIC = "statistic"
    HISTORICAL_EVENT = "historical_event"
    DATE = "date"
    QUOTE = "quote"
    CAUSE = "cause"
    EFFECT = "effect"
    COMPARISON = "comparison"
    RECORD = "record"
    MYTH = "myth"
    WARNING = "warning"


class VisualType(StrEnum):
    """How a fact could be rendered as a slide/graphic (drives the Canva Engine)."""

    CHART = "chart"
    MAP = "map"
    TIMELINE = "timeline"
    BEFORE_AFTER = "before_after"
    INFOBOX = "infobox"
    IMAGE = "image"


class HookType(StrEnum):
    """A candidate hook the Content Engine can open with."""

    SURPRISING_NUMBER = "surprising_number"
    CONTROVERSIAL_FACT = "controversial_fact"
    COMMON_MISCONCEPTION = "common_misconception"
    INCREDIBLE_RECORD = "incredible_record"


class SourceType(StrEnum):
    """Whether a source is the origin of a claim or reports it second-hand."""

    PRIMARY = "primary"
    SECONDARY = "secondary"
