"""Tests for structured logging."""

from __future__ import annotations

import json
import logging

from acis.core.logging import BoundLogger, JsonFormatter, configure_logging, get_logger


def _record(msg: str, context: dict | None = None) -> logging.LogRecord:
    record = logging.LogRecord("t", logging.INFO, __file__, 1, msg, (), None)
    if context is not None:
        record.context = context  # type: ignore[attr-defined]
    return record


def test_json_formatter_includes_context():
    formatted = JsonFormatter().format(_record("hello", {"platform": "instagram"}))
    payload = json.loads(formatted)
    assert payload["message"] == "hello"
    assert payload["level"] == "INFO"
    assert payload["platform"] == "instagram"


def test_configure_logging_is_idempotent():
    configure_logging(level="DEBUG", fmt="json")
    configure_logging(level="INFO", fmt="console")
    root = logging.getLogger()
    assert len(root.handlers) == 1
    assert root.level == logging.INFO


def test_bound_logger_binds_context(caplog):
    # NB: do not call configure_logging here - it replaces root handlers,
    # including the one pytest's caplog fixture installs. Rely on propagation.
    log = BoundLogger(get_logger("acis.test"), run_id="abc")
    with caplog.at_level(logging.INFO):
        log.info("did-thing", stage="research")
    record = next(r for r in caplog.records if r.getMessage() == "did-thing")
    assert record.context["run_id"] == "abc"
    assert record.context["stage"] == "research"


def test_bind_derives_child_context():
    log = BoundLogger(get_logger("acis.test"), a=1)
    child = log.bind(b=2)
    assert child._context == {"a": 1, "b": 2}
    assert log._context == {"a": 1}
