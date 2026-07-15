# Quality Engine — Design (impl. order #7)

> Interface: `acis.engines.interfaces.QualityEngine`
> Business rules: [CONTENT_INTELLIGENCE.md §7](../../../CONTENT_INTELLIGENCE.md)

## 1. Purpose & responsibilities
The **gatekeeper**. Score content against fact/source/spelling/design gates and
report whether it clears the threshold. It only *reports*; the pipeline enforces
the hard stop, so the rule lives in exactly one place.

## 2. Input / output data (domain models)
- **In:** `ContentPiece`, `KnowledgeBase`, `assets: list[Asset]`.
- **Out:** `QualityReport` (`scores: dict[QualityCheck, float]`, `passed`,
  `threshold`, `issues`). `overall` is derived from `OVERALL_SCORE`.

## 3. Interfaces to other modules
- **Consumes:** `LLMPort` (fact/spelling/style checks), quality + branding config.
- **Produces for:** the orchestrator (which raises `QualityGateError` if not
  `passed`).

## 4. Configuration parameters
- `quality.min_score` — publish threshold.
- `quality.require_fact_check|source_check|spelling_check|design_check` — toggles.
- `quality.min_sources_per_topic` — reused for source_check.
- (new) `quality.weights` — sub-score aggregation weights.

## 5. Error cases
- LLM checker unavailable → treat as failing the affected gate (fail-closed), log.
- Missing inputs (no assets/dossier) → corresponding gate scores 0.
- Never raises to publish anyway: absence of evidence = fail, not pass.

## 6. Quality criteria
- Fail-closed: uncertainty blocks publishing, never permits it.
- Every gate contributes an explicit sub-score; `issues` explains failures.
- Design gate enforces the accent-only-for-key-elements brand rule.
- Deterministic given the same inputs.

## 7. Test strategy
- Unit: each gate independently (pass/fail); aggregation math; threshold
  boundary; fail-closed on checker error.
- Integration: below-threshold content blocks publish (already in
  `tests/test_pipeline.py`).
- Contract: satisfies `QualityEngine`.

## 8. Extension possibilities
- Image-analysis-based design checks (contrast, overflow) beyond metadata.
- Plagiarism / originality check.
- Per-platform quality thresholds.
- Optional human-in-the-loop escape hatch for borderline scores (default off).
