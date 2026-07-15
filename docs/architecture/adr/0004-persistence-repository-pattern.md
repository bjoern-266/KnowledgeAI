# ADR-0004 — Persistence via a repository protocol

* Status: Accepted
* Date: 2026-07-15

## Context

Engines need to persist and retrieve domain objects (trends, topics, dossiers,
content, receipts, metrics). We want durability for real runs but zero-setup,
dependency-free storage for tests, and the freedom to move to a heavier database
later without rewriting callers.

## Decision

* A generic **`Repository` protocol**: a key–collection store that round-trips
  pydantic models as JSON, keyed by `collection` name and the model's `id`.
* Two implementations in the foundation:
  * `InMemoryRepository` — no I/O, for tests and the mock run;
  * `SqliteRepository` — durable single-file store using the standard-library
    `sqlite3`, one table per collection, created lazily.
* `build_repository(settings)` selects the backend from configuration.

Deliberately **not** an ORM: engines own their own query semantics; the store
stays a minimal, easily-replaced seam.

## Consequences

* Tests run against the exact (de)serialisation path used in production.
* A future Postgres/Redis backend implements the same protocol — callers are
  untouched.
* Trade-off: no rich querying at the storage layer. Acceptable now; if complex
  queries become common we revisit with a dedicated backend behind the same
  protocol.
