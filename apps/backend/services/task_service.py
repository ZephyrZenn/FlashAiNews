"""Task management service for async agent execution."""

import uuid
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskInfo:
    def __init__(self, task_id: str, group_ids: list[int], focus: str):
        self.task_id = task_id
        self.group_ids = group_ids
        self.focus = focus
        self.status = TaskStatus.PENDING
        self.logs: List[dict] = []
        self.result: Optional[str] = None
        self.error: Optional[str] = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def add_log(self, message: str):
        """添加日志条目"""
        self.logs.append({
            "text": message,
            "time": datetime.now().isoformat()
        })
        self.updated_at = datetime.now()

    def to_dict(self):
        """转换为字典格式"""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "logs": self.logs,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

# 全局任务存储（生产环境建议使用 Redis）
_tasks: Dict[str, TaskInfo] = {}

def create_task(group_ids: list[int], focus: str = "") -> str:
    """创建新任务并返回任务ID"""
    task_id = str(uuid.uuid4())
    task = TaskInfo(task_id, group_ids, focus)
    _tasks[task_id] = task
    logger.info(f"Created task {task_id} for groups {group_ids}")
    return task_id

def get_task(task_id: str) -> Optional[TaskInfo]:
    """获取任务信息"""
    return _tasks.get(task_id)

async def execute_brief_generation_task(task_id: str):
    """异步执行brief生成任务"""
    task = _tasks.get(task_id)
    if not task:
        logger.error(f"Task {task_id} not found")
        return
    
    try:
        task.status = TaskStatus.RUNNING
        task.add_log("🚀 Agent启动，开始执行任务...")
        
        # 创建回调函数来记录日志，添加异常处理
        def on_step(message: str):
            """日志回调函数，实时记录日志"""
            try:
                if task and task.status == TaskStatus.RUNNING:
                    task.add_log(message)
            except Exception as e:
                logger.error(f"Error in on_step callback for task {task_id}: {e}", exc_info=True)
        
        # 执行总结（使用brief_service的异步方法）
        from apps.backend.services.brief_service import generate_brief_for_groups_async
        brief = await generate_brief_for_groups_async(
            group_ids=task.group_ids,
            focus=task.focus,
            on_step=on_step
        )
        
        # 再次检查任务是否存在（可能在执行过程中被清理）
        if task_id not in _tasks:
            logger.warning(f"Task {task_id} was removed during execution")
            return
        
        task.result = brief
        task.status = TaskStatus.COMPLETED
        task.add_log("✅ Agent执行完成，摘要已保存")
        
    except asyncio.CancelledError:
        logger.warning(f"Task {task_id} was cancelled")
        if task_id in _tasks:
            task = _tasks[task_id]
            task.status = TaskStatus.FAILED
            task.error = "任务被取消"
            task.add_log("❌ 任务被取消")
        raise
    except Exception as e:
        logger.exception(f"Task {task_id} failed: {e}")
        # 确保任务状态被更新
        if task_id in _tasks:
            task = _tasks[task_id]
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.add_log(f"❌ 执行失败: {str(e)}")

def cleanup_completed_tasks(max_age_hours: int = 24):
    """清理已完成的任务（超过指定小时数的）"""
    now = datetime.now()
    cutoff_time = now - timedelta(hours=max_age_hours)
    
    tasks_to_remove = []
    for task_id, task in _tasks.items():
        if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            if task.updated_at < cutoff_time:
                tasks_to_remove.append(task_id)
    
    for task_id in tasks_to_remove:
        del _tasks[task_id]
        logger.info(f"Cleaned up completed task {task_id}")
    
    if tasks_to_remove:
        logger.info(f"Cleaned up {len(tasks_to_remove)} completed tasks")
    
    return len(tasks_to_remove)

def get_task_count() -> dict:
    """获取任务统计信息"""
    status_count = {}
    for status in TaskStatus:
        status_count[status.value] = sum(
            1 for task in _tasks.values() if task.status == status
        )
    return {
        "total": len(_tasks),
        "by_status": status_count,
    }
