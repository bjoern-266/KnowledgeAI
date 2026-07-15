"""Unit tests for the Virality Engine (Sprint 3)."""

from __future__ import annotations

from acis.domain.enums import TopicCategory
from acis.domain.models import Topic
from acis.engines.interfaces import ViralityEngine as ViralityEngineProto
from acis.engines.virality import ViralityEngine, ViralityEngineConfig


def _topic(
    title: str, category: TopicCategory, *, relevance: float = 0.5, angle: str = ""
) -> Topic:
    return Topic(title=title, category=category, relevance=relevance, angle=angle)


def test_satisfies_interface():
    assert isinstance(ViralityEngine(), ViralityEngineProto)


def test_score_is_bounded_and_transparent():
    score = ViralityEngine().score(_topic("Black Hole Jets", TopicCategory.SPACE, relevance=0.9))
    assert 0.0 <= score.value <= 1.0
    # Every component is exposed with a rationale (never a black box).
    assert set(score.components) == {
        "category_fit",
        "trend_momentum",
        "novelty",
        "shareability",
        "save_worthiness",
        "historical_fit",
    }
    assert score.rationale


def test_high_appeal_category_outranks_low():
    engine = ViralityEngine()
    space = engine.score(_topic("A", TopicCategory.SPACE, relevance=0.8))
    economy = engine.score(_topic("B", TopicCategory.ECONOMY, relevance=0.8))
    assert space.value > economy.value


def test_trend_momentum_influences_score():
    engine = ViralityEngine()
    high = engine.score(_topic("A", TopicCategory.SCIENCE, relevance=0.95))
    low = engine.score(_topic("A", TopicCategory.SCIENCE, relevance=0.1))
    assert high.value > low.value


def test_rank_sorts_and_attaches_scores():
    engine = ViralityEngine()
    topics = [
        _topic("Econ", TopicCategory.ECONOMY, relevance=0.4),
        _topic("Space", TopicCategory.SPACE, relevance=0.9),
        _topic("Tech", TopicCategory.TECHNOLOGY, relevance=0.5),
    ]
    ranked = engine.rank(topics)
    assert all(t.virality is not None for t in ranked)
    values = [t.virality.value for t in ranked]
    assert values == sorted(values, reverse=True)
    assert ranked[0].title == "Space"


def test_diversity_guard_limits_one_category_in_top():
    cfg = ViralityEngineConfig(diversity_top_n=4, max_per_category_in_top=2)
    engine = ViralityEngine(cfg)
    # Without the guard the top would be all SPACE; SCIENCE provides the diversity
    # the guard needs to enforce <= 2 SPACE in the top 4.
    topics = [_topic(f"S{i}", TopicCategory.SPACE, relevance=0.9) for i in range(6)]
    topics += [_topic(f"Sci{i}", TopicCategory.SCIENCE, relevance=0.88) for i in range(4)]
    ranked = engine.rank(topics)
    top4_space = sum(1 for t in ranked[:4] if t.category is TopicCategory.SPACE)
    assert top4_space <= 2
    # The demoted SPACE topics are not lost, just moved down.
    assert sum(1 for t in ranked if t.category is TopicCategory.SPACE) == 6


def test_learned_priors_override_category_fit():
    # A low-appeal category boosted by a strong learned prior should climb.
    boosted = ViralityEngine(historical_priors={"economy": 0.99})
    base = ViralityEngine()
    t = _topic("B", TopicCategory.ECONOMY, relevance=0.5)
    assert (
        boosted.score(t).value > base.score(_topic("B", TopicCategory.ECONOMY, relevance=0.5)).value
    )


def test_exploration_promotes_lower_ranked_when_enabled():
    cfg = ViralityEngineConfig(exploration_ratio=1.0, exploration_seed=1)
    engine = ViralityEngine(cfg)
    topics = [
        _topic("Space", TopicCategory.SPACE, relevance=0.95),
        _topic("Econ", TopicCategory.ECONOMY, relevance=0.2),
    ]
    ranked = engine.rank(topics)
    # With exploration forced on, the deterministic winner is displaced.
    assert ranked[0].title == "Econ"


def test_exploration_off_is_deterministic():
    engine = ViralityEngine()  # exploration_ratio defaults to 0.0
    topics = [
        _topic("Space", TopicCategory.SPACE, relevance=0.95),
        _topic("Econ", TopicCategory.ECONOMY, relevance=0.2),
    ]
    assert engine.rank(list(topics))[0].title == "Space"
    assert engine.rank(list(topics))[0].title == "Space"
