"""In-memory repository implementation.

Zero dependencies, no I/O - the default choice for tests and the mock
end-to-end run. Stores serialised JSON to mimic the round-tripping behaviour of
durable backends, so tests exercise the same (de)serialisation path.
"""

from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

from acis.core.errors import EntityNotFoundError
from acis.data.repository import Repository

TModel = TypeVar("TModel", bound=BaseModel)


class InMemoryRepository(Repository):
    def __init__(self) -> None:
        # collection -> {id -> json-string}
        self._store: dict[str, dict[str, str]] = {}

    def save(self, collection: str, model: BaseModel) -> None:
        entity_id = getattr(model, "id", None)
        if not entity_id:
            raise ValueError("Model must have a non-empty 'id' to be saved")
        self._store.setdefault(collection, {})[entity_id] = model.model_dump_json()

    def find(self, collection: str, entity_id: str, model_type: type[TModel]) -> TModel | None:
        raw = self._store.get(collection, {}).get(entity_id)
        if raw is None:
            return None
        return model_type.model_validate_json(raw)

    def get(self, collection: str, entity_id: str, model_type: type[TModel]) -> TModel:
        found = self.find(collection, entity_id, model_type)
        if found is None:
            raise EntityNotFoundError(
                f"{model_type.__name__} '{entity_id}' not found",
                context={"collection": collection, "id": entity_id},
            )
        return found

    def list(self, collection: str, model_type: type[TModel]) -> list[TModel]:
        return [
            model_type.model_validate_json(raw) for raw in self._store.get(collection, {}).values()
        ]

    def delete(self, collection: str, entity_id: str) -> None:
        self._store.get(collection, {}).pop(entity_id, None)

    def clear(self, collection: str | None = None) -> None:
        if collection is None:
            self._store.clear()
        else:
            self._store.pop(collection, None)
