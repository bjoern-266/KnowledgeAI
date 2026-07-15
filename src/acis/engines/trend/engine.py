"""Trend Intelligence Engine implementation.

Pipeline of this engine (see CONTENT_INTELLIGENCE.md §1):

    sources.fetch_trends()          # aggregate independent signals
      -> niche filter               # keep only allowed knowledge categories
      -> cross-source de-duplication  # merge near-identical keywords
      -> relevance scoring          # momentum + evergreen weighting
      -> ranked list of Trend       # discover()
      -> map to Topic + dedup vs. history  # to_topics()

The engine depends only on the ``TrendSourcePort`` (any number of sources) and a
``Repository`` (for historical de-duplication). It never imports another engine
and communicates purely via domain models.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from acis.core.base import Engine
from acis.data.repository import Repository
from acis.domain.enums import TopicCategory
from acis.domain.models import Topic, Trend
from acis.integrations.interfaces import TrendSourcePort

# How much lasting "library" value each category tends to carry. Used to bias the
# ranking toward evergreen knowledge over transient spikes (CONTENT_INTELLIGENCE §1).
_EVERGREEN_WEIGHT: dict[TopicCategory, float] = {
    TopicCategory.SCIENCE: 0.95,
    TopicCategory.SPACE: 0.95,
    TopicCategory.HISTORY: 0.90,
    TopicCategory.PSYCHOLOGY: 0.90,
    TopicCategory.MYTH_VS_REALITY: 0.88,
    TopicCategory.NATURE: 0.85,
    TopicCategory.HEALTH: 0.85,
    TopicCategory.NUTRITION: 0.82,
    TopicCategory.TECHNOLOGY: 0.80,
    TopicCategory.AI: 0.80,
    TopicCategory.GEOGRAPHY: 0.80,
    TopicCategory.STATISTICS: 0.80,
    TopicCategory.ECONOMY: 0.75,
    TopicCategory.RANKINGS: 0.72,
    TopicCategory.CURIOSITIES: 0.70,
    TopicCategory.CURRENT_AFFAIRS: 0.60,
}

# Default framing per category (the topic's initial angle).
_ANGLES: dict[TopicCategory, str] = {
    TopicCategory.MYTH_VS_REALITY: "Myth vs. reality",
    TopicCategory.STATISTICS: "The numbers that surprise everyone",
    TopicCategory.RANKINGS: "Ranked, with the data behind it",
    TopicCategory.CURIOSITIES: "The fact most people get wrong",
    TopicCategory.HISTORY: "What actually happened",
    TopicCategory.SPACE: "The scale nobody expects",
}
_DEFAULT_ANGLE = "What most people get wrong"

_STOPWORDS = frozenset(
    {"the", "a", "an", "of", "and", "or", "in", "to", "for", "with", "on", "2025", "new"}
)


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in _STOPWORDS}


def _normalize(text: str) -> str:
    return " ".join(sorted(_tokens(text)))


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


@dataclass(frozen=True)
class TrendEngineConfig:
    """Tuning parameters for the Trend Intelligence Engine."""

    allowed_categories: frozenset[TopicCategory]
    #: Weight of evergreen value vs. raw momentum in the relevance score [0..1].
    evergreen_bias: float = 0.4
    #: Token-Jaccard similarity at/above which two keywords are treated as one.
    dedup_threshold: float = 0.6
    #: How many signals to request from each source.
    per_source_limit: int = 100
    #: Repository collection holding already-published topics (historical dedup).
    history_collection: str = "published_topics"

    @classmethod
    def from_topic_values(cls, values: Sequence[str], **kw: object) -> TrendEngineConfig:
        """Build from a list of category *values* (e.g. ``settings.content.topics``)."""
        allowed: set[TopicCategory] = set()
        for value in values:
            try:
                allowed.add(TopicCategory(value))
            except ValueError:
                continue  # ignore unknown category names
        if not allowed:
            allowed = set(TopicCategory)  # permissive fallback
        return cls(allowed_categories=frozenset(allowed), **kw)  # type: ignore[arg-type]


class TrendEngine(Engine):
    """Aggregates trend signals into a ranked, de-duplicated topic list."""

    name = "trend_intelligence"

    def __init__(
        self,
        sources: Sequence[TrendSourcePort],
        repository: Repository,
        config: TrendEngineConfig,
    ) -> None:
        super().__init__()
        self._sources = list(sources)
        self._repo = repository
        self._cfg = config

    # -- step 1: discover -----------------------------------------------------
    def discover(self, *, region: str = "global", limit: int = 60) -> list[Trend]:
        raw: list[Trend] = []
        for source in self._sources:
            try:
                raw.extend(source.fetch_trends(region=region, limit=self._cfg.per_source_limit))
            except Exception:  # noqa: BLE001 - one bad source must not kill discovery
                self.log.exception("trend.source_failed")

        niche = [t for t in raw if t.category in self._cfg.allowed_categories]
        unique = self._dedup_trends(niche)
        for trend in unique:
            trend.metadata["relevance"] = self._relevance(trend)
        unique.sort(key=lambda t: t.metadata["relevance"], reverse=True)

        self.log.info(
            "trend.discovered",
            sources=len(self._sources),
            raw=len(raw),
            niche=len(niche),
            unique=len(unique),
            returned=min(limit, len(unique)),
        )
        return unique[:limit]

    # -- step 2: map to topics ------------------------------------------------
    def to_topics(self, trends: list[Trend]) -> list[Topic]:
        history = self._history_fingerprints()
        seen: set[str] = set()
        topics: list[Topic] = []
        for trend in trends:
            fingerprint = self._fingerprint(trend.category, trend.keyword)
            if fingerprint in seen or fingerprint in history:
                continue
            seen.add(fingerprint)
            category = trend.category or TopicCategory.CURIOSITIES
            relevance = float(trend.metadata.get("relevance", self._relevance(trend)))
            topics.append(
                Topic(
                    title=trend.keyword.strip().title(),
                    category=category,
                    angle=_ANGLES.get(category, _DEFAULT_ANGLE),
                    source_trends=[trend.id],
                    keywords=[trend.keyword],
                    relevance=relevance,
                )
            )
        topics.sort(key=lambda t: t.relevance, reverse=True)
        self.log.info("trend.topics", count=len(topics), suppressed=len(history))
        return topics

    # -- helpers --------------------------------------------------------------
    def _relevance(self, trend: Trend) -> float:
        evergreen = _EVERGREEN_WEIGHT.get(trend.category, 0.6) if trend.category else 0.6
        bias = self._cfg.evergreen_bias
        return round((1.0 - bias) * trend.score + bias * evergreen, 4)

    def _dedup_trends(self, trends: list[Trend]) -> list[Trend]:
        """Drop near-duplicate keywords within the same category, keep best score."""
        kept: list[Trend] = []
        for trend in sorted(trends, key=lambda t: t.score, reverse=True):
            tokens = _tokens(trend.keyword)
            if any(
                trend.category == other.category
                and _jaccard(tokens, _tokens(other.keyword)) >= self._cfg.dedup_threshold
                for other in kept
            ):
                continue
            kept.append(trend)
        return kept

    def _fingerprint(self, category: TopicCategory | None, keyword: str) -> str:
        cat = category.value if category else "none"
        return f"{cat}:{_normalize(keyword)}"

    def _history_fingerprints(self) -> set[str]:
        """Fingerprints of previously published topics (empty until Sprint 8)."""
        try:
            rows = self._repo.list(self._cfg.history_collection, Topic)
        except Exception:  # noqa: BLE001 - history is best-effort
            return set()
        return {
            self._fingerprint(t.category, t.keywords[0] if t.keywords else t.title) for t in rows
        }
