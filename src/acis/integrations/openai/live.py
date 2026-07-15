"""Live OpenAI adapter (skeleton).

Holds credential handling and the call shape. The concrete SDK/HTTP call is
implemented once the ``openai`` dependency and an API key are provided.
"""

from __future__ import annotations

from acis.core.config import IntegrationMode
from acis.core.errors import IntegrationUnavailableError
from acis.integrations.base import IntegrationAdapter


class LiveLLM(IntegrationAdapter):
    integration = "openai"
    required_credentials = ("api_key",)

    def __init__(self, config: dict | None = None) -> None:
        super().__init__(IntegrationMode.LIVE, config)
        self.model = (config or {}).get("model", "gpt-4o")

    def complete(self, prompt: str, *, system: str = "", max_tokens: int = 1024) -> str:
        # TODO(live): call the OpenAI API with self.config["api_key"] and self.model.
        raise IntegrationUnavailableError(
            "Live LLM adapter is not yet implemented; add the SDK call or run in mock mode.",
            context={"integration": self.integration, "model": self.model},
        )
