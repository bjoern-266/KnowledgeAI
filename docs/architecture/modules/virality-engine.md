# Virality Engine — Design (impl. order #3)

> **Status: ✅ Implemented (Sprint 3)** — `acis.engines.virality.ViralityEngine`,
> wired via `build_virality_engine`. Transparent weighted score + diversity
> guard + optional exploration. Learned priors override category fit once the
> Learning Engine supplies them.
> Interface: `acis.engines.interfaces.ViralityEngine`
> Business rules: [CONTENT_INTELLIGENCE.md §3](../../../CONTENT_INTELLIGENCE.md)

## 1. Purpose & responsibilities
Rank the **screened** topics by expected share/save potential so the pipeline
always works on the highest-leverage, evidence-backed idea.
- Produce a transparent, component-based score per topic.
- Rank; enforce category diversity / exploration.
- **Not** responsible for fact-checking (screening already guaranteed sources).

## 2. Input / output data (domain models)
- **In:** `Topic` (single) / `list[Topic]` (screened survivors).
- **Out:** `ViralityScore` (`value` ∈ [0..1], `components`, `rationale`) attached
  to each `Topic`; `rank` returns topics sorted best-first.

## 3. Interfaces to other modules
- **Consumes:** `LLMPort` (novelty/shareability estimates), `Repository`
  (Learning-Engine priors: category/angle/historical fit).
- **Produces for:** the orchestrator, which selects `ranked[0]` for deep research.
- Reads learned weights written by the Learning Engine (via repository, not a
  direct call).

## 4. Configuration parameters
Implemented via `ViralityEngineConfig`:
- `weights` — per-component weights (`category_fit`, `trend_momentum`, `novelty`,
  `shareability`, `save_worthiness`, `historical_fit`); auto-normalised. ✅
- `diversity_top_n`, `max_per_category_in_top` — category-collapse guard. ✅
- `exploration_ratio` (default 0.0), `exploration_seed` — exploration budget. ✅
- `historical_priors` (constructor) — learned category fit from the Learning
  Engine (Sprint 10); empty for now. ✅
- *Future:* promote weights/guards to explicit YAML keys.

## 5. Error cases
- LLM estimate unavailable → fall back to configured priors; log degraded mode.
- Empty input (nothing screened) → orchestrator already raised
  `NoViableTopicError`; `rank([])` returns `[]` defensively.
- Missing learned priors (cold start) → use config defaults.

## 6. Quality criteria
- Never a black box: every score carries `components` + `rationale`.
- Scores normalised and bounded [0..1].
- Diversity guard prevents category collapse across cycles.
- Deterministic given the same inputs and priors.

## 7. Test strategy
- Unit: weighting math; ranking order; diversity constraint; exploration
  sampling (seeded).
- Cold-start vs. warm (with priors) behaviour.
- Ordering: virality only ever receives screened topics (pipeline test).
- Contract: satisfies `ViralityEngine`.

## 8. Extension possibilities
- Replace fixed weights with a learned regression / contextual bandit as data
  grows (Learning Engine).
- Per-platform virality models (IG vs. TikTok differ).
- A/B of angles for the same topic.
