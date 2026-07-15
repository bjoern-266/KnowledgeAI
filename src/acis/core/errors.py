"""Central exception hierarchy for ACIS.

Every error raised inside the system derives from :class:`ACISError`. This
gives callers a single, predictable base to catch while still allowing
fine-grained handling. Errors carry an optional machine-readable ``code`` and
a ``context`` dict so failures can be logged and inspected structurally.

Design rules:
* Never raise bare ``Exception``; pick or add a specific subclass.
* Integrations translate vendor/SDK exceptions into :class:`IntegrationError`
  subclasses so the rest of the system stays vendor-agnostic.
* ``context`` must never contain secrets.
"""

from __future__ import annotations

from typing import Any


class ACISError(Exception):
    """Base class for all ACIS errors."""

    #: Stable, machine-readable identifier. Subclasses may override.
    code: str = "acis_error"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        self.context: dict[str, Any] = context or {}

    def __str__(self) -> str:  # pragma: no cover - trivial
        if self.context:
            return f"{self.message} (context={self.context})"
        return self.message


# --- Configuration ----------------------------------------------------------
class ConfigError(ACISError):
    """Invalid, missing, or contradictory configuration."""

    code = "config_error"


class MissingCredentialError(ConfigError):
    """A live integration was requested but its credentials are absent."""

    code = "missing_credential"


# --- Persistence ------------------------------------------------------------
class StorageError(ACISError):
    """Failure in the data/persistence layer."""

    code = "storage_error"


class EntityNotFoundError(StorageError):
    """A requested entity does not exist."""

    code = "entity_not_found"


# --- Integrations -----------------------------------------------------------
class IntegrationError(ACISError):
    """Base for any failure originating from an external integration."""

    code = "integration_error"


class IntegrationAuthError(IntegrationError):
    """Authentication/authorization against an external service failed."""

    code = "integration_auth_error"


class IntegrationRateLimitError(IntegrationError):
    """The external service rejected the call due to rate limiting."""

    code = "integration_rate_limit"


class IntegrationUnavailableError(IntegrationError):
    """The external service is unreachable or returned a server error."""

    code = "integration_unavailable"


# --- Domain / pipeline ------------------------------------------------------
class ValidationError(ACISError):
    """A domain object or payload failed validation."""

    code = "validation_error"


class PipelineError(ACISError):
    """A stage of the content pipeline failed."""

    code = "pipeline_error"


class NoViableTopicError(PipelineError):
    """No candidate topic survived early screening (e.g. insufficient sources).

    Raised before any expensive work (virality scoring, content creation) so the
    system spends resources only on topics with a defensible factual basis.
    """

    code = "no_viable_topic"


class QualityGateError(PipelineError):
    """Content did not meet the minimum quality threshold to be published."""

    code = "quality_gate_rejected"


class SchedulerError(ACISError):
    """The scheduler could not register, run, or cancel a job."""

    code = "scheduler_error"
