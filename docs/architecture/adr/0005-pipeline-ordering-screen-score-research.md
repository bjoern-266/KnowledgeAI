# ADR-0005 — Pipeline ordering: screen → score → deep-research

* Status: Accepted
* Date: 2026-07-15
* Supersedes the stage order implied by ADR-0002's first draft.

## Context

The original flow scored virality *before* researching facts. That risks
investing effort in a topic with high viral potential but a weak or
non-existent factual basis — exactly the content this system must not produce.
Full research (multi-source retrieval, extraction, cross-verification) is also
the most expensive stage, so running it for every candidate is wasteful.

## Decision

Split fact work into two stages and reorder:

1. **Trend Intelligence** → candidate topics.
2. **Research Engine — `screen(topic)`** (cheap): does the topic have enough
   credible sources to be worth pursuing? Returns `SourceAvailability`. Topics
   that fail are discarded immediately.
3. **Virality Engine** scores/ranks only the *screened* survivors.
4. **Research Engine — `research(topic)`** (expensive): deep fact gathering and
   cross-verification, run **only for the single selected winner**.
5. Content → Canva → TikTok → Quality gate → Publish → Analytics → Learning.

If no candidate passes screening, the run aborts early with
`NoViableTopicError` — no scoring, no content, no design.

## Consequences

* **Quality:** weak-evidence topics are eliminated before they can win on
  virality alone.
* **Cost:** deep research runs once per cycle instead of once per candidate;
  screening is intentionally lightweight (availability, not verification).
* **Contract:** the `ResearchEngine` interface now exposes both `screen` and
  `research`, and a new `SourceAvailability` domain model carries the screening
  result. The orchestrator and reference pipeline reflect the new order.
* **Trade-off:** two research operations to implement instead of one, and
  screening must be genuinely cheap or the savings evaporate. Both are
  acceptable and are called out in the Research Engine design doc and
  `CONTENT_INTELLIGENCE.md`.
