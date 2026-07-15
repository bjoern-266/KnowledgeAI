"""Live Canva adapter (skeleton).

Wired for the Canva Connect API / Canva MCP tooling. Credential handling is in
place; the concrete design-generation and export calls are implemented once
access is configured.
"""

from __future__ import annotations

from acis.core.config import IntegrationMode
from acis.core.errors import IntegrationUnavailableError
from acis.integrations.base import IntegrationAdapter


class LiveCanva(IntegrationAdapter):
    integration = "canva"
    required_credentials = ("api_key",)

    def __init__(self, config: dict | None = None) -> None:
        super().__init__(IntegrationMode.LIVE, config)
        self.brand_kit_id = (config or {}).get("brand_kit_id", "")

    def create_design(self, content):  # type: ignore[no-untyped-def]
        raise IntegrationUnavailableError(
            "Live Canva adapter is not yet implemented; configure Canva access or use mock mode.",
            context={"integration": self.integration},
        )

    def export(self, design_id: str, *, fmt: str = "png"):  # type: ignore[no-untyped-def]
        raise IntegrationUnavailableError(
            "Live Canva export is not yet implemented; configure Canva access or use mock mode.",
            context={"integration": self.integration, "design_id": design_id},
        )
