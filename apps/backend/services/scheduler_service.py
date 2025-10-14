"""Scheduler management utilities for brief generation."""

import logging
from datetime import time
from typing import Optional, Tuple, Union

from apscheduler.schedulers.background import BackgroundScheduler

from apps.backend.crons import generate_daily_brief

logger = logging.getLogger(__name__)

_BRIEF_JOB_ID = "generate_daily_brief"
_scheduler: Optional[BackgroundScheduler] = None


def _get_scheduler() -> BackgroundScheduler:
    """Lazily instantiate and return the global scheduler."""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler()
    return _scheduler


def _ensure_brief_job(hour: int, minute: int) -> None:
    """Create or update the daily brief job with the given schedule."""
    scheduler = _get_scheduler()
    job = scheduler.get_job(_BRIEF_JOB_ID)
    if job:
        scheduler.reschedule_job(
            _BRIEF_JOB_ID,
            trigger="cron",
            hour=hour,
            minute=minute,
        )
        logger.info("Rescheduled daily brief to %02d:%02d", hour, minute)
    else:
        scheduler.add_job(
            generate_daily_brief,
            "cron",
            id=_BRIEF_JOB_ID,
            hour=hour,
            minute=minute,
        )
        logger.info("Scheduled daily brief at %02d:%02d", hour, minute)


def _start_if_needed() -> None:
    scheduler = _get_scheduler()
    if not scheduler.running:
        scheduler.start()


def _parse_brief_time(brief_time: Union[str, time]) -> Tuple[int, int]:
    """Convert a supported time representation into hour/minute integers."""
    if isinstance(brief_time, time):
        return brief_time.hour, brief_time.minute

    hour_str, minute_str = brief_time.split(":", maxsplit=1)
    return int(hour_str), int(minute_str)


def start_scheduler(brief_time: Union[str, time]) -> None:
    """Start the scheduler and ensure the brief job is configured."""
    hour, minute = _parse_brief_time(brief_time)
    _ensure_brief_job(hour, minute)
    _start_if_needed()


def update_brief_schedule(brief_time: Union[str, time]) -> None:
    """Update the brief generation job schedule."""
    hour, minute = _parse_brief_time(brief_time)
    _ensure_brief_job(hour, minute)
    _start_if_needed()


def shutdown_scheduler() -> None:
    """Shutdown the scheduler if it is running."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown()
    _scheduler = None
