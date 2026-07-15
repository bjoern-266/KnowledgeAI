# Development Guidelines

Architecture, code quality, modularity, and maintainability take precedence over
speed. Follow these rules when extending ACIS.

## Golden rules

1. **Respect the layers.** Dependencies point downward only:
   `engines → integrations/data → domain → core`. An engine must never import
   another engine. If you need something from another module, express it as a
   domain model or a port.
2. **Talk to the outside world only through `acis.integrations`.** No `requests`,
   SDK, or network call may live in `engines`, `core`, `data`, or `domain`.
3. **Program to interfaces.** Depend on the `Protocol`s in
   `engines.interfaces` / `integrations.interfaces`, not concrete classes.
   Construct concretes only at the composition root (`AppContext` / `reference`).
4. **No secrets in code or YAML.** Credentials come from env vars / `.env` only.
5. **Every integration needs a mock.** The full system must run offline.
6. **Fail with typed errors.** Raise a specific `ACISError` subclass; never a
   bare `Exception`. Integrations translate vendor errors into `IntegrationError`.

## Adding a new engine implementation

1. Read/refresh its concept in `docs/architecture/modules/`.
2. Implement the `Protocol` from `acis.engines.interfaces` under
   `src/acis/engines/<name>/`. Depend on ports + domain models only; receive
   collaborators via the constructor.
3. Add unit tests with fake collaborators, plus wire it into
   `build_reference_pipeline` (swap the reference stand-in) and extend the e2e
   test.
4. Update the concept doc's status.

## Adding a new integration

1. Define/extend the port in `acis.integrations.interfaces`.
2. Create `mock.py`, `live.py`, `factory.py` under
   `src/acis/integrations/<name>/`. Subclass `IntegrationAdapter`; declare
   `required_credentials` on the live adapter.
3. Register it in `build_integrations` and add a config block + `.env.example`
   entries.
4. Test: mock behaviour, mode selection, and live-without-credentials failure.

## Domain models

* Add shared types to `acis.domain`; keep them pure data (no behaviour that
  reaches into other layers). Prefer immutability and explicit `id`s.
* Changing a model is changing a public contract — update all producers,
  consumers, and tests together.

## Code style & tooling

* Python 3.11, full type hints, `from __future__ import annotations`.
* Format/lint with **ruff**; type-check with **mypy** (`strict`).
* Docstrings explain *why*, not just *what*. Match the surrounding style.

```bash
ruff check src tests        # lint
ruff format src tests       # format
mypy                        # type-check
pytest                      # tests (fast, fully offline)
```

## Testing expectations

* Unit-test each engine/adapter in isolation with fakes.
* Keep the end-to-end `tests/test_pipeline.py` green — it encodes the Definition
  of Success.
* Tests must not require network or credentials. Use mock mode + in-memory
  storage (see `tests/conftest.py`).

## Commits & branches

* Small, focused commits with descriptive messages.
* One module per PR where possible; include/adjust docs and tests in the same
  change.
