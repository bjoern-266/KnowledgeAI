# Publishing Engine (step 7)

## Purpose
Publish approved content to **Instagram** and **TikTok** — or, when credentials
are absent, **prepare** it for one-click go-live.

## Interface
`acis.engines.interfaces.PublishingEngine`
- `publish(content, assets) -> PublishReceipt`

## Approach
1. **Per-platform publish** through `InstagramPort` / `TikTokPort`.
2. **Scheduling** to optimal posting windows (informed by the Analytics/Learning
   engines).
3. **Graceful degradation:** if a live adapter can't publish (missing creds /
   API down), emit a `PublishReceipt` with status `PREPARED` and the reason,
   rather than failing the whole run — satisfying "prepare or publish".
4. **Idempotency & retries** with backoff; persist receipts for auditing.

## Integrations
`instagram`, `tiktok`. Persists `PublishReceipt`s in the repository.

## Quality / risks
- Never publish content that didn't pass the quality gate (guaranteed upstream).
- Rate limits / token expiry → typed `IntegrationError`s with retry policy.
- Exactly-once semantics to avoid duplicate posts.

## Open questions
- Immediate vs. scheduled posting as the default.
- Cross-posting order and interdependencies.
