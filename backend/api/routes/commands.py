"""
Command submission REST API
Combines command parsing with task creation and agent execution
"""
import asyncio
from typing import Annotated
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.models.task_models import TaskCreate, AgentTask
from backend.repositories.task_repository import TaskRepository, get_db_session
from backend.core.command_parser import CommandParser
from backend.agents.base.agent_registry import AgentRegistry
from backend.api.websocket import get_ws_manager
from backend.auth.dependencies import get_current_active_user
from backend.auth.models import User
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/commands", tags=["commands"])


class CommandSubmissionRequest(BaseModel):
    """Request to submit a command"""
    text: str  # Removed user_id - will use from token


async def get_repo(session: AsyncSession = Depends(get_db_session)) -> TaskRepository:
    """Get task repository dependency"""
    return TaskRepository(session)


@router.post("", response_model=AgentTask)
async def submit_command(
    command: CommandSubmissionRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    repo: TaskRepository = Depends(get_repo),
):
    """
    Submit a command for processing (requires authentication)

    1. Parse command to determine target agent
    2. Create task in database
    3. Start agent execution in background
    4. Return task immediately
    """
    # Parse command to extract agent mentions
    parsed = CommandParser.parse(command.text)
    target_agent_id = CommandParser.get_target_agent_id(parsed)

    # Get agent from registry
    agent = AgentRegistry.get_agent(target_agent_id)
    if not agent:
        raise HTTPException(
            status_code=400,
            detail=f"Agent {target_agent_id} not found in registry"
        )

    # Create task using authenticated user's ID
    task_create = TaskCreate(
        user_id=current_user.id,  # Use user_id from token
        agent_id=target_agent_id,
        thread_id=uuid4(),
        command_text=command.text,
    )

    task = await repo.create_task(task_create)

    # Broadcast task created event
    from backend.models.task_models import TaskStatusChangeEvent
    ws_manager = get_ws_manager()
    await ws_manager.broadcast_task_event(
        TaskStatusChangeEvent(
            task_id=task.id,
            old_status=None,
            new_status=task.status,
            timestamp=task.created_at
        )
    )

    # Start agent execution in background
    from backend.core.command_executor import execute_agent_task
    asyncio.create_task(execute_agent_task(task.id))

    return task
