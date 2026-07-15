"""Integration layer - the ONLY place allowed to talk to external services.

Every external platform (Canva, Instagram, TikTok, OpenAI, trend sources,
analytics) is wrapped by an *adapter* that implements a small, stable interface
defined here in terms of domain models. For each interface there are two
implementations:

* a **mock** adapter that simulates the backend deterministically, requiring no
  credentials, so the whole system is testable offline; and
* a **live** adapter that calls the real API.

Which one is used is decided purely by configuration
(``integrations.<name>.mode`` or the global ``integrations.default_mode``).
Swapping mock -> live is a config change only - no code elsewhere changes.

Use :func:`build_integrations` to construct the full, wired set from settings.
"""

from acis.integrations.base import IntegrationBundle, build_integrations
from acis.integrations.interfaces import (
    AnalyticsPort,
    CanvaPort,
    InstagramPort,
    LLMPort,
    TikTokPort,
    TrendSourcePort,
)

__all__ = [
    "AnalyticsPort",
    "CanvaPort",
    "InstagramPort",
    "IntegrationBundle",
    "LLMPort",
    "TikTokPort",
    "TrendSourcePort",
    "build_integrations",
]
