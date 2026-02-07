"""
Scheduled Command Job
Executes scheduled commands by creating AgentTasks and tracking execution
"""

import logging
from datetime import datetime
from uuid import UUID, uuid4

from backend.core.database import get_session_maker
from backend.repositories.scheduled_command_repository import ScheduledCommandRepository
from backend.repositories.task_repository import TaskRepository, TaskCreate
from backend.models.scheduled_command_models import (
    ScheduledCommandExecutionCreate,
    ScheduledCommandExecutionUpdate,
    ExecutionStatus,
)
from backend.models.task_models import TaskStatus

logger = logging.getLogger(__name__)


async def execute_scheduled_command(schedule_id_str: str):
    """
    Execute a scheduled command by creating an AgentTask

    This function is called by APScheduler at the scheduled time.

    Args:
        schedule_id_str: String representation of the schedule UUID

    Flow:
        1. Load schedule from database
        2. Create execution record
        3. Create AgentTask via TaskRepository
        4. Execute task via existing execute_agent_task function
        5. Update execution record with results
        6. Calculate and update next_run_at
    """
    schedule_id = UUID(schedule_id_str)
    logger.info(f"Executing scheduled command: {schedule_id}")

    session_maker = get_session_maker()

    async with session_maker() as session:
        cmd_repo = ScheduledCommandRepository(session)
        task_repo = TaskRepository(session)

        try:
            # 1. Load schedule
            schedule = await cmd_repo.get_scheduled_command(schedule_id)
            if not schedule:
                logger.error(f"Schedule {schedule_id} not found")
                return

            if not schedule.enabled:
                logger.warning(f"Schedule {schedule_id} is disabled, skipping execution")
                return

            # 2. Create execution record
            execution_create = ScheduledCommandExecutionCreate(
                scheduled_command_id=schedule.id,
                triggered_at=datetime.utcnow(),
            )
            execution = await cmd_repo.create_execution(execution_create)
            logger.info(f"Created execution record: {execution.id}")

            # 3. Create AgentTask
            try:
                # Parse command to extract agent_id (already validated in schedule)
                # For MVP, we trust the stored agent_id
                task_create = TaskCreate(
                    user_id=schedule.user_id,
                    agent_id=schedule.agent_id,
                    thread_id=uuid4(),  # Create new thread for each scheduled execution
                    command_text=schedule.command_text,
                )

                task = await task_repo.create_task(task_create)
                logger.info(f"Created task {task.id} for scheduled command {schedule_id}")

                # Broadcast task created event to WebSocket clients
                try:
                    from backend.models.task_models import TaskStatusChangeEvent
                    from backend.api.websocket import get_ws_manager

                    ws_manager = get_ws_manager()
                    await ws_manager.broadcast_task_event(
                        TaskStatusChangeEvent(
                            task_id=task.id,
                            old_status=None,  # Indicates new task creation
                            new_status=task.status,
                            timestamp=task.created_at
                        )
                    )
                    logger.info(f"Broadcasted task_created event for task {task.id}")
                except Exception as e:
                    logger.warning(f"Failed to broadcast task_created event: {e}")

                # Update execution with task_id
                await cmd_repo.update_execution(
                    execution.id,
                    ScheduledCommandExecutionUpdate(
                        task_id=task.id,
                        started_at=datetime.utcnow(),
                        status=ExecutionStatus.RUNNING,
                    )
                )

            except Exception as e:
                logger.error(f"Failed to create task for schedule {schedule_id}: {e}", exc_info=True)
                # Update execution with error
                await cmd_repo.update_execution(
                    execution.id,
                    ScheduledCommandExecutionUpdate(
                        status=ExecutionStatus.FAILED,
                        error_message=f"Failed to create task: {str(e)}",
                        completed_at=datetime.utcnow(),
                    )
                )
                return

            # 4. Execute task asynchronously (existing pipeline)
            # Note: The task will be picked up by the agent execution system
            # We don't wait for completion here - execution tracking happens via WebSocket events
            # and task status updates

            # Import the task executor
            try:
                from backend.core.command_executor import execute_agent_task

                # Execute task in background (don't wait for completion in this job)
                # The execution will update task status, and we'll check it later
                await execute_agent_task(task.id)

                # After execution, get updated task to collect metrics
                updated_task = await task_repo.get_task(task.id)

                if updated_task:
                    # Calculate execution duration
                    duration_ms = None
                    if updated_task.started_at and updated_task.completed_at:
                        duration = updated_task.completed_at - updated_task.started_at
                        duration_ms = int(duration.total_seconds() * 1000)

                    # Extract metrics from task metadata
                    tokens_used = None
                    llm_calls = None
                    if updated_task.metadata and 'execution_metrics' in updated_task.metadata:
                        metrics = updated_task.metadata['execution_metrics']
                        tokens_used = metrics.get('total_tokens')
                        llm_calls = metrics.get('llm_calls')

                    # Determine execution status
                    exec_status = ExecutionStatus.SUCCESS
                    error_msg = None
                    if updated_task.status == TaskStatus.FAILED:
                        exec_status = ExecutionStatus.FAILED
                        error_msg = updated_task.error_message
                    elif updated_task.status == TaskStatus.COMPLETED:
                        exec_status = ExecutionStatus.SUCCESS

                    # Update execution record with results
                    await cmd_repo.update_execution(
                        execution.id,
                        ScheduledCommandExecutionUpdate(
                            completed_at=datetime.utcnow(),
                            status=exec_status,
                            result_summary=updated_task.result[:500] if updated_task.result else None,
                            error_message=error_msg,
                            execution_duration_ms=duration_ms,
                            tokens_used=tokens_used,
                            llm_calls=llm_calls,
                        )
                    )

                    logger.info(
                        f"Scheduled command {schedule_id} execution completed: "
                        f"status={exec_status}, duration={duration_ms}ms, tokens={tokens_used}"
                    )
                else:
                    logger.warning(f"Could not retrieve updated task {task.id}")

            except Exception as e:
                logger.error(f"Failed to execute task {task.id}: {e}", exc_info=True)
                # Update execution with error
                await cmd_repo.update_execution(
                    execution.id,
                    ScheduledCommandExecutionUpdate(
                        status=ExecutionStatus.FAILED,
                        error_message=f"Task execution failed: {str(e)}",
                        completed_at=datetime.utcnow(),
                    )
                )

            # 6. Calculate and update next_run_at
            try:
                from backend.core.scheduler import get_scheduler_service

                scheduler = get_scheduler_service()
                next_run = scheduler._calculate_next_run(schedule)

                if next_run:
                    await cmd_repo.update_next_run(
                        schedule.id,
                        next_run_at=next_run,
                        last_run_at=datetime.utcnow(),
                        last_run_status=exec_status if 'exec_status' in locals() else ExecutionStatus.SUCCESS,
                    )
                    logger.info(f"Next run for schedule {schedule_id}: {next_run}")

            except Exception as e:
                logger.error(f"Failed to update next_run_at for schedule {schedule_id}: {e}")

        except Exception as e:
            logger.error(f"Unexpected error executing scheduled command {schedule_id}: {e}", exc_info=True)


async def execute_scheduled_command_manual(schedule_id: UUID) -> dict:
    """
    Manually trigger a scheduled command execution (for "Run Now" button)

    Args:
        schedule_id: UUID of the schedule to execute

    Returns:
        Dictionary with execution results
    """
    logger.info(f"Manual execution triggered for schedule: {schedule_id}")

    try:
        await execute_scheduled_command(str(schedule_id))

        return {
            "status": "success",
            "message": f"Scheduled command {schedule_id} executed successfully",
            "schedule_id": str(schedule_id),
        }

    except Exception as e:
        logger.error(f"Manual execution failed for schedule {schedule_id}: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Execution failed: {str(e)}",
            "schedule_id": str(schedule_id),
        }
