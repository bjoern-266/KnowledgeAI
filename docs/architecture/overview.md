# Architecture Overview

ACIS is an **autonomous content factory**. It turns raw attention signals into
fact-checked, on-brand knowledge content and ships it to Instagram and TikTok,
then feeds performance back into future decisions — with no human in the loop.

The guiding principle is **strict modularity behind small interfaces**. Any
engine can be rewritten, and any external service swapped between mock and live,
without touching the rest of the system.

## The workflow (10 stages)

```
 ┌─────────────┐   ┌────────────┐   ┌──────────────┐   ┌─────────────┐
 │ 1-2 Trend   │──▶│ 3 Virality │──▶│ 4 Research   │──▶│ 5 Content   │
 │ Intelligence│   │  scoring   │   │ (multi-src)  │   │  authoring  │
 └─────────────┘   └────────────┘   └──────────────┘   └──────┬──────┘
                                                              │
        ┌─────────────────────────────────────────────────────┘
        ▼
 ┌─────────────┐   ┌──────────────┐   ┌─────────────┐   ┌──────────────┐
 │ 6 Canva     │──▶│ TikTok Video │──▶│ Quality gate│──▶│ 7 Publishing │
 │ automation  │   │  derivation  │   │ (hard stop) │   │  IG + TikTok │
 └─────────────┘   └──────────────┘   └─────────────┘   └──────┬───────┘
                                                               │
                                        ┌──────────────────────┘
                                        ▼
                              ┌────────────────┐   ┌──────────────┐
                              │ 8 Analytics    │──▶│ 9 Learning   │──▶ (feeds stage 1-3)
                              └────────────────┘   └──────────────┘
```

The order and data-hand-off are owned by the
[pipeline orchestrator](../../src/acis/core/pipeline.py). Each stage is an
engine that depends only on the previous stage's **domain models**.

## Layered structure

| Layer | Package | Responsibility | May depend on |
| --- | --- | --- | --- |
| Core | `acis.core` | config, logging, errors, base classes, scheduler, context, pipeline | domain |
| Domain | `acis.domain` | shared data contracts | — (nothing) |
| Data | `acis.data` | persistence (repository pattern) | domain, core |
| Integrations | `acis.integrations` | **only** layer that talks to external APIs | domain, core |
| Engines | `acis.engines` | the 10 business modules | domain, integrations (via ports), data |
| Composition | `acis.core.context`, `acis.reference`, `acis.cli` | wiring / entry points | everything |

**Dependency rule:** arrows point downward only. Engines never import other
engines; they communicate exclusively through domain models and the ports in
`acis.integrations.interfaces` / `acis.engines.interfaces`.

## Key seams

* **Integration factory** (`acis.integrations.base.build_integrations`) — the
  single place where mock vs. live is decided, from configuration alone.
* **Repository factory** (`acis.data.repository.build_repository`) — swap
  storage backend without touching callers.
* **Pipeline construction** (`acis.reference.build_reference_pipeline`) — swap a
  reference engine for its real implementation in one line.
* **AppContext** (`acis.core.context`) — the composition root; builds and owns
  the wired graph so nothing constructs dependencies ad-hoc.

## Configuration model

Four layers, each overriding the previous:
`config/default.yaml` → `config/<env>.yaml` → environment variables (`ACIS_*`)
→ `.env`. Secrets live only in the last two. See
[ADR-0001](adr/0001-configuration-layering.md).

## Quality gate

Before anything is published the [Quality Engine](modules/quality-engine.md)
produces a `QualityReport`. If `overall < quality.min_score`, the pipeline
raises `QualityGateError` and nothing is published. This is a hard,
non-bypassable rule enforced in the orchestrator, not in any single engine.

## Testability

Because every integration has a deterministic mock and storage can be in-memory,
the entire system — including a full end-to-end run — executes offline in
milliseconds. The reference pipeline + `tests/test_pipeline.py` demonstrate the
Definition of Success without any credentials.

## What exists today vs. next

* **Today (foundation):** all infrastructure, all integration adapters (mock +
  live skeletons), engine interfaces, a runnable reference pipeline, tests, docs.
* **Next (per-module, after review):** replace each reference engine with its
  full implementation under `acis/engines/<name>/`, guided by the concept docs
  in [modules/](modules).
