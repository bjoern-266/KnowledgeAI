"""Persistence layer.

Storage is accessed exclusively through the :class:`Repository` protocol, so
business code never depends on a concrete backend. Two implementations ship in
the foundation:

* :class:`~acis.data.memory.InMemoryRepository` - fast, dependency-free,
  ideal for tests and the mock end-to-end run.
* :class:`~acis.data.sqlite.SqliteRepository` - durable single-file store for
  local/production single-node use.

Additional backends (Postgres, etc.) can be added later without touching
callers, as long as they satisfy the same protocol.
"""

from acis.data.memory import InMemoryRepository
from acis.data.repository import Repository, build_repository
from acis.data.sqlite import SqliteRepository

__all__ = [
    "InMemoryRepository",
    "Repository",
    "SqliteRepository",
    "build_repository",
]
