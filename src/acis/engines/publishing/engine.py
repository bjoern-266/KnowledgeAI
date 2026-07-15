"""Publishing Engine implementation.

For each enabled platform the engine:

1. checks the repository for an existing PUBLISHED receipt (idempotency) and
   returns it instead of re-posting;
2. calls the platform port (Instagram carousel / TikTok video);
3. on any failure - missing credentials, live API not ready, rate limit -
   degrades to a PREPARED receipt carrying the reason, rather than failing the
   run ("prepare now, publish once credentials are in place");
4. persists the receipt for audit and idempotency.

The engine is vendor-agnostic: it depends only on the Instagram/TikTok ports, so
mock and live adapters are interchangeable by configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from acis.core.base import Engine
from acis.data.repository import Repository
from acis.domain.enums import Platform, PublishStatus
from acis.domain.models import Asset, ContentPiece, PublishReceipt, VideoResult
from acis.integrations.interfaces import InstagramPort, TikTokPort

_RECEIPTS = "publish_receipts"


@dataclass(frozen=True)
class PublishingEngineConfig:
    platforms: frozenset[Platform] = field(
        default_factory=lambda: frozenset({Platform.INSTAGRAM, Platform.TIKTOK})
    )

    @classmethod
    def from_settings(cls, settings: object) -> PublishingEngineConfig:
        content = getattr(settings, "content", None)
        names = list(getattr(content, "platforms", []) or []) if content else []
        platforms = set()
        for name in names:
            try:
                platforms.add(Platform(name))
            except ValueError:
                continue
        return cls(platforms=frozenset(platforms) if platforms else cls().platforms)


class PublishingEngine(Engine):
    """Publishes (or prepares) content to Instagram and TikTok."""

    name = "publishing"

    def __init__(
        self,
        instagram: InstagramPort,
        tiktok: TikTokPort,
        *,
        repository: Repository | None = None,
        config: PublishingEngineConfig | None = None,
    ) -> None:
        super().__init__()
        self._instagram = instagram
        self._tiktok = tiktok
        self._repo = repository
        self._cfg = config or PublishingEngineConfig()

    def publish(
        self, content: ContentPiece, assets: list[Asset], video: VideoResult
    ) -> list[PublishReceipt]:
        receipts: list[PublishReceipt] = []
        if Platform.INSTAGRAM in self._cfg.platforms:
            receipts.append(
                self._publish_one(
                    content,
                    Platform.INSTAGRAM,
                    lambda: self._instagram.publish_carousel(content, assets),
                )
            )
        if Platform.TIKTOK in self._cfg.platforms:
            receipts.append(
                self._publish_one(
                    content,
                    Platform.TIKTOK,
                    lambda: self._tiktok.publish_video(content, video),
                )
            )
        return receipts

    # -- internals ------------------------------------------------------------
    def _publish_one(self, content, platform, action) -> PublishReceipt:  # type: ignore[no-untyped-def]
        existing = self._existing(content.id, platform)
        if existing is not None:
            self.log.info("publish.idempotent_skip", platform=platform.value, content_id=content.id)
            return existing
        try:
            receipt = action()
            self.log.info(
                "publish.published", platform=platform.value, external_id=receipt.external_id
            )
        except Exception as exc:  # noqa: BLE001 - degrade to PREPARED, never fail the run
            receipt = PublishReceipt(
                content_id=content.id,
                platform=platform,
                status=PublishStatus.PREPARED,
                detail=f"prepared (publish unavailable: {exc})",
            )
            self.log.warning("publish.prepared", platform=platform.value, reason=str(exc))
        self._persist(receipt)
        return receipt

    def _existing(self, content_id: str, platform: Platform) -> PublishReceipt | None:
        if self._repo is None:
            return None
        try:
            for receipt in self._repo.list(_RECEIPTS, PublishReceipt):
                if (
                    receipt.content_id == content_id
                    and receipt.platform is platform
                    and receipt.status is PublishStatus.PUBLISHED
                ):
                    return receipt
        except Exception:  # noqa: BLE001 - idempotency lookup is best-effort
            return None
        return None

    def _persist(self, receipt: PublishReceipt) -> None:
        if self._repo is None:
            return
        try:
            self._repo.save(_RECEIPTS, receipt)
        except Exception:  # noqa: BLE001 - persistence is best-effort
            self.log.exception("publish.persist_failed")
