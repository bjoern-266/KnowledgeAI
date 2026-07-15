"""Unit tests for the Content Engine (Sprint 4)."""

from __future__ import annotations

from acis.domain.enums import ContentFormat, FactType, HookType, Platform, TopicCategory, VisualType
from acis.domain.models import Fact, HookCandidate, KnowledgeBase, Topic
from acis.engines.content import ContentEngine, ContentEngineConfig
from acis.engines.interfaces import ContentEngine as ContentEngineProto

STAT = "About 68% of studies report a measurable effect."
DEFN = "It is defined as a well-studied phenomenon."
HIST = "It was first documented in 1912."
RECORD = "It holds the record for the largest value."  # uncertain -> must be excluded


def _kb(topic: Topic) -> KnowledgeBase:
    facts = [
        Fact(
            topic_id=topic.id,
            statement=STAT,
            fact_type=FactType.STATISTIC,
            confidence=80,
            source_ids=["s1", "s2"],
            visual_potential=[VisualType.CHART, VisualType.INFOBOX],
        ),
        Fact(
            topic_id=topic.id,
            statement=DEFN,
            fact_type=FactType.DEFINITION,
            confidence=78,
            source_ids=["s1"],
            visual_potential=[VisualType.INFOBOX],
        ),
        Fact(
            topic_id=topic.id,
            statement=HIST,
            fact_type=FactType.HISTORICAL_EVENT,
            confidence=75,
            source_ids=["s2"],
            visual_potential=[VisualType.TIMELINE],
        ),
        Fact(
            topic_id=topic.id,
            statement=RECORD,
            fact_type=FactType.RECORD,
            confidence=40,
            source_ids=["s1"],
            uncertain=True,
        ),
    ]
    return KnowledgeBase(
        topic_id=topic.id,
        summary="A concise overview.",
        key_claims=[STAT, DEFN, HIST],
        facts=facts,
        hook_candidates=[
            HookCandidate(
                topic_id=topic.id, hook_type=HookType.SURPRISING_NUMBER, text=STAT, strength=80
            )
        ],
        confidence=0.78,
    )


def _topic() -> Topic:
    return Topic(title="Memory", category=TopicCategory.PSYCHOLOGY, keywords=["memory palaces"])


def _make(cfg: ContentEngineConfig | None = None):
    topic = _topic()
    engine = ContentEngine(cfg or ContentEngineConfig(carousel_slides=6))
    return topic, engine.create(topic, _kb(topic))


def test_satisfies_interface():
    assert isinstance(ContentEngine(), ContentEngineProto)


def test_produces_instagram_carousel():
    _, piece = _make()
    assert piece.platform is Platform.INSTAGRAM
    assert piece.content_format is ContentFormat.INSTAGRAM_CAROUSEL
    # title + fact slides + cta, within the configured budget.
    assert 3 <= len(piece.slides) <= 6
    assert piece.slides[0].notes == "cover slide"
    assert piece.slides[-1].notes == "cta slide"


def test_only_corroborated_facts_used():
    _, piece = _make()
    bodies = " ".join(s.body for s in piece.slides)
    assert RECORD not in bodies  # uncertain fact excluded
    assert STAT in bodies and DEFN in bodies


def test_highlight_only_for_key_number_facts():
    _, piece = _make()
    stat_slide = next(s for s in piece.slides if s.body == STAT and s.index >= 1)
    def_slide = next(s for s in piece.slides if s.body == DEFN)
    assert stat_slide.highlight == STAT  # accent-styled key number
    assert def_slide.highlight == ""


def test_fact_slides_carry_provenance_and_visual():
    _, piece = _make()
    stat_slide = next(s for s in piece.slides if s.body == STAT and s.index >= 1)
    assert stat_slide.source_ids == ["s1", "s2"]
    assert stat_slide.visual is VisualType.CHART


def test_hook_uses_top_hook_candidate():
    _, piece = _make()
    assert piece.hook == STAT
    assert piece.slides[0].highlight == STAT


def test_derives_tiktok_script_within_target_length():
    _, piece = _make(
        ContentEngineConfig(carousel_slides=8, tiktok_target_seconds=25, tiktok_max_beats=5)
    )
    assert piece.script
    assert piece.script[0].index == 0  # hook scene
    assert piece.script[-1].on_screen == "Follow for more"  # cta scene
    assert 20.0 <= piece.script_seconds <= 30.0
    # script beats also carry provenance (index >= 1 skips the hook scene)
    beat = next(s for s in piece.script if s.voiceover == STAT and s.index >= 1)
    assert beat.source_ids == ["s1", "s2"]


def test_caption_hashtags_and_cta():
    _, piece = _make()
    assert piece.caption
    assert piece.cta
    assert "#Psychology" in piece.hashtags
    assert "#knowledge" in piece.hashtags
    assert len(piece.hashtags) <= ContentEngineConfig().max_hashtags


def test_every_highlight_traces_to_a_fact():
    topic, piece = _make()
    kb = _kb(topic)
    fact_statements = {f.statement for f in kb.facts if not f.uncertain}
    for slide in piece.slides:
        if slide.highlight and slide.index != 0:  # cover slide highlight is the hook
            assert slide.highlight in fact_statements
