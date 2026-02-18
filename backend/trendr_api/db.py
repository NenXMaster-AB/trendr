import logging
import time

from sqlalchemy.exc import OperationalError
from sqlmodel import SQLModel, Session, create_engine
from .config import settings

engine = create_engine(settings.database_url, echo=False, pool_pre_ping=True)
logger = logging.getLogger(__name__)


def init_db() -> None:
    # For a skeleton, create tables on startup.
    # In production: use Alembic migrations.
    retries = 30
    wait_seconds = 2
    last_error: OperationalError | None = None

    for attempt in range(1, retries + 1):
        try:
            SQLModel.metadata.create_all(engine)
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
