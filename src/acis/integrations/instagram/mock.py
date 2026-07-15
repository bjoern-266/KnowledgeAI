"""Mock Instagram publisher.

Simulates a successful carousel upload and returns a deterministic receipt with
a fake post id and URL. No network, no credentials.
"""

from __future__ import annotations

from acis.core.config import IntegrationMode
from acis.domain.enums import Platform, PublishStatus
from acis.integrations.base import IntegrationAdapter


class MockInstagram(IntegrationAdapter):
    integration = "instagram"

    def __init__(self, config: dict | None = None) -> None:
        super().__init__(IntegrationMode.MOCK, config)

    def publish_carousel(self, content, assets):  # type: ignore[no-untyped-def]
        from acis.domain.models import PublishReceipt

        external_id = f"ig_mock_{content.id[:10]}"
        self.log.debug("mock.publish_carousel", external_id=external_id, assets=len(assets))
        return PublishReceipt(
            content_id=content.id,
            platform=Platform.INSTAGRAM,
            status=PublishStatus.PUBLISHED,
            external_id=external_id,
            url=f"https://instagram.com/p/{external_id}",
            detail="simulated publish",
        )
