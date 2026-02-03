"""
Command Executor - Runs agent tasks in the background
"""
import asyncio
import logging
from uuid import UUID

from backend.repositories.task_repository import TaskRepository, get_session_factory
from backend.agents.base.agent_registry import AgentRegistry
from backend.agents.base.agent_interface import AgentExecutionContext
from backend.core.task_callback import TaskProgressCallback
from backend.api.websocket import get_ws_manager
from backend.models.task_models import TaskUpdate, TaskStatus

logger = logging.getLogger(__name__)


async def execute_agent_task(task_id: UUID) -> None:
    """
    Execute an agent task in the background

    Steps:
    1. Load task from database
    2. Get agent from registry
    3. Create execution context with progress callback
    4. Execute agent
    5. Update task with result or error
    """
    try:
        # Get database session
        session_factory = get_session_factory()
        async with session_factory() as session:
            repo = TaskRepository(session)

            # Load task
            task = await repo.get_task(task_id)
            if not task:
                logger.error(f"Task {task_id} not found")
                return

            # Get agent from registry
            agent = AgentRegistry.get_agent(task.agent_id)
            if not agent:
                logger.error(f"Agent {task.agent_id} not found for task {task_id}")
                await repo.update_task(
                    task_id,
                    TaskUpdate(
                        status=TaskStatus.FAILED,
                        error_message=f"Agent {task.agent_id} not found in registry"
                    )
                )
                return

            # Create progress callback
            ws_manager = get_ws_manager()
            progress_callback = TaskProgressCallback(
                task_id=task_id,
                repo=repo,
                ws_manager=ws_manager
            )

            # Create execution context
            context = AgentExecutionContext(
                user_id=task.user_id,
                thread_id=task.thread_id,
                command=task.command_text,
                task_callback=progress_callback,
                metadata={
                    "task_id": str(task_id),
                    "agent_nickname": task.agent_nickname,
                }
            )

            logger.info(
                f"Executing agent {agent.agent_id} ({agent.nickname}) "
                f"for task {task_id}"
            )

            # Execute agent
            result = await agent.execute(
                command=task.command_text,
                context=context
            )

            # Update task with result
            if result.success:
                await repo.update_task(
                    task_id,
                    TaskUpdate(
                        status=TaskStatus.COMPLETED,
                        result=result.response,
                    )
                )
                logger.info(f"Task {task_id} completed successfully")

                # Broadcast completion event
                from backend.models.task_models import TaskStatusChangeEvent
                from datetime import datetime
                updated_task = await repo.get_task(task_id)
                if updated_task:
                    await ws_manager.broadcast_task_event(
                        TaskStatusChangeEvent(
                            task_id=task_id,
                            old_status=TaskStatus.IN_PROGRESS,
                            new_status=TaskStatus.COMPLETED,
                            timestamp=datetime.utcnow()
                        )
                    )
            else:
                await repo.update_task(
                    task_id,
                    TaskUpdate(
                        status=TaskStatus.FAILED,
                        error_message=result.error or "Unknown error",
                    )
                )
                logger.error(f"Task {task_id} failed: {result.error}")

                # Broadcast failure event
                from backend.models.task_models import TaskStatusChangeEvent
                from datetime import datetime
                await ws_manager.broadcast_task_event(
                    TaskStatusChangeEvent(
                        task_id=task_id,
                        old_status=TaskStatus.IN_PROGRESS,
                        new_status=TaskStatus.FAILED,
                        timestamp=datetime.utcnow()
                    )
                )

    except Exception as e:
        logger.exception(f"Unexpected error executing task {task_id}")

        # Try to update task status to failed
        try:
            session_factory = get_session_factory()
            async with session_factory() as session:
                repo = TaskRepository(session)
                await repo.update_task(
                    task_id,
                    TaskUpdate(
                        status=TaskStatus.FAILED,
                        error_message=f"Execution error: {str(e)}",
                    )
                )
        except Exception as update_error:
            logger.exception(f"Failed to update task {task_id} status: {update_error}")
