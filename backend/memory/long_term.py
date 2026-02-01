"""
Long-Term Memory (LTM) implementation using PostgreSQL
Provides persistent storage for agent memories and conversation history
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select, update, delete, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Text, DateTime, Integer, Float, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from backend.core.config import get_settings
from backend.memory.schemas import (
    ConversationMessage,
    AgentMemory,
    MemoryType,
    ConversationRole,
    CheckpointData,
)

Base = declarative_base()


class ConversationHistoryModel(Base):
    """SQLAlchemy model for conversation_history table"""

    __tablename__ = "conversation_history"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    user_id = Column(PGUUID(as_uuid=True), nullable=False)
    agent_id = Column(String(50), nullable=False)
    thread_id = Column(PGUUID(as_uuid=True), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    meta_data = Column("metadata", JSON, default={})  # Renamed to avoid SQLAlchemy reserved name
    created_at = Column(DateTime(timezone=True), server_default="CURRENT_TIMESTAMP")


class AgentMemoryModel(Base):
    """SQLAlchemy model for agent_memories table"""

    __tablename__ = "agent_memories"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    agent_id = Column(String(50), nullable=False)
    user_id = Column(PGUUID(as_uuid=True), nullable=True)
    memory_type = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    importance_score = Column(Float, default=0.5)
    access_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    meta_data = Column("metadata", JSON, default={})  # Renamed to avoid SQLAlchemy reserved name
    created_at = Column(DateTime(timezone=True), server_default="CURRENT_TIMESTAMP")


class AgentStateSnapshotModel(Base):
    """SQLAlchemy model for agent_state_snapshots table"""

    __tablename__ = "agent_state_snapshots"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    agent_id = Column(String(50), nullable=False)
    user_id = Column(PGUUID(as_uuid=True), nullable=False)
    thread_id = Column(PGUUID(as_uuid=True), nullable=False)
    checkpoint_id = Column(String(255), nullable=False, unique=True)
    state_data = Column(JSON, nullable=False)
    node_name = Column(String(100), nullable=True)
    parent_checkpoint_id = Column(String(255), nullable=True)
    meta_data = Column("metadata", JSON, default={})  # Renamed to avoid SQLAlchemy reserved name
    created_at = Column(DateTime(timezone=True), server_default="CURRENT_TIMESTAMP")


class LongTermMemory:
    """
    PostgreSQL-backed long-term memory for persistent conversation and agent memories
    """

    def __init__(self):
        self.settings = get_settings()
        self.engine = create_async_engine(
            self.settings.database_url,
            pool_size=self.settings.database_pool_size,
            max_overflow=self.settings.database_max_overflow,
            echo=self.settings.app_debug,
        )
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def save_conversation(self, message: ConversationMessage) -> UUID:
        """Save a conversation message to PostgreSQL"""
        async with self.async_session() as session:
            model = ConversationHistoryModel(
                user_id=message.user_id,
                agent_id=message.agent_id,
                thread_id=message.thread_id,
                role=message.role.value,
                content=message.content,
                metadata=message.metadata,
            )
            session.add(model)
            await session.commit()
            await session.refresh(model)
            return model.id

    async def get_conversation_history(
        self,
        user_id: UUID,
        agent_id: str,
        thread_id: UUID,
        limit: int = 50,
    ) -> list[ConversationMessage]:
        """Retrieve conversation history from PostgreSQL"""
        async with self.async_session() as session:
            stmt = (
                select(ConversationHistoryModel)
                .where(
                    and_(
                        ConversationHistoryModel.user_id == user_id,
                        ConversationHistoryModel.agent_id == agent_id,
                        ConversationHistoryModel.thread_id == thread_id,
                    )
                )
                .order_by(desc(ConversationHistoryModel.created_at))
                .limit(limit)
            )
            result = await session.execute(stmt)
            models = result.scalars().all()

            messages = [
                ConversationMessage(
                    id=m.id,
                    user_id=m.user_id,
                    agent_id=m.agent_id,
                    thread_id=m.thread_id,
                    role=ConversationRole(m.role),
                    content=m.content,
                    metadata=m.meta_data,
                    created_at=m.created_at,
                )
                for m in reversed(models)  # Reverse to get chronological order
            ]

            return messages

    async def save_memory(self, memory: AgentMemory) -> UUID:
        """Save an agent memory to PostgreSQL"""
        async with self.async_session() as session:
            model = AgentMemoryModel(
                agent_id=memory.agent_id,
                user_id=memory.user_id,
                memory_type=memory.memory_type.value,
                content=memory.content,
                importance_score=memory.importance_score,
                metadata=memory.metadata,
            )
            session.add(model)
            await session.commit()
            await session.refresh(model)
            return model.id

    async def update_memory_access(self, memory_id: UUID) -> None:
        """Update memory access count and timestamp"""
        async with self.async_session() as session:
            stmt = (
                update(AgentMemoryModel)
                .where(AgentMemoryModel.id == memory_id)
                .values(
                    access_count=AgentMemoryModel.access_count + 1,
                    last_accessed_at=datetime.now(),
                )
            )
            await session.execute(stmt)
            await session.commit()

    async def get_agent_memories(
        self,
        agent_id: str,
        user_id: UUID | None = None,
        memory_type: MemoryType | None = None,
        limit: int = 20,
    ) -> list[AgentMemory]:
        """Retrieve agent memories from PostgreSQL"""
        async with self.async_session() as session:
            conditions = [AgentMemoryModel.agent_id == agent_id]

            if user_id is not None:
                conditions.append(AgentMemoryModel.user_id == user_id)

            if memory_type is not None:
                conditions.append(AgentMemoryModel.memory_type == memory_type.value)

            stmt = (
                select(AgentMemoryModel)
                .where(and_(*conditions))
                .order_by(desc(AgentMemoryModel.importance_score))
                .limit(limit)
            )

            result = await session.execute(stmt)
            models = result.scalars().all()

            memories = [
                AgentMemory(
                    id=m.id,
                    agent_id=m.agent_id,
                    user_id=m.user_id,
                    memory_type=MemoryType(m.memory_type),
                    content=m.content,
                    importance_score=m.importance_score,
                    access_count=m.access_count,
                    last_accessed_at=m.last_accessed_at,
                    metadata=m.meta_data,
                    created_at=m.created_at,
                )
                for m in models
            ]

            return memories

    async def save_checkpoint_persistent(self, checkpoint: CheckpointData) -> UUID:
        """Save checkpoint to PostgreSQL for long-term persistence"""
        async with self.async_session() as session:
            model = AgentStateSnapshotModel(
                agent_id=checkpoint.agent_id,
                user_id=checkpoint.user_id,
                thread_id=checkpoint.thread_id,
                checkpoint_id=checkpoint.checkpoint_id,
                state_data=checkpoint.state_data,
                node_name=checkpoint.node_name,
                parent_checkpoint_id=checkpoint.parent_checkpoint_id,
                metadata=checkpoint.metadata,
            )
            session.add(model)
            await session.commit()
            await session.refresh(model)
            return model.id

    async def get_latest_checkpoint(
        self, agent_id: str, user_id: UUID, thread_id: UUID
    ) -> CheckpointData | None:
        """Get the most recent checkpoint for a thread"""
        async with self.async_session() as session:
            stmt = (
                select(AgentStateSnapshotModel)
                .where(
                    and_(
                        AgentStateSnapshotModel.agent_id == agent_id,
                        AgentStateSnapshotModel.user_id == user_id,
                        AgentStateSnapshotModel.thread_id == thread_id,
                    )
                )
                .order_by(desc(AgentStateSnapshotModel.created_at))
                .limit(1)
            )

            result = await session.execute(stmt)
            model = result.scalar_one_or_none()

            if not model:
                return None

            return CheckpointData(
                checkpoint_id=model.checkpoint_id,
                agent_id=model.agent_id,
                user_id=model.user_id,
                thread_id=model.thread_id,
                state_data=model.state_data,
                node_name=model.node_name,
                parent_checkpoint_id=model.parent_checkpoint_id,
                metadata=model.meta_data,
                created_at=model.created_at,
            )
