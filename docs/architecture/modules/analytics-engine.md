# Analytics Engine — Design (impl. order #9)

> Interface: `acis.engines.interfaces.AnalyticsEngine`
> Business rules: [CONTENT_INTELLIGENCE.md §8](../../../CONTENT_INTELLIGENCE.md)

## 1. Purpose & responsibilities
Collect **performance metrics** for published content and normalise them into
platform-agnostic KPIs — the raw material for learning.
- Fetch per-post metrics via the analytics port.
- Emphasise the north-star KPIs: **save rate**, **share rate**, **watch-through**.
- Collect over time (scheduled), not just a snapshot.

## 2. Input / output data (domain models)
- **In:** `PublishReceipt` (`external_id`, `platform`).
- **Out:** `dict[str, float]` normalised KPIs (impressions, likes, saves, shares,
  save_rate, share_rate, watch-through…), persisted linked to content/topic.

## 3. Interfaces to other modules
- **Consumes:** `AnalyticsPort`, `Repository`.
- **Produces for:** Learning Engine.
- Driven by the scheduler's `analytics_sync` job (time series).

## 4. Configuration parameters
- `integrations.analytics.*` — mode/credentials.
- `scheduler.jobs.analytics_sync.interval_seconds` — poll cadence.
- (new) `analytics.collection_points` — e.g. 1h/24h/7d snapshots; retention.

## 5. Error cases
- Metrics not yet available (lag after publish) → return partial/empty; retry on
  next sync (best-effort, never fail the pipeline).
- API quota exceeded → `IntegrationRateLimitError`; batch + back off.
- Unknown `external_id` (prepared-only) → skip.

## 6. Quality criteria
- KPIs normalised consistently across platforms.
- Rates computed defensively (no divide-by-zero).
- Time-series points timestamped and de-duplicated.

## 7. Test strategy
- Unit (mock `AnalyticsPort`): normalisation, rate math, empty/partial handling,
  deterministic derived KPIs.
- Scheduling: `analytics_sync` job registers and runs (scheduler test pattern).
- Contract: satisfies `AnalyticsEngine`.

## 8. Extension possibilities
- Richer attribution across reposts/formats.
- Cohort/growth analysis; anomaly detection.
- Additional platforms' insights behind the same port.
