"""Live analytics adapter (skeleton).

Pulls insights from the platform Graph/analytics APIs. Credential handling is
in place; concrete calls are implemented once access is configured.
"""

from __future__ import annotations

from acis.core.config import IntegrationMode
from acis.core.errors import IntegrationUnavailableError
from acis.integrations.base import IntegrationAdapter


class LiveAnalytics(IntegrationAdapter):
    integration = "analytics"
    required_credentials = ("api_key",)

    def __init__(self, config: dict | None = None) -> None:
        super().__init__(IntegrationMode.LIVE, config)

    def fetch_metrics(self, external_id: str) -> dict[str, float]:
        raise IntegrationUnavailableError(
            "Live analytics adapter is not yet implemented; add API calls or use mock mode.",
            context={"integration": self.integration, "external_id": external_id},
        )
