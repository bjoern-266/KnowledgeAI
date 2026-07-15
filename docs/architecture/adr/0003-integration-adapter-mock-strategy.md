# ADR-0003 — Integration adapters with a mandatory mock mode

* Status: Accepted
* Date: 2026-07-15

## Context

Development must proceed **without real API keys**, yet the same code must run
in production against Canva, Instagram, TikTok, OpenAI, trend and analytics
services. We also want a hard guarantee that no component outside a dedicated
layer ever talks to an external API.

## Decision

* A single **integration layer** (`acis.integrations`) is the only place
  permitted to perform external I/O. Every other layer depends on the ports in
  `acis.integrations.interfaces`.
* Each service ships **two adapters** implementing the same port:
  * a **mock** adapter — deterministic, credential-free, offline; and
  * a **live** adapter — real API calls, with declared `required_credentials`.
* A per-integration **factory** selects the implementation from
  `IntegrationMode` (`mock`/`live`), resolved purely from configuration.
  `build_integrations()` assembles the full `IntegrationBundle`.
* The shared `IntegrationAdapter` base validates credentials on `setup()`: a
  **live** adapter with missing credentials fails fast with
  `MissingCredentialError`; a **mock** adapter never needs any.

## Consequences

* The entire system — including a full end-to-end run — is testable offline and
  deterministically.
* Switching an integration from mock to live is a config change; no other code
  changes (satisfies the "swap in credentials, then run" goal).
* Vendor SDK exceptions are translated into the `IntegrationError` hierarchy, so
  the rest of the system stays vendor-agnostic.
* Live adapters currently raise `IntegrationUnavailableError` for calls that are
  not yet implemented, making the "not built yet" boundary explicit rather than
  silently returning empty data.
* Trade-off: two implementations per service to maintain. Kept cheap by keeping
  ports deliberately narrow.
