"""End-to-end pipeline tests (Definition of Success)."""

from __future__ import annotations

import pytest

from acis.core.errors import NoViableTopicError, QualityGateError
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


def test_screening_runs_before_virality_and_research(context):
    """Screening must gate topics before virality scoring and deep research.

    We spy on the engines to assert the ordering: every surviving topic is
    screened, virality only ever sees screened topics, and research (deep) runs
    exactly once - for the selected winner.
    """
    pipeline = build_reference_pipeline(context)
    screened: list[str] = []
    ranked_inputs: list[int] = []
    researched: list[str] = []

    real_screen = pipeline.research.screen
    real_rank = pipeline.virality.rank
    real_research = pipeline.research.research

    def spy_screen(topic):
        screened.append(topic.id)
        return real_screen(topic)

    def spy_rank(topics):
        ranked_inputs.append(len(topics))
        return real_rank(topics)

    def spy_research(topic):
        researched.append(topic.id)
        return real_research(topic)

    pipeline.research.screen = spy_screen  # type: ignore[method-assign]
    pipeline.virality.rank = spy_rank  # type: ignore[method-assign]
    pipeline.research.research = spy_research  # type: ignore[method-assign]

    result = pipeline.run_once(publish=False)

    assert screened, "screening was not run"
    # Virality only scores the topics that passed screening.
    assert ranked_inputs and ranked_inputs[0] <= len(screened)
    # Deep research runs exactly once, for the selected topic.
    assert researched == [result.topic.id]


def test_no_viable_topic_when_screening_rejects_all(context, monkeypatch):
    """If nothing passes screening, the run aborts before any expensive work."""
    from acis.domain.models import SourceAvailability

    pipeline = build_reference_pipeline(context)

    def reject_all(topic):
        return SourceAvailability(topic_id=topic.id, source_count=0, sufficient=False)

    monkeypatch.setattr(pipeline.research, "screen", reject_all)
    with pytest.raises(NoViableTopicError):
        pipeline.run_once(publish=False)
