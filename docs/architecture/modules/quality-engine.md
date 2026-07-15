# Quality Engine

## Purpose
The **gatekeeper**. No content is published unless it passes fact, source,
spelling, and design checks and clears the overall score threshold.

## Interface
`acis.engines.interfaces.QualityEngine`
- `evaluate(content, dossier, assets) -> QualityReport`

## Approach
Run independent checks, each yielding a `[0..1]` sub-score in
`QualityReport.scores` keyed by `QualityCheck`:
- **fact_check** — every `highlight`/claim traces to a dossier fact.
- **source_check** — ≥ `min_sources_per_topic` reliable sources present.
- **spelling_check** — grammar/spelling/tone (premium, technical) pass.
- **design_check** — assets exist, brand palette respected, accent used only for
  headings/numbers/key facts/CTA, contrast/overflow OK.
- **overall_score** — aggregate; must be ≥ `quality.min_score`.

The engine only *reports*; the **pipeline** enforces the hard stop
(`QualityGateError`) so the rule lives in one place and cannot be bypassed by an
individual engine.

## Integrations
`openai` (fact/spelling/style checks). Consumes `quality` and `branding` config.

## Quality / risks
- False negatives block good content; false positives publish bad content —
  thresholds are config-tunable and logged with full sub-score breakdown.
- Design checks may need image analysis, not just metadata.

## Open questions
- Weighting of sub-scores in the aggregate.
- Human-in-the-loop escape hatch for borderline scores (probably off by default).
