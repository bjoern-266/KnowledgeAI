# Virality Engine (step 3)

## Purpose
Rank topics by expected **share/save potential** so the pipeline always works on
the highest-leverage idea.

## Interface
`acis.engines.interfaces.ViralityEngine`
- `score(topic) -> ViralityScore`
- `rank(topics) -> list[Topic]` (sorted, best first; attaches the score)

## Approach
A transparent, weighted model combining sub-scores into a normalised `[0..1]`
`ViralityScore` with per-component breakdown and a rationale:
- **category fit** — some knowledge categories reliably over-index on saves;
- **novelty / surprise** — "counter-intuitive fact" signal (LLM-assisted);
- **shareability** — identity/utility/emotion heuristics;
- **trend momentum** — from the source signal strength;
- **historical performance** — feedback from the Learning Engine (closes the loop).

Weights live in configuration so the model is tunable without code changes.
Keeping components explicit makes decisions auditable.

## Integrations
`openai` (novelty/shareability estimation). Consumes learned weights from the
repository (written by the Learning Engine).

## Quality / risks
- Avoid a black-box score: always emit `components` + `rationale`.
- Guard against feedback collapse (only ever picking one category) via
  diversity constraints.

## Open questions
- Fixed weights vs. a learned regression once enough performance data exists.
