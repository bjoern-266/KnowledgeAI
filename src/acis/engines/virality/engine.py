"""Virality Engine implementation.

Produces a transparent, weighted :class:`ViralityScore` per topic:

    value = Σ weightᵢ · componentᵢ         (all in [0..1])

Components (CONTENT_INTELLIGENCE §3):
* category_fit     - does the category reliably over-index on saves/shares?
* trend_momentum   - the topic's preliminary relevance from the Trend Engine.
* novelty          - counter-intuitive / surprising framing.
* shareability     - identity / utility / emotion pull.
* save_worthiness  - reference value (lists, stats, rankings).
* historical_fit   - how past content on this category performed (Learning Engine).

At ranking time only the topic (+ learned priors) is known - deep research runs
later, for the winner only - so every signal is derived from the topic itself
or from persisted priors. A diversity guard prevents category collapse; an
optional (default-off) exploration budget promotes a lower-ranked topic to keep
the system discovering.
"""

from __future__ import annotations

import random
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from acis.core.base import Engine
from acis.domain.enums import TopicCategory
from acis.domain.models import Topic, ViralityScore

# Base per-category appeal for save/share in the knowledge niche [0..1].
_CATEGORY_FIT: dict[TopicCategory, float] = {
    TopicCategory.SPACE: 0.95,
    TopicCategory.SCIENCE: 0.90,
    TopicCategory.PSYCHOLOGY: 0.90,
    TopicCategory.MYTH_VS_REALITY: 0.90,
    TopicCategory.CURIOSITIES: 0.85,
    TopicCategory.STATISTICS: 0.85,
    TopicCategory.NATURE: 0.85,
    TopicCategory.HISTORY: 0.80,
    TopicCategory.RANKINGS: 0.80,
    TopicCategory.HEALTH: 0.80,
    TopicCategory.AI: 0.80,
    TopicCategory.NUTRITION: 0.78,
    TopicCategory.TECHNOLOGY: 0.75,
    TopicCategory.GEOGRAPHY: 0.75,
    TopicCategory.ECONOMY: 0.70,
    TopicCategory.CURRENT_AFFAIRS: 0.60,
}
_DEFAULT_FIT = 0.70

_NOVELTY_WORDS = ("myth", "surprising", "secret", "hidden", "wrong", "truth", "never", "actually")
_SHARE_WORDS = ("you", "why", "how", "everyone", "most people")
_SAVE_CATEGORIES = frozenset(
    {
        TopicCategory.STATISTICS,
        TopicCategory.RANKINGS,
        TopicCategory.HISTORY,
        TopicCategory.GEOGRAPHY,
        TopicCategory.SCIENCE,
    }
)
_HAS_NUMBER = re.compile(r"\d")


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


@dataclass(frozen=True)
class ViralityEngineConfig:
    """Weights and guards for the Virality Engine (all tunable via config)."""

    weights: Mapping[str, float] = field(
        default_factory=lambda: {
            "category_fit": 0.25,
            "trend_momentum": 0.20,
            "novelty": 0.20,
            "shareability": 0.15,
            "save_worthiness": 0.15,
            "historical_fit": 0.05,
        }
    )
    #: Within the first ``diversity_top_n`` ranks, allow at most this many topics
    #: per category (excess is demoted). Prevents category collapse.
    diversity_top_n: int = 10
    max_per_category_in_top: int = 3
    #: Fraction of runs that promote a lower-ranked topic (0 = deterministic).
    exploration_ratio: float = 0.0
    exploration_seed: int = 0


