"""TikTok Video Engine implementation.

Flow:

    content.script + design.assets
      -> storyboard (map each scene to a design frame, time it, place captions
         inside the TikTok safe zone)
      -> renderer(storyboard) -> video Asset        # injectable seam
      -> VideoResult

The engine contains all the storyboard logic and is fully deterministic; the
only thing it delegates is turning the storyboard into a file, via a ``renderer``
callable. The default renderer produces a deterministic mock asset so the whole
flow runs offline; a real ffmpeg/cloud renderer can be injected with no other
change (hook lands in the first scene; captions respect safe zones).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from acis.core.base import Engine
from acis.domain.enums import VisualType
from acis.domain.models import Asset, ContentPiece, DesignResult, VideoResult


@dataclass
class StoryboardScene:
    index: int
    seconds: float
    frame_uri: str
    on_screen: str = ""
    voiceover: str = ""
    visual: VisualType | None = None
    source_ids: list[str] = field(default_factory=list)


@dataclass
class Storyboard:
    width: int
    height: int
    fps: int
    safe_top: float
    safe_bottom: float
    scenes: list[StoryboardScene]

    @property
    def duration(self) -> float:
        return round(sum(s.seconds for s in self.scenes), 1)


Renderer = Callable[[str, Storyboard, str], Asset]


def _mock_render(content_id: str, storyboard: Storyboard, fmt: str) -> Asset:
    """Deterministic stand-in renderer. Real renderers write an actual file."""
    return Asset(
        kind="video",
        uri=f"mock://tiktok/{content_id[:8]}.{fmt}",
        mime_type=f"video/{fmt}",
        width=storyboard.width,
        height=storyboard.height,
        metadata={
            "rendered_by": "mock",
            "fps": storyboard.fps,
            "duration_seconds": storyboard.duration,
            "scene_count": len(storyboard.scenes),
            "hook_first": bool(storyboard.scenes) and storyboard.scenes[0].index == 0,
            "safe_top": storyboard.safe_top,
            "safe_bottom": storyboard.safe_bottom,
            "frames": [
                {
                    "scene": s.index,
                    "frame": s.frame_uri,
                    "seconds": s.seconds,
                    "on_screen": s.on_screen,
                    "visual": s.visual.value if s.visual else None,
                    "source_ids": s.source_ids,
                }
                for s in storyboard.scenes
            ],
        },
    )


@dataclass(frozen=True)
class TikTokVideoEngineConfig:
    width: int = 1080
    height: int = 1920
    fps: int = 30
    #: Fractions of the frame reserved for TikTok UI overlays (captions avoid these).
    safe_top: float = 0.12
    safe_bottom: float = 0.18
    default_scene_seconds: float = 4.0
    fmt: str = "mp4"


class TikTokVideoEngine(Engine):
    """Assembles a vertical TikTok video from a content piece + design."""

    name = "tiktok_video"

    def __init__(
        self,
        config: TikTokVideoEngineConfig | None = None,
        *,
        renderer: Renderer | None = None,
    ) -> None:
        super().__init__()
        self._cfg = config or TikTokVideoEngineConfig()
        self._render = renderer or _mock_render

    def render(self, content: ContentPiece, design: DesignResult) -> VideoResult:
        storyboard = self._build_storyboard(content, design)
        asset = self._render(content.id, storyboard, self._cfg.fmt)
        self.log.info(
            "tiktok.rendered",
            content_id=content.id,
            scenes=len(storyboard.scenes),
            seconds=storyboard.duration,
        )
        return VideoResult(content_id=content.id, asset=asset, duration_seconds=storyboard.duration)

    # -- storyboard -----------------------------------------------------------
    def _build_storyboard(self, content: ContentPiece, design: DesignResult) -> Storyboard:
        frames = design.assets
        scenes: list[StoryboardScene] = []

        if content.script:
            for scene in content.script:
                scenes.append(
                    StoryboardScene(
                        index=scene.index,
                        seconds=scene.seconds,
                        frame_uri=self._frame_for(scene.index, frames),
                        on_screen=scene.on_screen,
                        voiceover=scene.voiceover,
                        visual=scene.visual,
                        source_ids=scene.source_ids,
                    )
                )
        else:
            # Fallback: derive one scene per design frame if no script was produced.
            for i, frame in enumerate(frames):
                scenes.append(
                    StoryboardScene(
                        index=i,
                        seconds=self._cfg.default_scene_seconds,
                        frame_uri=frame.uri,
                    )
                )

        return Storyboard(
            width=self._cfg.width,
            height=self._cfg.height,
            fps=self._cfg.fps,
            safe_top=self._cfg.safe_top,
            safe_bottom=self._cfg.safe_bottom,
            scenes=scenes,
        )

    def _frame_for(self, scene_index: int, frames: list[Asset]) -> str:
        if not frames:
            return ""
        # Prefer the design asset whose slide_index matches the scene, else cycle.
        for frame in frames:
            if frame.metadata.get("slide_index") == scene_index:
                return frame.uri
        return frames[scene_index % len(frames)].uri
