import logging
import sys

import structlog


def configure_logging() -> None:
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    # SQLAlchemy's echo=True already installs its own handler on this logger
    # (the engine is created before basicConfig runs); without this, every SQL
    # statement would also propagate to the root handler and print twice.
    logging.getLogger("sqlalchemy.engine.Engine").propagate = False

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True, key="timestamp"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)


def bind_user_id(user_id: str) -> None:
    """Attach the authenticated user's id to all log lines for this request."""
    structlog.contextvars.bind_contextvars(user_id=user_id)
