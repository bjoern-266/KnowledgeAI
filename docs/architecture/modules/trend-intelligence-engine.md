# Trend Intelligence Engine (steps 1–2)

## Purpose
Detect what is gaining attention and turn raw signals into concrete, on-brand
**topic candidates** in the knowledge niche (science, history, space, …).

## Interface
`acis.engines.interfaces.TrendIntelligenceEngine`
- `discover(region, limit) -> list[Trend]`
- `to_topics(trends) -> list[Topic]`

## Approach
1. **Aggregate** signals from multiple `TrendSourcePort`s (Google Trends, TikTok
   creative/hashtag data, news, Reddit, Wikipedia pageviews). Each source is an
   integration adapter; the engine merges and de-duplicates.
2. **Filter to niche.** Drop signals that cannot become evergreen knowledge
   content. Map each surviving signal to a `TopicCategory`.
3. **Cluster** related keywords into a single topic and craft an initial
   `angle` (e.g. "myth vs. reality"). LLM assists clustering/naming via `LLMPort`.
4. **De-duplicate against history** (repository) to avoid repeating recent
   topics.

## Integrations
`trends` (multiple sources), `openai` (clustering/naming). Reads recent topics
from the repository.

## Quality / risks
- Trend freshness vs. evergreen value — the engine must prefer signals with
  long-term relevance (config-weighted).
- Source bias: aggregate ≥2 independent sources before trusting a trend.

## Open questions
- Which concrete trend sources ship first?
- Scoring for "evergreen-ness" — here or in the Virality Engine?
