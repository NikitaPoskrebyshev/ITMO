from __future__ import annotations

import logging


class KeyValueFormatter(logging.Formatter):
    """Key value formatter."""

    _reserved_fields = {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "message",
        "asctime",
    }

    def format(self, record: logging.LogRecord) -> str:
        base_message = f"level={record.levelname} logger={record.name} message={record.getMessage()}"
        extras: list[str] = []
        for key, value in record.__dict__.items():
            if key in self._reserved_fields:
                continue
            extras.append(f"{key}={value}")
        if extras:
            return f"{base_message} {' '.join(sorted(extras))}"
        return base_message


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(KeyValueFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
