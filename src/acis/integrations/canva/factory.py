"""Factory selecting the mock or live Canva adapter by mode."""

from __future__ import annotations

from typing import Any

from acis.core.config import IntegrationMode
from acis.integrations.interfaces import CanvaPort


def build_canva(mode: IntegrationMode, config: dict[str, Any]) -> CanvaPort:
    if mode is IntegrationMode.LIVE:
        from acis.integrations.canva.live import LiveCanva

        return LiveCanva(config)
    from acis.integrations.canva.mock import MockCanva

    return MockCanva(config)
