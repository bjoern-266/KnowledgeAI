# ACIS — Autonomous Content Intelligence System

A fully modular, self-driving pipeline that discovers trends, researches facts
from reliable sources, produces branded knowledge content for **Instagram** and
**TikTok**, publishes it, and learns from performance — **without manual
intervention**.

> This repository contains the full system: the foundation (configuration,
> logging, persistence, scheduling, the integration/adapter layer with mock
> modes, error handling, base classes, the pipeline orchestrator) **and all ten
> business engines** (Trend, Research, Virality, Content, Canva, TikTok, Quality,
> Publishing, Analytics, Learning). It runs end-to-end today — trend → research →
> score → write → design → video → quality gate → publish → measure → learn —
> entirely in mock mode, with the optimisation loop closed.

---

## Why it is built this way

* **Strict modularity.** Every capability lives behind a small interface.
  Modules never import each other's internals — they exchange
  [domain models](src/acis/domain/models.py) only. See
  [ADR-0002](docs/architecture/adr/0002-modular-architecture.md).
* **No credentials required to develop or test.** Every external service has a
  **mock** and a **live** adapter selected purely by config. The whole system
  runs offline. See [ADR-0003](docs/architecture/adr/0003-integration-adapter-mock-strategy.md).
* **Config- and env-driven.** Secrets are read from environment variables / a
  git-ignored `.env` only — never from source or YAML.
* **Quality gate is mandatory.** Content below the configured score is never
  published.

## Layers

```
src/acis/
├── core/          # config, logging, errors, base classes, scheduler, context, pipeline
├── domain/        # shared data contracts (the ONLY coupling between modules)
├── data/          # repository pattern: in-memory + sqlite backends
├── integrations/  # the ONLY layer allowed to call external APIs (mock + live)
│   ├── canva/  instagram/  tiktok/  openai/  trends/  research/  analytics/
├── engines/       # the 10 business modules — interfaces now, impls after review
└── reference.py   # foundation scaffolding proving the end-to-end flow
```

See [docs/architecture/overview.md](docs/architecture/overview.md) for the full
picture and [docs/architecture/modules/](docs/architecture/modules) for each
engine's concept.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Everything below works with NO credentials (mock mode):
acis config              # show resolved configuration (secrets redacted)
acis health              # check every integration adapter
acis topics              # Sprint 1: ranked, de-duplicated candidate topics
acis research --topic X  # Sprint 2: structured Knowledge Base for a topic
acis run-once            # one full autonomous cycle: trend → publish → learn
pytest                   # run the test suite
```

Example `acis run-once` output:

```
Topic     : James Webb Images (space)
Sources   : 2
Slides    : 5
Design    : mock-design-1f7345bc (5 assets)
Video     : mock://tiktok/1f7345bc.mp4
Quality   : 1.00 PASSED
Publish   : instagram -> published https://instagram.com/p/ig_mock_...
Metrics   : {"impressions": 19050.0, ... "save_rate": 0.0224, "share_rate": 0.0162}
```

## Going live

No code changes are required to go to production — only configuration:

1. Copy `.env.example` → `.env` and fill in real keys/tokens.
2. Set each integration's `mode` to `live` (or `ACIS_INTEGRATIONS__DEFAULT_MODE=live`).
3. Run `acis health` to confirm credentials are present, then `acis start`.

A live adapter refuses to start if its required credentials are missing, so
mis-configuration fails fast and loudly.

## Branding

Premium, modern, technical, minimalist. Palette:
black / anthracite / graphite / carbon, white & light-grey text, and a single
**strong yellow (`#FFD400`)** accent reserved for headings, numbers, statistics,
key facts, highlights and CTAs. See [docs/branding.md](docs/branding.md).

## Documentation

| Doc | Purpose |
| --- | --- |
| [Content Intelligence](CONTENT_INTELLIGENCE.md) | **The business brain** — what content is produced, why, and how it improves |
| [Architecture overview](docs/architecture/overview.md) | System design & data flow |
| [ADRs](docs/architecture/adr) | Why key decisions were made (incl. pipeline ordering) |
| [Module designs](docs/architecture/modules) | Detailed 8-section design doc per engine |
| [Development guidelines](docs/development-guidelines.md) | How to contribute |
| [Branding](docs/branding.md) | Visual identity spec |

> **Status:** all ten engines are implemented (Trend → Research → Virality →
> Content → Canva → TikTok → Quality → Publishing → Analytics → Learning). The
> pipeline runs end-to-end on production engines with mock integrations by
> default, and the optimisation loop is closed (Learning feeds Virality). Add
> credentials and flip integrations to `live` to publish for real — no code
> changes. See [module designs](docs/architecture/modules/README.md).

## License

Proprietary — all rights reserved.
