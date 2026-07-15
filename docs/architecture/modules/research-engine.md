# Research Engine — Design (impl. order #2)

> **Status: ✅ Implemented (Sprint 2)** — `acis.engines.research.ResearchEngine`,
> wired via `build_research_engine`. Try it: `acis research --topic "..."`.
> Produces a structured `KnowledgeBase` (not free text) via a new
> `ResearchSourcePort` retrieval integration (mock + live skeleton).
> Interface: `acis.engines.interfaces.ResearchEngine`
> Business rules: [CONTENT_INTELLIGENCE.md §2, §4](../../../CONTENT_INTELLIGENCE.md)
> Ordering rationale: [ADR-0005](../adr/0005-pipeline-ordering-screen-score-research.md)

## 1. Purpose & responsibilities
Guarantee a **defensible factual basis** for every published piece — and do so
cost-efficiently by splitting cheap screening from expensive research.
- `screen(topic)` — cheap pre-virality check: are there enough credible sources?
- `research(topic)` — deep, verified fact gathering for the winning topic only.
- Score source reliability; cross-verify claims; prevent hallucination.

## 2. Input / output data (domain models)
- `screen`: **in** `Topic` → **out** `SourceAvailability`
  (`source_count`, `sufficient`, `candidate_sources`, `reason`).
- `research`: **in** `Topic` → **out** `KnowledgeBase` — a structured object:
  `summary`, `key_claims`, typed `facts` (each with `confidence` 0-100,
  `source_ids`, `visual_potential`, `uncertain`), `statistics`, `timeline`,
  `definitions`, `sources` (weighted), `hook_candidates`, `visual_ideas`,
  `uncertainties`, `open_questions`, overall `confidence`.

## 3. Interfaces to other modules
- **Consumes:** research/search `TrendSourcePort`-style adapters + `LLMPort`
  (extraction/summarisation), `Repository` (source cache).
- **Produces for:** Virality Engine (via `screen` gate), Content Engine and
  Quality Engine (via `research`).
- Runs at **two points** in the pipeline (screen before scoring, research after
  selection).

## 4. Configuration parameters
- `quality.min_sources_per_topic` — screening threshold.
- (new) `research.source_tiers` — tier→reliability mapping (§2).
- (new) `research.max_sources`, `research.require_tier1_or_2` — verification depth.
- (new) `research.cache_ttl` — source reuse window.

## 5. Error cases
- Retrieval source down → `IntegrationUnavailableError`; screening returns
  `sufficient=False` with a reason rather than crashing.
- Fewer than min sources → `sufficient=False` (topic dropped upstream).
- Contradictory sources → resolve by tier or mark the claim contested; never
  silently pick one.
- LLM invents a fact with no source → rejected by the anti-hallucination rule.

## 6. Quality criteria
- Screening is genuinely cheap (no full fact extraction).
- Every dossier fact traces to ≥ 2 independent retrieved sources, ≥ 1 in Tier 1–2.
- Source independence enforced (shared wire stories collapse to one).
- Deterministic, auditable `reliability` scoring.

## 7. Test strategy
- Unit: screening threshold behaviour; cross-verification (accept/reject);
  tier/reliability scoring; conflict resolution — with fake sources + stub LLM.
- Anti-hallucination: a fact without a backing source is dropped.
- Cost: `research` is never called during screening (spy/ordering test — already
  present in `tests/test_pipeline.py`).
- Contract: satisfies `ResearchEngine`.

## 8. Extension possibilities
- Add retrieval backends (Wikipedia/Wikidata, OpenAlex, official stats APIs) as
  adapters.
- Embedding-based claim clustering & contradiction detection.
- Per-domain reliability models; source reputation learned over time.
