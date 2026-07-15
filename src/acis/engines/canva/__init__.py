"""Canva Automation Engine (Sprint 5).

Renders a :class:`~acis.domain.models.ContentPiece` into on-brand designs fully
automatically - no human ever edits a design. It computes a branded spec per
slide (dark palette background, white/grey text, strong-yellow accent reserved
for headings/numbers/key facts/CTA), enforces the accent-discipline brand rule,
then drives the Canva port to create and export the slides.

See ``docs/architecture/modules/canva-automation-engine.md`` and
``docs/branding.md``.
"""

from acis.engines.canva.engine import CanvaEngine, CanvaEngineConfig

__all__ = ["CanvaEngine", "CanvaEngineConfig"]