class ViralityEngine(Engine):
    """Scores and ranks screened topics by share/save potential."""

    name = "virality"

    def __init__(
        self,
        config: ViralityEngineConfig | None = None,
        *,
        historical_priors: Mapping[str, float] | None = None,
    ) -> None:
        super().__init__()
        self._cfg = config or ViralityEngineConfig()
        # category value -> learned fit [0..1], provided by the Learning Engine.
        self._priors: dict[str, float] = dict(historical_priors or {})
        self._rng = random.Random(self._cfg.exploration_seed)

    # -- scoring --------------------------------------------------------------
    def score(self, topic: Topic) -> ViralityScore:
        components = {
            "category_fit": self._category_fit(topic),
            "trend_momentum": self._trend_momentum(topic),
            "novelty": self._novelty(topic),
            "shareability": self._shareability(topic),
            "save_worthiness": self._save_worthiness(topic),
            "historical_fit": self._historical_fit(topic),
        }
        weights = self._cfg.weights
        total_weight = sum(weights.values()) or 1.0
        value = sum(weights.get(k, 0.0) * v for k, v in components.items()) / total_weight
        top = max(components, key=lambda k: components[k])
        return ViralityScore(
            value=round(_clamp(value), 4),
            components={k: round(v, 4) for k, v in components.items()},
            rationale=f"{topic.category.value}: strongest signal '{top}'",
        )

    def rank(self, topics: list[Topic]) -> list[Topic]:
        for topic in topics:
            topic.virality = self.score(topic)
        ranked = sorted(topics, key=lambda t: t.virality.value if t.virality else 0.0, reverse=True)
        ranked = self._apply_diversity(ranked)
        ranked = self._apply_exploration(ranked)
        if ranked:
            self.log.info(
                "virality.ranked",
                count=len(ranked),
                winner=ranked[0].title,
                score=ranked[0].virality.value if ranked[0].virality else 0.0,
            )
        return ranked

    # -- components -----------------------------------------------------------
    def _category_fit(self, topic: Topic) -> float:
        # A learned prior (if present) overrides the base category appeal.
        if topic.category.value in self._priors:
            return _clamp(self._priors[topic.category.value])
        return _CATEGORY_FIT.get(topic.category, _DEFAULT_FIT)

    def _trend_momentum(self, topic: Topic) -> float:
        return _clamp(topic.relevance) if topic.relevance else 0.5

    def _novelty(self, topic: Topic) -> float:
        text = f"{topic.title} {topic.angle}".lower()
        score = 0.5
        if topic.category in (TopicCategory.MYTH_VS_REALITY, TopicCategory.CURIOSITIES):
            score += 0.3
        if any(w in text for w in _NOVELTY_WORDS):
            score += 0.2
        if _HAS_NUMBER.search(topic.title):
            score += 0.1
        return _clamp(score)

    def _shareability(self, topic: Topic) -> float:
        text = f"{topic.title} {topic.angle}".lower()
        score = 0.5
        if topic.category in (
            TopicCategory.PSYCHOLOGY,
            TopicCategory.HEALTH,
            TopicCategory.MYTH_VS_REALITY,
        ):
            score += 0.2
        if topic.category in (TopicCategory.CURIOSITIES, TopicCategory.SPACE):
            score += 0.15
        if any(w in text for w in _SHARE_WORDS):
            score += 0.1
        return _clamp(score)

    def _save_worthiness(self, topic: Topic) -> float:
        score = 0.5
        if topic.category in _SAVE_CATEGORIES:
            score += 0.3
        if topic.category in (TopicCategory.RANKINGS, TopicCategory.STATISTICS):
            score += 0.2
        if _HAS_NUMBER.search(topic.title):
            score += 0.1
        return _clamp(score)

    def _historical_fit(self, topic: Topic) -> float:
        # Neutral until the Learning Engine supplies priors (Sprint 10).
        return _clamp(self._priors.get(topic.category.value, 0.5))

    # -- guards ---------------------------------------------------------------
    def _apply_diversity(self, ranked: list[Topic]) -> list[Topic]:
        top_n = self._cfg.diversity_top_n
        max_per = self._cfg.max_per_category_in_top
        kept: list[Topic] = []
        deferred: list[Topic] = []
        counts: dict[TopicCategory, int] = {}
        for topic in ranked:
            if len(kept) < top_n and counts.get(topic.category, 0) >= max_per:
                deferred.append(topic)
            else:
                kept.append(topic)
                counts[topic.category] = counts.get(topic.category, 0) + 1
        return kept + deferred

    def _apply_exploration(self, ranked: list[Topic]) -> list[Topic]:
        if self._cfg.exploration_ratio <= 0.0 or len(ranked) < 2:
            return ranked
        if self._rng.random() < self._cfg.exploration_ratio:
            idx = self._rng.randrange(1, len(ranked))
            pick = ranked.pop(idx)
            ranked.insert(0, pick)
            self.log.info("virality.exploration", promoted=pick.title)
        return ranked


def build_priors_from_rates(rates: Sequence[tuple[str, float]]) -> dict[str, float]:
    """Helper for the Learning Engine: category -> normalised fit from save/share rates."""
    return {category: _clamp(value) for category, value in rates}
