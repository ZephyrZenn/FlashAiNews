"""Scheduler management utilities for brief generation."""

import json
import logging
import os
import uuid
from datetime import time
from pathlib import Path
from typing import List, Optional, Tuple, Union

from apscheduler.schedulers.background import BackgroundScheduler

from apps.backend.crons import generate_scheduled_brief
from apps.backend.services.feed_service import retrieve_new_feeds

logger = logging.getLogger(__name__)

_scheduler: Optional[BackgroundScheduler] = None

# Schedule configuration file path
_SCHEDULE_CONFIG_FILE = os.getenv("SCHEDULE_CONFIG_FILE", "schedules.json")
_SCHEDULE_CONFIG_PATH = Path(_SCHEDULE_CONFIG_FILE)


class Schedule:
    """Internal schedule model."""

    def __init__(
        self,
        id: str,
        time: time,
        focus: str,
        group_ids: List[int],
        enabled: bool = True,
    ):
        self.id = id
        self.time = time
        self.focus = focus
        self.group_ids = group_ids
        self.enabled = enabled

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "time": self.time.strftime("%H:%M"),
            "focus": self.focus,
            "group_ids": self.group_ids,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Schedule":
        time_value = data["time"]
        # Handle both string and time object
        if isinstance(time_value, str):
            hour, minute = map(int, time_value.split(":"))
            schedule_time = time(hour, minute)
        elif isinstance(time_value, time):  # type: ignore
            schedule_time = time_value
        else:
            raise ValueError(f"Invalid time format: {time_value}")
        return cls(
            id=data["id"],
            time=schedule_time,
            focus=data["focus"],
            group_ids=data["group_ids"],
            enabled=data.get("enabled", True),
        )


def _get_scheduler() -> BackgroundScheduler:
    """Lazily instantiate and return the global scheduler."""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler()

        _scheduler.add_job(
            retrieve_new_feeds, "cron", id="retrieve_new_feeds", hour="*/6", minute=0
        )
    return _scheduler


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


def shutdown_scheduler() -> None:
    """Shutdown the scheduler if it is running."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown()
    _scheduler = None


def add_schedule_job(
    schedule_id: str, hour: int, minute: int, group_ids: list[int], focus: str
) -> None:
    """Add a scheduled brief generation job."""
    scheduler = _get_scheduler()
    job_id = f"schedule_{schedule_id}"

    # Remove existing job if any
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    scheduler.add_job(
        generate_scheduled_brief,
        "cron",
        id=job_id,
        hour=hour,
        minute=minute,
        args=[schedule_id, group_ids, focus],
    )
    logger.info(f"Added schedule job {job_id} at {hour:02d}:{minute:02d}")
    _start_if_needed()


def remove_schedule_job(schedule_id: str) -> None:
    """Remove a scheduled brief generation job."""
    scheduler = _get_scheduler()
    job_id = f"schedule_{schedule_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info(f"Removed schedule job {job_id}")


def _load_schedules() -> List[Schedule]:
    """Load schedules from configuration file."""
    if not _SCHEDULE_CONFIG_PATH.exists():
        return []

    try:
        with open(_SCHEDULE_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [Schedule.from_dict(item) for item in data]
    except Exception as e:
        logger.error(f"Error loading schedules: {e}")
        return []


def _save_schedules(schedules: List[Schedule]) -> None:
    """Save schedules to configuration file."""
    try:
        data = [s.to_dict() for s in schedules]
        with open(_SCHEDULE_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(schedules)} schedules to {_SCHEDULE_CONFIG_PATH}")
    except Exception as e:
        logger.error(f"Error saving schedules: {e}")
        raise


def get_all_schedules() -> List[Schedule]:
    """Get all schedules."""
    return _load_schedules()


def get_schedule(schedule_id: str) -> Optional[Schedule]:
    """Get a schedule by ID."""
    schedules = _load_schedules()
    for schedule in schedules:
        if schedule.id == schedule_id:
            return schedule
    return None


def create_schedule(time_str: str, focus: str, group_ids: List[int]) -> Schedule:
    """Create a new schedule."""
    schedules = _load_schedules()

    # Generate ID
    schedule_id = str(uuid.uuid4())[:8]

    # Parse time - handle both string and time object
    if isinstance(time_str, str):
        hour, minute = map(int, time_str.split(":"))
        schedule_time = time(hour, minute)
    elif isinstance(time_str, time):  # type: ignore
        schedule_time = time_str
        hour = schedule_time.hour
        minute = schedule_time.minute
    else:
        raise ValueError(f"Invalid time format: {time_str}")

    schedule = Schedule(
        id=schedule_id,
        time=schedule_time,
        focus=focus,
        group_ids=group_ids,
        enabled=True,
    )

    schedules.append(schedule)
    _save_schedules(schedules)

    # Add to scheduler
    add_schedule_job(schedule_id, hour, minute, group_ids, focus)

    logger.info(f"Created schedule {schedule_id} at {time_str}")
    return schedule


def update_schedule(
    schedule_id: str,
    time_str: Optional[str] = None,
    focus: Optional[str] = None,
    group_ids: Optional[List[int]] = None,
    enabled: Optional[bool] = None,
) -> Optional[Schedule]:
    """Update an existing schedule."""
    schedules = _load_schedules()

    for schedule in schedules:
        if schedule.id == schedule_id:
            if time_str is not None:
                # Parse time - handle both string and time object
                if isinstance(time_str, str):
                    hour, minute = map(int, time_str.split(":"))
                    schedule.time = time(hour, minute)
                elif isinstance(time_str, time):
                    schedule.time = time_str
                else:
                    raise ValueError(f"Invalid time format: {time_str}")
            if focus is not None:
                schedule.focus = focus
            if group_ids is not None:
                schedule.group_ids = group_ids
            if enabled is not None:
                schedule.enabled = enabled

            _save_schedules(schedules)

            # Update scheduler job
            remove_schedule_job(schedule_id)
            if schedule.enabled:
                add_schedule_job(
                    schedule.id,
                    schedule.time.hour,
                    schedule.time.minute,
                    schedule.group_ids,
                    schedule.focus,
                )

            logger.info(f"Updated schedule {schedule_id}")
            return schedule

    return None


def delete_schedule(schedule_id: str) -> bool:
    """Delete a schedule."""
    schedules = _load_schedules()
    original_count = len(schedules)
    schedules = [s for s in schedules if s.id != schedule_id]

    if len(schedules) < original_count:
        _save_schedules(schedules)
        remove_schedule_job(schedule_id)
        logger.info(f"Deleted schedule {schedule_id}")
        return True
    return False


def update_schedule_jobs() -> None:
    """Update all schedule jobs based on current schedule configuration."""
    schedules = get_all_schedules()
    scheduler = _get_scheduler()

    # Remove all existing schedule jobs
    for job in scheduler.get_jobs():
        if job.id.startswith("schedule_"):
            scheduler.remove_job(job.id)

    # Add enabled schedules
    for schedule in schedules:
        if schedule.enabled:
            add_schedule_job(
                schedule.id,
                schedule.time.hour,
                schedule.time.minute,
                schedule.group_ids,
                schedule.focus,
            )

    logger.info(f"Updated {len([s for s in schedules if s.enabled])} schedule jobs")
