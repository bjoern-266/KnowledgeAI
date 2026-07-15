"""Mock Canva adapter.

Simulates automated design creation and export against the brand system
(black/anthracite/graphite/carbon with a single strong-yellow accent). Produces
deterministic local ``Asset`` references (no files written) so the pipeline can
run end-to-end offline.
"""

from __future__ import annotations

from acis.core.config import IntegrationMode
from acis.integrations.base import IntegrationAdapter


class MockCanva(IntegrationAdapter):
    integration = "canva"

    def __init__(self, config: dict | None = None) -> None:
        super().__init__(IntegrationMode.MOCK, config)

    def create_design(self, content):  # type: ignore[no-untyped-def]
        from acis.domain.models import Asset, DesignResult

        design_id = f"mock-design-{content.id[:8]}"
        assets = [
            Asset(
                kind="image",
                uri=f"mock://canva/{design_id}/slide-{slide.index}.png",
                mime_type="image/png",
                width=1080,
                height=1350,
                metadata={"slide_index": slide.index, "accent": "#FFD400"},
            )
            for slide in content.slides
        ]
        self.log.debug("mock.create_design", design_id=design_id, slides=len(assets))
        return DesignResult(content_id=content.id, design_id=design_id, assets=assets)

    def export(self, design_id: str, *, fmt: str = "png"):  # type: ignore[no-untyped-def]
        from acis.domain.models import Asset

        return [
            Asset(
                kind="image",
                uri=f"mock://canva/{design_id}/export.{fmt}",
                mime_type=f"image/{fmt}",
            )
        ]
