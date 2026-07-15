"""Research Engine implementation.

Two operations (ADR-0005):

* ``screen(topic)``  - cheap: are there enough credible sources? -> SourceAvailability
* ``research(topic)`` - full: retrieve -> cross-verify -> type -> score -> KnowledgeBase

The engine builds facts ONLY from retrieved document snippets. Classification,
confidence, visual potential, hooks and the structured sub-lists are derived by
deterministic heuristics so the whole thing runs offline and reproducibly. An
LLM may later polish the summary, but must never introduce new claims.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from acis.core.base import Engine
from acis.data.repository import Repository
from acis.domain.enums import FactType, HookType, VisualType
from acis.domain.models import (
    Definition,
    Fact,
    HookCandidate,
    KnowledgeBase,
    RetrievedDocument,
    Source,
    SourceAvailability,
    Statistic,
    TimelineEntry,
    Topic,
    VisualIdea,
)
from acis.integrations.interfaces import ResearchSourcePort

_YEAR = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\b")
_NUMBER = re.compile(r"\d[\d,\.]*\s?(%|percent|billion|million|thousand|km|kg|°c|years)?", re.I)
_HEDGES = ("could", "may", "might", "suggest", "limited", "unclear", "possibly", "estimated")
_MAP_HINTS = ("map", "region", "country", "located", "border", "continent", "ocean")

_STOPWORDS = frozenset({"the", "a", "an", "of", "and", "or", "in", "to", "is", "was", "for", "on"})


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in _STOPWORDS}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _classify(statement: str) -> FactType:
    s = statement.lower()
    if '"' in statement or "“" in statement:
        return FactType.QUOTE
    if "contrary to" in s or "myth" in s or "misconception" in s or "popular belief" in s:
        return FactType.MYTH
    if "holds the record" in s or "record for" in s or "largest" in s or "smallest" in s:
        return FactType.RECORD
    if "defined as" in s or "refers to" in s or "is the term" in s:
        return FactType.DEFINITION
    if _YEAR.search(statement):
        return FactType.HISTORICAL_EVENT
    if "%" in s or "percent" in s or re.search(r"\d", s):
        return FactType.STATISTIC
    if "caused by" in s:
        return FactType.EFFECT
    if "causes" in s or "leads to" in s or "because" in s:
        return FactType.CAUSE
    if "compared to" in s or " than " in s:
        return FactType.COMPARISON
    if "warning" in s or "risk" in s or "danger" in s:
        return FactType.WARNING
    return FactType.KEY_CLAIM


_VISUALS: dict[FactType, list[VisualType]] = {
    FactType.STATISTIC: [VisualType.CHART, VisualType.INFOBOX],
    FactType.HISTORICAL_EVENT: [VisualType.TIMELINE],
    FactType.DATE: [VisualType.TIMELINE],
    FactType.DEFINITION: [VisualType.INFOBOX],
    FactType.RECORD: [VisualType.INFOBOX, VisualType.CHART],
    FactType.COMPARISON: [VisualType.BEFORE_AFTER, VisualType.CHART],
    FactType.MYTH: [VisualType.BEFORE_AFTER, VisualType.INFOBOX],
    FactType.CAUSE: [VisualType.INFOBOX],
    FactType.EFFECT: [VisualType.INFOBOX],
    FactType.QUOTE: [VisualType.INFOBOX],
    FactType.WARNING: [VisualType.INFOBOX],
    FactType.KEY_CLAIM: [VisualType.IMAGE],
}


def _visuals_for(fact_type: FactType, statement: str) -> list[VisualType]:
    visuals = list(_VISUALS.get(fact_type, [VisualType.IMAGE]))
    if any(h in statement.lower() for h in _MAP_HINTS) and VisualType.MAP not in visuals:
        visuals.append(VisualType.MAP)
    return visuals


@dataclass(frozen=True)
class ResearchEngineConfig:
    """Tuning parameters for the Research Engine."""

    min_sources: int = 2  # screening threshold (usually quality.min_sources_per_topic)
    screen_limit: int = 5  # docs to pull during the cheap screen
    max_documents: int = 12  # docs to pull during deep research
    similarity_threshold: float = 0.6  # token-Jaccard to treat two claims as one
    recency_years: float = 5.0
    max_key_claims: int = 5

    @classmethod
    def from_settings(cls, min_sources: int, **kw: object) -> ResearchEngineConfig:
        return cls(min_sources=min_sources, **kw)  # type: ignore[arg-type]


class _Cluster:
    """A group of corroborating claim occurrences (one candidate fact)."""

    def __init__(self, statement: str, source: Source) -> None:
        self.tokens = _tokens(statement)
        # Keep the statement from the highest-weight source as representative.
        self.best_statement = statement
        self.best_weight = source.weight()
        self.source_ids: set[str] = {source.id}

    def add(self, statement: str, source: Source) -> None:
        self.source_ids.add(source.id)
        weight = source.weight()
        if weight > self.best_weight:
            self.best_statement = statement
            self.best_weight = weight


class ResearchEngine(Engine):
    """Turns retrieved documents into a structured, source-grounded KnowledgeBase."""

    name = "research"

    def __init__(
        self,
        sources: Sequence[ResearchSourcePort],
        repository: Repository,
        config: ResearchEngineConfig,
    ) -> None:
        super().__init__()
        self._sources = list(sources)
        self._repo = repository
        self._cfg = config

    # -- retrieval ------------------------------------------------------------
    def _gather(self, query: str, limit: int) -> list[RetrievedDocument]:
        docs: list[RetrievedDocument] = []
        seen: set[str] = set()
        for source in self._sources:
            try:
                for doc in source.search(query, limit=limit):
                    if doc.url not in seen:
                        seen.add(doc.url)
                        docs.append(doc)
            except Exception:  # noqa: BLE001 - one bad source must not kill research
                self.log.exception("research.source_failed")
        return docs

    # -- screen (cheap) -------------------------------------------------------
    def screen(self, topic: Topic) -> SourceAvailability:
        docs = self._gather(topic.title, self._cfg.screen_limit)
        credible = [d for d in docs if d.reliability >= 0.5]
        count = len(credible)
        sufficient = count >= self._cfg.min_sources
        self.log.info("research.screen", topic=topic.title, sources=count, sufficient=sufficient)
        return SourceAvailability(
            topic_id=topic.id,
            source_count=count,
            sufficient=sufficient,
            candidate_sources=[d.to_source() for d in credible],
            reason="" if sufficient else "insufficient credible sources",
        )

    # -- research (deep) ------------------------------------------------------
    def research(self, topic: Topic) -> KnowledgeBase:
        docs = self._gather(topic.title, self._cfg.max_documents)
        sources = [d.to_source() for d in docs]
        source_by_id = {s.id: s for s in sources}

        clusters = self._cluster_claims(docs, sources)
        facts = [self._to_fact(topic.id, c, source_by_id) for c in clusters]
        facts.sort(key=lambda f: f.confidence, reverse=True)

        corroborated = [f for f in facts if not f.uncertain]
        kb = KnowledgeBase(
            topic_id=topic.id,
            sources=sources,
            facts=facts,
            statistics=self._statistics(topic.id, corroborated),
            timeline=self._timeline(topic.id, corroborated),
            definitions=self._definitions(topic, corroborated),
            hook_candidates=self._hooks(topic.id, facts),
            visual_ideas=self._visual_ideas(topic.id, facts),
            key_claims=[f.statement for f in corroborated[: self._cfg.max_key_claims]],
            uncertainties=[f.statement for f in facts if f.uncertain],
            open_questions=self._open_questions(facts),
            confidence=self._overall_confidence(facts),
        )
        kb.summary = self._summary(topic, kb)
        self.log.info(
            "research.completed",
            topic=topic.title,
            facts=len(facts),
            corroborated=len(corroborated),
            confidence=kb.confidence,
        )
        return kb

    # -- internals ------------------------------------------------------------
    def _cluster_claims(
        self, docs: list[RetrievedDocument], sources: list[Source]
    ) -> list[_Cluster]:
        source_by_url = {d.url: s for d, s in zip(docs, sources, strict=True)}
        clusters: list[_Cluster] = []
        for doc in docs:
            source = source_by_url[doc.url]
            for snippet in doc.snippets:
                tokens = _tokens(snippet)
                match = next(
                    (
                        c
                        for c in clusters
                        if _jaccard(tokens, c.tokens) >= self._cfg.similarity_threshold
                    ),
                    None,
                )
                if match is None:
                    clusters.append(_Cluster(snippet, source))
                else:
                    match.add(snippet, source)
        return clusters

    def _confidence(self, support: int, avg_weight: float, hedged: bool) -> tuple[int, bool]:
        base = 0.5 * min(1.0, support / 3.0) + 0.5 * avg_weight
        uncertain = support < self._cfg.min_sources or hedged
        if uncertain:
            base *= 0.6
        return max(0, min(100, round(base * 100))), uncertain

    def _to_fact(self, topic_id: str, cluster: _Cluster, source_by_id: dict[str, Source]) -> Fact:
        statement = cluster.best_statement
        weights = [
            source_by_id[sid].weight(recency_years=self._cfg.recency_years)
            for sid in cluster.source_ids
        ]
        avg_weight = sum(weights) / len(weights)
        hedged = any(h in statement.lower() for h in _HEDGES)
        confidence, uncertain = self._confidence(len(cluster.source_ids), avg_weight, hedged)
        fact_type = _classify(statement)
        return Fact(
            topic_id=topic_id,
            statement=statement,
            fact_type=fact_type,
            confidence=confidence,
            source_ids=sorted(cluster.source_ids),
            visual_potential=_visuals_for(fact_type, statement),
            uncertain=uncertain,
        )

    def _statistics(self, topic_id: str, facts: list[Fact]) -> list[Statistic]:
        out: list[Statistic] = []
        for fact in facts:
            if fact.fact_type is not FactType.STATISTIC:
                continue
            match = _NUMBER.search(fact.statement)
            value = match.group(0).strip() if match else ""
            unit = (match.group(1) or "").strip() if match else ""
            out.append(
                Statistic(
                    topic_id=topic_id,
                    label=fact.statement,
                    value=value,
                    unit=unit,
                    source_ids=fact.source_ids,
                    confidence=fact.confidence,
                )
            )
        return out

    def _timeline(self, topic_id: str, facts: list[Fact]) -> list[TimelineEntry]:
        out: list[TimelineEntry] = []
        for fact in facts:
            if fact.fact_type not in (FactType.HISTORICAL_EVENT, FactType.DATE):
                continue
            year = _YEAR.search(fact.statement)
            out.append(
                TimelineEntry(
                    topic_id=topic_id,
                    when=year.group(0) if year else "",
                    label=fact.statement,
                    source_ids=fact.source_ids,
                    confidence=fact.confidence,
                )
            )
        out.sort(key=lambda e: e.when)
        return out

    def _definitions(self, topic: Topic, facts: list[Fact]) -> list[Definition]:
        return [
            Definition(
                topic_id=topic.id,
                term=topic.title,
                definition=fact.statement,
                source_ids=fact.source_ids,
                confidence=fact.confidence,
            )
            for fact in facts
            if fact.fact_type is FactType.DEFINITION
        ]

    def _hooks(self, topic_id: str, facts: list[Fact]) -> list[HookCandidate]:
        mapping = {
            FactType.STATISTIC: HookType.SURPRISING_NUMBER,
            FactType.MYTH: HookType.COMMON_MISCONCEPTION,
            FactType.RECORD: HookType.INCREDIBLE_RECORD,
            FactType.COMPARISON: HookType.CONTROVERSIAL_FACT,
        }
        hooks: list[HookCandidate] = []
        for fact in facts:
            hook_type = mapping.get(fact.fact_type)
            if hook_type is None:
                continue
            hooks.append(
                HookCandidate(
                    topic_id=topic_id,
                    hook_type=hook_type,
                    text=fact.statement,
                    fact_id=fact.id,
                    strength=fact.confidence,
                )
            )
        hooks.sort(key=lambda h: h.strength, reverse=True)
        return hooks

    def _visual_ideas(self, topic_id: str, facts: list[Fact]) -> list[VisualIdea]:
        by_type: dict[VisualType, VisualIdea] = {}
        for fact in facts:
            for visual in fact.visual_potential:
                idea = by_type.get(visual)
                if idea is None:
                    label = visual.value.replace("_", " ").title()
                    by_type[visual] = VisualIdea(
                        topic_id=topic_id,
                        visual_type=visual,
                        description=f"{label} for: {fact.statement}",
                        fact_ids=[fact.id],
                        priority=fact.confidence,
                    )
                else:
                    idea.fact_ids.append(fact.id)
                    idea.priority = max(idea.priority, fact.confidence)
        return sorted(by_type.values(), key=lambda v: v.priority, reverse=True)

    def _open_questions(self, facts: list[Fact]) -> list[str]:
        return [f"Is it confirmed that: {f.statement}" for f in facts if f.uncertain][:3]

    def _overall_confidence(self, facts: list[Fact]) -> float:
        if not facts:
            return 0.0
        return round(sum(f.confidence for f in facts) / len(facts) / 100.0, 3)

    def _summary(self, topic: Topic, kb: KnowledgeBase) -> str:
        if not kb.key_claims:
            return f"Insufficient corroborated facts for {topic.title}."
        # Built purely from corroborated statements - no new claims introduced.
        return f"{topic.title}: " + " ".join(kb.key_claims[:3])
