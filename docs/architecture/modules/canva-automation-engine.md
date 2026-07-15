# Canva Automation Engine — Design (impl. order #5)

> Interface: `acis.engines.interfaces.CanvaAutomationEngine`
> Business rules: [branding.md](../../branding.md),
> [CONTENT_INTELLIGENCE.md §6](../../../CONTENT_INTELLIGENCE.md)

## 1. Purpose & responsibilities
Render a `ContentPiece` into **on-brand designs** via Canva Premium, fully
automated — a human never edits a design.
- Map slide data onto brand templates.
- Enforce the palette and the single strong-yellow accent rule.
- Export rendered assets.

## 2. Input / output data (domain models)
- **In:** `ContentPiece`.
- **Out:** `DesignResult` (`design_id`, `assets: list[Asset]` — one per slide,
  with dimensions/mime/metadata).

## 3. Interfaces to other modules
- **Consumes:** `CanvaPort` (create/export), branding config.
- **Produces for:** TikTok Video Engine (frame assets), Quality Engine
  (design_check), Publishing Engine (carousel assets).

## 4. Configuration parameters
- `branding.palette`, `branding.accent_usage`, `branding.design_language`.
- `integrations.canva.*` — mode, api_key, `brand_kit_id`.
- (new) `canva.templates` — per-format brand template ids.

## 5. Error cases
- Missing credentials in live mode → `MissingCredentialError` at setup.
- Canva API failure/rate limit → typed `IntegrationError`; retry with backoff.
- Text overflow / low contrast → flag for the design_check gate; regenerate.
- Template not found → `ConfigError`.

## 6. Quality criteria
- Accent colour used **only** for headings/numbers/key facts/CTA (hard brand rule).
- One asset per slide; correct dimensions per format.
- Deterministic, reproducible output for the same content.
- Fully unattended — no manual step.

## 7. Test strategy
- Unit (mock `CanvaPort`): asset-per-slide mapping, accent-field mapping,
  dimension correctness.
- Brand-rule assertion: accent applied to the right elements only.
- Failure handling: API error → retry/typed error.
- Contract: satisfies `CanvaAutomationEngine`.

## 8. Extension possibilities
- Multiple template variants for A/B testing (feeds Learning Engine).
- New formats (stories, reels covers) by adding templates.
- Choice of Canva Connect API vs. Canva MCP tooling behind the same port.
