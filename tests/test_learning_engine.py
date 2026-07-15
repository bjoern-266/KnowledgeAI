"""Unit tests for the Learning Engine (Sprint 10)."""

from __future__ import annotations

from acis.data.memory import InMemoryRepository
from acis.domain.enums import Platform, PublishStatus, TopicCategory
from acis.domain.models import CategoryPrior, PublishReceipt, Topic
from acis.engines.interfaces import LearningEngine as LearningEngineProto
from acis.engines.learning import LearningEngine, LearningEngineConfig
from acis.engines.learning.engine import load_category_priors


def _topic(category: TopicCategory = TopicCategory.SCIENCE) -> Topic:
    return Topic(title="T", category=category)


def _receipt(topic: Topic) -> PublishReceipt:
    return PublishReceipt(
        content_id="c1", platform=Platform.INSTAGRAM, status=PublishStatus.PUBLISHED
    )


def _engine(repo=None, cfg=None) -> LearningEngine:
    return LearningEngine(repository=repo, config=cfg or LearningEngineConfig())


def test_satisfies_interface():
    assert isinstance(_engine(), LearningEngineProto)


def test_strong_performance_raises_prior_toward_target():
    repo = InMemoryRepository()
    topic = _topic()
    engine = _engine(repo)
    # Perfect KPIs -> target 1.0, prior should move up from base 0.7.
    signal = engine.learn(topic, _receipt(topic), {"save_rate": 0.10, "share_rate": 0.06})
    assert signal["target"] == 1.0
    assert 0.7 < signal["category_fit"] <= 1.0
    stored = repo.get("category_priors", topic.category.value, CategoryPrior)
    assert stored.value == signal["category_fit"]
    assert stored.samples == 1


def test_weak_performance_lowers_prior():
    repo = InMemoryRepository()
    topic = _topic()
    engine = _engine(repo)
    signal = engine.learn(topic, _receipt(topic), {"save_rate": 0.0, "share_rate": 0.0})
    assert signal["target"] == 0.0
    assert signal["category_fit"] < 0.7  # moved down from base


def test_shrinkage_makes_first_updates_small():
    repo = InMemoryRepository()
    topic = _topic()
    cfg = LearningEngineConfig(alpha=0.3, min_samples=5)
    engine = _engine(repo, cfg)
    # First update: effective alpha = 0.3 * (1/5) = 0.06 -> tiny move toward 1.0.
    s1 = engine.learn(topic, _receipt(topic), {"save_rate": 0.10, "share_rate": 0.06})
    assert abs(s1["category_fit"] - (0.7 + 0.06 * (1.0 - 0.7))) < 1e-6


def test_repeated_updates_converge_upward():
    repo = InMemoryRepository()
    topic = _topic()
    engine = _engine(repo)
    values = []
    for _ in range(6):
        values.append(
            engine.learn(topic, _receipt(topic), {"save_rate": 0.10, "share_rate": 0.06})[
                "category_fit"
            ]
        )
    assert values == sorted(values)  # monotonically increasing toward 1.0
    assert values[-1] > values[0]


def test_load_category_priors_roundtrip_for_virality():
    repo = InMemoryRepository()
    topic = _topic(TopicCategory.SPACE)
    engine = _engine(repo)
    engine.learn(topic, _receipt(topic), {"save_rate": 0.08, "share_rate": 0.05})
    priors = load_category_priors(repo)
    assert "space" in priors
    assert 0.0 <= priors["space"] <= 1.0


def test_no_repository_still_returns_signal():
    topic = _topic()
    signal = _engine(repo=None).learn(
        topic, _receipt(topic), {"save_rate": 0.10, "share_rate": 0.06}
    )
    assert signal["category_fit"] > 0.7
    assert signal["samples"] == 1.0
