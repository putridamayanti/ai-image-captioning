# celery_app.py
from celery import Celery

celery = Celery(
    "demo",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
    task_serializer='json',
)

celery.conf.task_routes = {
    "caption.generate": {"queue": "emails"},
}

from worker import tasks
