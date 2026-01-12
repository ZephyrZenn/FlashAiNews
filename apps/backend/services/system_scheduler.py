"""System-level scheduler for maintenance tasks (separate from user schedules)."""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from apps.backend.services import task_service
from apps.backend.services.feed_service import retrieve_new_feeds

logger = logging.getLogger(__name__)

_system_scheduler: BackgroundScheduler | None = None


def init_system_scheduler():
    """初始化系统定时任务调度器"""
    global _system_scheduler
    if _system_scheduler is None:
        _system_scheduler = BackgroundScheduler()
        _system_scheduler.start()
        logger.info("System scheduler started")

    # 添加清理已完成任务的任务（每小时执行一次）
    _system_scheduler.add_job(
        cleanup_completed_tasks_job,
        trigger=IntervalTrigger(hours=1),
        id="cleanup_completed_tasks",
        name="Cleanup completed tasks",
        replace_existing=True,
    )
    _system_scheduler.add_job(
        retrieve_new_feeds, trigger=IntervalTrigger(hours=6), id="retrieve_new_feeds", name="Retrieve new feeds", replace_existing=True,
    )
    logger.info("Added cleanup_completed_tasks job to system scheduler")


def cleanup_completed_tasks_job():
    """清理已完成任务的定时任务"""
    try:
        count = task_service.cleanup_completed_tasks(max_age_hours=24)
        logger.info(f"Cleanup job completed, removed {count} tasks")
    except Exception as e:
        logger.exception(f"Error in cleanup job: {e}")


def shutdown_system_scheduler():
    """关闭系统定时任务调度器"""
    global _system_scheduler
    if _system_scheduler and _system_scheduler.running:
        _system_scheduler.shutdown()
        logger.info("System scheduler shut down")
    _system_scheduler = None
