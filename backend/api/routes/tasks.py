"""
Task management REST API
"""
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException

from backend.models.task_models import (
    AgentTask, TaskCreate, TaskUpdate, TaskStatusChangeEvent
)
from backend.repositories.task_repository import TaskRepository, get_db_session
from backend.api.websocket import get_ws_manager
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


async def get_repo(session: AsyncSession = Depends(get_db_session)) -> TaskRepository:
    """Get task repository dependency"""
    return TaskRepository(session)


@router.post("", response_model=AgentTask)
async def create_task(
    task: TaskCreate,
    repo: TaskRepository = Depends(get_repo),
):
    """Create new task"""
    agent_task = await repo.create_task(task)

    # Broadcast task created event via WebSocket
    ws_manager = get_ws_manager()
    await ws_manager.broadcast_task_event(
        TaskStatusChangeEvent(
            task_id=agent_task.id,
            old_status=None,
            new_status=agent_task.status,
            timestamp=agent_task.created_at
        )
    )

    return agent_task


@router.get("", response_model=list[AgentTask])
async def list_tasks(
    user_id: UUID,
    limit: int = 50,
    repo: TaskRepository = Depends(get_repo),
):
    """List tasks for a user"""
    return await repo.get_user_tasks(user_id, limit)


@router.get("/{task_id}", response_model=AgentTask)
async def get_task(
    task_id: UUID,
    repo: TaskRepository = Depends(get_repo),
):
    """Get specific task"""
    task = await repo.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=AgentTask)
async def update_task(
    task_id: UUID,
    update: TaskUpdate,
    repo: TaskRepository = Depends(get_repo),
):
    """Update task"""
    # Get old status before update
    old_task = await repo.get_task(task_id)
    if not old_task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Update task
    task = await repo.update_task(task_id, update)

    # Broadcast update via WebSocket
    ws_manager = get_ws_manager()
    if update.status:
        await ws_manager.broadcast_task_event(
            TaskStatusChangeEvent(
                task_id=task_id,
                old_status=old_task.status,
                new_status=update.status,
                timestamp=datetime.utcnow()
            )
        )

    return task
