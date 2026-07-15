"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from acis.core.config import Settings, load_settings
from acis.core.context import AppContext
from acis.data.memory import InMemoryRepository
from acis.integrations.base import build_integrations


@pytest.fixture
def settings(tmp_path) -> Settings:
    """Fully mock, in-memory settings isolated from disk state."""
    return load_settings(
        env="development",
        overrides={
            "storage": {"backend": "memory"},
            "integrations": {"default_mode": "mock"},
            "log": {"level": "WARNING"},
        },
    )


@pytest.fixture
def context(settings: Settings) -> AppContext:
    ctx = AppContext(
        settings,
        repository=InMemoryRepository(),
        integrations=build_integrations(settings),
    )
    ctx.startup()
    yield ctx
    ctx.shutdown()
