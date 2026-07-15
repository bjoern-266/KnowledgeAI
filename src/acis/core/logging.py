"""Structured logging for ACIS.

Provides two formatters selectable via config:

* ``console`` - human-readable, for local development.
* ``json``    - one JSON object per line, for production log pipelines.

A :class:`BoundLogger` binds contextual key/value pairs (e.g. a ``run_id`` or
the current pipeline stage) that are then attached to every log record and
rendered by both formatters.

Usage::

    from acis.core.logging import configure_logging, get_logger
    configure_logging(level="INFO", fmt="json")
    log = get_logger(__name__)
    log.info("published", extra={"context": {"platform": "instagram"}})
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

_RESERVED = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys()) | {
    "message",
    "asctime",
    "context",
}


class JsonFormatter(logging.Formatter):
    """Render log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        context = getattr(record, "context", None)
        if isinstance(context, dict):
            payload.update(context)
        # Include any ad-hoc `extra=` attributes that are not LogRecord internals.
        for key, value in record.__dict__.items():
            if key not in _RESERVED and key not in payload:
                payload[key] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, ensure_ascii=False)


class ConsoleFormatter(logging.Formatter):
    """Compact, readable formatter for terminals."""

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.fromtimestamp(record.created, tz=UTC).strftime("%H:%M:%S")
        base = f"{ts} {record.levelname:<7} {record.name}: {record.getMessage()}"
        context = getattr(record, "context", None)
        if isinstance(context, dict) and context:
            rendered = " ".join(f"{k}={v}" for k, v in context.items())
            base = f"{base} [{rendered}]"
        if record.exc_info:
            base = f"{base}\n{self.formatException(record.exc_info)}"
        return base


def configure_logging(level: str = "INFO", fmt: str = "console") -> None:
    """Configure the root logger. Idempotent - safe to call more than once."""
    formatter: logging.Formatter = JsonFormatter() if fmt.lower() == "json" else ConsoleFormatter()
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level.upper())
    # Replace existing handlers to keep configuration deterministic.
    for existing in list(root.handlers):
        root.removeHandler(existing)
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger."""
    return logging.getLogger(name)


class BoundLogger:
    """A logger wrapper that attaches fixed context to every emitted record.

    ``log = BoundLogger(get_logger(__name__), run_id="abc")`` will include
    ``run_id=abc`` on all messages. Use :meth:`bind` to derive a child with
    additional context.
    """

    def __init__(self, logger: logging.Logger, **context: Any) -> None:
        self._logger = logger
        self._context = context

    def bind(self, **context: Any) -> BoundLogger:
        merged = {**self._context, **context}
        return BoundLogger(self._logger, **merged)

    def _log(self, level: int, msg: str, **context: Any) -> None:
        merged = {**self._context, **context}
        self._logger.log(level, msg, extra={"context": merged})

    def debug(self, msg: str, **context: Any) -> None:
        self._log(logging.DEBUG, msg, **context)

    def info(self, msg: str, **context: Any) -> None:
        self._log(logging.INFO, msg, **context)

    def warning(self, msg: str, **context: Any) -> None:
        self._log(logging.WARNING, msg, **context)

    def error(self, msg: str, **context: Any) -> None:
        self._log(logging.ERROR, msg, **context)

    def exception(self, msg: str, **context: Any) -> None:
        merged = {**self._context, **context}
        self._logger.exception(msg, extra={"context": merged})
