"""End-to-end pipeline tests (Definition of Success)."""

from __future__ import annotations

import pytest

from acis.core.errors import QualityGateError
from acis.domain.enums import PublishStatus
from acis.reference import build_reference_pipeline


def test_full_run_produces_all_artifacts(context):
    """The system autonomously selects a topic, researches, creates a carousel,
    designs it, derives a TikTok video, and publishes - all in mock mode."""
    pipeline = build_reference_pipeline(context)
    result = pipeline.run_once(publish=True)

    # A topic was chosen autonomously.
    assert result.topic.title
    assert result.topic.virality is not None

    # Research gathered multiple sources.
    assert result.dossier.source_count >= 2

    # An Instagram carousel exists.
    assert len(result.content.slides) >= 3

    # A design was produced with one asset per slide.
    assert result.design.design_id
    assert len(result.design.assets) == len(result.content.slides)

    # A TikTok video was derived.
    assert result.video.asset.kind == "video"

    # Quality gate passed and content was published.
    assert result.quality.passed
    assert result.receipts
    assert result.receipts[0].status is PublishStatus.PUBLISHED
    assert result.metrics  # analytics collected


def test_quality_gate_blocks_publish_when_threshold_high(settings):
    """Content below the min score must never be published."""
    from acis.core.context import AppContext
    from acis.data.memory import InMemoryRepository
    from acis.integrations.base import build_integrations

    strict_quality = settings.quality.model_copy(update={"min_score": 1.01})
    strict = settings.model_copy(update={"quality": strict_quality})
    ctx = AppContext(
        strict, repository=InMemoryRepository(), integrations=build_integrations(strict)
    )
    ctx.startup()
    try:
        pipeline = build_reference_pipeline(ctx)
        with pytest.raises(QualityGateError):
            pipeline.run_once(publish=True)
    finally:
        ctx.shutdown()


def test_run_without_publish_skips_platforms(context):
    pipeline = build_reference_pipeline(context)
    result = pipeline.run_once(publish=False)
    assert result.receipts == []
    assert result.metrics == {}
