"""Deterministic mock LLM.

Returns structured, deterministic text derived from the prompt so research and
content generation can be exercised without an API key or network. The output
is intentionally simple but shaped like real completions (headline + bullets).
"""

from __future__ import annotations

import hashlib

from acis.core.config import IntegrationMode
from acis.integrations.base import IntegrationAdapter


class MockLLM(IntegrationAdapter):
    integration = "openai"

    def __init__(self, config: dict | None = None) -> None:
        super().__init__(IntegrationMode.MOCK, config)

    def complete(self, prompt: str, *, system: str = "", max_tokens: int = 1024) -> str:
        digest = hashlib.sha256((system + "\n" + prompt).encode()).hexdigest()[:8]
        self.log.debug("mock.complete", tokens=max_tokens, digest=digest)
        # Echo a compact, deterministic "completion" the engines can parse/use.
        first_line = prompt.strip().splitlines()[0] if prompt.strip() else "topic"
        return (
            f"[mock:{digest}] {first_line}\n"
            "- Key fact one, backed by evidence.\n"
            "- Key fact two, with a surprising number.\n"
            "- Key fact three that invites a share."
        )
