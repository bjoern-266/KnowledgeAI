# ADR-0002 — Modular architecture with interface-only coupling

* Status: Accepted
* Date: 2026-07-15

## Context

The brief is explicit: **no monolith**, each module must work independently, and
modules may communicate only through defined interfaces. The system has ten
distinct engines plus infrastructure; we need boundaries that survive years of
change and let engines be built, tested, and replaced in isolation.

## Decision

* A **layered package structure** (`core`, `domain`, `data`, `integrations`,
  `engines`) with a strict downward dependency rule. Engines never import other
  engines.
* The **domain layer** (`acis.domain`) holds the only types allowed to cross
  module boundaries. Every engine consumes some domain models and produces
  others; that is the entire contract between stages.
* **Ports as `Protocol` classes.** Engine contracts live in
  `acis.engines.interfaces`; integration contracts in
  `acis.integrations.interfaces`. Consumers depend on the Protocol, never a
  concrete class, so implementations (and mocks) are interchangeable and
  duck-typed without inheritance coupling.
* A **composition root** (`AppContext`) wires concrete objects; the
  orchestrator receives them by constructor injection.

## Consequences

* Engines are independently testable with fake collaborators; a change inside
  one engine cannot ripple into another.
* Replacing a reference engine with its production implementation is a one-line
  change at the composition root.
* `Protocol` gives structural typing — implementations need not inherit a base,
  keeping them decoupled while `mypy` still checks conformance.
* Trade-off: more small files and explicit interfaces up front. This is the
  intended cost of modularity and pays off as engines are added.
