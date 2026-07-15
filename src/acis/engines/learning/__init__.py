"""Learning Engine (Sprint 10).

Closes the loop: turns published performance into learned per-category priors
that the Virality Engine reads on the next cycle, so the system keeps improving
what it produces. Uses an exponential moving average with shrinkage (early
samples move a prior only a little) to avoid overreacting to noise.

See ``docs/architecture/modules/learning-engine.md`` and
``CONTENT_INTELLIGENCE.md`` §3, §8.
"""

from acis.engines.learning.engine import (
    LearningEngine,
    LearningEngineConfig,
    load_category_priors,
)

__all__ = ["LearningEngine", "LearningEngineConfig", "load_category_priors"]
