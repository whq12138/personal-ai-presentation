"""
In-Process Async Task Queue — lightweight Celery alternative.

Runs tasks as asyncio background coroutines with DB-persisted status.
Supports progress reporting and cancellation.

Production upgrade path: swap with Celery + Redis, keeping the same Task model.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Callable, Awaitable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models.task import Task, TaskStatus
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class TaskManager:
    """Manages background task lifecycle with DB persistence."""

    def __init__(self):
        self._active_tasks: dict[str, asyncio.Task] = {}
        self._semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_TASKS)

    async def create_task(
        self,
        user_id: str,
        task_type: str,
        input_payload: dict,
    ) -> str:
        """Create a new task record and return the task_id."""
        async with async_session() as db:
            task = Task(
                user_id=user_id,
                task_type=task_type,
                status=TaskStatus.QUEUED,
                input_payload=json.dumps(input_payload),
            )
            db.add(task)
            await db.commit()
            await db.refresh(task)
            return task.id

    async def get_task_status(self, task_id: str, user_id: str) -> Optional[dict]:
        """Get the current status of a task (scoped to user)."""
        async with async_session() as db:
            result = await db.execute(
                select(Task).where(Task.id == task_id, Task.user_id == user_id)
            )
            task = result.scalar_one_or_none()
            if not task:
                return None
            return {
                "task_id": task.id,
                "status": task.status.value,
                "progress": task.progress,
                "progress_message": task.progress_message,
                "error": task.error_message,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            }

    async def get_task_result(self, task_id: str, user_id: str) -> Optional[dict]:
        """Get the completed result of a task. Returns None if not completed."""
        async with async_session() as db:
            result = await db.execute(
                select(Task).where(Task.id == task_id, Task.user_id == user_id)
            )
            task = result.scalar_one_or_none()
            if not task or task.status != TaskStatus.COMPLETED:
                return None
            return json.loads(task.result_json) if task.result_json else None

    async def enqueue(
        self,
        task_id: str,
        coro_factory: Callable[[str, AsyncSession, dict], Awaitable[dict]],
        input_payload: dict,
    ):
        """
        Enqueue a background task with concurrency control.
        The coro_factory receives (task_id, db_session, input_payload)
        and should return the result dict.

        Progress updates can be made via self.update_progress(task_id, ...)
        from within the coroutine.
        """
        async def _runner():
            async with self._semaphore:
                async with async_session() as db:
                    # Mark as processing
                    result = await db.execute(select(Task).where(Task.id == task_id))
                    task = result.scalar_one_or_none()
                    if not task:
                        return
                    task.status = TaskStatus.PROCESSING
                    task.started_at = datetime.now(timezone.utc)
                    task.progress = 0.05
                    task.progress_message = "Initializing AI pipeline..."
                    await db.commit()

                try:
                    async with async_session() as db:
                        output = await coro_factory(task_id, db, input_payload)

                    # Mark as completed
                    async with async_session() as db:
                        result = await db.execute(select(Task).where(Task.id == task_id))
                        task = result.scalar_one_or_none()
                        if task:
                            task.status = TaskStatus.COMPLETED
                            task.progress = 1.0
                            task.progress_message = "Done!"
                            task.result_json = json.dumps(output)
                            task.completed_at = datetime.now(timezone.utc)
                            await db.commit()

                except Exception as e:
                    logger.exception(f"Task {task_id} failed: {e}")
                    async with async_session() as db:
                        result = await db.execute(select(Task).where(Task.id == task_id))
                        task = result.scalar_one_or_none()
                        if task:
                            task.status = TaskStatus.FAILED
                            task.error_message = str(e)
                            task.completed_at = datetime.now(timezone.utc)
                            await db.commit()

                finally:
                    self._active_tasks.pop(task_id, None)

        t = asyncio.create_task(_runner())
        self._active_tasks[task_id] = t

    async def update_progress(
        self, task_id: str, progress: float, message: str
    ):
        """Update task progress (call from within the running coroutine)."""
        async with async_session() as db:
            result = await db.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one_or_none()
            if task:
                task.progress = min(1.0, max(0.0, progress))
                task.progress_message = message
                await db.commit()


# Global singleton
task_manager = TaskManager()
