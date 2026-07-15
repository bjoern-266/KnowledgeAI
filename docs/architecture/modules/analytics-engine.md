# Analytics Engine (step 8)

## Purpose
Collect **performance metrics** for published content — impressions, likes,
saves, shares, and derived rates — as the raw material for learning.

## Interface
`acis.engines.interfaces.AnalyticsEngine`
- `collect(receipt) -> dict[str, float]`

## Approach
1. **Fetch** per-post metrics via `AnalyticsPort` using the platform `external_id`.
2. **Normalise** into platform-agnostic KPIs, emphasising the north-star metrics
   for knowledge content: **save rate** and **share rate**.
3. **Time series:** collect at intervals (e.g. 1h/24h/7d) via a scheduled job to
   capture growth, not just a snapshot.
4. **Persist** metrics linked to the content/topic for the Learning Engine.

## Integrations
`analytics` (Instagram/TikTok insights). Driven by the scheduler's
`analytics_sync` job. Persists to the repository.

## Quality / risks
- Metric availability lag after publishing.
- Attribution across reposts/formats.
- API quotas → batch and back off.

## Open questions
- Retention window and aggregation granularity.
- Which KPIs feed which learning signals.
