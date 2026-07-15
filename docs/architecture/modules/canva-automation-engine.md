# Canva Automation Engine (step 6)

## Purpose
Automatically render a `ContentPiece` into **on-brand designs** via Canva
Premium — no manual editing, ever.

## Interface
`acis.engines.interfaces.CanvaAutomationEngine`
- `design(content) -> DesignResult`

## Approach
1. **Brand template** per format (carousel slide, TikTok frame) in Canva,
   encoding the palette (black/anthracite/graphite/carbon), typography, and the
   single strong-yellow accent reserved for headings/numbers/key facts/CTA.
2. **Autofill** each template with slide data through the `CanvaPort`
   (`create_design`), mapping `highlight` fields to accent-styled elements.
3. **Export** rendered assets (`export`) as image/PDF `Asset`s per slide.
4. Return a `DesignResult` linking the external `design_id` and produced assets.

The engine never hand-edits; it drives templated automation so output is
deterministic and always brand-compliant.

## Integrations
`canva` (Canva Connect API / Canva MCP tooling). Consumes `branding` config.

## Quality / risks
- Accent-colour discipline is a design-check gate in the Quality Engine.
- Text overflow / contrast — validated before export.
- Template drift: brand templates are versioned.

## Open questions
- Canva Connect API vs. the Canva MCP tools for autofill/export.
- Where brand templates are stored/versioned.
