"""Learning Engine implementation.

    (topic, receipt, metrics)
      -> performance target = f(save_rate, share_rate)   # normalised [0..1]
      -> load the category's prior (or its base)
      -> EMA update with shrinkage (early samples move it only a little)
      -> persist the updated CategoryPrior
      -> return the learned signal

The persisted priors are read by the Virality Engine (`historical_priors`) on
the next run, closing the optimisation loop. Exploration - deliberately trying
new categories/angles so the system keeps discovering - is handled by the
Virality Engine's exploration budget; here we only learn from what happened.
"""

from __future__ import annotations

from dataclasses import dataclass

from acis.core.base import Engine
from acis.data.repository import Repository
from acis.domain.models import CategoryPrior, PublishReceipt, Topic

_PRIORS = "category_priors"


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


@dataclass(frozen=True)
class LearningEngineConfig:
    alpha: float = 0.3  # base EMA learning rate
    min_samples: int = 5  # shrinkage floor - full alpha only after this many samples
    base_fit: float = 0.7  # starting prior for an unseen category
    #: KPI values that map to a perfect (1.0) performance target.
    save_target: float = 0.10
    share_target: float = 0.06
    save_weight: float = 0.6
    share_weight: float = 0.4
    collection: str = _PRIORS


class LearningEngine(Engine):
    """Updates learned category priors from published performance."""

    name = "learning"

    def __init__(
        self, *, repository: Repository | None = None, config: LearningEngineConfig | None = None
    ) -> None:
        super().__init__()
        self._repo = repository
        self._cfg = config or LearningEngineConfig()

    def learn(
        self, topic: Topic, receipt: PublishReceipt, metrics: dict[str, float]
    ) -> dict[str, float]:
        target = self._target(metrics)
        prior = self._load(topic) or CategoryPrior(
            id=topic.category.value, category=topic.category, value=self._cfg.base_fit, samples=0
        )

        # Shrinkage: the effective learning rate ramps up with the sample count.
        shrink = min(1.0, (prior.samples + 1) / self._cfg.min_samples)
        alpha = self._cfg.alpha * shrink
        new_value = _clamp(prior.value + alpha * (target - prior.value))

        updated = CategoryPrior(
            id=topic.category.value,
            category=topic.category,
            value=round(new_value, 4),
            samples=prior.samples + 1,
        )
        self._persist(updated)
        self.log.info(
            "learning.updated",
            category=topic.category.value,
            target=round(target, 3),
            prior=updated.value,
            samples=updated.samples,
        )
        return {
            "category_fit": updated.value,
            "target": round(target, 4),
            "samples": float(updated.samples),
        }

    # -- internals ------------------------------------------------------------
    def _target(self, metrics: dict[str, float]) -> float:
        save = metrics.get("save_rate", 0.0) / self._cfg.save_target
        share = metrics.get("share_rate", 0.0) / self._cfg.share_target
        return _clamp(self._cfg.save_weight * save + self._cfg.share_weight * share)

    def _load(self, topic: Topic) -> CategoryPrior | None:
        if self._repo is None:
            return None
        try:
            return self._repo.find(self._cfg.collection, topic.category.value, CategoryPrior)
        except Exception:  # noqa: BLE001 - best-effort
            return None

    def _persist(self, prior: CategoryPrior) -> None:
        if self._repo is None:
            return
        try:
            self._repo.save(self._cfg.collection, prior)
        except Exception:  # noqa: BLE001 - persistence is best-effort
            self.log.exception("learning.persist_failed")


def load_category_priors(repository: Repository) -> dict[str, float]:
    """Read learned priors as a ``category value -> fit`` map for the Virality Engine."""
    try:
        return {p.category.value: p.value for p in repository.list(_PRIORS, CategoryPrior)}
    except Exception:  # noqa: BLE001 - best-effort
        return {}
