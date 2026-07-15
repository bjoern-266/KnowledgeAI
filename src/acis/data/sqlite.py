"""SQLite repository implementation.

Durable single-file persistence built on the standard library ``sqlite3``. Each
collection maps to one table with ``(id TEXT PRIMARY KEY, data TEXT)`` where
``data`` is the model serialised to JSON. Tables are created lazily on first
use, so no migration step is required for the foundation.

This backend is intentionally simple; if richer querying is ever needed it can
be replaced behind the :class:`Repository` protocol without touching callers.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from acis.core.errors import EntityNotFoundError, StorageError
from acis.data.repository import Repository

TModel = TypeVar("TModel", bound=BaseModel)

_VALID_COLLECTION = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


class SqliteRepository(Repository):
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._path))
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._known_tables: set[str] = set()

    # -- helpers --------------------------------------------------------------
    @staticmethod
    def _table(collection: str) -> str:
        if not _VALID_COLLECTION.match(collection):
            raise StorageError(f"Invalid collection name: {collection!r}")
        return f"coll_{collection}"

    def _ensure_table(self, collection: str) -> str:
        table = self._table(collection)
        if table not in self._known_tables:
            self._conn.execute(
                f"CREATE TABLE IF NOT EXISTS {table} (id TEXT PRIMARY KEY, data TEXT NOT NULL)"
            )
            self._conn.commit()
            self._known_tables.add(table)
        return table

    # -- Repository protocol --------------------------------------------------
    def save(self, collection: str, model: BaseModel) -> None:
        entity_id = getattr(model, "id", None)
        if not entity_id:
            raise ValueError("Model must have a non-empty 'id' to be saved")
        table = self._ensure_table(collection)
        self._conn.execute(
            f"INSERT INTO {table} (id, data) VALUES (?, ?) "
            "ON CONFLICT(id) DO UPDATE SET data=excluded.data",
            (entity_id, model.model_dump_json()),
        )
        self._conn.commit()

    def find(self, collection: str, entity_id: str, model_type: type[TModel]) -> TModel | None:
        table = self._ensure_table(collection)
        row = self._conn.execute(f"SELECT data FROM {table} WHERE id = ?", (entity_id,)).fetchone()
        if row is None:
            return None
        return model_type.model_validate_json(row[0])

    def get(self, collection: str, entity_id: str, model_type: type[TModel]) -> TModel:
        found = self.find(collection, entity_id, model_type)
        if found is None:
            raise EntityNotFoundError(
                f"{model_type.__name__} '{entity_id}' not found",
                context={"collection": collection, "id": entity_id},
            )
        return found

    def list(self, collection: str, model_type: type[TModel]) -> list[TModel]:
        table = self._ensure_table(collection)
        rows = self._conn.execute(f"SELECT data FROM {table} ORDER BY rowid").fetchall()
        return [model_type.model_validate_json(row[0]) for row in rows]

    def delete(self, collection: str, entity_id: str) -> None:
        table = self._ensure_table(collection)
        self._conn.execute(f"DELETE FROM {table} WHERE id = ?", (entity_id,))
        self._conn.commit()

    def clear(self, collection: str | None = None) -> None:
        if collection is None:
            for table in list(self._known_tables):
                self._conn.execute(f"DELETE FROM {table}")
        else:
            self._conn.execute(f"DELETE FROM {self._ensure_table(collection)}")
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
