"""Factory selecting the mock or live research source by mode."""

from __future__ import annotations

from typing import Any

from acis.core.config import IntegrationMode
from acis.integrations.interfaces import ResearchSourcePort


def build_research_source(mode: IntegrationMode, config: dict[str, Any]) -> ResearchSourcePort:
    if mode is IntegrationMode.LIVE:
        from acis.integrations.research.live import LiveResearchSource

        return LiveResearchSource(config)
    from acis.integrations.research.mock import MockResearchSource

    return MockResearchSource(config)
