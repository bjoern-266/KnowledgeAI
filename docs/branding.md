# Branding

All content follows one unified visual identity. The system enforces it
automatically — a human never hand-edits a design.

## Design language
Premium · modern · technical · minimalist.

## Color system

| Role | Usage | Value(s) |
| --- | --- | --- |
| Background | Base surfaces, slide backgrounds | Black `#000000`, Anthracite `#1C1C1C`, Graphite `#2B2B2B`, Carbon `#333333` |
| Text primary | Body copy | White `#FFFFFF` |
| Text secondary | Supporting copy | Light grey `#B0B0B0` |
| **Accent** | **Only** headings, numbers, statistics, key facts, highlights, CTA | Strong yellow `#FFD400` |

**Accent discipline is a hard rule.** Yellow is reserved for the elements above
and nothing else. This is checked by the Quality Engine's `design_check` gate.
The palette and accent-usage list are defined once in
[`config/default.yaml`](../config/default.yaml) under `branding`, so both design
automation and quality checks read the same source of truth.

## Typography & layout
- Clean, technical sans-serif; generous negative space; strong hierarchy.
- One idea per slide. The key number/fact (`Slide.highlight`) is the accent
  focal point of each slide.

## Formats
- **Instagram carousel** — 1080×1350, ~8 slides (config: `content.instagram_carousel_slides`).
- **TikTok video** — 1080×1920 vertical, derived from the same design.

## Voice
Authoritative, precise, curiosity-driven. Evidence-based; every claim is sourced.
Optimised for **saves and shares** in the knowledge niche.

## Implementation
Branding lives in configuration and Canva brand templates (see the
[Canva Automation Engine concept](architecture/modules/canva-automation-engine.md)).
Changing the identity is a config/template change — not a code change.
