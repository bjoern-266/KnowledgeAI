"""Domain models - the contracts passed between pipeline stages.

Each model is an immutable-ish pydantic object with a stable ``id`` so it can
be persisted and referenced across stages. The flow is:

    Trend ->(collect)-> Topic ->(screen)-> SourceAvailability
          ->(score)-> Topic(+ViralityScore) ->(research)-> KnowledgeBase
          ->(create)-> ContentPiece ->(design)-> DesignResult / VideoResult
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
    FactType,
    HookType,
    Platform,
    PublishStatus,
    QualityCheck,
    SourceType,
    TopicCategory,
    VisualType,
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
    """A citation backing a fact, with the metadata needed to weight it.

    ``weight`` combines credibility, recency, primary-vs-secondary, and
    scientific standing into a single [0..1] score the Research/Quality engines
    use when deciding how much to trust a claim.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=_uuid)
    url: str
    title: str = ""
    publisher: str = ""
    institution: str = ""
    #: Credibility of the source itself [0..1] (tier-based, see CONTENT_INTELLIGENCE §2).
    reliability: float = Field(default=0.5, ge=0.0, le=1.0)
    source_type: SourceType = SourceType.SECONDARY
    scientific: bool = False
    published_at: datetime | None = None  # when the source was published (for recency)
    retrieved_at: datetime = Field(default_factory=_now)

    def weight(self, *, recency_years: float = 5.0) -> float:
        """Combined trust weight in [0..1]."""
        score = self.reliability
        if self.source_type is SourceType.PRIMARY:
            score += 0.10
        if self.scientific:
            score += 0.05
        if self.published_at is not None:
            age_years = (_now() - self.published_at).days / 365.25
            score += 0.05 if age_years <= recency_years else -0.05
        return max(0.0, min(1.0, round(score, 4)))


class RetrievedDocument(BaseModel):
    """A document returned by a research source adapter (retrieval layer).

    Carries source metadata plus candidate claim ``snippets`` extracted verbatim
    from the document. The Research Engine may only build facts from these
    snippets - never from the LLM's own knowledge (no-hallucination rule).
    """

    model_config = ConfigDict(extra="forbid")

    url: str
    title: str = ""
    publisher: str = ""
    institution: str = ""
    reliability: float = Field(default=0.5, ge=0.0, le=1.0)
    source_type: SourceType = SourceType.SECONDARY
    scientific: bool = False
    published_at: datetime | None = None
    snippets: list[str] = Field(default_factory=list)

    def to_source(self) -> Source:
        return Source(
            url=self.url,
            title=self.title,
            publisher=self.publisher,
            institution=self.institution,
            reliability=self.reliability,
            source_type=self.source_type,
            scientific=self.scientific,
            published_at=self.published_at,
        )


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


class Fact(DomainModel):
    """A single typed, source-backed fact with a confidence score."""

    topic_id: str
    statement: str
    fact_type: FactType = FactType.KEY_CLAIM
    #: 0-100. Scales with number of corroborating sources and their weight.
    confidence: int = Field(default=0, ge=0, le=100)
    source_ids: list[str] = Field(default_factory=list)
    #: Which visual treatments suit this fact (drives the Canva Engine).
    visual_potential: list[VisualType] = Field(default_factory=list)
    #: True when not clearly corroborated - flagged, never dropped silently.
    uncertain: bool = False
    notes: str = ""

    @property
    def supporting_sources(self) -> int:
        return len(self.source_ids)


class Statistic(DomainModel):
    """A numeric fact broken out for easy charting."""

    topic_id: str
    label: str
    value: str  # kept as text to preserve units/precision, e.g. "3.2 billion"
    unit: str = ""
    as_of: str = ""  # the point in time the figure refers to
    source_ids: list[str] = Field(default_factory=list)
    confidence: int = Field(default=0, ge=0, le=100)


class TimelineEntry(DomainModel):
    """A dated event, broken out for timeline visuals."""

    topic_id: str
    when: str  # human date/period, e.g. "1912" or "3rd century BCE"
    label: str
    description: str = ""
    source_ids: list[str] = Field(default_factory=list)
    confidence: int = Field(default=0, ge=0, le=100)


class Definition(DomainModel):
    """A term and its meaning, broken out for infobox visuals."""

    topic_id: str
    term: str
    definition: str
    source_ids: list[str] = Field(default_factory=list)
    confidence: int = Field(default=0, ge=0, le=100)


class HookCandidate(DomainModel):
    """A ready-to-use opening hook detected during research."""

    topic_id: str
    hook_type: HookType
    text: str
    fact_id: str = ""
    strength: int = Field(default=0, ge=0, le=100)


class VisualIdea(DomainModel):
    """A concrete slide/graphic suggestion for the Canva Engine."""

    topic_id: str
    visual_type: VisualType
    description: str
    fact_ids: list[str] = Field(default_factory=list)
    priority: int = Field(default=50, ge=0, le=100)


class KnowledgeBase(DomainModel):
    """The structured knowledge object produced by the Research Engine.

    This is NOT free text or a list of search hits: it is a typed dataset that
    later engines consume directly. The Content Engine never researches on its
    own - it draws entirely from this object. Everything here traces back to a
    retrieved source; anything not corroborated is flagged in ``uncertainties``
    or marked ``uncertain`` on the fact, never invented.
    """

    topic_id: str
    summary: str = ""
    key_claims: list[str] = Field(default_factory=list)
    facts: list[Fact] = Field(default_factory=list)
    statistics: list[Statistic] = Field(default_factory=list)
    timeline: list[TimelineEntry] = Field(default_factory=list)
    definitions: list[Definition] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)
    hook_candidates: list[HookCandidate] = Field(default_factory=list)
    visual_ideas: list[VisualIdea] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    #: Overall confidence in the knowledge base [0..1].
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    @property
    def source_count(self) -> int:
        return len(self.sources)

    @property
    def fact_count(self) -> int:
        return len(self.facts)

    @property
    def charts(self) -> list[VisualIdea]:
        return [v for v in self.visual_ideas if v.visual_type is VisualType.CHART]

    @property
    def images(self) -> list[VisualIdea]:
        return [v for v in self.visual_ideas if v.visual_type is VisualType.IMAGE]


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
    visual: VisualType | None = None  # suggested treatment (from research visual potential)
    source_ids: list[str] = Field(default_factory=list)  # provenance for this slide's fact


class ScriptScene(BaseModel):
    """One scene of the derived TikTok script."""

    model_config = ConfigDict(extra="forbid")

    index: int
    on_screen: str = ""  # short on-screen text
    voiceover: str = ""  # narration / spoken line
    seconds: float = 3.0
    visual: VisualType | None = None
    source_ids: list[str] = Field(default_factory=list)


class ContentPiece(DomainModel):
    """The written, structured content ready to be designed/rendered.

    Carries the primary Instagram carousel (``slides``) and the derived TikTok
    ``script`` - both produced from the same KnowledgeBase so one research effort
    yields both formats. Design/rendering happen later (Canva / TikTok engines).
    """

    topic_id: str
    knowledge_id: str
    platform: Platform
    content_format: ContentFormat
    hook: str = ""
    slides: list[Slide] = Field(default_factory=list)
    script: list[ScriptScene] = Field(default_factory=list)  # derived TikTok scenes
    caption: str = ""
    hashtags: list[str] = Field(default_factory=list)
    cta: str = ""
    status: PublishStatus = PublishStatus.DRAFT

    @property
    def script_seconds(self) -> float:
        return round(sum(s.seconds for s in self.script), 1)


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
