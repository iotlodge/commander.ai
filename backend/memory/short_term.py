"""
Short-Term Memory (STM) implementation using Redis
Provides fast access to recent conversation context and temporary state
"""

import json
from datetime import datetime
from typing import Any
from uuid import UUID

import redis.asyncio as redis
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint, CheckpointMetadata

from backend.core.config import get_settings
from backend.memory.schemas import ConversationMessage, CheckpointData


class ShortTermMemory:
    """
    Redis-backed short-term memory for recent conversations and active state
    """

    def __init__(self, redis_client: redis.Redis | None = None):
        self.settings = get_settings()
        self.redis = redis_client
        self._connected = False

    async def connect(self) -> None:
        """Establish Redis connection"""
        if not self.redis:
            self.redis = await redis.from_url(
                self.settings.redis_url,
                max_connections=self.settings.redis_max_connections,
                decode_responses=True,
            )
        self._connected = True

    async def disconnect(self) -> None:
        """Close Redis connection"""
        if self.redis:
            await self.redis.aclose()
            self._connected = False

    def _conversation_key(self, user_id: UUID, agent_id: str, thread_id: UUID) -> str:
        """Generate Redis key for conversation history"""
        return f"conversation:{user_id}:{agent_id}:{thread_id}"

    def _checkpoint_key(self, checkpoint_id: str) -> str:
        """Generate Redis key for checkpoint"""
        return f"checkpoint:{checkpoint_id}"

    async def save_message(
        self,
        user_id: UUID,
        agent_id: str,
        thread_id: UUID,
        message: ConversationMessage,
    ) -> None:
        """Save a conversation message to Redis with TTL"""
        key = self._conversation_key(user_id, agent_id, thread_id)
        message_json = message.model_dump_json()

        # Use Redis list to store conversation chronologically
        await self.redis.rpush(key, message_json)

        # Set TTL on the key
        await self.redis.expire(key, self.settings.stm_ttl_seconds)

    async def get_conversation_context(
        self,
        user_id: UUID,
        agent_id: str,
        thread_id: UUID,
        limit: int = 20,
    ) -> list[ConversationMessage]:
        """Retrieve recent conversation messages from Redis"""
        key = self._conversation_key(user_id, agent_id, thread_id)

        # Get last N messages
        messages_json = await self.redis.lrange(key, -limit, -1)

        messages = [ConversationMessage.model_validate_json(msg) for msg in messages_json]

        return messages

    async def save_checkpoint(self, checkpoint_data: CheckpointData) -> None:
        """Save a LangGraph checkpoint to Redis"""
        key = self._checkpoint_key(checkpoint_data.checkpoint_id)
        data_json = checkpoint_data.model_dump_json()

        # Save with TTL
        await self.redis.setex(
            key,
            self.settings.stm_ttl_seconds,
            data_json,
        )

    async def load_checkpoint(self, checkpoint_id: str) -> CheckpointData | None:
        """Load a checkpoint from Redis"""
        key = self._checkpoint_key(checkpoint_id)
        data_json = await self.redis.get(key)

        if not data_json:
            return None

        return CheckpointData.model_validate_json(data_json)

    async def clear_conversation(self, user_id: UUID, agent_id: str, thread_id: UUID) -> None:
        """Clear conversation history for a thread"""
        key = self._conversation_key(user_id, agent_id, thread_id)
        await self.redis.delete(key)


class RedisCheckpointSaver(BaseCheckpointSaver):
    """
    LangGraph checkpoint saver using Redis for short-term state persistence
    """

    def __init__(self, stm: ShortTermMemory):
        super().__init__()
        self.stm = stm

    async def aget(self, config: RunnableConfig) -> tuple[Checkpoint, CheckpointMetadata] | None:
        """Get checkpoint from Redis"""
        checkpoint_id = config.get("configurable", {}).get("checkpoint_id")
        if not checkpoint_id:
            return None

        checkpoint_data = await self.stm.load_checkpoint(checkpoint_id)
        if not checkpoint_data:
            return None

        # Convert to LangGraph Checkpoint format
        checkpoint = Checkpoint(
            v=1,
            ts=checkpoint_data.created_at.isoformat() if checkpoint_data.created_at else None,
            id=checkpoint_data.checkpoint_id,
            channel_values=checkpoint_data.state_data,
        )

        metadata = CheckpointMetadata(source="redis", step=0, writes={}, parents={})

        return (checkpoint, metadata)

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
    ) -> RunnableConfig:
        """Save checkpoint to Redis"""
        checkpoint_id = checkpoint.id or str(UUID.uuid4())

        checkpoint_data = CheckpointData(
            checkpoint_id=checkpoint_id,
            agent_id=config.get("configurable", {}).get("agent_id", "unknown"),
            user_id=UUID(config.get("configurable", {}).get("user_id")),
            thread_id=UUID(config.get("configurable", {}).get("thread_id")),
            state_data=checkpoint.channel_values,
            node_name=metadata.get("node_name"),
            metadata=metadata,
        )

        await self.stm.save_checkpoint(checkpoint_data)

        return {
            "configurable": {
                **config.get("configurable", {}),
                "checkpoint_id": checkpoint_id,
            }
        }
