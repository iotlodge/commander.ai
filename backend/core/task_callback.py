"""
Task progress callbacks for agent execution
"""
from uuid import UUID
from datetime import datetime

from backend.models.task_models import (
    TaskStatus, TaskStatusChangeEvent, TaskProgressEvent,
    ConsultationStartedEvent, ConsultationCompletedEvent
)
from backend.repositories.task_repository import TaskRepository
from backend.api.websocket import TaskWebSocketManager


class TaskProgressCallback:
    """Callback for tracking agent execution progress"""

    def __init__(
        self,
        task_id: UUID,
        repo: TaskRepository,
        ws_manager: TaskWebSocketManager
    ):
        self.task_id = task_id
        self.repo = repo
        self.ws_manager = ws_manager

    async def on_status_change(self, old_status: TaskStatus, new_status: TaskStatus):
        """Called when task status changes"""
        kwargs = {}
        if new_status == TaskStatus.IN_PROGRESS:
            kwargs['started_at'] = datetime.utcnow()
        elif new_status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            kwargs['completed_at'] = datetime.utcnow()

        await self.repo.set_status(self.task_id, new_status, **kwargs)

        event = TaskStatusChangeEvent(
            task_id=self.task_id,
            old_status=old_status,
            new_status=new_status,
            timestamp=datetime.utcnow()
        )
        await self.ws_manager.broadcast_task_event(event)

    async def on_progress_update(self, progress: int, current_node: str):
        """Called when agent reports progress"""
        await self.repo.update_progress(self.task_id, progress, current_node)

        event = TaskProgressEvent(
            task_id=self.task_id,
            progress_percentage=progress,
            current_node=current_node,
            timestamp=datetime.utcnow()
        )
        await self.ws_manager.broadcast_task_event(event)

    async def on_consultation_started(
        self,
        requesting_agent_id: str,
        target_agent_id: str,
        target_nickname: str
    ):
        """Called when agent consults another agent"""
        from backend.models.task_models import TaskUpdate

        await self.repo.update_task(
            self.task_id,
            TaskUpdate(
                status=TaskStatus.TOOL_CALL,
                consultation_target_id=target_agent_id
            )
        )

        event = ConsultationStartedEvent(
            task_id=self.task_id,
            requesting_agent_id=requesting_agent_id,
            target_agent_id=target_agent_id,
            target_agent_nickname=target_nickname,
            timestamp=datetime.utcnow()
        )
        await self.ws_manager.broadcast_task_event(event)

    async def on_consultation_completed(self):
        """Called when consultation completes"""
        event = ConsultationCompletedEvent(
            task_id=self.task_id,
            timestamp=datetime.utcnow()
        )
        await self.ws_manager.broadcast_task_event(event)
