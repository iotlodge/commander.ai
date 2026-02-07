"""
Scheduled Commands API Routes
REST endpoints for managing scheduled NLP commands
"""

import logging
from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db_session
from backend.repositories.scheduled_command_repository import ScheduledCommandRepository
from backend.models.scheduled_command_models import (
    ScheduledCommand,
    ScheduledCommandCreate,
    ScheduledCommandUpdate,
    ScheduledCommandExecution,
)
from backend.core.scheduler import get_scheduler_service
from backend.jobs.scheduled_command_job import execute_scheduled_command_manual
from backend.auth.dependencies import MVP_USER_ID

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/scheduled-commands", tags=["scheduled-commands"])


@router.post("", response_model=ScheduledCommand)
async def create_scheduled_command(
    command: ScheduledCommandCreate,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user_id: UUID = Query(default=MVP_USER_ID, description="MVP user bypass"),
):
    """
    Create a new scheduled command

    The command will be automatically added to the scheduler if enabled.
    """
    repo = ScheduledCommandRepository(session)

    # Enforce user_id for MVP (in production, extract from JWT)
    command.user_id = user_id

    # Check schedule limit (max 50 per user)
    count = await repo.count_user_schedules(user_id)
    if count >= 50:
        raise HTTPException(
            status_code=400,
            detail="Maximum number of schedules (50) reached for this user"
        )

    # Create schedule in database
    schedule = await repo.create_scheduled_command(command)
    logger.info(f"Created scheduled command: {schedule.id}")

    # Add to scheduler if enabled
    if schedule.enabled:
        scheduler = get_scheduler_service()
        success = await scheduler.add_schedule(schedule.id)

        if not success:
            logger.warning(f"Failed to add schedule {schedule.id} to scheduler")

    return schedule


@router.get("")
async def list_scheduled_commands(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user_id: UUID = Query(default=MVP_USER_ID, description="MVP user bypass"),
    enabled: bool = Query(default=True, description="Filter to enabled schedules only"),
    agent_id: str | None = Query(default=None, description="Filter by agent ID"),
):
    """
    List all scheduled commands for the current user

    Optional filters:
    - enabled: Only return enabled schedules (default: true)
    - agent_id: Only return schedules for a specific agent
    """
    repo = ScheduledCommandRepository(session)
    schedules = await repo.get_user_scheduled_commands(
        user_id=user_id,
        enabled_only=enabled,
        agent_id=agent_id,
    )

    # Return in format expected by frontend
    return {"schedules": schedules}


@router.get("/{schedule_id}", response_model=ScheduledCommand)
async def get_scheduled_command(
    schedule_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user_id: UUID = Query(default=MVP_USER_ID, description="MVP user bypass"),
):
    """Get a specific scheduled command by ID"""
    repo = ScheduledCommandRepository(session)
    schedule = await repo.get_scheduled_command(schedule_id)

    if not schedule:
        raise HTTPException(status_code=404, detail="Scheduled command not found")

    # Verify ownership (in production, check JWT user_id)
    if schedule.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return schedule


