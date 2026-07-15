"""Factory selecting the mock or live Instagram adapter by mode."""

from __future__ import annotations

from typing import Any

from acis.core.config import IntegrationMode
from acis.integrations.interfaces import InstagramPort


def build_instagram(mode: IntegrationMode, config: dict[str, Any]) -> InstagramPort:
    if mode is IntegrationMode.LIVE:
        from acis.integrations.instagram.live import LiveInstagram

        return LiveInstagram(config)
    from acis.integrations.instagram.mock import MockInstagram

    return MockInstagram(config)
