"""Canva Automation Engine implementation.

Flow:

    content -> per-slide branded spec (background / text / accent elements)
            -> brand-compliance check (accent only on allowed elements)
            -> canva.create_design(content)   # autofill the branded template
            -> enrich each exported asset with its brand metadata
            -> DesignResult

The accent-discipline rule is enforced here: strong yellow may style only
headings, numbers, statistics, key facts, highlights and CTAs. If a spec would
apply the accent anywhere else the engine raises ``ValidationError`` rather than
shipping an off-brand design. The metadata attached to each asset lets the
Quality Engine's design gate verify compliance later.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from acis.core.base import Engine
from acis.core.errors import ValidationError
from acis.domain.models import Asset, ContentPiece, DesignResult, Slide
from acis.integrations.interfaces import CanvaPort

# Canonical accent element types (mirrors branding.accent_usage).
_HEADINGS = "headings"
_HIGHLIGHTS = "highlights"
_CTA = "cta"


@dataclass(frozen=True)
class CanvaEngineConfig:
    """Branding parameters for automated design."""

    # Dark palette: [0] is the cover background; [1:] rotate across content slides.
    backgrounds: list[str] = field(
        default_factory=lambda: ["#000000", "#1C1C1C", "#2B2B2B", "#333333"]
    )
    text_primary: str = "#FFFFFF"
    text_secondary: str = "#B0B0B0"
    accent: str = "#FFD400"
    allowed_accent_elements: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {"headings", "numbers", "statistics", "key_facts", "highlights", "cta"}
        )
    )
    export_format: str = "png"

    @classmethod
    def from_branding(cls, branding: object) -> CanvaEngineConfig:
        """Build from ``settings.branding`` (duck-typed to stay decoupled)."""
        palette = getattr(branding, "palette", None)
        backgrounds = list(getattr(palette, "background", []) or []) if palette else []
        accent_usage = list(getattr(branding, "accent_usage", []) or [])
        kwargs: dict[str, object] = {}
        if backgrounds:
            kwargs["backgrounds"] = backgrounds
        if palette is not None:
            kwargs["text_primary"] = getattr(palette, "text_primary", cls.text_primary)
            kwargs["text_secondary"] = getattr(palette, "text_secondary", cls.text_secondary)
            kwargs["accent"] = getattr(palette, "accent", cls.accent)
        if accent_usage:
            kwargs["allowed_accent_elements"] = frozenset(accent_usage)
        return cls(**kwargs)  # type: ignore[arg-type]


class CanvaEngine(Engine):
    """Automated, on-brand design creation and export via the Canva port."""

    name = "canva_automation"

    def __init__(self, canva: CanvaPort, config: CanvaEngineConfig | None = None) -> None:
        super().__init__()
        self._canva = canva
        self._cfg = config or CanvaEngineConfig()

    def design(self, content: ContentPiece) -> DesignResult:
        specs = [
            self._slide_spec(slide, i, len(content.slides))
            for i, slide in enumerate(content.slides)
        ]
        self._validate_accent(specs)

        design = self._canva.create_design(content)
        assets = self._apply_branding(design.assets, specs)

        result = DesignResult(content_id=content.id, design_id=design.design_id, assets=assets)
        self.log.info(
            "canva.designed",
            content_id=content.id,
            design_id=design.design_id,
            assets=len(assets),
            accent=self._cfg.accent,
        )
        return result

    # -- branding -------------------------------------------------------------
    def _background_for(self, index: int) -> str:
        bg = self._cfg.backgrounds
        if not bg:
            return "#000000"
        if index == 0:
            return bg[0]
        rotation = bg[1:] or bg
        return rotation[(index - 1) % len(rotation)]

    def _slide_spec(self, slide: Slide, index: int, total: int) -> dict:
        accent_elements: list[str] = []
        is_cover = index == 0
        is_cta = slide.notes == "cta slide" or index == total - 1
        if is_cover:
            accent_elements.append(_HEADINGS)  # the title/hook headline
        if slide.highlight:
            accent_elements.append(_HIGHLIGHTS)  # the key number/fact
        if is_cta:
            accent_elements.append(_CTA)
        return {
            "slide_index": index,
            "background": self._background_for(index),
            "text_primary": self._cfg.text_primary,
            "text_secondary": self._cfg.text_secondary,
            "accent": self._cfg.accent,
            "accent_elements": accent_elements,
        }

    def _validate_accent(self, specs: list[dict]) -> None:
        allowed = self._cfg.allowed_accent_elements
        violations = [
            (spec["slide_index"], el)
            for spec in specs
            for el in spec["accent_elements"]
            if el not in allowed
        ]
        if violations:
            raise ValidationError(
                "Accent colour applied to non-allowed elements",
                context={"violations": violations, "allowed": sorted(allowed)},
            )

    def _apply_branding(self, assets: list[Asset], specs: list[dict]) -> list[Asset]:
        by_index = {spec["slide_index"]: spec for spec in specs}
        branded: list[Asset] = []
        for i, asset in enumerate(assets):
            spec = by_index.get(asset.metadata.get("slide_index", i), {})
            metadata = {**asset.metadata, **spec, "brand_compliant": True}
            branded.append(asset.model_copy(update={"metadata": metadata}))
        return branded
