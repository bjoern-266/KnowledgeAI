# TikTok Video Engine

## Purpose
Derive a vertical **TikTok video** from the same content/design used for the
Instagram carousel, so one research effort yields both formats.

## Interface
`acis.engines.interfaces.TikTokVideoEngine`
- `render(content, design) -> VideoResult`

## Approach
1. **Storyboard** from the carousel slides: hook → fact beats → CTA, timed for a
   15–30s vertical (1080×1920) video.
2. **Assemble** frames from the Canva design assets, add motion (pan/zoom),
   captions, and optional synthesized voiceover/subtitles.
3. **Encode** to MP4 and return a `VideoResult` (asset + duration).

Reuses the Canva-rendered visuals to guarantee brand consistency across
platforms rather than designing twice.

## Integrations
`canva` (frame assets), optional TTS/voiceover adapter, a rendering step
(local ffmpeg or a cloud render adapter).

## Quality / risks
- Pacing: first second must carry the hook.
- Caption legibility on mobile; safe-zones for TikTok UI overlays.
- Licensing of any audio.

## Open questions
- Local ffmpeg vs. a hosted rendering service.
- Voiceover: synthesized vs. text-only.
