# Module Architecture Concepts

Each engine owns exactly one stage of the workflow and is defined by a
`Protocol` in [`acis.engines.interfaces`](../../../src/acis/engines/interfaces.py).
Implementations are added **one module at a time, after the concept below is
reviewed**. Until an engine is built, the [reference
pipeline](../../../src/acis/reference.py) provides a minimal stand-in so the
end-to-end flow always runs.

| # | Engine | Concept |
| --- | --- | --- |
| 1–2 | Trend Intelligence | [trend-intelligence-engine.md](trend-intelligence-engine.md) |
| 3 | Virality | [virality-engine.md](virality-engine.md) |
| 4 | Research | [research-engine.md](research-engine.md) |
| 5 | Content | [content-engine.md](content-engine.md) |
| 6 | Canva Automation | [canva-automation-engine.md](canva-automation-engine.md) |
| — | TikTok Video | [tiktok-video-engine.md](tiktok-video-engine.md) |
| — | Quality | [quality-engine.md](quality-engine.md) |
| 7 | Publishing | [publishing-engine.md](publishing-engine.md) |
| 8 | Analytics | [analytics-engine.md](analytics-engine.md) |
| 9 | Learning | [learning-engine.md](learning-engine.md) |

Every concept follows the same shape: **Purpose → Interface → Approach →
Integrations → Quality/risks → Open questions.**
