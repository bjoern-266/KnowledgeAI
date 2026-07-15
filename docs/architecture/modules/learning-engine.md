# Learning Engine (step 9)

## Purpose
Close the loop: turn performance data into **guidance that improves future
content** — which topics, angles, formats, and posting times work.

## Interface
`acis.engines.interfaces.LearningEngine`
- `learn(receipt, metrics) -> dict[str, float]`

## Approach
1. **Attribute** outcomes to the content's features (category, angle, hook style,
   slide count, posting time, design variants).
2. **Update models:** maintain per-feature performance priors (e.g. category →
   expected save rate). Start with simple exponential-moving-average priors;
   graduate to a bandit/regression as data grows.
3. **Emit weights** consumed by the Virality Engine (topic scoring) and the
   Publishing Engine (timing), persisted for the next cycle.
4. **Experimentation:** allocate a fraction of runs to exploration so the system
   keeps discovering, avoiding local maxima.

This is what makes the system *autonomous and improving* rather than merely
automated.

## Integrations
None external — pure analysis over persisted metrics. Reads/writes the
repository.

## Quality / risks
- Feedback collapse (exploiting one winning pattern) → enforce exploration &
  diversity constraints.
- Small-sample noise → shrinkage/priors before acting on a signal.
- Overfitting to a platform's transient algorithm changes.

## Open questions
- EMA priors vs. contextual bandit vs. regression — sequencing by data volume.
- How aggressively learned weights override configured defaults.
