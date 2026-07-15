"""Common base classes and lifecycle contracts.

Every long-lived building block in ACIS (engines, integration adapters,
repositories, the scheduler) is a :class:`Component`. Components share a
uniform lifecycle - ``setup`` / ``teardown`` - and a health check, so the
application container can start and stop them consistently.

``Component`` is deliberately tiny; specialised bases (``Engine``,
``BaseAdapter``) add domain-specific contracts on top.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from acis.core.logging import BoundLogger, get_logger


@dataclass(frozen=True)
class HealthStatus:
    """Result of a component health check."""

    healthy: bool
    detail: str = ""
    data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(cls, detail: str = "", **data: Any) -> HealthStatus:
        return cls(healthy=True, detail=detail, data=data)

    @classmethod
    def down(cls, detail: str, **data: Any) -> HealthStatus:
        return cls(healthy=False, detail=detail, data=data)


class Component:
    """Base for any managed building block with a start/stop lifecycle.

    Concrete on its own (subclasses override the ``_on_setup`` / ``_on_teardown``
    hooks as needed); not declared ``abc.ABC`` because it has no abstract members.
    """

    #: Stable, human-readable name used in logs and the registry.
    name: str = "component"

    def __init__(self) -> None:
        self._started = False
        self.log: BoundLogger = BoundLogger(
            get_logger(f"acis.{self.__class__.__module__.split('.')[-1]}"),
            component=self.name,
        )

    @property
    def is_started(self) -> bool:
        return self._started

    def setup(self) -> None:
        """Acquire resources / establish connections. Idempotent."""
        if self._started:
            return
        self._on_setup()
        self._started = True
        self.log.debug("component.setup")

    def teardown(self) -> None:
        """Release resources. Idempotent."""
        if not self._started:
            return
        self._on_teardown()
        self._started = False
        self.log.debug("component.teardown")

    def health_check(self) -> HealthStatus:
        """Report whether the component is ready to do work."""
        return HealthStatus.ok() if self._started else HealthStatus.down("not started")

    # -- Hooks for subclasses -------------------------------------------------
    def _on_setup(self) -> None:  # noqa: B027 - intentional optional hook
        """Override to acquire resources."""

    def _on_teardown(self) -> None:  # noqa: B027 - intentional optional hook
        """Override to release resources."""

    # Context-manager sugar so components can be used with ``with``.
    def __enter__(self) -> Component:
        self.setup()
        return self

    def __exit__(self, *exc: object) -> None:
        self.teardown()


class Engine(Component):
    """Base for business modules (Trend, Research, Content, ...).

    Engines encapsulate one responsibility of the pipeline. They receive their
    collaborators (integrations, repositories) via the constructor - never by
    importing another engine - and expose a single well-defined operation
    described by the subclass. The foundation ships only this base and the
    per-engine interface stubs in :mod:`acis.engines`.
    """

    name = "engine"


class BaseAdapter(Component):
    """Base for external-service adapters (see :mod:`acis.integrations`)."""

    name = "adapter"
