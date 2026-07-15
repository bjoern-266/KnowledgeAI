# ACIS — Autonomous Content Intelligence System

A fully modular, self-driving pipeline that discovers trends, researches facts
from reliable sources, produces branded knowledge content for **Instagram** and
**TikTok**, publishes it, and learns from performance — **without manual
intervention**.

> This repository currently contains the **foundation**: architecture, project
> structure, configuration, logging, persistence, scheduling, the
> integration/adapter layer (with mock modes), error handling, base classes,
> the pipeline orchestrator, tests, and documentation. The ten business engines
> are specified as interfaces + architecture concepts and implemented one at a
> time after review. A runnable **reference pipeline** proves the end-to-end
> flow today, entirely in mock mode.

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
│   ├── canva/  instagram/  tiktok/  openai/  trends/  analytics/
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
| [Architecture overview](docs/architecture/overview.md) | System design & data flow |
| [ADRs](docs/architecture/adr) | Why key decisions were made |
| [Module concepts](docs/architecture/modules) | One concept per engine |
| [Development guidelines](docs/development-guidelines.md) | How to contribute |
| [Branding](docs/branding.md) | Visual identity spec |

## License

Proprietary — all rights reserved.
