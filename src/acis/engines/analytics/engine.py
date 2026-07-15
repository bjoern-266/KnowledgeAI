"""Analytics Engine implementation.

    receipt -> fetch raw metrics (analytics port)
            -> normalise into platform-agnostic KPIs (guarded rates)
            -> persist a MetricSnapshot (time series)
            -> return the normalised KPIs

Best-effort by design: a prepared-only receipt (no external id), an unavailable
API, or metric lag never fails the pipeline - the engine returns ``{}`` and the
run continues. Rates are computed defensively (no divide-by-zero).
"""

from __future__ import annotations

from dataclasses import dataclass

from acis.core.base import Engine
from acis.data.repository import Repository
from acis.domain.models import MetricSnapshot, PublishReceipt
from acis.integrations.interfaces import AnalyticsPort

_SNAPSHOTS = "metric_snapshots"


@dataclass(frozen=True)
class AnalyticsEngineConfig:
    collection: str = _SNAPSHOTS


class AnalyticsEngine(Engine):
    """Collects, normalises and persists performance KPIs for a published post."""

    name = "analytics"

    def __init__(
        self,
        analytics: AnalyticsPort,
        *,
        repository: Repository | None = None,
        config: AnalyticsEngineConfig | None = None,
    ) -> None:
        super().__init__()
        self._analytics = analytics
        self._repo = repository
        self._cfg = config or AnalyticsEngineConfig()

    def collect(self, receipt: PublishReceipt) -> dict[str, float]:
        if not receipt.external_id:
            return {}  # prepared only - nothing published to measure yet
        try:
            raw = self._analytics.fetch_metrics(receipt.external_id)
        except Exception:  # noqa: BLE001 - metrics are best-effort
            self.log.warning("analytics.fetch_failed", external_id=receipt.external_id)
            return {}

        metrics = self._normalise(raw)
        self._persist(receipt, metrics)
        self.log.info(
            "analytics.collected",
            platform=receipt.platform.value,
            external_id=receipt.external_id,
            save_rate=metrics.get("save_rate", 0.0),
            share_rate=metrics.get("share_rate", 0.0),
        )
        return metrics

    # -- internals ------------------------------------------------------------
    def _normalise(self, raw: dict[str, float]) -> dict[str, float]:
        out = {k: float(v) for k, v in raw.items()}
        impressions = out.get("impressions", 0.0)
        likes = out.get("likes", 0.0)
        saves = out.get("saves", 0.0)
        shares = out.get("shares", 0.0)
        if impressions > 0:
            out.setdefault("save_rate", round(saves / impressions, 4))
            out.setdefault("share_rate", round(shares / impressions, 4))
            out["engagement_rate"] = round((likes + saves + shares) / impressions, 4)
        else:
            out.setdefault("save_rate", 0.0)
            out.setdefault("share_rate", 0.0)
            out["engagement_rate"] = 0.0
        return out

    def _persist(self, receipt: PublishReceipt, metrics: dict[str, float]) -> None:
        if self._repo is None:
            return
        snapshot = MetricSnapshot(
            content_id=receipt.content_id,
            platform=receipt.platform,
            external_id=receipt.external_id,
            metrics=metrics,
        )
        try:
            self._repo.save(self._cfg.collection, snapshot)
        except Exception:  # noqa: BLE001 - persistence is best-effort
            self.log.exception("analytics.persist_failed")
