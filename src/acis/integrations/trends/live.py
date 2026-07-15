"""Live trend source adapter (skeleton).

Wired for a real trend provider. The foundation ships the structure and
credential handling; the concrete HTTP calls are implemented once a provider
and credentials are chosen. Until then, calling it raises a clear error rather
than silently returning nothing.
"""

from __future__ import annotations

from acis.core.config import IntegrationMode
from acis.core.errors import IntegrationUnavailableError
from acis.integrations.base import IntegrationAdapter


class LiveTrendSource(IntegrationAdapter):
    integration = "trends"
    required_credentials = ("api_key",)

    def __init__(self, config: dict | None = None) -> None:
        super().__init__(IntegrationMode.LIVE, config)

    def fetch_trends(self, *, region: str = "global", limit: int = 20) -> list:
        # TODO(live): call the configured trend API using self.config["api_key"].
        raise IntegrationUnavailableError(
            "Live trend source is not yet implemented; provide an adapter or run in mock mode.",
            context={"integration": self.integration, "region": region},
        )
