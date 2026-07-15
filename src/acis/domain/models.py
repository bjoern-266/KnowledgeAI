"""Domain models - the contracts passed between pipeline stages.

Each model is an immutable-ish pydantic object with a stable ``id`` so it can
be persisted and referenced across stages. The flow is:

    Trend ->(collect)-> Topic ->(score)-> Topic(+ViralityScore)
          ->(research)-> ResearchDossier ->(create)-> ContentPiece
          ->(design)-> DesignResult / VideoResult
          ->(quality)-> QualityReport ->(publish)-> PublishReceipt

Models never reference engines or integrations; they are pure data.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from acis.domain.enums import (
    ContentFormat,
    Platform,
    PublishStatus,
    QualityCheck,
    TopicCategory,
)


def _uuid() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    return datetime.now(tz=UTC)


class DomainModel(BaseModel):
    """Base for all domain entities."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    id: str = Field(default_factory=_uuid)
    created_at: datetime = Field(default_factory=_now)


# --------------------------------------------------------------------------- #
# Discovery
# --------------------------------------------------------------------------- #
class Trend(DomainModel):
    """A raw signal that something is gaining attention."""

    keyword: str
    source: str  # e.g. "google_trends", "tiktok"
    score: float = 0.0  # source-native popularity signal
    region: str = "global"
    category: TopicCategory | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Topic(DomainModel):
    """A concrete content idea derived from one or more trends."""

    title: str
    category: TopicCategory
    angle: str = ""  # the specific hook / framing
    source_trends: list[str] = Field(default_factory=list)  # Trend ids
    keywords: list[str] = Field(default_factory=list)
    #: Preliminary relevance from the Trend Intelligence Engine (momentum +
    #: evergreen weighting), used only for the initial candidate ranking. The
    #: Virality Engine later sets ``virality`` for the final scoring.
    relevance: float = 0.0
    virality: ViralityScore | None = None


class ViralityScore(BaseModel):
    """A topic's estimated share/save potential, produced by the Virality Engine."""

    model_config = ConfigDict(extra="forbid")

    value: float = Field(ge=0.0, le=1.0)  # normalised [0..1]
    components: dict[str, float] = Field(default_factory=dict)  # sub-scores
    rationale: str = ""


# --------------------------------------------------------------------------- #
# Research
# --------------------------------------------------------------------------- #
class Source(BaseModel):
    """A citation backing a fact."""

    model_config = ConfigDict(extra="forbid")

    url: str
    title: str = ""
    publisher: str = ""
    reliability: float = Field(default=0.5, ge=0.0, le=1.0)
    retrieved_at: datetime = Field(default_factory=_now)


class SourceAvailability(BaseModel):
    """Result of the cheap pre-research *screening* check.

    Produced by the Research Engine's ``screen`` before virality scoring. It only
    establishes whether a topic has enough credible sources to be worth pursuing;
    it does NOT extract or verify facts (that is the full ``research`` step).
    """

    model_config = ConfigDict(extra="forbid")

    topic_id: str
    source_count: int = 0
    sufficient: bool = False
    candidate_sources: list[Source] = Field(default_factory=list)
    reason: str = ""


class ResearchDossier(DomainModel):
    """Verified facts and sources gathered for a topic (full research output)."""

    topic_id: str
    summary: str = ""
    facts: list[str] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)

    @property
    def source_count(self) -> int:
        return len(self.sources)


# --------------------------------------------------------------------------- #
# Content
# --------------------------------------------------------------------------- #
class Slide(BaseModel):
    """A single carousel slide or video scene."""

    model_config = ConfigDict(extra="forbid")

    index: int
    headline: str = ""
    body: str = ""
    highlight: str = ""  # the key number/fact (accent-styled)
    notes: str = ""  # design/voiceover hints


class ContentPiece(DomainModel):
    """The written, structured content ready to be designed/rendered."""

    topic_id: str
    dossier_id: str
    platform: Platform
    content_format: ContentFormat
    hook: str = ""
    slides: list[Slide] = Field(default_factory=list)
    caption: str = ""
    hashtags: list[str] = Field(default_factory=list)
    cta: str = ""
    status: PublishStatus = PublishStatus.DRAFT


# --------------------------------------------------------------------------- #
# Design / rendering artifacts
# --------------------------------------------------------------------------- #
class Asset(BaseModel):
    """A produced file/URL artifact (image, video, export)."""

    model_config = ConfigDict(extra="forbid")

    kind: str  # "image" | "video" | "pdf" | ...
    uri: str  # local path or remote URL
    mime_type: str = ""
    width: int | None = None
    height: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DesignResult(DomainModel):
    """Output of the Canva Automation Engine for a content piece."""

    content_id: str
    design_id: str = ""  # external (Canva) design id
    assets: list[Asset] = Field(default_factory=list)


class VideoResult(DomainModel):
    """Output of the TikTok Video Engine."""

    content_id: str
    asset: Asset
    duration_seconds: float = 0.0


# --------------------------------------------------------------------------- #
# Quality & publishing
# --------------------------------------------------------------------------- #
class QualityReport(DomainModel):
    """Aggregated result of all quality gates for a content piece."""

    content_id: str
    scores: dict[QualityCheck, float] = Field(default_factory=dict)
    passed: bool = False
    threshold: float = 0.0
    issues: list[str] = Field(default_factory=list)

    @property
    def overall(self) -> float:
        return self.scores.get(QualityCheck.OVERALL_SCORE, 0.0)


class PublishReceipt(DomainModel):
    """Proof of a publish attempt (real or prepared/simulated)."""

    content_id: str
    platform: Platform
    status: PublishStatus
    external_id: str = ""  # post id from the platform
    url: str = ""
    detail: str = ""


# Resolve forward reference (Topic -> ViralityScore).
Topic.model_rebuild()
