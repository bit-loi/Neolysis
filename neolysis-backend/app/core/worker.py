"""
Neolysis Celery Worker
======================
Background task queue powered by Redis as the broker.

Current tasks:
  - (placeholder) compute_docking_score — reserved for future live AutoDock Vina integration

Usage:
  celery -A app.core.worker worker --loglevel=info
"""
from celery import Celery
from app.config import settings

celery_app = Celery(
    "neolysis_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.core.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Limit task time to avoid runaway processes
    task_time_limit=300,
    task_soft_time_limit=240,
)
