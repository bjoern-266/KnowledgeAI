"""Tests for both repository backends via the shared protocol."""

from __future__ import annotations

import pytest

from acis.core.errors import EntityNotFoundError
from acis.data.memory import InMemoryRepository
from acis.data.sqlite import SqliteRepository
from acis.domain.enums import TopicCategory
from acis.domain.models import Topic


def _repos(tmp_path):
    return [
        ("memory", InMemoryRepository()),
        ("sqlite", SqliteRepository(tmp_path / "test.db")),
    ]


@pytest.fixture(params=["memory", "sqlite"])
def repo(request, tmp_path):
    if request.param == "memory":
        return InMemoryRepository()
    return SqliteRepository(tmp_path / "test.db")


def _topic(title: str = "Test") -> Topic:
    return Topic(title=title, category=TopicCategory.SCIENCE)


def test_save_and_get_roundtrip(repo):
    topic = _topic("Black Holes")
    repo.save("topics", topic)
    loaded = repo.get("topics", topic.id, Topic)
    assert loaded.id == topic.id
    assert loaded.title == "Black Holes"
    assert loaded.category is TopicCategory.SCIENCE


def test_find_missing_returns_none(repo):
    assert repo.find("topics", "nope", Topic) is None


def test_get_missing_raises(repo):
    with pytest.raises(EntityNotFoundError):
        repo.get("topics", "nope", Topic)


def test_list_returns_all(repo):
    a, b = _topic("A"), _topic("B")
    repo.save("topics", a)
    repo.save("topics", b)
    ids = {t.id for t in repo.list("topics", Topic)}
    assert ids == {a.id, b.id}


def test_update_overwrites(repo):
    topic = _topic("Old")
    repo.save("topics", topic)
    topic.title = "New"
    repo.save("topics", topic)
    assert repo.get("topics", topic.id, Topic).title == "New"
    assert len(repo.list("topics", Topic)) == 1


def test_delete_and_clear(repo):
    topic = _topic()
    repo.save("topics", topic)
    repo.delete("topics", topic.id)
    assert repo.find("topics", topic.id, Topic) is None
    repo.save("topics", _topic())
    repo.clear("topics")
    assert repo.list("topics", Topic) == []
