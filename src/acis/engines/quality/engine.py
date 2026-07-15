"""Quality Engine implementation.

Four independent gates, each yielding a [0..1] sub-score:

* source_check   - enough credible sources (weighted by reliability).
* fact_check     - corroborated facts exist and every on-screen highlight traces
                   to one; overall research confidence.
* spelling_check - language/tone sanity (no empty/placeholder text, caption/tags).
* design_check   - assets present, brand-compliant, accent discipline, dark
                   palette, valid dimensions.

The gates are combined with configurable weights into OVERALL_SCORE. Content
passes only if the overall clears ``min_score`` AND no required gate has failed
outright (fail-closed). Everything is deterministic and offline.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from acis.core.base import Engine
from acis.domain.enums import QualityCheck
from acis.domain.models import Asset, ContentPiece, KnowledgeBase, QualityReport

_PLACEHOLDERS = ("[mock", "todo", "lorem", "placeholder", "tbd", "xxx")


@dataclass(frozen=True)
class QualityEngineConfig:
    min_score: float = 0.75
    min_sources: int = 2
    require_fact_check: bool = True
    require_source_check: bool = True
    require_spelling_check: bool = True
    require_design_check: bool = True
    weights: dict[str, float] = field(
        default_factory=lambda: {
            "fact": 0.35,
            "source": 0.25,
            "spelling": 0.15,
            "design": 0.25,
        }
    )
    allowed_accent_elements: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {"headings", "numbers", "statistics", "key_facts", "highlights", "cta"}
        )
    )
    dark_backgrounds: frozenset[str] = field(
        default_factory=lambda: frozenset({"#000000", "#1C1C1C", "#2B2B2B", "#333333"})
    )

    @classmethod
    def from_settings(cls, settings: object) -> QualityEngineConfig:
        quality = getattr(settings, "quality", None)
        branding = getattr(settings, "branding", None)
        kwargs: dict[str, object] = {}
        if quality is not None:
            kwargs.update(
                min_score=quality.min_score,
                min_sources=quality.min_sources_per_topic,
                require_fact_check=quality.require_fact_check,
                require_source_check=quality.require_source_check,
                require_spelling_check=quality.require_spelling_check,
                require_design_check=quality.require_design_check,
            )
        if branding is not None:
            accent_usage = list(getattr(branding, "accent_usage", []) or [])
            if accent_usage:
                kwargs["allowed_accent_elements"] = frozenset(accent_usage)
            palette = getattr(branding, "palette", None)
            backgrounds = list(getattr(palette, "background", []) or []) if palette else []
            if backgrounds:
                kwargs["dark_backgrounds"] = frozenset(backgrounds)
        return cls(**kwargs)  # type: ignore[arg-type]


class QualityEngine(Engine):
    """Scores content against fact/source/language/design gates before publishing."""

    name = "quality"

    def __init__(self, config: QualityEngineConfig | None = None) -> None:
        super().__init__()
        self._cfg = config or QualityEngineConfig()

    def evaluate(
        self, content: ContentPiece, knowledge: KnowledgeBase, assets: list[Asset]
    ) -> QualityReport:
        issues: list[str] = []
        source = self._source_check(knowledge, issues)
        fact = self._fact_check(content, knowledge, issues)
        spelling = self._spelling_check(content, issues)
        design = self._design_check(content, assets, issues)

        w = self._cfg.weights
        total = sum(w.values()) or 1.0
        overall = (
            w.get("fact", 0) * fact
            + w.get("source", 0) * source
            + w.get("spelling", 0) * spelling
            + w.get("design", 0) * design
        ) / total

        scores = {
            QualityCheck.SOURCE_CHECK: round(source, 3),
            QualityCheck.FACT_CHECK: round(fact, 3),
            QualityCheck.SPELLING_CHECK: round(spelling, 3),
            QualityCheck.DESIGN_CHECK: round(design, 3),
            QualityCheck.OVERALL_SCORE: round(overall, 3),
        }
        passed = self._passed(overall, scores)
        if not passed and "below threshold" not in issues and overall < self._cfg.min_score:
            issues.append(f"overall {overall:.2f} < {self._cfg.min_score:.2f}")

        self.log.info(
            "quality.evaluated",
            content_id=content.id,
            overall=scores[QualityCheck.OVERALL_SCORE],
            passed=passed,
            issues=len(issues),
        )
        return QualityReport(
            content_id=content.id,
            scores=scores,
            threshold=self._cfg.min_score,
            passed=passed,
            issues=issues,
        )

    # -- gates ----------------------------------------------------------------
    def _source_check(self, knowledge: KnowledgeBase, issues: list[str]) -> float:
        if knowledge.source_count < self._cfg.min_sources:
            issues.append("insufficient sources")
            return 0.0
        weights = [s.weight() for s in knowledge.sources]
        return round(sum(weights) / len(weights), 3) if weights else 0.0

    def _fact_check(
        self, content: ContentPiece, knowledge: KnowledgeBase, issues: list[str]
    ) -> float:
        corroborated = {f.statement for f in knowledge.facts if not f.uncertain}
        if not corroborated:
            issues.append("no corroborated facts")
            return 0.0
        # Every highlighted fact (beyond the editorial cover hook) must be backed.
        unbacked = [
            s.index
            for s in content.slides
            if s.highlight and s.index != 0 and s.highlight not in corroborated
        ]
        score = knowledge.confidence
        if unbacked:
            issues.append(f"unbacked highlights on slides {unbacked}")
            score *= 0.5
        return round(score, 3)

    def _spelling_check(self, content: ContentPiece, issues: list[str]) -> float:
        score = 1.0
        content_slides = [s for s in content.slides if s.notes not in ("cover slide", "cta slide")]
        if any(not s.headline or not s.body for s in content_slides):
            issues.append("empty slide text")
            score -= 0.3
        texts = " ".join(f"{s.headline} {s.body} {s.highlight}" for s in content.slides).lower()
        texts += " " + content.caption.lower()
        if any(marker in texts for marker in _PLACEHOLDERS):
            issues.append("placeholder text present")
            score -= 0.5
        if not content.caption:
            issues.append("empty caption")
            score -= 0.2
        if not content.hashtags:
            issues.append("no hashtags")
            score -= 0.1
        return round(max(0.0, score), 3)

    def _design_check(self, content: ContentPiece, assets: list[Asset], issues: list[str]) -> float:
        if not assets:
            issues.append("no design assets")
            return 0.0
        if len(assets) < len(content.slides):
            issues.append("fewer assets than slides")
        allowed = self._cfg.allowed_accent_elements
        dark = self._cfg.dark_backgrounds
        ok = 0
        for asset in assets:
            meta = asset.metadata
            compliant = bool(meta.get("brand_compliant"))
            accent_ok = set(meta.get("accent_elements", [])) <= allowed
            bg_ok = (not dark) or meta.get("background") in dark
            dims_ok = asset.width is not None and asset.height is not None
            if compliant and accent_ok and bg_ok and dims_ok:
                ok += 1
        if ok < len(assets):
            issues.append(f"{len(assets) - ok} off-brand assets")
        return round(ok / len(assets), 3)

    # -- verdict --------------------------------------------------------------
    def _passed(self, overall: float, scores: dict[QualityCheck, float]) -> bool:
        if overall < self._cfg.min_score:
            return False
        # Fail-closed: a required gate scoring zero blocks publishing outright.
        if self._cfg.require_source_check and scores[QualityCheck.SOURCE_CHECK] <= 0.0:
            return False
        if self._cfg.require_fact_check and scores[QualityCheck.FACT_CHECK] <= 0.0:
            return False
        return not (self._cfg.require_design_check and scores[QualityCheck.DESIGN_CHECK] <= 0.0)
