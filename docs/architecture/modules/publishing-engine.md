# Publishing Engine — Design (impl. order #8)

> **Status: ✅ Implemented (Sprint 8)** — `acis.engines.publishing.PublishingEngine`,
> wired via `build_publishing_engine`. Publishes the carousel to Instagram and
> the video to TikTok, returning one receipt per platform; degrades to PREPARED
> when a live API/credentials are absent; idempotent (persisted receipts, no
> double-post). `publish(content, assets, video) -> list[PublishReceipt]`.
> Interface: `acis.engines.interfaces.PublishingEngine`
> Business rules: [CONTENT_INTELLIGENCE.md §6, §8](../../../CONTENT_INTELLIGENCE.md)

## 1. Purpose & responsibilities
Publish approved content to **Instagram** and **TikTok** — or, when credentials
are absent/unavailable, **prepare** it for one-click go-live.
- Per-platform publish via ports.
- Schedule to optimal windows (Learning-Engine informed).
- Idempotency, retries, receipt persistence.

## 2. Input / output data (domain models)
- **In:** `ContentPiece`, `assets: list[Asset]` (and `VideoResult` for TikTok).
- **Out:** `PublishReceipt` (`platform`, `status`, `external_id`, `url`, `detail`).
  `status` is `PUBLISHED`, `PREPARED` (creds absent), `SCHEDULED`, or `FAILED`.

## 3. Interfaces to other modules
- **Consumes:** `InstagramPort`, `TikTokPort`, `Repository` (receipts, dedup).
- **Produces for:** Analytics Engine (`external_id`).
- Only runs after the quality gate passed (guaranteed by the orchestrator).

## 4. Configuration parameters
- `content.platforms` — which platforms to target.
- `integrations.instagram.*`, `integrations.tiktok.*` — mode/credentials.
- (new) `publishing.schedule` — immediate vs. optimal-window; retry policy.

## 5. Error cases
- Missing credentials in live mode → `PREPARED` receipt + reason (graceful
  degradation), not a run failure.
- Rate limit / token expiry → `IntegrationRateLimitError` / `IntegrationAuthError`;
  retry with backoff, then `FAILED` with detail.
- Duplicate publish attempt → idempotency guard prevents double posting.

## 6. Quality criteria
- Never publishes content that didn't pass the gate.
- Exactly-once semantics per (content, platform).
- Every attempt yields a persisted receipt (audit trail).

## 7. Test strategy
- Unit (mock ports): success → `PUBLISHED`; missing creds → `PREPARED`; API
  error → retry then `FAILED`; idempotency.
- Contract: satisfies `PublishingEngine`.

## 8. Extension possibilities
- More platforms (YouTube Shorts, etc.) via new ports.
- Optimal-time scheduling from analytics.
- Cross-post coordination / staggering.
