from celery import Celery
from celery.schedules import crontab
from app.config import settings

# Use PostgreSQL as broker and backend
broker_url = settings.database_url.replace("postgresql://", "db+postgresql://")

celery_app = Celery(
    "notionshare",
    broker=broker_url,
    backend=broker_url,
    include=["app.tasks.sync_tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Celery Beat schedule
celery_app.conf.beat_schedule = {
    "sync-all-enabled-configs": {
        "task": "app.tasks.sync_tasks.sync_all_enabled",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
    },
}
