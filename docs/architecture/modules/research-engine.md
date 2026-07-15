# Research Engine (step 4)

## Purpose
Produce a **fact-checked dossier** for a topic: verified facts each backed by
multiple reliable sources.

## Interface
`acis.engines.interfaces.ResearchEngine`
- `research(topic) -> ResearchDossier`

## Approach
1. **Query expansion** from the topic angle (LLM).
2. **Retrieve** from reliable sources (encyclopedic, academic, official
   statistics) via research adapters.
3. **Extract candidate facts** and attach citations.
4. **Cross-verify:** keep a fact only if corroborated by ≥ `min_sources_per_topic`
   independent sources; score each source's `reliability`.
5. **Summarise** into a coherent `ResearchDossier` (facts + `Source[]`).

Sources are first-class domain objects so the Quality Engine and captions can
cite them.

## Integrations
`openai` (extraction/summarisation) plus research/search adapters (future).

## Quality / risks
- Hallucination control: facts must trace to a real retrieved source, not the
  LLM alone.
- Source reliability scoring drives the Quality Engine's source-check gate.
- Recency vs. correctness for "current developments" topics.

## Open questions
- Which retrieval backends first (Wikipedia/Wikidata, OpenAlex, official stats)?
- Caching/deduplication of sources across runs.
