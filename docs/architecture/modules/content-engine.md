# Content Engine — Design (impl. order #4)

> Interface: `acis.engines.interfaces.ContentEngine`
> Business rules: [CONTENT_INTELLIGENCE.md §4, §6](../../../CONTENT_INTELLIGENCE.md)

## 1. Purpose & responsibilities
Turn a verified dossier into **platform-ready written content** — the Instagram
carousel (primary) and the material the TikTok Video Engine will script from.
- Write a scroll-stopping hook.
- Structure facts into slides (one idea per slide).
- Produce caption, hashtags, CTA; decide/annotate platform fit (§6).
- Keep every `highlight` mapped to a verified dossier fact.

## 2. Input / output data (domain models)
- **In:** `Topic`, `KnowledgeBase` (typed facts, hooks, visual ideas — the
  Content Engine consumes these directly and never researches on its own).
- **Out:** `ContentPiece` (`hook`, `slides: list[Slide]`, `caption`, `hashtags`,
  `cta`, `platform`, `content_format`, `status=DRAFT`). Each `Slide` separates
  `headline`, `body`, and `highlight` (the accent-styled key number/fact).

## 3. Interfaces to other modules
- **Consumes:** `LLMPort` (writing), branding + content config.
- **Produces for:** Canva Automation Engine, TikTok Video Engine, Quality Engine.

## 4. Configuration parameters
- `content.instagram_carousel_slides` — target slide count.
- `content.platforms` — enabled platforms.
- `branding.*` — tone/voice constraints (premium, technical, minimalist).
- (new) `content.hook_styles`, `content.caption_max_len`.

## 5. Error cases
- LLM output malformed → re-prompt with stricter schema; cap retries.
- A `highlight` not backed by the dossier → drop it or fail the piece (must not
  ship unbacked numbers).
- Over-length output → truncate to slide/caption limits deterministically.

## 6. Quality criteria
- Every `highlight`/claim maps to a verified fact (checked here and re-checked by
  the Quality Engine).
- Tone matches branding; reading level appropriate for mobile.
- Slide count within configured bounds; title + CTA slides present.
- Sources referenced (caption / "sources in comments").

## 7. Test strategy
- Unit: slide structuring, hook/caption generation, length discipline,
  highlight-to-fact mapping — with a stub LLM returning canned facts.
- Fact integrity: injected unbacked highlight is rejected.
- Contract: satisfies `ContentEngine`.

## 8. Extension possibilities
- Per-platform content variants from one dossier.
- Multi-language output.
- Template/hook libraries informed by Learning-Engine watch-through data.
