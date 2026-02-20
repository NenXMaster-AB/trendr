import logging
import time

from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlmodel import Session, create_engine
from .config import settings

engine = create_engine(settings.database_url, echo=False, pool_pre_ping=True)
logger = logging.getLogger(__name__)


def wait_for_db() -> None:
    """Wait until a database connection can be established."""
    retries = 30
    wait_seconds = 2
    last_error: OperationalError | None = None

    for attempt in range(1, retries + 1):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return
        except OperationalError as exc:
            last_error = exc
            logger.warning(
                "Database not ready (attempt %s/%s). Retrying in %ss.",
                attempt,
                retries,
                wait_seconds,
            )
            if attempt < retries:
                time.sleep(wait_seconds)

    if last_error is not None:
        raise last_error


def get_session():
    with Session(engine) as session:
        yield session
