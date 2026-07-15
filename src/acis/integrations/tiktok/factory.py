"""Factory selecting the mock or live TikTok adapter by mode."""

from __future__ import annotations

from typing import Any

from acis.core.config import IntegrationMode
from acis.integrations.interfaces import TikTokPort


def build_tiktok(mode: IntegrationMode, config: dict[str, Any]) -> TikTokPort:
    if mode is IntegrationMode.LIVE:
        from acis.integrations.tiktok.live import LiveTikTok

        return LiveTikTok(config)
    from acis.integrations.tiktok.mock import MockTikTok

    return MockTikTok(config)
