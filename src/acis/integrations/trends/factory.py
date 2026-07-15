"""Factory selecting the mock or live trend source by mode."""

from __future__ import annotations

from typing import Any

from acis.core.config import IntegrationMode
from acis.integrations.interfaces import TrendSourcePort


def build_trends(mode: IntegrationMode, config: dict[str, Any]) -> TrendSourcePort:
    if mode is IntegrationMode.LIVE:
        from acis.integrations.trends.live import LiveTrendSource

        return LiveTrendSource(config)
    from acis.integrations.trends.mock import MockTrendSource

    return MockTrendSource(config)
