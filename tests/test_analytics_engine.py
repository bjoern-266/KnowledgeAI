"""Unit tests for the Analytics Engine (Sprint 9)."""

from __future__ import annotations

from acis.data.memory import InMemoryRepository
from acis.domain.enums import Platform, PublishStatus
from acis.domain.models import MetricSnapshot, PublishReceipt
from acis.engines.analytics import AnalyticsEngine
from acis.engines.interfaces import AnalyticsEngine as AnalyticsEngineProto


class FakeAnalytics:
    def __init__(self, metrics: dict[str, float] | None = None, *, boom: bool = False) -> None:
        self._metrics = metrics or {}
        self._boom = boom

    def fetch_metrics(self, external_id: str) -> dict[str, float]:
        if self._boom:
            raise RuntimeError("api down")
        return dict(self._metrics)


def _receipt(external_id: str = "ig_1") -> PublishReceipt:
    return PublishReceipt(
        content_id="c1",
        platform=Platform.INSTAGRAM,
        status=PublishStatus.PUBLISHED,
        external_id=external_id,
    )


_RAW = {"impressions": 10000.0, "likes": 500.0, "saves": 400.0, "shares": 200.0}


def _engine(metrics=_RAW, repo=None, boom=False) -> AnalyticsEngine:
    return AnalyticsEngine(FakeAnalytics(metrics, boom=boom), repository=repo)


def test_satisfies_interface():
    assert isinstance(_engine(), AnalyticsEngineProto)


def test_collects_and_derives_rates():
    metrics = _engine().collect(_receipt())
    assert metrics["save_rate"] == 0.04  # 400 / 10000
    assert metrics["share_rate"] == 0.02  # 200 / 10000
    assert metrics["engagement_rate"] == 0.11  # (500+400+200)/10000


def test_prepared_receipt_returns_empty():
    prepared = PublishReceipt(
        content_id="c1", platform=Platform.TIKTOK, status=PublishStatus.PREPARED
    )
    assert _engine().collect(prepared) == {}


def test_api_failure_is_best_effort():
    assert _engine(boom=True).collect(_receipt()) == {}


def test_zero_impressions_guarded():
    metrics = _engine({"impressions": 0.0, "saves": 5.0}).collect(_receipt())
    assert metrics["save_rate"] == 0.0
    assert metrics["engagement_rate"] == 0.0


def test_persists_snapshot_time_series():
    repo = InMemoryRepository()
    engine = _engine(repo=repo)
    engine.collect(_receipt("ig_1"))
    engine.collect(_receipt("ig_1"))  # second reading over time
    snapshots = repo.list("metric_snapshots", MetricSnapshot)
    assert len(snapshots) == 2
    assert snapshots[0].platform is Platform.INSTAGRAM
    assert snapshots[0].save_rate == 0.04


def test_no_repository_still_returns_metrics():
    metrics = _engine(repo=None).collect(_receipt())
    assert metrics["save_rate"] == 0.04
