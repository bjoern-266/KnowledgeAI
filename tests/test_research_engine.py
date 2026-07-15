"""Unit tests for the Research Engine (Sprint 2)."""

from __future__ import annotations

from datetime import timedelta

from acis.data.memory import InMemoryRepository
from acis.domain.enums import FactType, HookType, SourceType, TopicCategory, VisualType
from acis.domain.models import RetrievedDocument, Topic, _now
from acis.engines.interfaces import ResearchEngine as ResearchEngineProto
from acis.engines.research import ResearchEngine, ResearchEngineConfig

C_HIST = "X was first documented in 1912."
C_STAT = "About 68% of studies report a measurable effect related to X."
C_DEF = "X is defined as a well-studied phenomenon."
C_MYTH = "Contrary to popular belief, X is not caused by everyday habits."
C_RECORD = "X holds the record for the largest value ever measured."
C_PROJ = "Some researchers suggest X could double by 2050, though evidence remains limited."


class FakeResearchSource:
    def __init__(self, docs: list[RetrievedDocument]) -> None:
        self._docs = docs

    def search(self, query: str, *, limit: int = 10) -> list[RetrievedDocument]:
        return self._docs[:limit]


def _docs() -> list[RetrievedDocument]:
    recent = _now() - timedelta(days=200)
    old = _now() - timedelta(days=365 * 8)
    return [
        RetrievedDocument(
            url="https://journal.example/1",
            institution="Nature",
            reliability=0.95,
            source_type=SourceType.PRIMARY,
            scientific=True,
            published_at=recent,
            snippets=[C_HIST, C_STAT, C_DEF, C_MYTH, C_RECORD],
        ),
        RetrievedDocument(
            url="https://encyclopedia.example/2",
            institution="Encyclopaedia",
            reliability=0.80,
            published_at=recent,
            snippets=[C_HIST, C_STAT, C_DEF, C_MYTH],
        ),
        RetrievedDocument(
            url="https://news.example/3",
            institution="ScienceDaily",
            reliability=0.65,
            published_at=old,
            snippets=[C_HIST, C_PROJ],
        ),
    ]


def _engine(docs: list[RetrievedDocument] | None = None) -> ResearchEngine:
    source = FakeResearchSource(docs if docs is not None else _docs())
    return ResearchEngine([source], InMemoryRepository(), ResearchEngineConfig(min_sources=2))


def _topic() -> Topic:
    return Topic(title="X", category=TopicCategory.SCIENCE)


def _fact(kb, statement):
    return next(f for f in kb.facts if f.statement == statement)


def test_satisfies_interface():
    assert isinstance(_engine(), ResearchEngineProto)


def test_screen_sufficient_and_insufficient():
    engine = _engine()
    ok = engine.screen(_topic())
    assert ok.sufficient and ok.source_count >= 2

    empty = ResearchEngine([FakeResearchSource([])], InMemoryRepository(), ResearchEngineConfig())
    bad = empty.screen(_topic())
    assert not bad.sufficient and bad.source_count == 0


def test_research_builds_structured_knowledge_base():
    kb = _engine().research(_topic())
    assert kb.facts and kb.sources
    assert kb.summary and kb.key_claims
    assert 0.0 < kb.confidence <= 1.0


def test_cross_verification_scores_and_flags_uncertainty():
    kb = _engine().research(_topic())
    hist = _fact(kb, C_HIST)  # 3 sources
    record = _fact(kb, C_RECORD)  # 1 source
    proj = _fact(kb, C_PROJ)  # 1 source + hedged

    assert hist.supporting_sources == 3 and not hist.uncertain
    assert record.supporting_sources == 1 and record.uncertain
    assert proj.uncertain
    assert hist.confidence > record.confidence


def test_facts_are_typed():
    kb = _engine().research(_topic())
    assert _fact(kb, C_STAT).fact_type is FactType.STATISTIC
    assert _fact(kb, C_DEF).fact_type is FactType.DEFINITION
    assert _fact(kb, C_MYTH).fact_type is FactType.MYTH
    assert _fact(kb, C_HIST).fact_type is FactType.HISTORICAL_EVENT
    assert _fact(kb, C_RECORD).fact_type is FactType.RECORD


def test_visual_potential_assigned():
    kb = _engine().research(_topic())
    assert VisualType.CHART in _fact(kb, C_STAT).visual_potential
    assert VisualType.TIMELINE in _fact(kb, C_HIST).visual_potential
    assert kb.charts  # aggregated visual ideas expose charts


def test_typed_sublists_only_from_corroborated_facts():
    kb = _engine().research(_topic())
    assert any(s.label == C_STAT for s in kb.statistics)
    assert any(d.definition == C_DEF for d in kb.definitions)
    # Timeline includes the corroborated 1912 event, not the uncertain 2050 projection.
    whens = {e.when for e in kb.timeline}
    assert "1912" in whens
    assert "2050" not in whens


def test_hook_candidates_detected():
    kb = _engine().research(_topic())
    types = {h.hook_type for h in kb.hook_candidates}
    assert HookType.SURPRISING_NUMBER in types
    assert HookType.COMMON_MISCONCEPTION in types
    assert HookType.INCREDIBLE_RECORD in types


def test_no_hallucination_every_fact_traces_to_a_snippet():
    docs = _docs()
    allowed = {s for d in docs for s in d.snippets}
    kb = _engine(docs).research(_topic())
    assert all(f.statement in allowed for f in kb.facts)


def test_uncertainties_and_open_questions_surface_weak_facts():
    kb = _engine().research(_topic())
    assert C_RECORD in kb.uncertainties
    assert C_PROJ in kb.uncertainties
    assert kb.open_questions


def test_source_weighting_prefers_primary_recent_scientific():
    docs = _docs()
    primary = docs[0].to_source()  # primary, scientific, recent
    weak = docs[2].to_source()  # secondary, old
    assert primary.weight() > weak.weight()


def test_failing_source_does_not_break_research():
    class Boom:
        def search(self, query: str, *, limit: int = 10):
            raise RuntimeError("down")

    engine = ResearchEngine(
        [Boom(), FakeResearchSource(_docs())], InMemoryRepository(), ResearchEngineConfig()
    )
    kb = engine.research(_topic())
    assert kb.facts  # good source still produced facts
