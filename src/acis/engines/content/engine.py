"""Content Engine implementation.

Builds an Instagram carousel and a derived TikTok script from the KnowledgeBase:

    hook (from research hook_candidates)
      -> title slide + one slide per corroborated fact + CTA slide
      -> TikTok script scenes (hook -> beats -> CTA), timed to a target length
      -> caption + hashtags + CTA

Only corroborated (non-uncertain) facts are used, and each fact's strongest
visual potential is attached to its slide/scene so the Canva and TikTok engines
need no extra analysis. Nothing is invented here - the engine never researches.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from acis.core.base import Engine
from acis.domain.enums import ContentFormat, FactType, Platform, PublishStatus, VisualType
from acis.domain.models import (
    ContentPiece,
    Fact,
    KnowledgeBase,
    ScriptScene,
    Slide,
    Topic,
)

# Fact types whose statement is a "key number/fact" and should be accent-styled.
_HIGHLIGHT_TYPES = {FactType.STATISTIC, FactType.RECORD}
_WORD = re.compile(r"[A-Za-z0-9]+")


def _hashtagify(text: str) -> str:
    return "#" + "".join(w.capitalize() for w in _WORD.findall(text))[:30]


@dataclass(frozen=True)
class ContentEngineConfig:
    """Tuning parameters for the Content Engine."""

    carousel_slides: int = 8  # total slides incl. title + CTA
    max_hashtags: int = 8
    tiktok_target_seconds: float = 25.0
    tiktok_max_beats: int = 5
    cta_text: str = "Save this for later — and follow for more."

    @classmethod
    def from_settings(cls, carousel_slides: int, **kw: object) -> ContentEngineConfig:
        return cls(carousel_slides=carousel_slides, **kw)  # type: ignore[arg-type]


class ContentEngine(Engine):
    """Turns a KnowledgeBase into a carousel + TikTok script."""

    name = "content"

    def __init__(self, config: ContentEngineConfig | None = None) -> None:
        super().__init__()
        self._cfg = config or ContentEngineConfig()

    def create(self, topic: Topic, knowledge: KnowledgeBase) -> ContentPiece:
        facts = [f for f in knowledge.facts if not f.uncertain]  # verified only
        hook = knowledge.hook_candidates[0].text if knowledge.hook_candidates else topic.angle

        slides = self._build_slides(topic, knowledge, facts, hook)
        script = self._build_script(topic, facts, hook)
        piece = ContentPiece(
            topic_id=topic.id,
            knowledge_id=knowledge.id,
            platform=Platform.INSTAGRAM,
            content_format=ContentFormat.INSTAGRAM_CAROUSEL,
            hook=hook,
            slides=slides,
            script=script,
            caption=self._caption(topic, knowledge, hook),
            hashtags=self._hashtags(topic),
            cta=self._cfg.cta_text,
            status=PublishStatus.DRAFT,
        )
        self.log.info(
            "content.created",
            topic=topic.title,
            slides=len(slides),
            scenes=len(script),
            seconds=piece.script_seconds,
        )
        return piece

    # -- carousel -------------------------------------------------------------
    def _build_slides(
        self, topic: Topic, knowledge: KnowledgeBase, facts: list[Fact], hook: str
    ) -> list[Slide]:
        slides = [
            Slide(
                index=0,
                headline=topic.title,
                body=hook,
                highlight=hook,
                notes="cover slide",
                visual=VisualType.IMAGE,
            )
        ]
        for i, fact in enumerate(facts[: self._cfg.carousel_slides - 2], start=1):
            highlight = fact.statement if fact.fact_type in _HIGHLIGHT_TYPES else ""
            slides.append(
                Slide(
                    index=i,
                    headline=fact.fact_type.value.replace("_", " ").title(),
                    body=fact.statement,
                    highlight=highlight,
                    visual=fact.visual_potential[0] if fact.visual_potential else None,
                    source_ids=fact.source_ids,
                )
            )
        slides.append(
            Slide(
                index=len(slides),
                headline="Save & share",
                body=self._cfg.cta_text,
                notes="cta slide",
                visual=VisualType.INFOBOX,
            )
        )
        return slides

    # -- tiktok script --------------------------------------------------------
    def _build_script(self, topic: Topic, facts: list[Fact], hook: str) -> list[ScriptScene]:
        beats = facts[: self._cfg.tiktok_max_beats]
        # Reserve time for hook + CTA, split the rest across beats.
        hook_s, cta_s = 3.0, 3.0
        body_budget = max(1.0, self._cfg.tiktok_target_seconds - hook_s - cta_s)
        per_beat = round(body_budget / max(1, len(beats)), 1)

        scenes = [ScriptScene(index=0, on_screen=topic.title, voiceover=hook, seconds=hook_s)]
        for i, fact in enumerate(beats, start=1):
            scenes.append(
                ScriptScene(
                    index=i,
                    on_screen=fact.statement if fact.fact_type in _HIGHLIGHT_TYPES else "",
                    voiceover=fact.statement,
                    seconds=per_beat,
                    visual=fact.visual_potential[0] if fact.visual_potential else None,
                    source_ids=fact.source_ids,
                )
            )
        scenes.append(
            ScriptScene(
                index=len(scenes),
                on_screen="Follow for more",
                voiceover=self._cfg.cta_text,
                seconds=cta_s,
            )
        )
        return scenes

    # -- caption / hashtags ---------------------------------------------------
    def _caption(self, topic: Topic, knowledge: KnowledgeBase, hook: str) -> str:
        lead = hook or knowledge.summary
        return f"{lead}\n\nHere's what the evidence actually says 👇 Sources in comments."

    def _hashtags(self, topic: Topic) -> list[str]:
        tags = ["#knowledge", "#didyouknow", _hashtagify(topic.category.value)]
        for keyword in topic.keywords:
            tag = _hashtagify(keyword)
            if tag not in tags:
                tags.append(tag)
        return tags[: self._cfg.max_hashtags]
