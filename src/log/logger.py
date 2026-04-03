import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

_request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


def get_request_id() -> str:
    return _request_id_var.get()


def set_request_id(request_id: str) -> None:
    _request_id_var.set(request_id)


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "request_id": get_request_id(),
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "__dict__"):
            for key, value in record.__dict__.items():
                if key not in (
                    "msg",
                    "args",
                    "levelname",
                    "levelno",
                    "name",
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
                    "taskName",
                ):
                    log_entry[key] = value
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


class ColoredFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        request_id = get_request_id()[:8]
        ts = datetime.now(UTC).strftime("%H:%M:%S.%f")[:-3]
        prefix = f"[{ts}][{request_id}] {color}{record.levelname:<8}{self.RESET}"
        location = f"{record.name}:{record.lineno}"
        message = record.getMessage()
        return f"{prefix} {location} - {message}"


def configure_logging(is_production: bool = False) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter() if is_production else ColoredFormatter())

    root = logging.getLogger()
    root.setLevel(logging.DEBUG if not is_production else logging.INFO)
    root.handlers.clear()
    root.addHandler(handler)

    # Quiet noisy libraries
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("passlib").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def generate_request_id() -> str:
    return uuid4().hex
