# Content Engine (step 5)

## Purpose
Turn a dossier into **platform-ready written content**: an Instagram carousel
(primary) and the script for a TikTok derivation.

## Interface
`acis.engines.interfaces.ContentEngine`
- `create(topic, dossier) -> ContentPiece`

## Approach
1. **Hook first.** Generate a scroll-stopping opening line from the topic angle.
2. **Structure into slides** (`Slide[]`): title slide → one key fact per slide →
   CTA slide. Each slide separates `headline`, `body`, and a `highlight` (the key
   number/fact that the design renders in the accent colour).
3. **Caption + hashtags + CTA** tuned per platform, always citing sources.
4. **Length discipline** to `content.instagram_carousel_slides`.

Output is pure structured data — no styling. Visual treatment is the Canva
Engine's job, keeping content and design cleanly separated.

## Integrations
`openai` (writing). Reads branding/config for slide count and tone.

## Quality / risks
- Every `highlight` must correspond to a verified fact in the dossier.
- Tone consistency (premium/technical) — enforced via system prompt + Quality
  Engine spelling/style check.

## Open questions
- One `ContentPiece` per platform vs. a shared piece with platform variants.
