"""Unit tests for the Canva Automation Engine (Sprint 5)."""

from __future__ import annotations

import pytest

from acis.core.errors import ValidationError
from acis.domain.enums import ContentFormat, Platform
from acis.domain.models import ContentPiece, Slide
from acis.engines.canva import CanvaEngine, CanvaEngineConfig
from acis.engines.interfaces import CanvaAutomationEngine
from acis.integrations.canva.mock import MockCanva


def _content(slides: list[Slide] | None = None) -> ContentPiece:
    slides = slides or [
        Slide(index=0, headline="Title", body="hook", highlight="hook", notes="cover slide"),
        Slide(index=1, headline="Statistic", body="68% of ...", highlight="68% of ..."),
        Slide(index=2, headline="Definition", body="It is ...", highlight=""),
        Slide(index=3, headline="Save & share", body="Follow", notes="cta slide"),
    ]
    return ContentPiece(
        topic_id="t1",
        knowledge_id="k1",
        platform=Platform.INSTAGRAM,
        content_format=ContentFormat.INSTAGRAM_CAROUSEL,
        slides=slides,
    )


def _engine(cfg: CanvaEngineConfig | None = None) -> CanvaEngine:
    return CanvaEngine(MockCanva(), cfg)


def test_satisfies_interface():
    assert isinstance(_engine(), CanvaAutomationEngine)


def test_one_asset_per_slide_with_design_id():
    content = _content()
    result = _engine().design(content)
    assert result.design_id
    assert len(result.assets) == len(content.slides)


def test_dark_palette_backgrounds_applied():
    result = _engine().design(_content())
    backgrounds = [a.metadata["background"] for a in result.assets]
    assert backgrounds[0] == "#000000"  # cover is black
    # content slides rotate through anthracite/graphite/carbon (never black)
    assert all(bg != "#000000" for bg in backgrounds[1:])
    assert all(bg in {"#1C1C1C", "#2B2B2B", "#333333"} for bg in backgrounds[1:])


def test_accent_and_text_colors_present():
    result = _engine().design(_content())
    for asset in result.assets:
        assert asset.metadata["accent"] == "#FFD400"
        assert asset.metadata["text_primary"] == "#FFFFFF"
        assert asset.metadata["brand_compliant"] is True


def test_accent_only_on_allowed_elements():
    result = _engine().design(_content())
    allowed = {"headings", "numbers", "statistics", "key_facts", "highlights", "cta"}
    for asset in result.assets:
        assert set(asset.metadata["accent_elements"]) <= allowed
    # The definition slide (no highlight, not cover/cta) carries no accent.
    def_asset = result.assets[2]
    assert def_asset.metadata["accent_elements"] == []


def test_cover_and_cta_get_accent():
    result = _engine().design(_content())
    assert "headings" in result.assets[0].metadata["accent_elements"]  # cover
    assert "highlights" in result.assets[1].metadata["accent_elements"]  # stat highlight
    assert "cta" in result.assets[-1].metadata["accent_elements"]  # cta slide


def test_brand_violation_raises():
    # Accent usage that forbids highlights, but a slide has a highlight -> violation.
    cfg = CanvaEngineConfig(allowed_accent_elements=frozenset({"headings", "cta"}))
    with pytest.raises(ValidationError):
        _engine(cfg).design(_content())


def test_from_branding_reads_palette():
    class _Palette:
        background = ["#000000", "#1C1C1C", "#2B2B2B", "#333333"]
        text_primary = "#FFFFFF"
        text_secondary = "#B0B0B0"
        accent = "#FFD400"

    class _Branding:
        palette = _Palette()
        accent_usage = ["headings", "highlights", "cta"]

    cfg = CanvaEngineConfig.from_branding(_Branding())
    assert cfg.accent == "#FFD400"
    assert cfg.allowed_accent_elements == frozenset({"headings", "highlights", "cta"})
