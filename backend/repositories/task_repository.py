"""
Task repository for database operations
"""
from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update, desc
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Text, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB

from backend.core.config import get_settings
from backend.models.task_models import AgentTask, TaskCreate, TaskUpdate, TaskStatus


Base = declarative_base()


class AgentTaskModel(Base):
    """SQLAlchemy model for agent_tasks table"""

    __tablename__ = "agent_tasks"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    user_id = Column(PGUUID(as_uuid=True), nullable=False)
    agent_id = Column(String(50), nullable=False)
    agent_nickname = Column(String(50), nullable=False)
    thread_id = Column(PGUUID(as_uuid=True), nullable=False)
    command_text = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, server_default="queued")
    progress_percentage = Column(Integer, server_default="0")
    current_node = Column(String(100), nullable=True)
    consultation_target_id = Column(String(50), nullable=True)
    consultation_target_nickname = Column(String(50), nullable=True)
    result = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    meta_data = Column("metadata", JSONB, server_default="{}")  # Renamed to avoid SQLAlchemy reserved name
    created_at = Column(DateTime, server_default="NOW()")
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


class TaskRepository:
    """Data access layer for agent tasks"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_task(self, task: TaskCreate) -> AgentTask:
        """Create new task in database"""
        # Get agent nickname from registry
        from backend.agents.base.agent_registry import AgentRegistry

        agent = AgentRegistry.get_specialist(task.agent_id)
        agent_nickname = agent.nickname if agent else task.agent_id

        model = AgentTaskModel(
            user_id=task.user_id,
            agent_id=task.agent_id,
            agent_nickname=agent_nickname,
            thread_id=task.thread_id,
            command_text=task.command_text,
            status=TaskStatus.QUEUED.value,
            progress_percentage=0,
            metadata={},
        )
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)

        return self._model_to_pydantic(model)

    async def get_task(self, task_id: UUID) -> AgentTask | None:
        """Get task by ID"""
        stmt = select(AgentTaskModel).where(AgentTaskModel.id == task_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._model_to_pydantic(model)

    async def get_user_tasks(self, user_id: UUID, limit: int = 50) -> list[AgentTask]:
        """Get tasks for a user (most recent first)"""
        stmt = (
            select(AgentTaskModel)
            .where(AgentTaskModel.user_id == user_id)
            .order_by(desc(AgentTaskModel.created_at))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._model_to_pydantic(m) for m in models]

    async def update_task(self, task_id: UUID, task_update: TaskUpdate) -> AgentTask:
        """Update task with partial data"""
        # Build update dict from non-None fields
        update_data = {}
        if task_update.status is not None:
            update_data["status"] = task_update.status.value
        if task_update.progress_percentage is not None:
            update_data["progress_percentage"] = task_update.progress_percentage
        if task_update.current_node is not None:
            update_data["current_node"] = task_update.current_node
        if task_update.consultation_target_id is not None:
            update_data["consultation_target_id"] = task_update.consultation_target_id
        if task_update.result is not None:
            update_data["result"] = task_update.result
        if task_update.error_message is not None:
            update_data["error_message"] = task_update.error_message

        if update_data:
            stmt = (
                update(AgentTaskModel)
                .where(AgentTaskModel.id == task_id)
                .values(**update_data)
            )
            await self.session.execute(stmt)
            await self.session.commit()

        # Return updated task
        return await self.get_task(task_id)

    async def update_progress(self, task_id: UUID, progress: int, current_node: str) -> None:
        """Update task progress and current node"""
        stmt = (
            update(AgentTaskModel)
            .where(AgentTaskModel.id == task_id)
            .values(progress_percentage=progress, current_node=current_node)
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def set_status(self, task_id: UUID, status: TaskStatus, **kwargs) -> None:
        """Update task status (with optional started_at/completed_at)"""
        update_data = {"status": status.value}

        # Add timestamp fields if provided
        if "started_at" in kwargs:
            update_data["started_at"] = kwargs["started_at"]
        if "completed_at" in kwargs:
            update_data["completed_at"] = kwargs["completed_at"]
        if "error_message" in kwargs:
            update_data["error_message"] = kwargs["error_message"]

        stmt = (
            update(AgentTaskModel)
            .where(AgentTaskModel.id == task_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def delete_tasks_by_status(self, user_id: UUID, status: TaskStatus) -> list[UUID]:
        """Delete all tasks with given status for a user, return deleted task IDs"""
        # Get task IDs before deletion
        stmt = select(AgentTaskModel.id).where(
            AgentTaskModel.user_id == user_id,
            AgentTaskModel.status == status.value
        )
        result = await self.session.execute(stmt)
        task_ids = [row[0] for row in result.fetchall()]

        # Delete tasks
        from sqlalchemy import delete as sql_delete
        stmt = sql_delete(AgentTaskModel).where(
            AgentTaskModel.user_id == user_id,
            AgentTaskModel.status == status.value
        )
        await self.session.execute(stmt)
        await self.session.commit()

        return task_ids

    def _model_to_pydantic(self, model: AgentTaskModel) -> AgentTask:
        """Convert SQLAlchemy model to Pydantic model"""
        return AgentTask(
            id=model.id,
            user_id=model.user_id,
            agent_id=model.agent_id,
            agent_nickname=model.agent_nickname,
            thread_id=model.thread_id,
            command_text=model.command_text,
            status=TaskStatus(model.status),
            progress_percentage=model.progress_percentage,
            current_node=model.current_node,
            consultation_target_id=model.consultation_target_id,
            consultation_target_nickname=model.consultation_target_nickname,
            result=model.result,
            error_message=model.error_message,
            metadata=model.meta_data or {},
            created_at=model.created_at,
            started_at=model.started_at,
            completed_at=model.completed_at,
        )


# Database session factory
_session_factory = None


def get_session_factory():
    """Get or create the session factory singleton"""
    global _session_factory
    if _session_factory is None:
        settings = get_settings()
        engine = create_async_engine(
            settings.database_url,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            echo=settings.app_debug,
        )
        _session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


async def get_db_session():
    """Dependency for getting database session"""
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session


async def get_task_repository(session: AsyncSession = None):
    """Dependency injection for TaskRepository"""
    if session is None:
        # Create a new session if not provided
        session_factory = get_session_factory()
        async with session_factory() as session:
            yield TaskRepository(session)
    else:
        yield TaskRepository(session)
