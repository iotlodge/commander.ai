"""
Task management REST API
"""
from datetime import datetime
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException

from backend.models.task_models import (
    AgentTask, TaskCreate, TaskUpdate, TaskStatusChangeEvent, TaskDeletedEvent, TaskStatus
)
from backend.repositories.task_repository import TaskRepository, get_db_session
from backend.api.websocket import get_ws_manager
from backend.auth.dependencies import get_current_active_user
from backend.auth.models import User
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


async def get_repo(session: AsyncSession = Depends(get_db_session)) -> TaskRepository:
    """Get task repository dependency"""
    return TaskRepository(session)


@router.post("", response_model=AgentTask)
async def create_task(
    task: TaskCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    repo: TaskRepository = Depends(get_repo),
):
    """Create new task (requires authentication)"""
    # Override user_id from token (don't trust client-provided user_id)
    task.user_id = current_user.id
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
    current_user: Annotated[User, Depends(get_current_active_user)],
    limit: int = 50,
    repo: TaskRepository = Depends(get_repo),
):
    """List tasks for authenticated user"""
    # Use user_id from token for security
    return await repo.get_user_tasks(current_user.id, limit)


@router.get("/{task_id}", response_model=AgentTask)
async def get_task(
    task_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    repo: TaskRepository = Depends(get_repo),
):
    """Get specific task (requires authentication)"""
    task = await repo.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Verify task belongs to current user
    if task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return task


@router.patch("/{task_id}", response_model=AgentTask)
async def update_task(
    task_id: UUID,
    update: TaskUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    repo: TaskRepository = Depends(get_repo),
):
    """Update task (requires authentication)"""
    # Get old status before update
    old_task = await repo.get_task(task_id)
    if not old_task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Verify task belongs to current user
    if old_task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

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


@router.delete("/{task_id}")
async def delete_task(
    task_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    repo: TaskRepository = Depends(get_repo),
):
    """Delete a specific task (requires authentication)"""
    # Check if task exists
    task = await repo.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Verify task belongs to current user
    if task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Delete the task
    await repo.delete_task(task_id)

    # Broadcast deletion event via WebSocket
    ws_manager = get_ws_manager()
    await ws_manager.broadcast_task_event(
        TaskDeletedEvent(
            task_id=task_id,
            timestamp=datetime.utcnow()
        )
    )

    return {"deleted": True, "task_id": str(task_id)}


@router.delete("/purge/completed")
async def purge_completed_tasks(
    current_user: Annotated[User, Depends(get_current_active_user)],
    repo: TaskRepository = Depends(get_repo),
):
    """Delete all completed tasks for authenticated user"""
    # Use user_id from token for security
    deleted_ids = await repo.delete_tasks_by_status(current_user.id, TaskStatus.COMPLETED)

    # Broadcast deletion events via WebSocket
    ws_manager = get_ws_manager()
    for task_id in deleted_ids:
        await ws_manager.broadcast_task_event(
            TaskDeletedEvent(
                task_id=task_id,
                timestamp=datetime.utcnow()
            )
        )

    return {"deleted_count": len(deleted_ids), "task_ids": deleted_ids}


@router.delete("/purge/failed")
async def purge_failed_tasks(
    current_user: Annotated[User, Depends(get_current_active_user)],
    repo: TaskRepository = Depends(get_repo),
):
    """Delete all failed tasks for authenticated user"""
    # Use user_id from token for security
    deleted_ids = await repo.delete_tasks_by_status(current_user.id, TaskStatus.FAILED)

    # Broadcast deletion events via WebSocket
    ws_manager = get_ws_manager()
    for task_id in deleted_ids:
        await ws_manager.broadcast_task_event(
            TaskDeletedEvent(
                task_id=task_id,
                timestamp=datetime.utcnow()
            )
        )

    return {"deleted_count": len(deleted_ids), "task_ids": deleted_ids}
