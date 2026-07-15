"""Tests for the scheduler abstraction."""

from __future__ import annotations

import pytest

from acis.core.errors import SchedulerError
from acis.core.scheduler import ManualScheduler


def test_job_runs_when_due():
    scheduler = ManualScheduler()
    calls: list[int] = []
    scheduler.register("job", lambda: calls.append(1), interval_seconds=10)

    assert scheduler.tick(now=0) == ["job"]  # first run (last_run=0, due immediately)
    assert scheduler.tick(now=5) == []  # not yet due
    assert scheduler.tick(now=10) == ["job"]  # due again
    assert len(calls) == 2


def test_disabled_job_does_not_run():
    scheduler = ManualScheduler()
    scheduler.register("job", lambda: None, interval_seconds=1, enabled=False)
    assert scheduler.tick(now=100) == []


def test_duplicate_registration_raises():
    scheduler = ManualScheduler()
    scheduler.register("job", lambda: None, interval_seconds=1)
    with pytest.raises(SchedulerError):
        scheduler.register("job", lambda: None, interval_seconds=1)


def test_non_positive_interval_raises():
    scheduler = ManualScheduler()
    with pytest.raises(SchedulerError):
        scheduler.register("job", lambda: None, interval_seconds=0)


def test_failing_job_does_not_break_loop():
    scheduler = ManualScheduler()
    ran: list[str] = []

    def boom() -> None:
        raise RuntimeError("boom")

    scheduler.register("bad", boom, interval_seconds=1)
    scheduler.register("good", lambda: ran.append("good"), interval_seconds=1)

    result = scheduler.tick(now=1)
    assert set(result) == {"bad", "good"}
    assert ran == ["good"]
