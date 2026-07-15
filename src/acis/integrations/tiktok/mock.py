"""Mock TikTok publisher.

Simulates a successful video upload and returns a deterministic receipt.
"""

from __future__ import annotations

from acis.core.config import IntegrationMode
from acis.domain.enums import Platform, PublishStatus
from acis.integrations.base import IntegrationAdapter


class MockTikTok(IntegrationAdapter):
    integration = "tiktok"

    def __init__(self, config: dict | None = None) -> None:
        super().__init__(IntegrationMode.MOCK, config)

    def publish_video(self, content, video):  # type: ignore[no-untyped-def]
        from acis.domain.models import PublishReceipt

        external_id = f"tt_mock_{content.id[:10]}"
        self.log.debug("mock.publish_video", external_id=external_id)
        return PublishReceipt(
            content_id=content.id,
            platform=Platform.TIKTOK,
            status=PublishStatus.PUBLISHED,
            external_id=external_id,
            url=f"https://tiktok.com/@acis/video/{external_id}",
            detail="simulated publish",
        )
