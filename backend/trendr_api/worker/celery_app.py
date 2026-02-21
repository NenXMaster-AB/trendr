from celery import Celery
from ..config import settings
from ..plugins.providers import register_all

celery_app = Celery(
    "trendr",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_track_started=True,
    task_time_limit=60 * 15,
    broker_connection_retry_on_startup=True,
)

# Worker runs in a separate process from FastAPI, so providers must be
# registered here as well.
register_all()
