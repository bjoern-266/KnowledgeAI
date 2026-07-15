# Module Design Documents (Business Architecture)

Each engine owns exactly one stage of the workflow and is defined by a
`Protocol` in [`acis.engines.interfaces`](../../../src/acis/engines/interfaces.py).
**No engine is implemented until its design below is reviewed and approved.**
Until then, the [reference pipeline](../../../src/acis/reference.py) provides a
minimal stand-in so the end-to-end flow always runs.

The overarching content strategy these engines serve is defined once in
[CONTENT_INTELLIGENCE.md](../../../CONTENT_INTELLIGENCE.md).

Every design doc follows the same 8-section template:
**Purpose & responsibilities · Input/output (domain models) · Interfaces to other
modules · Configuration parameters · Error cases · Quality criteria · Test
strategy · Extension possibilities.**

## Implementation order

Ordering reflects [ADR-0005](../adr/0005-pipeline-ordering-screen-score-research.md):
find topics → **screen sources** → score virality → invest in creation. Research
is built **before** Virality so weak-evidence topics are discarded cheaply.

| # | Engine | Stage | Design |
| --- | --- | --- | --- |
| 1 | Trend Intelligence | find topics | [trend-intelligence-engine.md](trend-intelligence-engine.md) |
| 2 | Research | screen (cheap) + deep research | [research-engine.md](research-engine.md) |
| 3 | Virality | score screened topics | [virality-engine.md](virality-engine.md) |
| 4 | Content | write carousel/script | [content-engine.md](content-engine.md) |
| 5 | Canva Automation | design | [canva-automation-engine.md](canva-automation-engine.md) |
| 6 | TikTok Video | derive video | [tiktok-video-engine.md](tiktok-video-engine.md) |
| 7 | Quality | gate | [quality-engine.md](quality-engine.md) |
| 8 | Publishing | publish/prepare | [publishing-engine.md](publishing-engine.md) |
| 9 | Analytics | measure | [analytics-engine.md](analytics-engine.md) |
| 10 | Learning | optimise | [learning-engine.md](learning-engine.md) |

> Note: the Research Engine runs at **two** pipeline points — cheap `screen`
> before virality scoring, and deep `research` after the winner is selected.