@router.put("/{schedule_id}", response_model=ScheduledCommand)
async def update_scheduled_command(
    schedule_id: UUID,
    command_update: ScheduledCommandUpdate,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user_id: UUID = Query(default=MVP_USER_ID, description="MVP user bypass"),
):
    """
    Update a scheduled command

    If the schedule is enabled and schedule configuration changes,
    it will be automatically updated in the scheduler.
    """
    repo = ScheduledCommandRepository(session)

    # Verify ownership
    existing = await repo.get_scheduled_command(schedule_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Scheduled command not found")

    if existing.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Update in database
    updated = await repo.update_scheduled_command(schedule_id, command_update)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update scheduled command")

    # Update in scheduler if configuration changed
    scheduler = get_scheduler_service()
    if updated.enabled:
        await scheduler.update_schedule(schedule_id)
    else:
        await scheduler.remove_schedule(schedule_id)

    logger.info(f"Updated scheduled command: {schedule_id}")
    return updated


@router.delete("/{schedule_id}")
async def delete_scheduled_command(
    schedule_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user_id: UUID = Query(default=MVP_USER_ID, description="MVP user bypass"),
):
    """
    Delete a scheduled command

    This will also remove it from the scheduler.
    """
    repo = ScheduledCommandRepository(session)

    # Verify ownership
    existing = await repo.get_scheduled_command(schedule_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Scheduled command not found")

    if existing.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Remove from scheduler
    scheduler = get_scheduler_service()
    await scheduler.remove_schedule(schedule_id)

    # Delete from database
    success = await repo.delete_scheduled_command(schedule_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete scheduled command")

    logger.info(f"Deleted scheduled command: {schedule_id}")
    return {"message": "Scheduled command deleted successfully"}


@router.post("/{schedule_id}/enable")
async def enable_scheduled_command(
    schedule_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user_id: UUID = Query(default=MVP_USER_ID, description="MVP user bypass"),
):
    """
    Enable a scheduled command

    This will add it to the scheduler and start executing on schedule.
    """
    repo = ScheduledCommandRepository(session)

    # Verify ownership
    existing = await repo.get_scheduled_command(schedule_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Scheduled command not found")

    if existing.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Enable in database
    update = ScheduledCommandUpdate(enabled=True)
    updated = await repo.update_scheduled_command(schedule_id, update)

    # Add to scheduler
    scheduler = get_scheduler_service()
    success = await scheduler.add_schedule(schedule_id)

    if not success:
        logger.error(f"Failed to add schedule {schedule_id} to scheduler")
        raise HTTPException(status_code=500, detail="Failed to enable schedule in scheduler")

    logger.info(f"Enabled scheduled command: {schedule_id}")
    return updated


@router.post("/{schedule_id}/disable")
async def disable_scheduled_command(
    schedule_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user_id: UUID = Query(default=MVP_USER_ID, description="MVP user bypass"),
):
    """
    Disable a scheduled command

    This will remove it from the scheduler and stop execution.
    """
    repo = ScheduledCommandRepository(session)

    # Verify ownership
    existing = await repo.get_scheduled_command(schedule_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Scheduled command not found")

    if existing.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Disable in database
    update = ScheduledCommandUpdate(enabled=False)
    updated = await repo.update_scheduled_command(schedule_id, update)

    # Remove from scheduler
    scheduler = get_scheduler_service()
    await scheduler.remove_schedule(schedule_id)

    logger.info(f"Disabled scheduled command: {schedule_id}")
    return updated


@router.post("/{schedule_id}/execute")
async def execute_scheduled_command_now(
    schedule_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user_id: UUID = Query(default=MVP_USER_ID, description="MVP user bypass"),
):
    """
    Manually trigger execution of a scheduled command (Run Now button)

    This will execute the command immediately without affecting the schedule.
    """
    repo = ScheduledCommandRepository(session)

    # Verify ownership
    existing = await repo.get_scheduled_command(schedule_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Scheduled command not found")

    if existing.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Execute manually
    result = await execute_scheduled_command_manual(schedule_id)

    logger.info(f"Manually executed scheduled command: {schedule_id}")
    return result


@router.get("/{schedule_id}/executions")
async def get_execution_history(
    schedule_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user_id: UUID = Query(default=MVP_USER_ID, description="MVP user bypass"),
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of executions to return"),
):
    """
    Get execution history for a scheduled command

    Returns up to `limit` most recent executions (default 50, max 100).
    """
    repo = ScheduledCommandRepository(session)

    # Verify ownership
    existing = await repo.get_scheduled_command(schedule_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Scheduled command not found")

    if existing.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get execution history
    executions = await repo.get_command_executions(schedule_id, limit=limit)

    # Return in format expected by frontend
    return {"executions": executions}


@router.get("/scheduler/status")
async def get_scheduler_status():
    """
    Get current scheduler status and job information

    Useful for debugging and monitoring.
    """
    scheduler = get_scheduler_service()
    status = scheduler.get_scheduler_status()

    return status
