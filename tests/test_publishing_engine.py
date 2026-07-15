"""Unit tests for the Publishing Engine (Sprint 8)."""

from __future__ import annotations

from acis.data.memory import InMemoryRepository
from acis.domain.enums import ContentFormat, Platform, PublishStatus
from acis.domain.models import Asset, ContentPiece, PublishReceipt, VideoResult
from acis.engines.interfaces import PublishingEngine as PublishingEngineProto
from acis.engines.publishing import PublishingEngine, PublishingEngineConfig
from acis.integrations.instagram.mock import MockInstagram
from acis.integrations.tiktok.mock import MockTikTok


def _content() -> ContentPiece:
    return ContentPiece(
        topic_id="t1",
        knowledge_id="k1",
        platform=Platform.INSTAGRAM,
        content_format=ContentFormat.INSTAGRAM_CAROUSEL,
    )


def _assets() -> list[Asset]:
    return [Asset(kind="image", uri="mock://0.png")]


def _video(content: ContentPiece) -> VideoResult:
    return VideoResult(content_id=content.id, asset=Asset(kind="video", uri="mock://v.mp4"))


def _engine(**kw) -> PublishingEngine:
    return PublishingEngine(MockInstagram(), MockTikTok(), **kw)


def test_satisfies_interface():
    assert isinstance(_engine(), PublishingEngineProto)


def test_publishes_to_both_platforms():
    content = _content()
    receipts = _engine().publish(content, _assets(), _video(content))
    platforms = {r.platform for r in receipts}
    assert platforms == {Platform.INSTAGRAM, Platform.TIKTOK}
    assert all(r.status is PublishStatus.PUBLISHED for r in receipts)
    assert all(r.external_id for r in receipts)


def test_respects_configured_platforms():
    content = _content()
    engine = _engine(config=PublishingEngineConfig(platforms=frozenset({Platform.TIKTOK})))
    receipts = engine.publish(content, _assets(), _video(content))
    assert [r.platform for r in receipts] == [Platform.TIKTOK]


def test_graceful_degradation_to_prepared():
    class BoomInstagram:
        def publish_carousel(self, content, assets):
            raise RuntimeError("missing credentials")

    content = _content()
    engine = PublishingEngine(BoomInstagram(), MockTikTok())
    receipts = engine.publish(content, _assets(), _video(content))
    ig = next(r for r in receipts if r.platform is Platform.INSTAGRAM)
    assert ig.status is PublishStatus.PREPARED
    assert "missing credentials" in ig.detail
    # TikTok still publishes despite Instagram failing.
    tt = next(r for r in receipts if r.platform is Platform.TIKTOK)
    assert tt.status is PublishStatus.PUBLISHED


def test_persists_receipts():
    repo = InMemoryRepository()
    content = _content()
    _engine(repository=repo).publish(content, _assets(), _video(content))
    stored = repo.list("publish_receipts", PublishReceipt)
    assert len(stored) == 2


def test_idempotent_no_double_publish():
    repo = InMemoryRepository()
    content = _content()
    engine = _engine(repository=repo)
    first = engine.publish(content, _assets(), _video(content))
    second = engine.publish(content, _assets(), _video(content))
    # Same receipts returned; nothing new persisted.
    assert {r.id for r in first} == {r.id for r in second}
    assert len(repo.list("publish_receipts", PublishReceipt)) == 2
