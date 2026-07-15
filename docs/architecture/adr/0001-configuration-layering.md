# ADR-0001 — Layered configuration with secrets from the environment only

* Status: Accepted
* Date: 2026-07-15

## Context

The system integrates many external services, each needing credentials, and
must run in several environments (development, staging, production) as well as
fully offline in tests. We need configuration that is (a) explicit and
version-controlled for non-secret values, (b) environment-aware, and (c) safe —
credentials must never be committed.

## Decision

Configuration is resolved from four layers, each overriding the previous:

1. `config/default.yaml` — safe, committed defaults.
2. `config/<env>.yaml` — environment-specific overrides.
3. Process environment variables — `ACIS_*`, nested via `__`.
4. `.env` — developer convenience, git-ignored.

`Settings` is a `pydantic-settings` model: fully typed, validated, and
**frozen** (immutable) once built. Secrets are only ever read from layers 3–4;
YAML files must contain no credentials. A `load_settings()` function performs a
deep-merge of the YAML layers and lets pydantic apply env/`.env` on top.

Integration mode (`mock`/`live`) is part of config, with per-integration
override and a global `default_mode` fallback (`resolve_mode`).

## Consequences

* One obvious, testable place to construct configuration; tests inject
  `overrides=` without touching disk or the environment.
* Immutability prevents accidental runtime mutation and makes settings safely
  shareable across threads (the scheduler).
* Going live is a configuration change only — no code edits.
* Trade-off: four layers add a little indirection, mitigated by a single loader
  and strong typing.
