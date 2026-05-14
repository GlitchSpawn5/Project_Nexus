"""
NEXUS — Celery Application
============================
Initialises Celery with Redis broker/backend from app config.
"""

from celery import Celery

from app.config import settings

celery = Celery(
    "nexus",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# JSON serialisation everywhere
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Autodiscover tasks inside app.worker.tasks
celery.autodiscover_tasks(["app.worker.tasks"])
