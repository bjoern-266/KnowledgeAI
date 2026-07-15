"""Adapter base class and the integration factory.

``IntegrationAdapter`` is the common base for every adapter (mock or live). It
stores its resolved :class:`IntegrationMode` and a config bag, exposes a
credential-validation hook, and - crucially - guarantees that a *live* adapter
refuses to start without its required credentials, while a *mock* adapter never
needs any.

:func:`build_integrations` reads :class:`Settings`, resolves each integration's
mode, and returns a fully wired :class:`IntegrationBundle`. This is the single
seam where mock/live selection happens.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from acis.core.base import BaseAdapter, HealthStatus
from acis.core.config import IntegrationMode, Settings
from acis.core.errors import MissingCredentialError
from acis.integrations.interfaces import (
    AnalyticsPort,
    CanvaPort,
    InstagramPort,
    LLMPort,
    ResearchSourcePort,
    TikTokPort,
    TrendSourcePort,
)


class IntegrationAdapter(BaseAdapter):
    """Base class shared by all mock and live adapters."""

    #: Integration key, e.g. "canva". Set by subclasses.
    integration: str = "integration"
    #: Credential keys a *live* adapter needs. Mock adapters ignore these.
    required_credentials: tuple[str, ...] = ()

    def __init__(self, mode: IntegrationMode, config: dict[str, Any] | None = None) -> None:
        self.name = f"{self.integration}:{mode.value}"
        super().__init__()
        self.mode = mode
        self.config = config or {}

    @property
    def is_live(self) -> bool:
        return self.mode is IntegrationMode.LIVE

    def missing_credentials(self) -> list[str]:
        """Return required credential keys that are absent or empty."""
        return [key for key in self.required_credentials if not self.config.get(key)]

    def validate_credentials(self) -> None:
        """Raise if a live adapter is missing required credentials."""
        if not self.is_live:
            return
        missing = self.missing_credentials()
        if missing:
            raise MissingCredentialError(
                f"Integration '{self.integration}' is in live mode but missing "
                f"credentials: {', '.join(missing)}",
                context={"integration": self.integration, "missing": missing},
            )

    def _on_setup(self) -> None:
        self.validate_credentials()

    def health_check(self) -> HealthStatus:
        if self.is_live and self.missing_credentials():
            return HealthStatus.down("missing credentials", missing=self.missing_credentials())
        return HealthStatus.ok(mode=self.mode.value)


@dataclass
class IntegrationBundle:
    """The complete set of integration ports the application uses."""

    trends: TrendSourcePort
    research: ResearchSourcePort
    llm: LLMPort
    canva: CanvaPort
    instagram: InstagramPort
    tiktok: TikTokPort
    analytics: AnalyticsPort

    def adapters(self) -> list[IntegrationAdapter]:
        """All adapters as components (for lifecycle management)."""
        return [
            a
            for a in (
                self.trends,
                self.research,
                self.llm,
                self.canva,
                self.instagram,
                self.tiktok,
                self.analytics,
            )
            if isinstance(a, IntegrationAdapter)
        ]

    def setup_all(self) -> None:
        for adapter in self.adapters():
            adapter.setup()

    def teardown_all(self) -> None:
        for adapter in self.adapters():
            adapter.teardown()


def _config_for(settings: Settings, name: str) -> dict[str, Any]:
    """Extract an integration's raw config as a plain dict."""
    integration = getattr(settings.integrations, name, None)
    if integration is None:
        return {}
    data = integration.model_dump()
    data.pop("mode", None)
    return data


def build_integrations(settings: Settings) -> IntegrationBundle:
    """Construct every adapter in the mode dictated by configuration."""
    # Local imports avoid import cycles and keep vendor code lazy.
    from acis.integrations.analytics.factory import build_analytics
    from acis.integrations.canva.factory import build_canva
    from acis.integrations.instagram.factory import build_instagram
    from acis.integrations.openai.factory import build_llm
    from acis.integrations.research.factory import build_research_source
    from acis.integrations.tiktok.factory import build_tiktok
    from acis.integrations.trends.factory import build_trends

    resolve = settings.integrations.resolve_mode
    return IntegrationBundle(
        trends=build_trends(resolve("trends"), _config_for(settings, "trends")),
        research=build_research_source(resolve("research"), _config_for(settings, "research")),
        llm=build_llm(resolve("openai"), _config_for(settings, "openai")),
        canva=build_canva(resolve("canva"), _config_for(settings, "canva")),
        instagram=build_instagram(resolve("instagram"), _config_for(settings, "instagram")),
        tiktok=build_tiktok(resolve("tiktok"), _config_for(settings, "tiktok")),
        analytics=build_analytics(resolve("analytics"), _config_for(settings, "analytics")),
    )
