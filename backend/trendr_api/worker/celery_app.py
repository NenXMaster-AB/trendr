from celery import Celery
from ..config import settings
from ..observability import configure_logging
from ..plugins.providers import register_all

configure_logging()

celery_app = Celery(
    "trendr",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_track_started=True,
    task_time_limit=60 * 15,
    broker_connection_retry_on_startup=True,
    beat_schedule={
        "check-scheduled-posts": {
            "task": "trendr.check_scheduled_posts",
            "schedule": 60.0,
        },
    },
)

# Worker runs in a separate process from FastAPI, so providers must be
# registered here as well.
register_all()
