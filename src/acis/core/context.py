"""Application context - the composition root / dependency container.

:class:`AppContext` builds and owns the shared infrastructure (settings,
logging, repository, integrations, scheduler) exactly once and hands it to the
rest of the system. Nothing constructs its own dependencies ad-hoc; everything
receives them from here. This keeps wiring in one place and makes the whole
application trivially reconfigurable (e.g. flipping every integration to mock
for a test) by swapping the settings passed in.
"""

from __future__ import annotations

from acis.core.config import Settings, load_settings
from acis.core.logging import BoundLogger, configure_logging, get_logger
from acis.core.scheduler import Scheduler, ThreadedScheduler
from acis.data.repository import Repository, build_repository
from acis.integrations.base import IntegrationBundle, build_integrations


class AppContext:
    """Owns the wired application graph."""

    def __init__(
        self,
        settings: Settings,
        *,
        repository: Repository | None = None,
        integrations: IntegrationBundle | None = None,
        scheduler: Scheduler | None = None,
    ) -> None:
        self.settings = settings
        configure_logging(level=settings.log.level, fmt=settings.log.format.value)
        self.log: BoundLogger = BoundLogger(get_logger("acis.app"), env=settings.env)

        self.repository: Repository = repository or build_repository(settings)
        self.integrations: IntegrationBundle = integrations or build_integrations(settings)
        self.scheduler: Scheduler = scheduler or ThreadedScheduler()

    @classmethod
    def create(cls, env: str | None = None) -> AppContext:
        """Convenience constructor that loads settings from disk/env."""
        return cls(load_settings(env))

    def startup(self) -> None:
        """Start all managed components."""
        self.integrations.setup_all()
        self.log.info("app.startup", integrations=len(self.integrations.adapters()))

    def shutdown(self) -> None:
        """Stop all managed components."""
        try:
            self.scheduler.stop()
        except Exception:  # noqa: BLE001 - best-effort shutdown
            self.log.exception("app.scheduler_stop_failed")
        self.integrations.teardown_all()
        self.log.info("app.shutdown")

    def __enter__(self) -> AppContext:
        self.startup()
        return self

    def __exit__(self, *exc: object) -> None:
        self.shutdown()
