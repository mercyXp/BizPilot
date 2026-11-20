import logging
import sys
import uuid
from contextvars import ContextVar

from pythonjsonlogger.jsonlogger import JsonFormatter

request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get() or "-"
        return True


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s")
    )
    handler.addFilter(RequestIdFilter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

    logging.getLogger("uvicorn.access").handlers.clear()
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def new_request_id() -> str:
    value = str(uuid.uuid4())
    request_id_ctx.set(value)
    return value
