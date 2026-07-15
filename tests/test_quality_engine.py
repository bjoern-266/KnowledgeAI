"""Unit tests for the Quality Engine (Sprint 7)."""

from __future__ import annotations

from acis.domain.enums import ContentFormat, FactType, Platform, QualityCheck
from acis.domain.models import (
    Asset,
    ContentPiece,
    Fact,
    KnowledgeBase,
    Slide,
    Source,
)
from acis.engines.interfaces import QualityEngine as QualityEngineProto
from acis.engines.quality import QualityEngine, QualityEngineConfig

STAT = "68% of the claim is measurable."


def _knowledge(*, corroborated: bool = True, sources: int = 3) -> KnowledgeBase:
    facts = [
        Fact(
            topic_id="t1",
            statement=STAT,
            fact_type=FactType.STATISTIC,
            confidence=85,
            source_ids=["s1", "s2"],
            uncertain=not corroborated,
        )
    ]
    src = [Source(url=f"https://x/{i}", reliability=0.9, scientific=True) for i in range(sources)]
    return KnowledgeBase(
        topic_id="t1", facts=facts, sources=src, confidence=0.85 if corroborated else 0.2
    )


def _content(*, highlight: str = STAT, caption: str = "Great facts here.") -> ContentPiece:
    return ContentPiece(
        topic_id="t1",
        knowledge_id="k1",
        platform=Platform.INSTAGRAM,
        content_format=ContentFormat.INSTAGRAM_CAROUSEL,
        slides=[
            Slide(index=0, headline="Title", body="hook", highlight="hook", notes="cover slide"),
            Slide(index=1, headline="Statistic", body=STAT, highlight=highlight),
            Slide(index=2, headline="Save", body="Follow", notes="cta slide"),
        ],
        caption=caption,
        hashtags=["#knowledge"],
    )


def _assets(n: int = 3, *, compliant: bool = True, bg: str = "#1C1C1C") -> list[Asset]:
    return [
        Asset(
            kind="image",
            uri=f"mock://{i}.png",
            width=1080,
            height=1350,
            metadata={
                "slide_index": i,
                "brand_compliant": compliant,
                "accent_elements": ["highlights"],
                "background": "#000000" if i == 0 else bg,
            },
        )
        for i in range(n)
    ]


def _engine() -> QualityEngine:
    return QualityEngine(QualityEngineConfig(min_score=0.75))


def test_satisfies_interface():
    assert isinstance(_engine(), QualityEngineProto)


def test_good_content_passes_with_all_gates():
    report = _engine().evaluate(_content(), _knowledge(), _assets())
    assert report.passed
    assert report.overall >= 0.75
    for gate in (
        QualityCheck.SOURCE_CHECK,
        QualityCheck.FACT_CHECK,
        QualityCheck.SPELLING_CHECK,
        QualityCheck.DESIGN_CHECK,
    ):
        assert report.scores[gate] > 0.0


def test_insufficient_sources_fails_closed():
    report = _engine().evaluate(_content(), _knowledge(sources=1), _assets())
    assert report.scores[QualityCheck.SOURCE_CHECK] == 0.0
    assert not report.passed
    assert any("insufficient sources" in i for i in report.issues)


def test_no_corroborated_facts_fails_closed():
    report = _engine().evaluate(_content(), _knowledge(corroborated=False), _assets())
    assert report.scores[QualityCheck.FACT_CHECK] == 0.0
    assert not report.passed


def test_unbacked_highlight_penalises_fact_check():
    kb = _knowledge()
    # A highlight that no corroborated fact supports.
    report = _engine().evaluate(_content(highlight="Totally made up number."), kb, _assets())
    assert any("unbacked highlight" in i for i in report.issues)
    backed = _engine().evaluate(_content(), kb, _assets())
    assert report.scores[QualityCheck.FACT_CHECK] < backed.scores[QualityCheck.FACT_CHECK]


def test_placeholder_text_lowers_spelling():
    report = _engine().evaluate(_content(caption="[mock] TODO caption"), _knowledge(), _assets())
    assert report.scores[QualityCheck.SPELLING_CHECK] < 1.0
    assert any("placeholder" in i for i in report.issues)


def test_off_brand_assets_lower_design():
    report = _engine().evaluate(_content(), _knowledge(), _assets(compliant=False))
    assert report.scores[QualityCheck.DESIGN_CHECK] == 0.0
    assert not report.passed


def test_no_assets_fails_design_closed():
    report = _engine().evaluate(_content(), _knowledge(), [])
    assert report.scores[QualityCheck.DESIGN_CHECK] == 0.0
    assert not report.passed
    assert any("no design assets" in i for i in report.issues)


def test_threshold_is_reported():
    report = _engine().evaluate(_content(), _knowledge(), _assets())
    assert report.threshold == 0.75
