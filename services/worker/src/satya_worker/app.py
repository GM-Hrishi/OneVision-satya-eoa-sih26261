"""Celery app on Valkey (broker + result backend). Advisory processing only; synthetic data only.

Run: celery -A satya_worker.app worker --beat --loglevel INFO
Feature tasks (M2 to M13) arrive in later slices; stubs point to their P-n issue (docs/ISSUES.md).
"""

import logging
import os

from celery import Celery
from celery.schedules import crontab
from celery.signals import after_setup_logger

from satya_worker.logs import JsonFormatter


def _broker_url() -> str:
    url = os.environ.get("SATYA_VALKEY_URL", "")
    if not url:
        raise RuntimeError("SATYA_VALKEY_URL is not set")
    return url


def _result_url(broker: str) -> str:
    # Results in database 1, broker in database 0.
    base, _, _db = broker.rpartition("/")
    return f"{base}/1" if base.startswith(("redis://", "rediss://")) else broker


app = Celery("satya_worker", include=["satya_worker.tasks"])
_broker = os.environ.get("SATYA_VALKEY_URL", "memory://")
app.conf.update(
    broker_url=_broker,
    result_backend=_result_url(_broker) if _broker != "memory://" else "cache+memory://",
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    result_expires=86_400,
    task_time_limit=300,
    task_soft_time_limit=240,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_hijack_root_logger=False,
    broker_connection_retry_on_startup=True,
    timezone="Asia/Kolkata",
    enable_utc=True,
    beat_schedule_filename="/tmp/celerybeat-schedule",  # noqa: S108 - container-local, non-secret
    beat_schedule={
        # Daily monitoring sweep (Portal spec §8.6): expiries, compliance windows, trust anchors.
        # Placeholder only in slice 0; logic arrives with M4 (P-7) and M12/M13 (P-11, P-8).
        "daily-sweep": {"task": "satya.daily_sweep", "schedule": crontab(hour=2, minute=17)},
    },
)


@after_setup_logger.connect
def _json_logs(logger: logging.Logger, **_: object) -> None:
    for handler in logger.handlers:
        handler.setFormatter(JsonFormatter())
