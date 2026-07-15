"""Unit tests for the Trend Intelligence Engine (Sprint 1)."""

from __future__ import annotations

from acis.data.memory import InMemoryRepository
from acis.domain.enums import TopicCategory
from acis.domain.models import Topic, Trend
from acis.engines.interfaces import TrendIntelligenceEngine
from acis.engines.trend import TrendEngine, TrendEngineConfig


class FakeSource:
    """A controllable in-memory trend source."""

    def __init__(self, trends: list[Trend]) -> None:
        self._trends = trends

    def fetch_trends(self, *, region: str = "global", limit: int = 20) -> list[Trend]:
        return self._trends[:limit]


def _trend(keyword: str, category: TopicCategory, score: float) -> Trend:
    return Trend(keyword=keyword, source="fake", score=score, category=category)


def _engine(trends: list[Trend], repo: InMemoryRepository | None = None, **cfg) -> TrendEngine:
    config = TrendEngineConfig(
        allowed_categories=frozenset(TopicCategory),
        **cfg,
    )
    return TrendEngine([FakeSource(trends)], repo or InMemoryRepository(), config)


def test_satisfies_interface():
    assert isinstance(_engine([]), TrendIntelligenceEngine)


def test_niche_filter_drops_disallowed_categories():
    trends = [
        _trend("dark matter", TopicCategory.SCIENCE, 0.9),
        _trend("celebrity drama", TopicCategory.CURRENT_AFFAIRS, 0.95),
    ]
    config = TrendEngineConfig(allowed_categories=frozenset({TopicCategory.SCIENCE}))
    engine = TrendEngine([FakeSource(trends)], InMemoryRepository(), config)
    result = engine.discover()
    assert [t.keyword for t in result] == ["dark matter"]


def test_deduplicates_near_identical_keywords():
    trends = [
        _trend("black hole jets", TopicCategory.SPACE, 0.9),
        _trend("black hole jets explained", TopicCategory.SPACE, 0.7),  # near-duplicate
        _trend("Mars water", TopicCategory.SPACE, 0.6),
    ]
    result = _engine(trends).discover()
    keywords = [t.keyword for t in result]
    assert "black hole jets" in keywords  # higher score kept
    assert "black hole jets explained" not in keywords
    assert "Mars water" in keywords


def test_relevance_scoring_blends_momentum_and_evergreen():
    # Same momentum, different evergreen weight -> space outranks rankings.
    trends = [
        _trend("largest deserts", TopicCategory.RANKINGS, 0.8),
        _trend("exoplanet oceans", TopicCategory.SPACE, 0.8),
    ]
    result = _engine(trends, evergreen_bias=0.5).discover()
    assert result[0].category is TopicCategory.SPACE


def test_discover_respects_limit_and_ranking():
    trends = [_trend(f"topic {i}", TopicCategory.SCIENCE, i / 10) for i in range(10)]
    result = _engine(trends).discover(limit=3)
    assert len(result) == 3
    scores = [t.metadata["relevance"] for t in result]
    assert scores == sorted(scores, reverse=True)


def test_to_topics_produces_well_formed_ranked_topics():
    trends = [
        _trend("CRISPR gene editing", TopicCategory.SCIENCE, 0.9),
        _trend("octopus intelligence", TopicCategory.NATURE, 0.7),
    ]
    engine = _engine(trends)
    topics = engine.to_topics(engine.discover())
    assert all(t.title and t.angle and t.keywords and t.category for t in topics)
    assert [t.relevance for t in topics] == sorted([t.relevance for t in topics], reverse=True)


def test_to_topics_dedupes_within_run():
    trends = [
        _trend("Honey never spoils", TopicCategory.CURIOSITIES, 0.9),
        _trend("honey never spoils", TopicCategory.CURIOSITIES, 0.8),  # same fingerprint
    ]
    engine = _engine(trends, dedup_threshold=2.0)  # disable discover-level merge
    # Both survive discover (threshold impossible), but to_topics collapses them.
    topics = engine.to_topics(engine.discover())
    assert len(topics) == 1


def test_history_suppresses_previously_published_topics():
    repo = InMemoryRepository()
    published = Topic(
        title="Dark Matter",
        category=TopicCategory.SCIENCE,
        keywords=["dark matter"],
    )
    repo.save("published_topics", published)

    trends = [
        _trend("dark matter", TopicCategory.SCIENCE, 0.9),
        _trend("superconductors", TopicCategory.SCIENCE, 0.8),
    ]
    engine = _engine(trends, repo=repo)
    topics = engine.to_topics(engine.discover())
    titles = {t.title for t in topics}
    assert "Dark Matter" not in titles
    assert "Superconductors" in titles


def test_failing_source_does_not_break_discovery():
    class BoomSource:
        def fetch_trends(self, *, region: str = "global", limit: int = 20) -> list[Trend]:
            raise RuntimeError("source down")

    good = FakeSource([_trend("dark matter", TopicCategory.SCIENCE, 0.9)])
    config = TrendEngineConfig(allowed_categories=frozenset(TopicCategory))
    engine = TrendEngine([BoomSource(), good], InMemoryRepository(), config)
    result = engine.discover()
    assert [t.keyword for t in result] == ["dark matter"]
