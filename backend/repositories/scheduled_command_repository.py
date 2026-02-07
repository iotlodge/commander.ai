"""
Scheduled Command repository for database operations
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, select, desc, and_, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.base import Base
from backend.models.scheduled_command_models import (
    ScheduledCommand,
    ScheduledCommandCreate,
    ScheduledCommandUpdate,
    ScheduledCommandExecution,
    ScheduledCommandExecutionCreate,
    ScheduledCommandExecutionUpdate,
    ScheduleType,
    IntervalUnit,
    ExecutionStatus,
)


class ScheduledCommandModel(Base):
    """SQLAlchemy model for scheduled_commands table"""

    __tablename__ = "scheduled_commands"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    # Command
    command_text = Column(Text, nullable=False)
    agent_id = Column(String(50), nullable=False)
    agent_nickname = Column(String(50), nullable=False)

    # Schedule
    schedule_type = Column(String(20), nullable=False)
    cron_expression = Column(String(100), nullable=True)
    interval_value = Column(Integer, nullable=True)
    interval_unit = Column(String(20), nullable=True)
    timezone = Column(String(50), nullable=False, server_default=text("'UTC'"))

    # Status
    enabled = Column(Boolean, nullable=False, server_default=text("true"), index=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True, index=True)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    last_run_status = Column(String(20), nullable=True)

    # Configuration
    max_retries = Column(Integer, nullable=False, server_default=text("3"))
    retry_delay_minutes = Column(Integer, nullable=False, server_default=text("5"))
    timeout_seconds = Column(Integer, nullable=False, server_default=text("300"))
    description = Column(Text, nullable=True)
    tags = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    meta_data = Column("metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    # Audit
    created_at = Column(DateTime, nullable=False, server_default=text("NOW()"))
    updated_at = Column(DateTime, nullable=False, server_default=text("NOW()"), onupdate=datetime.utcnow)


class ScheduledCommandExecutionModel(Base):
    """SQLAlchemy model for scheduled_command_executions table"""

    __tablename__ = "scheduled_command_executions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    scheduled_command_id = Column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    task_id = Column(PGUUID(as_uuid=True), nullable=True)

    triggered_at = Column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, server_default=text("'pending'"), index=True)

    result_summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, server_default=text("0"))
    execution_duration_ms = Column(Integer, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    llm_calls = Column(Integer, nullable=True)

    meta_data = Column("metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb"))


class ScheduledCommandRepository:
    """Data access layer for scheduled commands"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_scheduled_command(
        self, command: ScheduledCommandCreate
    ) -> ScheduledCommand:
        """Create new scheduled command"""
        # Get agent nickname from registry
        from backend.agents.base.agent_registry import AgentRegistry

        agent = AgentRegistry.get_specialist(command.agent_id)
        agent_nickname = agent.nickname if agent else command.agent_id

        from uuid import uuid4

        model = ScheduledCommandModel(
            id=str(uuid4()),  # Generate UUID as string for SQLite compatibility
            user_id=str(command.user_id) if isinstance(command.user_id, UUID) else command.user_id,
            command_text=command.command_text,
            agent_id=command.agent_id,
            agent_nickname=agent_nickname,
            schedule_type=command.schedule_type.value,
            cron_expression=command.cron_expression,
            interval_value=command.interval_value,
            interval_unit=command.interval_unit.value if command.interval_unit else None,
            timezone=command.timezone,
            enabled=command.enabled,
            max_retries=command.max_retries,
            retry_delay_minutes=command.retry_delay_minutes,
            timeout_seconds=command.timeout_seconds,
            description=command.description,
            tags=command.tags,
            meta_data=command.metadata,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)

        return self._model_to_pydantic(model)

    async def get_scheduled_command(self, command_id: UUID) -> ScheduledCommand | None:
        """Get scheduled command by ID"""
        # Convert UUID to string for SQLite compatibility
        id_value = str(command_id) if isinstance(command_id, UUID) else command_id
        stmt = select(ScheduledCommandModel).where(ScheduledCommandModel.id == id_value)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._model_to_pydantic(model)

    async def get_user_scheduled_commands(
        self,
        user_id: UUID,
        enabled_only: bool = False,
        agent_id: str | None = None,
    ) -> list[ScheduledCommand]:
        """Get scheduled commands for a user"""
        # Convert UUID to string for SQLite compatibility
        user_id_value = str(user_id) if isinstance(user_id, UUID) else user_id
        conditions = [ScheduledCommandModel.user_id == user_id_value]

        if enabled_only:
            conditions.append(ScheduledCommandModel.enabled == True)

        if agent_id:
            conditions.append(ScheduledCommandModel.agent_id == agent_id)

        stmt = (
            select(ScheduledCommandModel)
            .where(and_(*conditions))
            .order_by(desc(ScheduledCommandModel.created_at))
        )

        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._model_to_pydantic(m) for m in models]

    async def get_enabled_scheduled_commands(self) -> list[ScheduledCommand]:
        """Get all enabled scheduled commands (for scheduler initialization)"""
        stmt = (
            select(ScheduledCommandModel)
            .where(ScheduledCommandModel.enabled == True)
            .order_by(ScheduledCommandModel.next_run_at)
        )

        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._model_to_pydantic(m) for m in models]

    async def update_scheduled_command(
        self, command_id: UUID, command_update: ScheduledCommandUpdate
    ) -> ScheduledCommand | None:
        """Update scheduled command"""
        # Convert UUID to string for SQLite compatibility
        command_id_value = str(command_id) if isinstance(command_id, UUID) else command_id

        # Get existing command
        command = await self.get_scheduled_command(command_id)
        if not command:
            return None

        # Build update dict from non-None fields
        update_data = {"updated_at": datetime.utcnow()}

        if command_update.command_text is not None:
            update_data["command_text"] = command_update.command_text
        if command_update.schedule_type is not None:
            update_data["schedule_type"] = command_update.schedule_type.value
        if command_update.cron_expression is not None:
            update_data["cron_expression"] = command_update.cron_expression
        if command_update.interval_value is not None:
            update_data["interval_value"] = command_update.interval_value
        if command_update.interval_unit is not None:
            update_data["interval_unit"] = command_update.interval_unit.value
        if command_update.timezone is not None:
            update_data["timezone"] = command_update.timezone
        if command_update.enabled is not None:
            update_data["enabled"] = command_update.enabled
        if command_update.max_retries is not None:
            update_data["max_retries"] = command_update.max_retries
        if command_update.retry_delay_minutes is not None:
            update_data["retry_delay_minutes"] = command_update.retry_delay_minutes
        if command_update.timeout_seconds is not None:
            update_data["timeout_seconds"] = command_update.timeout_seconds
        if command_update.description is not None:
            update_data["description"] = command_update.description
        if command_update.tags is not None:
            update_data["tags"] = command_update.tags
        if command_update.metadata is not None:
            update_data["meta_data"] = command_update.metadata

        # Update the model
        from sqlalchemy import update
        stmt = (
            update(ScheduledCommandModel)
            .where(ScheduledCommandModel.id == command_id_value)
            .values(**update_data)
        )
        await self.session.execute(stmt)
        await self.session.commit()

        # Return updated command
        return await self.get_scheduled_command(command_id)

    async def update_next_run(
        self,
        command_id: UUID,
        next_run_at: datetime | None,
        last_run_at: datetime | None = None,
        last_run_status: ExecutionStatus | None = None,
    ) -> None:
        """Update next_run_at and optionally last_run_at"""
        from sqlalchemy import update

        # Convert UUID to string for SQLite compatibility
        command_id_value = str(command_id) if isinstance(command_id, UUID) else command_id

        update_data = {
            "next_run_at": next_run_at,
            "updated_at": datetime.utcnow(),
        }

        if last_run_at is not None:
            update_data["last_run_at"] = last_run_at
        if last_run_status is not None:
            update_data["last_run_status"] = last_run_status.value

        stmt = (
            update(ScheduledCommandModel)
            .where(ScheduledCommandModel.id == command_id_value)
            .values(**update_data)
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def delete_scheduled_command(self, command_id: UUID) -> bool:
        """Delete a scheduled command"""
        from sqlalchemy import delete

        # Convert UUID to string for SQLite compatibility
        command_id_value = str(command_id) if isinstance(command_id, UUID) else command_id

        stmt = delete(ScheduledCommandModel).where(ScheduledCommandModel.id == command_id_value)
        result = await self.session.execute(stmt)
        await self.session.commit()

        return result.rowcount > 0

    async def count_user_schedules(self, user_id: UUID) -> int:
        """Count total schedules for a user"""
        from sqlalchemy import func

        # Convert UUID to string for SQLite compatibility
        user_id_value = str(user_id) if isinstance(user_id, UUID) else user_id

        stmt = select(func.count()).select_from(ScheduledCommandModel).where(
            ScheduledCommandModel.user_id == user_id_value
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    # --- Execution tracking methods ---

    async def create_execution(
        self, execution: ScheduledCommandExecutionCreate
    ) -> ScheduledCommandExecution:
        """Create new execution record"""
        from uuid import uuid4

        model = ScheduledCommandExecutionModel(
            id=str(uuid4()),  # Generate UUID as string for SQLite compatibility
            scheduled_command_id=str(execution.scheduled_command_id) if isinstance(execution.scheduled_command_id, UUID) else execution.scheduled_command_id,
            task_id=str(execution.task_id) if execution.task_id and isinstance(execution.task_id, UUID) else execution.task_id,
            triggered_at=execution.triggered_at or datetime.utcnow(),
            status=ExecutionStatus.PENDING.value,
            retry_count=0,
            meta_data={},  # Initialize empty metadata
        )

        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)

        return self._execution_model_to_pydantic(model)

    async def get_execution(self, execution_id: UUID) -> ScheduledCommandExecution | None:
        """Get execution by ID"""
        # Convert UUID to string for SQLite compatibility
        execution_id_value = str(execution_id) if isinstance(execution_id, UUID) else execution_id

        stmt = select(ScheduledCommandExecutionModel).where(
            ScheduledCommandExecutionModel.id == execution_id_value
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._execution_model_to_pydantic(model)

    async def get_command_executions(
        self, command_id: UUID, limit: int = 50
    ) -> list[ScheduledCommandExecution]:
        """Get execution history for a scheduled command"""
        # Convert UUID to string for SQLite compatibility
        command_id_value = str(command_id) if isinstance(command_id, UUID) else command_id

        stmt = (
            select(ScheduledCommandExecutionModel)
            .where(ScheduledCommandExecutionModel.scheduled_command_id == command_id_value)
            .order_by(desc(ScheduledCommandExecutionModel.triggered_at))
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._execution_model_to_pydantic(m) for m in models]

    async def update_execution(
        self, execution_id: UUID, execution_update: ScheduledCommandExecutionUpdate
    ) -> ScheduledCommandExecution | None:
        """Update execution record"""
        # Convert UUID to string for SQLite compatibility
        execution_id_value = str(execution_id) if isinstance(execution_id, UUID) else execution_id

        # Build update dict
        update_data = {}

        if execution_update.task_id is not None:
            update_data["task_id"] = execution_update.task_id
        if execution_update.started_at is not None:
            update_data["started_at"] = execution_update.started_at
        if execution_update.completed_at is not None:
            update_data["completed_at"] = execution_update.completed_at
        if execution_update.status is not None:
            update_data["status"] = execution_update.status.value
        if execution_update.result_summary is not None:
            update_data["result_summary"] = execution_update.result_summary
        if execution_update.error_message is not None:
            update_data["error_message"] = execution_update.error_message
        if execution_update.retry_count is not None:
            update_data["retry_count"] = execution_update.retry_count
        if execution_update.execution_duration_ms is not None:
            update_data["execution_duration_ms"] = execution_update.execution_duration_ms
        if execution_update.tokens_used is not None:
            update_data["tokens_used"] = execution_update.tokens_used
        if execution_update.llm_calls is not None:
            update_data["llm_calls"] = execution_update.llm_calls
        if execution_update.metadata is not None:
            update_data["meta_data"] = execution_update.metadata

        if update_data:
            from sqlalchemy import update
            stmt = (
                update(ScheduledCommandExecutionModel)
                .where(ScheduledCommandExecutionModel.id == execution_id_value)
                .values(**update_data)
            )
            await self.session.execute(stmt)
            await self.session.commit()

        return await self.get_execution(execution_id)

    def _model_to_pydantic(self, model: ScheduledCommandModel) -> ScheduledCommand:
        """Convert SQLAlchemy model to Pydantic model"""
        return ScheduledCommand(
            id=model.id,
            user_id=model.user_id,
            command_text=model.command_text,
            agent_id=model.agent_id,
            agent_nickname=model.agent_nickname,
            schedule_type=ScheduleType(model.schedule_type),
            cron_expression=model.cron_expression,
            interval_value=model.interval_value,
            interval_unit=IntervalUnit(model.interval_unit) if model.interval_unit else None,
            timezone=model.timezone,
            enabled=model.enabled,
            next_run_at=model.next_run_at,
            last_run_at=model.last_run_at,
            last_run_status=ExecutionStatus(model.last_run_status) if model.last_run_status else None,
            max_retries=model.max_retries,
            retry_delay_minutes=model.retry_delay_minutes,
            timeout_seconds=model.timeout_seconds,
            description=model.description,
            tags=model.tags or [],
            metadata=model.meta_data or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _execution_model_to_pydantic(
        self, model: ScheduledCommandExecutionModel
    ) -> ScheduledCommandExecution:
        """Convert SQLAlchemy execution model to Pydantic model"""
        return ScheduledCommandExecution(
            id=model.id,
            scheduled_command_id=model.scheduled_command_id,
            task_id=model.task_id,
            triggered_at=model.triggered_at,
            started_at=model.started_at,
            completed_at=model.completed_at,
            status=ExecutionStatus(model.status),
            result_summary=model.result_summary,
            error_message=model.error_message,
            retry_count=model.retry_count,
            execution_duration_ms=model.execution_duration_ms,
            tokens_used=model.tokens_used,
            llm_calls=model.llm_calls,
            metadata=model.meta_data or {},
        )
