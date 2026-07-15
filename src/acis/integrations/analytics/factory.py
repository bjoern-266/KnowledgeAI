"""Factory selecting the mock or live analytics adapter by mode."""

from __future__ import annotations

from typing import Any

from acis.core.config import IntegrationMode
from acis.integrations.interfaces import AnalyticsPort


def build_analytics(mode: IntegrationMode, config: dict[str, Any]) -> AnalyticsPort:
    if mode is IntegrationMode.LIVE:
        from acis.integrations.analytics.live import LiveAnalytics

        return LiveAnalytics(config)
    from acis.integrations.analytics.mock import MockAnalytics

    return MockAnalytics(config)
