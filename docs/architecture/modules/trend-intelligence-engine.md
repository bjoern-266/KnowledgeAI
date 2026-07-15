# Trend Intelligence Engine — Design (impl. order #1)

> **Status: ✅ Implemented (Sprint 1)** — `acis.engines.trend.TrendEngine`,
> wired into the live pipeline via `build_trend_engine`. Try it: `acis topics`.
> Interface: `acis.engines.interfaces.TrendIntelligenceEngine`
> Business rules: [CONTENT_INTELLIGENCE.md §1](../../../CONTENT_INTELLIGENCE.md)

## 1. Purpose & responsibilities
Detect what is gaining attention and turn raw signals into concrete, on-brand,
evergreen-leaning **topic candidates** in the knowledge niche.
- Aggregate multiple independent trend signals.
- Filter to the niche and map to a `TopicCategory`.
- Cluster related keywords into topics; propose title + angle.
- De-duplicate against recent history (§5 of Content Intelligence).
- **Not** responsible for scoring virality or checking sources (later stages).

## 2. Input / output data (domain models)
- **In:** `region: str`, `limit: int`, plus recent-topic fingerprints (repo).
- **Out:** `list[Trend]` (raw signals) and `list[Topic]` (clustered candidates
  with `title`, `category`, `angle`, `source_trends`, `keywords`).

## 3. Interfaces to other modules
- **Consumes:** `TrendSourcePort` (one or many), `LLMPort` (clustering/naming),
  `Repository` (dedup history).
- **Produces for:** Research Engine (`screen`), then Virality Engine.
- No dependency on any other engine — communicates via `Topic` only.

## 4. Configuration parameters
Implemented via `TrendEngineConfig` (constructed in `build_trend_engine`):
- `content.topics` — allowed categories (read from settings). ✅
- `integrations.trends.*` — source mode/credentials. ✅
- `evergreen_bias` (default 0.4) — reactive-vs-evergreen mix (§1). ✅
- `dedup_threshold` (default 0.6) — token-Jaccard merge cutoff. ✅
- `per_source_limit` (default 100), `history_collection` (`published_topics`). ✅
- *Future:* promote these to explicit YAML keys and add multi-source weights.

## 5. Error cases
- Source unavailable / rate-limited → `IntegrationError`; degrade to remaining
  sources, never fail the whole run on one source.
- No signals returned → return `[]`; the orchestrator raises `NoViableTopicError`.
- LLM failure during clustering → fall back to keyword-based clustering.

## 6. Quality criteria
- ≥ 2 independent sources contribute before a trend is trusted.
- Every emitted `Topic` has a non-empty `title`, a valid `category`, and an
  `angle`.
- No near-duplicate of a recently published topic (dedup enforced).
- Evergreen bias respected.

## 7. Test strategy
- Unit: clustering, niche filter, category mapping, dedup logic — with a fake
  `TrendSourcePort` and stub LLM.
- Determinism: mock source yields reproducible topics.
- Property: `limit` honoured; output topics always well-formed.
- Contract: satisfies `TrendIntelligenceEngine` (isinstance check).

## 8. Extension possibilities
- Add sources by implementing new `TrendSourcePort` adapters (no engine change).
- Swap keyword clustering for embedding clustering.
- Regional/multi-language expansion via `region`.
- Feed Learning-Engine category priors into the niche filter.
