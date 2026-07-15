"""Live Instagram adapter (skeleton).

Wired for the Instagram Graph API (create media container -> publish). Holds
credential handling; the concrete Graph API calls are implemented once an
access token and business account id are provided.
"""

from __future__ import annotations

from acis.core.config import IntegrationMode
from acis.core.errors import IntegrationUnavailableError
from acis.integrations.base import IntegrationAdapter


class LiveInstagram(IntegrationAdapter):
    integration = "instagram"
    required_credentials = ("access_token", "business_account_id")

    def __init__(self, config: dict | None = None) -> None:
        super().__init__(IntegrationMode.LIVE, config)

    def publish_carousel(self, content, assets):  # type: ignore[no-untyped-def]
        raise IntegrationUnavailableError(
            "Live Instagram adapter is not yet implemented; add Graph API calls or use mock mode.",
            context={"integration": self.integration},
        )
