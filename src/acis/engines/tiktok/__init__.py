"""TikTok Video Engine (Sprint 6).

Derives a vertical TikTok video from the same ContentPiece (its script) and the
Canva design (its frames), so one research effort yields both formats. The
engine owns the storyboard, per-scene timing, frame mapping and safe-zone
layout; the actual file production is delegated to an injectable ``renderer``
seam (a real ffmpeg/cloud renderer plugs in without touching the engine).

See ``docs/architecture/modules/tiktok-video-engine.md``.
"""

from acis.engines.tiktok.engine import TikTokVideoEngine, TikTokVideoEngineConfig

__all__ = ["TikTokVideoEngine", "TikTokVideoEngineConfig"]
