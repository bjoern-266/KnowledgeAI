"""Repository abstraction.

A repository stores and retrieves domain models keyed by a *collection* name
(e.g. ``"topics"``, ``"content_pieces"``) and the model's ``id``. It is a thin,
generic key-collection store rather than an ORM - engines own their query
semantics and keep persistence concerns minimal.

The :class:`Repository` protocol is the contract; concrete backends live in
sibling modules. Use :func:`build_repository` to construct one from settings.
"""

from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel

from acis.core.config import Settings, StorageBackend
from acis.core.errors import ConfigError

TModel = TypeVar("TModel", bound=BaseModel)


@runtime_checkable
class Repository(Protocol):
    """Contract for a persistence backend.

    Implementations must round-trip pydantic models by serialising to JSON. The
    caller supplies the model ``type`` on read so the backend can rehydrate.
    """

    def save(self, collection: str, model: BaseModel) -> None:
        """Insert or update ``model`` (identified by ``model.id``)."""
        ...

    def get(self, collection: str, entity_id: str, model_type: type[TModel]) -> TModel:
        """Return the entity or raise :class:`EntityNotFoundError`."""
        ...

    def find(self, collection: str, entity_id: str, model_type: type[TModel]) -> TModel | None:
        """Return the entity or ``None`` if it does not exist."""
        ...

    def list(self, collection: str, model_type: type[TModel]) -> list[TModel]:
        """Return all entities in a collection (insertion order)."""
        ...

    def delete(self, collection: str, entity_id: str) -> None:
        """Remove an entity if present (no error if missing)."""
        ...

    def clear(self, collection: str | None = None) -> None:
        """Clear one collection, or everything when ``collection`` is None."""
        ...


def build_repository(settings: Settings) -> Repository:
    """Construct the configured repository backend."""
    backend = settings.storage.backend
    if backend is StorageBackend.MEMORY:
        from acis.data.memory import InMemoryRepository

        return InMemoryRepository()
    if backend is StorageBackend.SQLITE:
        from acis.data.sqlite import SqliteRepository

        path = settings.project_root / settings.storage.sqlite_path
        return SqliteRepository(path)
    raise ConfigError(f"Unknown storage backend: {backend}")
