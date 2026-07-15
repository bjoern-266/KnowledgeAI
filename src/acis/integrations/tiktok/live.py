"""Live TikTok adapter (skeleton).

Wired for the TikTok Content Posting API. Holds credential handling; concrete
upload/publish calls are implemented once client credentials and an access
token are provided.
"""

from __future__ import annotations

from acis.core.config import IntegrationMode
from acis.core.errors import IntegrationUnavailableError
from acis.integrations.base import IntegrationAdapter


class LiveTikTok(IntegrationAdapter):
    integration = "tiktok"
    required_credentials = ("client_key", "client_secret", "access_token")

    def __init__(self, config: dict | None = None) -> None:
        super().__init__(IntegrationMode.LIVE, config)

    def publish_video(self, content, video):  # type: ignore[no-untyped-def]
        raise IntegrationUnavailableError(
            "Live TikTok adapter is not yet implemented; add API calls or use mock mode.",
            context={"integration": self.integration},
        )
