"""Factory selecting the mock or live LLM by mode."""

from __future__ import annotations

from typing import Any

from acis.core.config import IntegrationMode
from acis.integrations.interfaces import LLMPort


def build_llm(mode: IntegrationMode, config: dict[str, Any]) -> LLMPort:
    if mode is IntegrationMode.LIVE:
        from acis.integrations.openai.live import LiveLLM

        return LiveLLM(config)
    from acis.integrations.openai.mock import MockLLM

    return MockLLM(config)
