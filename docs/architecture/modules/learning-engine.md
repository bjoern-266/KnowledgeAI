# Learning Engine — Design (impl. order #10)

> **Status: ✅ Implemented (Sprint 10)** — `acis.engines.learning.LearningEngine`,
> wired via `build_learning_engine`. Turns save/share performance into learned
> per-category priors via an EMA with shrinkage; persists `CategoryPrior`s that
> the Virality Engine loads on the next run. Closes the optimisation loop.
> Interface: `acis.engines.interfaces.LearningEngine`
> Business rules: [CONTENT_INTELLIGENCE.md §3, §8](../../../CONTENT_INTELLIGENCE.md)

## 1. Purpose & responsibilities
Close the loop: turn performance into **guidance that improves future content** —
which topics, angles, formats, and posting times work. This is what makes the
system autonomous *and improving*, not merely automated.

## 2. Input / output data (domain models)
- **In:** `PublishReceipt`, metrics `dict[str, float]` (from Analytics).
- **Out:** learned signals `dict[str, float]` (e.g. per-category save/share
  priors, best posting windows), persisted for the next cycle.

## 3. Interfaces to other modules
- **Consumes:** `Repository` (historical metrics + current priors). No external
  I/O — pure analysis.
- **Produces for:** Virality Engine (`category_fit`, `save_worthiness`,
  `historical_fit`), Content/TikTok engines (hook/pacing), Publishing (timing).
- Communicates only via persisted signals (no direct engine calls).

## 4. Configuration parameters
- (new) `learning.method` — `ema` | `bandit` | `regression`.
- (new) `learning.ema_alpha`, `learning.min_samples` (shrinkage).
- (new) `learning.exploration_ratio` — exploration budget (shared with virality).

## 5. Error cases
- Sparse data (cold start) → return priors unchanged; never overfit one post.
- Corrupt/missing metrics → skip that data point.
- Feedback collapse risk → exploration budget + diversity constraint mitigate.

## 6. Quality criteria
- Shrinkage/priors applied before acting on small samples.
- Exploration preserved (system keeps discovering).
- Updates are explainable and bounded; no runaway weights.
- Deterministic given the same history + seed.

## 7. Test strategy
- Unit: EMA update math; shrinkage on small n; exploration sampling (seeded);
  collapse-guard behaviour.
- Loop: metrics in → priors shift in the expected direction → virality picks
  differently next cycle (integration).
- Contract: satisfies `LearningEngine`.

## 8. Extension possibilities
- Graduate EMA → contextual bandit → regression as data volume grows.
- Per-platform and per-angle models.
- Automatic weight tuning for the virality components.
