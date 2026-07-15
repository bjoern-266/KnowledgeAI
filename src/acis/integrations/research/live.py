"""Live research source adapter (skeleton).

Wired for a real retrieval backend (encyclopedic/academic/stats APIs). Holds
credential handling; concrete search calls are implemented once a provider is
chosen. Until then it raises a clear error rather than returning nothing.
"""

from __future__ import annotations

from acis.core.config import IntegrationMode
from acis.core.errors import IntegrationUnavailableError
from acis.domain.models import RetrievedDocument
from acis.integrations.base import IntegrationAdapter


class LiveResearchSource(IntegrationAdapter):
    integration = "research"
    required_credentials = ("api_key",)

    def __init__(self, config: dict | None = None) -> None:
        super().__init__(IntegrationMode.LIVE, config)

    def search(self, query: str, *, limit: int = 10) -> list[RetrievedDocument]:
        raise IntegrationUnavailableError(
            "Live research source is not yet implemented; add a retrieval adapter "
            "or run in mock mode.",
            context={"integration": self.integration, "query": query},
        )
