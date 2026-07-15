"""Unit tests for the TikTok Video Engine (Sprint 6)."""

from __future__ import annotations

from acis.domain.enums import ContentFormat, Platform, VisualType
from acis.domain.models import Asset, ContentPiece, DesignResult, ScriptScene, Slide
from acis.engines.interfaces import TikTokVideoEngine as TikTokVideoEngineProto
from acis.engines.tiktok import TikTokVideoEngine, TikTokVideoEngineConfig


def _content(with_script: bool = True) -> ContentPiece:
    slides = [Slide(index=i, headline=f"s{i}", body=f"body {i}") for i in range(3)]
    script = (
        [
            ScriptScene(index=0, on_screen="Title", voiceover="hook", seconds=3.0),
            ScriptScene(
                index=1,
                on_screen="68%",
                voiceover="stat",
                seconds=9.0,
                visual=VisualType.CHART,
                source_ids=["s1", "s2"],
            ),
            ScriptScene(index=2, on_screen="Follow for more", voiceover="cta", seconds=3.0),
        ]
        if with_script
        else []
    )
    return ContentPiece(
        topic_id="t1",
        knowledge_id="k1",
        platform=Platform.INSTAGRAM,
        content_format=ContentFormat.INSTAGRAM_CAROUSEL,
        slides=slides,
        script=script,
    )


def _design(content: ContentPiece) -> DesignResult:
    assets = [
        Asset(kind="image", uri=f"mock://canva/slide-{i}.png", metadata={"slide_index": i})
        for i in range(len(content.slides))
    ]
    return DesignResult(content_id=content.id, design_id="d1", assets=assets)


def _render(content: ContentPiece):
    engine = TikTokVideoEngine()
    return engine.render(content, _design(content))


def test_satisfies_interface():
    assert isinstance(TikTokVideoEngine(), TikTokVideoEngineProto)


def test_produces_vertical_video():
    content = _content()
    result = _render(content)
    assert result.asset.kind == "video"
    assert result.asset.mime_type == "video/mp4"
    assert result.asset.width == 1080 and result.asset.height == 1920


def test_duration_matches_script():
    content = _content()
    result = _render(content)
    assert result.duration_seconds == content.script_seconds == 15.0


def test_storyboard_has_scene_per_script_scene():
    content = _content()
    result = _render(content)
    frames = result.asset.metadata["frames"]
    assert len(frames) == len(content.script)
    assert result.asset.metadata["scene_count"] == len(content.script)


def test_hook_is_first_and_safe_zones_present():
    result = _render(_content())
    assert result.asset.metadata["hook_first"] is True
    assert result.asset.metadata["safe_top"] > 0
    assert result.asset.metadata["safe_bottom"] > 0


def test_frames_map_to_matching_design_slides_and_carry_provenance():
    content = _content()
    result = _render(content)
    frames = result.asset.metadata["frames"]
    # Scene 1 maps to the design asset with slide_index == 1.
    assert frames[1]["frame"] == "mock://canva/slide-1.png"
    assert frames[1]["source_ids"] == ["s1", "s2"]
    assert frames[1]["visual"] == "chart"


def test_falls_back_to_design_frames_without_script():
    content = _content(with_script=False)
    result = _render(content)
    # One scene per design frame, timed by the default.
    assert result.asset.metadata["scene_count"] == len(content.slides)
    assert result.duration_seconds > 0


def test_custom_renderer_is_used():
    calls = {}

    def fake_renderer(content_id, storyboard, fmt):
        calls["content_id"] = content_id
        calls["scenes"] = len(storyboard.scenes)
        return Asset(kind="video", uri="file://out.mp4", mime_type="video/mp4")

    content = _content()
    engine = TikTokVideoEngine(TikTokVideoEngineConfig(), renderer=fake_renderer)
    result = engine.render(content, _design(content))
    assert result.asset.uri == "file://out.mp4"
    assert calls["content_id"] == content.id
    assert calls["scenes"] == len(content.script)
