# TikTok Video Engine — Design (impl. order #6)

> **Status: ✅ Implemented (Sprint 6)** — `acis.engines.tiktok.TikTokVideoEngine`,
> wired via `build_tiktok_video_engine`. Builds the storyboard (scene→frame
> mapping, timing, safe zones, hook-first) from the ContentPiece script + Canva
> design; file production is delegated to an injectable `renderer` seam (mock by
> default; real ffmpeg/cloud renderer plugs in unchanged).
> Interface: `acis.engines.interfaces.TikTokVideoEngine`
> Business rules: [CONTENT_INTELLIGENCE.md §6, §8](../../../CONTENT_INTELLIGENCE.md)

## 1. Purpose & responsibilities
Derive a vertical **TikTok video** from the same content/design used for the
carousel, so one research effort yields both formats with consistent branding.
- Storyboard from slides (hook → beats → CTA).
- Assemble frames from Canva assets; add motion, captions, optional voiceover.
- Encode to a publish-ready MP4.

## 2. Input / output data (domain models)
- **In:** `ContentPiece`, `DesignResult`.
- **Out:** `VideoResult` (`asset: Asset` (video, 1080×1920), `duration_seconds`).

## 3. Interfaces to other modules
- **Consumes:** Canva design assets, optional TTS/voiceover adapter, a render
  step (local ffmpeg or a cloud render adapter).
- **Produces for:** Quality Engine, Publishing Engine (TikTok).

## 4. Configuration parameters
- (new) `tiktok_video.target_seconds`, `tiktok_video.fps`.
- (new) `tiktok_video.voiceover` (on/off, voice), `tiktok_video.subtitles`.
- `branding.*` — colours, safe-zones for TikTok UI overlays.

## 5. Error cases
- Render tool unavailable → `IntegrationUnavailableError`; run can still prepare
  the carousel (video marked not-produced).
- Asset missing/corrupt → fail this piece with context.
- Audio licensing constraint → skip audio, keep subtitles.

## 6. Quality criteria
- Hook lands in the first second.
- Captions legible on mobile; content inside TikTok safe-zones.
- Duration within target; brand-consistent visuals (reused from Canva).

## 7. Test strategy
- Unit (mock render/TTS): storyboard from slides, duration calc, safe-zone
  layout, asset assembly order.
- Failure: missing asset / render error handled.
- Contract: satisfies `TikTokVideoEngine`.

## 8. Extension possibilities
- Local ffmpeg vs. hosted rendering behind one port.
- Synthesized voiceover, auto-captions, trending-sound integration.
- Pacing tuned by Learning-Engine watch-through data.
