"""Scheduler abstraction.

The system runs recurring jobs (the content pipeline, analytics sync). The
scheduler is abstracted behind :class:`Scheduler` so the driving mechanism is
swappable and, importantly, testable without real time passing.

Two implementations ship in the foundation:

* :class:`ManualScheduler` - advances only when ``tick`` is called, giving
  tests full, deterministic control over "time".
* :class:`ThreadedScheduler` - a lightweight, dependency-free background loop
  for local/single-node runs. A production deployment can later drop in an
  APScheduler/cron-backed implementation behind the same interface.
"""

from __future__ import annotations

import abc
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from acis.core.base import Component
from acis.core.errors import SchedulerError

JobFunc = Callable[[], None]


@dataclass
class Job:
    name: str
    interval_seconds: float
    func: JobFunc
    enabled: bool = True
    #: ``None`` until the job has run once. A never-run job is due immediately
    #: so freshly started pipelines don't wait a full interval before working.
    last_run: float | None = None
    run_count: int = field(default=0)

    def due(self, now: float) -> bool:
        if not self.enabled:
            return False
        if self.last_run is None:
            return True
        return (now - self.last_run) >= self.interval_seconds


class Scheduler(Component):
    """Base scheduler: registers jobs and runs them on an interval."""

    name = "scheduler"

    def __init__(self) -> None:
        super().__init__()
        self._jobs: dict[str, Job] = {}

    def register(
        self,
        name: str,
        func: JobFunc,
        *,
        interval_seconds: float,
        enabled: bool = True,
    ) -> Job:
        if interval_seconds <= 0:
            raise SchedulerError(f"Job '{name}' needs a positive interval")
        if name in self._jobs:
            raise SchedulerError(f"Job '{name}' already registered")
        job = Job(name=name, interval_seconds=interval_seconds, func=func, enabled=enabled)
        self._jobs[name] = job
        self.log.debug("scheduler.register", job=name, interval=interval_seconds)
        return job

    def jobs(self) -> list[Job]:
        return list(self._jobs.values())

    def _run_due(self, now: float) -> list[str]:
        """Run all due jobs; return the names that ran."""
        ran: list[str] = []
        for job in self._jobs.values():
            if job.due(now):
                self._run_job(job, now)
                ran.append(job.name)
        return ran

    def _run_job(self, job: Job, now: float) -> None:
        try:
            job.func()
        except Exception:  # noqa: BLE001 - a failing job must not kill the loop
            self.log.exception("scheduler.job_failed", job=job.name)
        finally:
            job.last_run = now
            job.run_count += 1

    @abc.abstractmethod
    def start(self) -> None:
        """Begin executing jobs (blocking or background per implementation)."""

    @abc.abstractmethod
    def stop(self) -> None:
        """Stop executing jobs."""


class ManualScheduler(Scheduler):
    """Deterministic scheduler driven by explicit ``tick`` calls (for tests)."""

    def start(self) -> None:
        self.setup()

    def stop(self) -> None:
        self.teardown()

    def tick(self, now: float) -> list[str]:
        """Advance virtual time to ``now`` and run any due jobs."""
        return self._run_due(now)


class ThreadedScheduler(Scheduler):
    """Background-thread scheduler polling on a short resolution."""

    def __init__(self, resolution_seconds: float = 1.0) -> None:
        super().__init__()
        self._resolution = resolution_seconds
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def _loop(self) -> None:
        while not self._stop.is_set():
            self._run_due(time.monotonic())
            self._stop.wait(self._resolution)

    def start(self) -> None:
        if self._thread is not None:
            raise SchedulerError("Scheduler already started")
        self.setup()
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="acis-scheduler", daemon=True)
        self._thread.start()
        self.log.info("scheduler.started", jobs=len(self._jobs))

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=self._resolution * 2)
            self._thread = None
        self.teardown()
        self.log.info("scheduler.stopped")
